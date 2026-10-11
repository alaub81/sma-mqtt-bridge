"""Power-limit mapping, live metadata guards and confirmed command readback."""

import tempfile
import unittest
from dataclasses import replace
from unittest.mock import AsyncMock

from sma_mqtt_bridge.adapters.echarger import EChargerReader, SempReader, settings_values
from sma_mqtt_bridge.commands import LocalCommands, command_target
from sma_mqtt_bridge.config import ECharger, load_config
from sma_mqtt_bridge.errors import ProtocolError
from sma_mqtt_bridge.homie import discovery
from sma_mqtt_bridge.model import Property, SourceState
from sma_mqtt_bridge.translation import load_translation

CHANNEL = "Parameter.Inverter.WMaxIn"
KEY = "settings/max-charge-power"


def catalog(value="11000", **changes):
    return {
        "Parameter.Nameplate.ModelStr": {"value": "EVC22-3AC-20"},
        "Parameter.Nameplate.PkgRev": {"value": "2.6.37.R"},
        CHANNEL: {"value": value, "editable": True, "state": "Confirmed", "min": 4500, "max": 22000}
        | changes,
        # A different output-power parameter must never be written as a fallback.
        "Parameter.Inverter.WMax": {"value": "22000", "editable": True, "state": "Confirmed"},
    }


class PowerMetadataTests(unittest.TestCase):
    def test_mapping_bounds_and_whole_watt_payload(self):
        for target in ("4500", "11000", "22000"):
            self.assertEqual(
                command_target("max-charge-power", target, catalog()), (CHANNEL, target)
            )
        for target in (
            "4000",
            "4499",
            "22001",
            "4",
            "4 kW",
            "4500.5",
            "4500.0",
            " 4500",
            "+4500",
            "04500",
            "NaN",
            "Infinity",
            "4.5e3",
            "４５００",
        ):
            with self.subTest(target=target), self.assertRaises(ProtocolError):
                command_target("max-charge-power", target, catalog())

    def test_rights_units_and_malformed_bounds_fail_closed(self):
        for changes in (
            {"editable": False},
            {"state": "Pending"},
            {"unit": "kW"},
            {"unit": ""},
            {"min": None},
            {"max": None},
            {"min": True},
            {"max": "NaN"},
            {"min": 23000},
            {"min": 0},
            {"max": 30000},
            {"step": 0},
            {"step": "NaN"},
            {"possibleValues": ["11000"]},
            {"possibleValues": "4500"},
        ):
            with self.subTest(changes=changes), self.assertRaises(ProtocolError):
                command_target("max-charge-power", "4500", catalog(**changes))
        self.assertEqual(command_target("max-charge-power", "5000", catalog(step=100))[1], "5000")
        with self.assertRaises(ProtocolError):
            command_target("max-charge-power", "5000", catalog(step=1000))
        missing = catalog()
        del missing[CHANNEL]
        with self.assertRaises(ProtocolError):
            command_target("max-charge-power", "4500", missing)

    def test_firmware_scoped_unit_and_confirmed_observations(self):
        self.assertEqual(settings_values(catalog())[KEY], 11000)
        for c in (
            catalog(state="Pending"),
            catalog(unit="kW"),
            catalog(value="11000.5"),
            catalog() | {"Parameter.Nameplate.PkgRev": {"value": "unknown"}},
            catalog() | {"Parameter.Nameplate.ModelStr": {"value": "other"}},
        ):
            self.assertIsNone(settings_values(c)[KEY])
        unknown = catalog() | {"Parameter.Nameplate.PkgRev": {"value": "unknown"}}
        with self.assertRaises(ProtocolError):
            command_target("max-charge-power", "4500", unknown)
        unknown[CHANNEL]["unit"] = "W"
        self.assertEqual(command_target("max-charge-power", "4500", unknown)[1], "4500")
        self.assertNotIn(KEY, settings_values(catalog(), from_api=False))

    def test_api_ownership_and_translated_integer_channel(self):
        api = EChargerReader(ECharger(), 4096)
        prop = next(p for p in api.properties if p.key == KEY)
        self.assertFalse(prop.settable)
        self.assertNotIn(KEY, {p.key for p in SempReader(ECharger(), 4096).properties})
        metadata = discovery(
            "homie",
            "sma-echarger",
            (replace(prop, settable=True),),
            load_translation("de", "/nonexistent-smab-translation-fixture"),
        )
        root = "homie/sma-echarger/settings/maxchargepower/"
        self.assertEqual(metadata[root + "$name"], "Maximale Ladeleistung")
        self.assertEqual(metadata[root + "$datatype"], "integer")
        self.assertEqual(metadata[root + "$unit"], "W")
        self.assertEqual(metadata[root + "$settable"], "true")


class PowerCommandTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        c = load_config({"SMAB_STATE_DIR": self.tmp.name})
        self.config = replace(
            c,
            echarger=replace(c.echarger, enabled=True, commands_enabled=True),
            commands=replace(
                c.commands,
                enabled=True,
                readback_timeout_seconds=0.02,
                readback_interval_seconds=0.001,
            ),
        )
        self.api = SourceState(
            "api",
            "sma-echarger",
            (Property("settings", "max-charge-power", "Max Charge Power", "integer", "W"),),
            180,
        )
        self.result = SourceState(
            "commands",
            "sma-echarger",
            (Property("commands", "local-result", "Result", "string"),),
            180,
        )
        self.controller = LocalCommands(self.config, self.api, self.result)
        self.controller.catalog = AsyncMock(side_effect=[catalog(), catalog(value="4500.0")])
        self.controller.reader.access_token = AsyncMock(return_value="fixture-token")
        self.controller.reader.http.request = AsyncMock(return_value=(200, {}, ""))
        self.addAsyncCleanup(self.controller.close)

    def status(self):
        return self.result.fresh_values()["commands/local-result"]

    async def test_single_parameter_put_and_numeric_confirmed_readback(self):
        await self.controller.handle("max-charge-power", b"4500")
        request = self.controller.reader.http.request
        request.assert_awaited_once()
        values = request.call_args.kwargs["json"]["values"]
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0]["channelId"], CHANNEL)
        self.assertEqual(values[0]["value"], "4500")
        self.assertEqual(self.status(), "confirmed")
        self.assertEqual(self.api.fresh_values()[KEY], "4500")
        self.assertFalse(self.controller.journal.exists())

    async def test_4000_retained_and_disabled_never_write(self):
        await self.controller.handle("max-charge-power", b"4000")
        self.assertEqual(self.status(), "rejected")
        # Pylint also sees a two-argument instance replacement in test_commands.
        await self.controller.handle("max-charge-power", b"4500", retained=True)  # pylint: disable=unexpected-keyword-arg
        self.assertEqual(self.status(), "rejected-retained")
        self.controller.config = replace(
            self.config, commands=replace(self.config.commands, enabled=False)
        )
        await self.controller.handle("max-charge-power", b"4500")
        self.assertEqual(self.status(), "rejected-disabled")
        self.controller.reader.http.request.assert_not_awaited()
        self.assertFalse(self.controller.journal.exists())

    async def test_same_numeric_value_needs_no_write(self):
        self.controller.catalog.side_effect = None
        self.controller.catalog.return_value = catalog(value="4500.0")
        await self.controller.handle("max-charge-power", b"4500")
        self.assertEqual(self.status(), "already-confirmed")
        self.controller.reader.http.request.assert_not_awaited()

    async def test_pending_wrong_unit_and_wrong_value_do_not_confirm(self):
        for entry in (
            catalog(value="4500", state="Pending"),
            catalog(value="4500", unit="kW"),
            catalog(),
        ):
            with self.subTest(entry=entry[CHANNEL]):
                self.controller.catalog.side_effect = None
                self.controller.catalog.return_value = entry
                # Preflight is valid; only the subsequent readback is faulty.
                self.controller.catalog.side_effect = [catalog()] + [entry] * 100
                await self.controller.handle("max-charge-power", b"4500")
                self.assertEqual(self.status(), "uncertain")
                self.assertEqual(self.api.fresh_values(), {})
                self.controller.reader.http.request.assert_awaited_once()
                self.controller.journal.unlink()
                self.controller.reader.http.request.reset_mock()

    async def test_lost_response_blocks_repeat_without_another_put(self):
        self.controller.reader.http.request.side_effect = ProtocolError("Fixture response lost")
        await self.controller.handle("max-charge-power", b"4500")
        self.assertEqual(self.status(), "uncertain")
        await self.controller.handle("max-charge-power", b"4500")
        self.assertEqual(self.status(), "blocked-uncertain")
        self.controller.reader.http.request.assert_awaited_once()
        self.assertEqual(self.api.fresh_values(), {})
