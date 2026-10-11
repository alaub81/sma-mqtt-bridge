"""Offline two-stage planning and independently gated portal protocol checks."""

import asyncio
import json
import tempfile
import unittest
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

from sma_mqtt_bridge.adapters.portal import PortalReader
from sma_mqtt_bridge.commands import LocalCommands
from sma_mqtt_bridge.config import load_config
from sma_mqtt_bridge.errors import ConfigError, ProtocolError
from sma_mqtt_bridge.model import Property, SourceState
from sma_mqtt_bridge.portal_commands import CommandRouter, PortalCommands

ENERGY = "Parameter.Chrg.Plan.En"
END = "Parameter.Chrg.Plan.StopTm"
MODE = "Parameter.Chrg.ActChaMod"


def parameters(energy="0", end="0", mode="4719"):
    return {
        "Parameter.Nameplate.ModelStr": {"value": "EVC22-3AC-20"},
        "Parameter.Nameplate.PkgRev": {"value": "2.6.37.R"},
        "Parameter.Nameplate.SerNum": {"value": "123"},
        ENERGY: {"value": energy, "editable": True, "state": "Confirmed", "min": 0, "max": 100},
        END: {"value": end, "editable": True, "state": "Confirmed", "min": 0},
        MODE: {
            "value": mode,
            "editable": True,
            "state": "Confirmed",
            "possibleValues": ["4718", "4719", "4720", "4721"],
        },
    }


def device(pv=60, **options):
    return {
        "plantId": "plant-fixture",
        "deviceId": "device-fixture",
        "productTagId": 19143,
        "consumerTypes": ["EVehicle"],
        "_links": {"ui_Edit_OptionalEnergyDemand": []},
        "optionalEnergyDemand": {
            "isOptionalConsumer": True,
            "minPvPercentage": pv,
            "pvSurplusOnly": None,
            "usePriceLimit": False,
            "priceLimit": 0.35,
            "feedInLimitation": {"untouched": True},
            **options,
        },
    }


class WriteTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        cfg = load_config({"SMAB_STATE_DIR": self.tmp.name})
        self.config = replace(
            cfg,
            commands=replace(
                cfg.commands,
                enabled=True,
                readback_timeout_seconds=0.02,
                readback_interval_seconds=0.001,
            ),
            echarger=replace(
                cfg.echarger, enabled=True, commands_enabled=True, expected_serial="123"
            ),
            portal=replace(
                cfg.portal,
                enabled=True,
                commands_enabled=True,
                plant_id="plant-fixture",
                device_id="device-fixture",
            ),
        )
        self.api = SourceState(
            "api",
            "sma-echarger",
            (
                Property("settings", "plan-energy", "Energy", "float", "kWh"),
                Property("settings", "plan-end", "End", "string"),
                Property("settings", "charge-mode", "Mode", "enum", format="4718,4719,4720,4721"),
            ),
            180,
        )
        self.portal = SourceState("portal", "sma-echarger", PortalReader.properties, 180)
        self.results = SourceState(
            "commands",
            "sma-echarger",
            (
                Property("commands", "local-result", "Local", "string"),
                Property("commands", "portal-result", "Portal", "string"),
                Property("commands", "plan", "Plan", "string"),
            ),
            180,
        )
        self.local = LocalCommands(self.config, self.api, self.results)
        self.cloud = PortalCommands(self.config, self.portal, self.results)
        self.addAsyncCleanup(self.local.close)
        self.addAsyncCleanup(self.cloud.close)
        for reader in (self.local.reader, self.cloud.reader):
            reader.access_token = AsyncMock(return_value="fixture-token")
            reader.http.request = AsyncMock(return_value=(204, {}, ""))
        self.end = (datetime.now(timezone.utc) + timedelta(hours=2)).replace(microsecond=0)
        self.seconds = str(int(self.end.timestamp()))
        self.payload = json.dumps({"energyKWh": 12.5, "endTime": self.end.isoformat()}).encode()
        self.initial = parameters()
        self.confirmed = parameters("12.5", self.seconds)
        self.active = parameters("12.5", self.seconds, "4720")
        # Exercise the actual identity parser on every local catalog read.
        self.local.reader.http.get_json = AsyncMock(
            side_effect=[self.reply(p) for p in (self.initial, self.confirmed, self.active)]
        )
        self.cloud.reader.read_device = AsyncMock(side_effect=[device(), device(75)])

    def reply(self, catalog):
        return [
            {
                "componentId": "IGULD:SELF",
                "values": [{"channelId": c, **v} for c, v in catalog.items()],
            }
        ]

    def status(self, source="local"):
        return self.results.fresh_values()["commands/" + source + "-result"]

    async def test_plan_confirmed_before_separate_mode_put(self):
        phases = []

        async def write(method, url, **kwargs):
            phases.append(kwargs["json"]["values"])
            if len(phases) == 2:
                self.assertEqual(self.local.reader.http.get_json.await_count, 2)
                self.assertEqual(phases[1][0]["channelId"], MODE)
                self.assertTrue(self.local.journal.exists())
                saved = json.loads(self.local.journal.read_text())
                self.assertEqual(saved["phase"], "mode")
            return 200, {}, ""

        self.local.reader.http.request.side_effect = write
        await self.local.handle("plan", self.payload)
        self.assertEqual(len(phases), 2)
        self.assertEqual(
            [(v["channelId"], v["value"]) for v in phases[0]],
            [(ENERGY, "12.5"), (END, self.seconds)],
        )
        self.assertEqual(phases[0][0]["timestamp"], phases[0][1]["timestamp"])
        self.assertEqual(phases[1][0]["value"], "4720")
        self.assertEqual(self.status(), "confirmed")
        self.assertEqual(self.api.fresh_values()["settings/charge-mode"], "4720")
        self.assertFalse(self.local.journal.exists())
        self.assertEqual(
            json.loads(self.results.fresh_values()["commands/plan"])["energyKWh"], 12.5
        )

    async def test_partial_or_pending_plan_never_activates_target_mode(self):
        for change in (
            {END: {"value": "0"}},
            {ENERGY: {"state": "Pending"}},
            {END: {"unit": "ms"}},
            {ENERGY: {"unit": "Wh"}},
        ):
            partial = deepcopy(self.confirmed)
            for key, fields in change.items():
                partial[key].update(fields)
            self.local.reader.http.get_json.side_effect = None
            reads = 0

            async def read(*args, **kwargs):
                nonlocal reads
                reads += 1
                return self.reply(self.initial if reads == 1 else partial)

            self.local.reader.http.get_json.side_effect = read
            await self.local.handle("plan", self.payload)
            self.assertEqual(self.status(), "uncertain")
            self.local.reader.http.request.assert_awaited_once()
            self.assertTrue(self.local.journal.exists())
            self.assertEqual(self.api.fresh_values(), {})
            self.local.journal.unlink()  # Isolated fixture reset, never runtime recovery.
            self.local.reader.http.request.reset_mock()

    async def test_mode_readback_with_wrong_plan_units_remains_uncertain(self):
        invalid = deepcopy(self.active)
        invalid[END]["unit"] = "ms"
        reads = 0

        async def read(*args, **kwargs):
            nonlocal reads
            reads += 1
            return self.reply(
                self.initial if reads == 1 else self.confirmed if reads == 2 else invalid
            )

        self.local.reader.http.get_json.side_effect = read
        await self.local.handle("plan", self.payload)
        self.assertEqual(self.status(), "uncertain")
        self.assertEqual(self.local.reader.http.request.await_count, 2)
        self.assertTrue(self.local.journal.exists())
        self.assertEqual(self.api.fresh_values(), {})
        self.assertNotIn("commands/plan", self.results.fresh_values())

    async def test_mode_loss_keeps_plan_guard_across_restart(self):
        self.local.reader.http.request.side_effect = [
            (200, {}, ""),
            ProtocolError("fixture response lost"),
        ]
        await self.local.handle("plan", self.payload)
        self.assertEqual(self.status(), "uncertain")
        self.assertEqual(self.local.reader.http.request.await_count, 2)
        self.assertEqual(self.local.journal.stat().st_mode & 0o777, 0o600)
        newer = LocalCommands(self.config, self.api, self.results)
        try:
            newer.catalog = AsyncMock()
            await newer.handle("plan", self.payload)
            self.assertEqual(self.status(), "blocked-uncertain")
            newer.catalog.assert_not_awaited()
        finally:
            await newer.close()

    async def test_invalid_plan_payload_rejected_before_device_io(self):
        for plan in (
            {"energyKWh": 0, "endTime": self.end.isoformat()},
            {"energyKWh": True, "endTime": self.end.isoformat()},
            {"energyKWh": 10, "endTime": "2030-01-01T12:00:00"},
            {"energyKWh": 10, "endTime": "2000-01-01T12:00:00Z"},
            {"energyKWh": 10, "endTime": self.end.isoformat(), "activate": True},
        ):
            await self.local.handle("plan", json.dumps(plan).encode())
            self.assertEqual(self.status(), "rejected")
        for data in (
            b'{"energyKWh":NaN,"endTime":"2030-01-01T12:00:00Z"}',
            b'{"energyKWh":10,"energyKWh":20,"endTime":"2030-01-01T12:00:00Z"}',
            b"x" * 513,
        ):
            await self.local.handle("plan", data)
        self.local.reader.http.get_json.assert_not_awaited()
        self.local.reader.http.request.assert_not_awaited()

    async def test_plan_units_bounds_identity_and_rights_fail_closed(self):
        cases = [
            (ENERGY, {"unit": "Wh"}),
            (ENERGY, {"max": 5}),
            (ENERGY, {"editable": False}),
            (ENERGY, {"min": "invalid"}),
            (END, {"unit": "ms"}),
            (END, {"max": 1}),
            (END, {"state": "Pending"}),
            (MODE, {"possibleValues": ["4719"]}),
            ("Parameter.Nameplate.SerNum", {"value": "999"}),
            ("Parameter.Nameplate.PkgRev", {"value": "unknown"}),
        ]
        for key, fields in cases:
            with self.subTest(key=key, fields=fields):
                invalid = deepcopy(self.initial)
                invalid[key].update(fields)
                self.local.reader.http.get_json.side_effect = None
                self.local.reader.http.get_json.return_value = self.reply(invalid)
                await self.local.handle("plan", self.payload)
                self.assertEqual(self.status(), "rejected")
                self.local.reader.http.request.assert_not_awaited()

    async def test_plan_equality_and_already_active_plan(self):
        self.local.reader.http.get_json.side_effect = [self.reply(self.active)]
        await self.local.handle("plan", self.payload)
        self.assertEqual(self.status(), "already-confirmed")
        self.local.reader.http.request.assert_not_awaited()
        self.local.reader.http.get_json.side_effect = [self.reply(parameters("1", "0", "4720"))]
        await self.local.handle("plan", self.payload)
        self.assertEqual(self.status(), "rejected")
        self.local.reader.http.request.assert_not_awaited()

    async def test_confirmed_plan_only_needs_mode_write(self):
        self.local.reader.http.get_json.side_effect = [
            self.reply(self.confirmed),
            self.reply(self.active),
        ]
        await self.local.handle("plan", self.payload)
        self.local.reader.http.request.assert_awaited_once()
        values = self.local.reader.http.request.call_args.kwargs["json"]["values"]
        self.assertEqual([(v["channelId"], v["value"]) for v in values], [(MODE, "4720")])
        self.assertEqual(self.status(), "confirmed")

    async def test_recheck_rights_and_end_before_activation(self):
        invalid = deepcopy(self.confirmed)
        invalid[MODE]["editable"] = False
        self.local.reader.http.get_json.side_effect = [
            self.reply(self.initial),
            self.reply(invalid),
        ]
        await self.local.handle("plan", self.payload)
        self.assertEqual(self.status(), "uncertain")
        self.local.reader.http.request.assert_awaited_once()
        self.local.journal.unlink()
        self.local.reader.http.request.reset_mock()
        self.local.reader.http.get_json.side_effect = [
            self.reply(self.initial),
            self.reply(self.confirmed),
        ]
        import sma_mqtt_bridge.commands as commands

        real_datetime = datetime

        class Clock:
            fromisoformat = staticmethod(real_datetime.fromisoformat)
            fromtimestamp = staticmethod(real_datetime.fromtimestamp)
            calls = 0

            @classmethod
            def now(cls, tz):
                cls.calls += 1
                return self.end + timedelta(seconds=1) if cls.calls >= 4 else real_datetime.now(tz)

        with patch.object(commands, "datetime", Clock):
            await self.local.handle("plan", self.payload)
        self.assertEqual(self.status(), "uncertain")
        self.local.reader.http.request.assert_awaited_once()

    async def test_portal_exact_payload_preserves_options_and_readback(self):
        await self.cloud.handle("pv-minimum", b"75")
        self.cloud.reader.http.request.assert_awaited_once()
        args, kwargs = self.cloud.reader.http.request.call_args
        self.assertEqual(args, ("PUT", self.cloud.reader.device_url() + "/optionalenergydemand"))
        self.assertEqual(
            kwargs["json"],
            {
                "minPvPercentage": 75,
                "pvSurplusOnly": None,
                "usePriceLimit": False,
                "priceLimit": 0.35,
            },
        )
        self.assertEqual(self.status("portal"), "confirmed")
        self.assertEqual(self.portal.fresh_values()["portal/grid-share"], "25")
        self.assertFalse(self.cloud.journal.exists())

    async def test_portal_special_modes_permissions_and_identity_never_write(self):
        bad = [
            device(usePriceLimit=True),
            device(pvSurplusOnly=True),
            device() | {"_links": {}},
            device() | {"deviceId": "wrong"},
            device() | {"plantId": "wrong"},
            device() | {"productTagId": 0},
            device() | {"consumerTypes": ["other"]},
            device(isOptionalConsumer=False),
        ]
        missing = device()
        del missing["optionalEnergyDemand"]["priceLimit"]
        bad.append(missing)
        for reply in bad:
            self.cloud.reader.read_device.side_effect = None
            self.cloud.reader.read_device.return_value = reply
            await self.cloud.handle("pv-minimum", b"75")
            self.assertEqual(self.status("portal"), "rejected")
        self.cloud.reader.http.request.assert_not_awaited()

    async def test_portal_http_success_does_not_confirm_changed_other_options(self):
        self.cloud.reader.read_device.side_effect = None
        count = 0

        async def read():
            nonlocal count
            count += 1
            return device() if count == 1 else device(75, priceLimit=0.40)

        self.cloud.reader.read_device.side_effect = read
        await self.cloud.handle("pv-minimum", b"75")
        self.assertEqual(self.status("portal"), "uncertain")
        self.cloud.reader.http.request.assert_awaited_once()
        self.assertTrue(self.cloud.journal.exists())
        self.assertEqual(self.portal.fresh_values(), {})

    async def test_portal_lost_response_and_cancel_never_retry(self):
        for failure in (ProtocolError("fixture lost"), asyncio.CancelledError()):
            self.cloud.reader.read_device.side_effect = None
            self.cloud.reader.read_device.return_value = device()
            self.cloud.reader.http.request.side_effect = failure
            if isinstance(failure, asyncio.CancelledError):
                with self.assertRaises(asyncio.CancelledError):
                    await self.cloud.handle("pv-minimum", b"75")
            else:
                await self.cloud.handle("pv-minimum", b"75")
            self.assertEqual(self.status("portal"), "uncertain")
            self.cloud.reader.http.request.assert_awaited_once()
            newer = PortalCommands(self.config, self.portal, self.results)
            newer.reader.read_device = AsyncMock()
            try:
                await newer.handle("pv-minimum", b"75")
                self.assertEqual(self.status("portal"), "blocked-uncertain")
                newer.reader.read_device.assert_not_awaited()
            finally:
                await newer.close()
            self.cloud.journal.unlink()
            self.cloud.reader.http.request.reset_mock()

    async def test_portal_retained_malformed_disabled_busy_and_equal(self):
        await self.cloud.handle("pv-minimum", b"75", retained=True)
        self.assertEqual(self.status("portal"), "rejected-retained")
        for payload in (b"75.0", b"-1", b"101", b" 75", b"075", b"\xff"):
            await self.cloud.handle("pv-minimum", payload)
            self.assertEqual(self.status("portal"), "rejected")
        self.cloud.reader.read_device.assert_not_awaited()
        self.cloud.config = replace(
            self.config, portal=replace(self.config.portal, commands_enabled=False)
        )
        await self.cloud.handle("pv-minimum", b"75")
        self.assertEqual(self.status("portal"), "rejected-disabled")
        self.cloud.config = self.config
        async with self.cloud.lock:
            await self.cloud.handle("pv-minimum", b"75")
            self.assertEqual(self.status("portal"), "rejected-busy")
        self.cloud.reader.read_device.side_effect = [device(75)]
        await self.cloud.handle("pv-minimum", b"75")
        self.assertEqual(self.status("portal"), "already-confirmed")
        self.cloud.reader.http.request.assert_not_awaited()

    async def test_portal_only_runtime_does_not_activate_local_api_or_write(self):
        from sma_mqtt_bridge.runtime import run

        cfg = replace(
            self.config,
            echarger=replace(self.config.echarger, enabled=False, commands_enabled=False),
            runtime=replace(self.config.runtime, health_interval_seconds=0.001),
        )
        self.cloud.reader.read = AsyncMock(return_value={})
        stop = asyncio.Event()
        captured = []

        class Publisher:
            status = {}

            def __init__(self, config, states):
                captured.append(self)
                self.states = states

            async def run(self, stop):
                await asyncio.sleep(0.01)
                stop.set()

        with patch(
            "sma_mqtt_bridge.runtime.sources", return_value=[(self.portal, self.cloud.reader, 0)]
        ):
            self.portal.properties = self.cloud.reader.properties
            await run(cfg, stop=stop, publisher_factory=Publisher)
        controller = captured[0].command_controller
        self.assertIsInstance(controller, CommandRouter)
        self.assertIsNone(controller.local)
        self.assertIs(controller.portal.reader, self.cloud.reader)
        self.assertTrue(next(p for p in self.portal.properties if p.id == "pv-minimum").settable)
        self.assertFalse(next(p for p in self.portal.properties if p.id == "grid-share").settable)
        self.cloud.reader.read.assert_not_awaited()
        self.cloud.reader.http.request.assert_not_awaited()
        self.assertFalse(Path(self.tmp.name, "portal-command-pending.json").exists())

    def test_independent_portal_config_switches(self):
        env = {
            "SMAB_PORTAL_ENABLED": "true",
            "SMAB_PORTAL_COMMANDS_ENABLED": "true",
            "SMAB_COMMANDS_ENABLED": "true",
            "SMAB_PORTAL_USERNAME": "fixture",
            "SMAB_PORTAL_PASSWORD": "fixture",
            "SMAB_PORTAL_PLANT_ID": "plant-fixture",
            "SMAB_PORTAL_DEVICE_ID": "device-fixture",
            "SMAB_MQTT_HOST": "fixture.invalid",
            "SMAB_MQTT_TLS": "false",
        }
        cfg = load_config(env)
        self.assertTrue(cfg.portal.commands_enabled)
        self.assertFalse(cfg.echarger.enabled)
        self.assertFalse(cfg.echarger.commands_enabled)
        self.assertEqual(cfg.portal.poll_interval_seconds, 0)
        with self.assertRaises(ConfigError):
            load_config(env | {"SMAB_PORTAL_ENABLED": "false"})
        cfg = load_config(env | {"SMAB_COMMANDS_ENABLED": "false"})
        self.assertFalse(cfg.commands.enabled)
