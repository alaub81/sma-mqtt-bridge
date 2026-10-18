"""Independent battery condition and strict, opt-in Wallbox diagnostic observations."""

import copy
import tempfile
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from sma_mqtt_bridge.adapters.echarger import EChargerReader, SempReader, api_diagnostic_values
from sma_mqtt_bridge.adapters.modbus import ModbusReader, decode
from sma_mqtt_bridge.config import ECharger, Inverter
from sma_mqtt_bridge.homie import discovery
from sma_mqtt_bridge.model import SourceState
from sma_mqtt_bridge.plant import energy_binding_profile
from sma_mqtt_bridge.profiles import load_profile
from tests.test_inverter_counters import words


class BatteryObservationTests(unittest.TestCase):
    def test_battery_condition_and_measured_temperature_extrema(self):
        with tempfile.TemporaryDirectory() as directory:
            profile = load_profile("sma-sbs3-7-10", directory, require_validated=True)
        defs = {p["id"]: p for p in profile["properties"]}
        blocks = {b["id"]: b for b in profile["pollers"]}
        for key, address in (
            ("battery-temperature-max", 32221),
            ("battery-temperature-min", 32227),
        ):
            prop = defs[key]
            self.assertEqual(blocks[prop["poller"]]["start"], address)
            self.assertEqual(blocks[prop["poller"]]["count"], 2)
            self.assertEqual(blocks[prop["poller"]]["intervalSeconds"], 120)
            for raw, expected in ((250, Decimal(25)), (-55, Decimal("-5.5")), (0, Decimal(0))):
                self.assertEqual(decode(words(prop, raw & 0xFFFFFFFF), prop), expected)
            self.assertIsNone(decode(words(prop, 0x80000000), prop))
        condition = defs["battery-condition"]
        self.assertEqual(blocks[condition["poller"]]["start"], 31391)
        for raw, expected in (
            (35, "Störung (Alm)"),
            (303, "Aus (Off)"),
            (307, "OK (Ok)"),
            (455, "Warnung (Wrn)"),
        ):
            self.assertEqual(decode(words(condition, raw), condition), expected)
        for raw in (16777213, 0xFFFFFFFF, 2291, 9999):
            self.assertIsNone(decode(words(condition, raw), condition))
        self.assertEqual(blocks[defs["battery-status"]["poller"]]["start"], 30955)
        reader = ModbusReader(
            Inverter(advanced_channels_enabled=False, diagnostics_enabled=False), profile
        )
        props = {p.key: p for p in reader.properties}
        for key in ("battery-condition", "battery-temperature-min", "battery-temperature-max"):
            self.assertEqual(props["measurements/" + key].channel_group, "basic")
            self.assertFalse(props["measurements/" + key].settable)
        state = SourceState("fixture", "fixture", reader.properties, 180)
        state.update({"measurements/status": "Ok (Ok)"}, now=10)
        self.assertEqual(state.status(10), "ready")
        binding = energy_binding_profile(profile)
        for key in ("battery-condition", "battery-temperature-max", "battery-temperature-min"):
            changed = copy.deepcopy(profile)
            next(p for p in changed["properties"] if p["id"] == key)["scale"] = 2
            self.assertNotEqual(energy_binding_profile(changed), binding)


class WallboxDiagnosticTests(unittest.IsolatedAsyncioTestCase):
    async def read_fixture(self, diagnostics, stamp, event="3701", code=0):
        reader = EChargerReader(
            ECharger(
                expected_serial="123",
                advanced_channels_enabled=False,
                diagnostics_enabled=diagnostics,
            ),
            10000,
            include_base=False,
        )
        reader.access_token = AsyncMock(return_value="fixture-token")
        catalog = [
            {
                "componentId": "IGULD:SELF",
                "values": [
                    {"channelId": "Parameter.Nameplate.SerNum", "value": "123"},
                    {"channelId": "Parameter.Nameplate.ModelStr", "value": "EVC22-3AC-20"},
                    {"channelId": "Parameter.Nameplate.PkgRev", "value": "2.6.37.R"},
                ],
            }
        ]
        live = [
            {"channelId": channel, "values": [{"value": value, "time": stamp}]}
            for channel, value in (
                ("Measurement.Operation.Evt.EvtNo", event),
                ("Measurement.Operation.WMaxLimSrc", code),
            )
        ]
        reader.http.get_json = AsyncMock(side_effect=[catalog, live])
        try:
            with patch("sma_mqtt_bridge.adapters.echarger.datetime") as clock:
                clock.now.return_value = datetime(2026, 10, 18, 12, tzinfo=timezone.utc)
                clock.fromisoformat.side_effect = datetime.fromisoformat
                result = await reader.read()
            self.assertEqual(reader.http.get_json.await_count, 2)
            return reader, result
        finally:
            await reader.close()

    async def test_fresh_values_zero_read_only_and_single_owner(self):
        reader, values = await self.read_fixture(True, "2026-10-18T12:00:00Z")
        self.assertEqual(values["diagnostics/event-number"], "3701")
        self.assertEqual(values["diagnostics/power-limitation-source-code"], 0)
        props = {p.key: p for p in reader.properties}
        semp = {
            p.key
            for p in SempReader(
                ECharger(advanced_channels_enabled=True, diagnostics_enabled=True), 10000
            ).properties
        }
        topics = discovery("homie", "fixture", reader.properties)
        for key in ("event-number", "power-limitation-source-code"):
            self.assertEqual(props["diagnostics/" + key].channel_group, "diagnostics")
            self.assertFalse(props["diagnostics/" + key].required_for_ready)
            self.assertNotIn("diagnostics/" + key, semp)
            self.assertEqual(
                topics["homie/fixture/diagnostics/" + key.replace("-", "") + "/$settable"], "false"
            )

    async def test_stale_future_missing_time_and_disabled_are_unavailable(self):
        for stamp in ("2026-10-18T11:56:59Z", "2026-10-18T12:00:01Z", None, "invalid"):
            _, values = await self.read_fixture(True, stamp)
            self.assertIsNone(values["diagnostics/event-number"])
            self.assertIsNone(values["diagnostics/power-limitation-source-code"])
        reader, values = await self.read_fixture(False, "2026-10-18T12:00:00Z")
        self.assertNotIn("diagnostics/event-number", values)
        self.assertFalse(any(p.key.startswith("diagnostics/") for p in reader.properties))

    def test_malformed_values_do_not_become_diagnostic_codes(self):
        for value in (-1, "NaN", "Infinity", 1.5, {}, True, 4294967296):
            self.assertIsNone(
                api_diagnostic_values({"Measurement.Operation.WMaxLimSrc": value})[
                    "diagnostics/power-limitation-source-code"
                ]
            )
        for value in (None, 123, "", "bad\nvalue", "x" * 129):
            self.assertIsNone(
                api_diagnostic_values({"Measurement.Operation.Evt.EvtNo": value})[
                    "diagnostics/event-number"
                ]
            )
