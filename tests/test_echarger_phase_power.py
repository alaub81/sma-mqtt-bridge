"""Local phase-power unit scope, read-only ownership and unchanged numerical values."""

import tempfile
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from sma_mqtt_bridge.adapters.echarger import EChargerReader, SempReader
from sma_mqtt_bridge.config import ECharger, load_config
from sma_mqtt_bridge.homie import HomiePublisher, discovery
from sma_mqtt_bridge.model import SourceState
from sma_mqtt_bridge.translation import load_translation


class EChargerPhasePowerTests(unittest.IsolatedAsyncioTestCase):
    def catalog(self, firmware="2.6.37.R"):
        return [
            {
                "componentId": "IGULD:SELF",
                "values": [
                    {"channelId": "Parameter.Nameplate.SerNum", "value": "123"},
                    {"channelId": "Parameter.Nameplate.ModelStr", "value": "EVC22-3AC-20"},
                    {"channelId": "Parameter.Nameplate.PkgRev", "value": firmware},
                ],
            }
        ]

    async def read(self, live, firmware="2.6.37.R", include_base=False):
        adapter = EChargerReader(
            ECharger(
                expected_serial="123", advanced_channels_enabled=False, diagnostics_enabled=False
            ),
            10000,
            include_base=include_base,
        )
        adapter.access_token = AsyncMock(return_value="fixture-token")
        adapter.http.get_json = AsyncMock(side_effect=[self.catalog(firmware), live])
        now = datetime(2026, 10, 12, 10, 0, tzinfo=timezone.utc)
        with patch("sma_mqtt_bridge.adapters.echarger.datetime") as clock:
            clock.now.return_value = now
            clock.fromisoformat.side_effect = datetime.fromisoformat
            values = await adapter.read()
        self.assertEqual(adapter.http.get_json.await_count, 2)
        for call in adapter.http.get_json.call_args_list:
            self.assertEqual(call.args[0], "POST")
            self.assertTrue(call.args[1].endswith(("/parameters/search", "/measurements/live")))
        await adapter.close()
        return adapter, values

    def measurement(self, phase, value, **fields):
        return {
            "channelId": "Measurement.GridMs.W.phs" + phase,
            "values": [{"value": value, "time": "2026-10-12T10:00:00Z"}],
        } | fields

    async def test_phase_mapping_watts_fractional_signed_zero_and_existing_power(self):
        live = [
            self.measurement("A", "1234.5"),
            self.measurement("B", "0"),
            self.measurement("C", "-2.125"),
            {
                "channelId": "Measurement.Metering.GridMs.TotWIn.ChaSta",
                "values": [{"value": 5678, "time": "2026-10-12T10:00:00Z"}],
            },
        ]
        for include_base in (False, True):
            adapter, values = await self.read(live, include_base=include_base)
            self.assertEqual(values["measurements/power-l1"], Decimal("1234.5"))
            self.assertEqual(values["measurements/power-l2"], 0)
            self.assertEqual(values["measurements/power-l3"], Decimal("-2.125"))
            if include_base:
                self.assertEqual(values["measurements/power"], 5678)
            else:
                self.assertNotIn("measurements/power", values)
            with tempfile.TemporaryDirectory() as tmp:
                labels = load_translation("de", tmp)
                metadata = discovery("homie", "fixture", adapter.properties, labels)
                for phase in (1, 2, 3):
                    topic = f"homie/fixture/measurements/powerl{phase}"
                    self.assertEqual(metadata[topic + "/$unit"], "W")
                    self.assertEqual(metadata[topic + "/$datatype"], "float")
                    self.assertEqual(metadata[topic + "/$settable"], "false")
                    self.assertEqual(metadata[topic + "/$name"], f"Leistung Phase L{phase}")
                state = SourceState("api", "fixture", adapter.properties, 60)
                state.update(values, now=10)
                config = load_config({"SMAB_STATE_DIR": tmp})
                snapshot, _ = HomiePublisher(config, [state]).snapshot([state], now=10)
                self.assertEqual(snapshot["measurements/power-l1"], "1234.5")
                self.assertEqual(snapshot["measurements/power-l2"], "0")
                self.assertEqual(snapshot["measurements/power-l3"], "-2.125")
                self.assertNotIn("measurements/power-l1", state.required_keys)
        semp = SempReader(ECharger(), 10000)
        self.assertFalse(any(p.id.startswith("power-l") for p in semp.properties))
        await semp.close()

    async def test_missing_nan_and_timestamp_rejection_stay_unavailable(self):
        for value in (None, "NaN", "Infinity", True):
            _, values = await self.read([self.measurement("A", value)])
            self.assertIsNone(values["measurements/power-l1"])
            self.assertIsNone(values["measurements/power-l2"])
            self.assertIsNone(values["measurements/power-l3"])
        for stamp in ("2000-01-01T00:00:00Z", "2026-10-12T10:01:00Z", "invalid"):
            live = self.measurement("A", 123)
            live["values"][0]["time"] = stamp
            _, values = await self.read([live])
            self.assertIsNone(values["measurements/power-l1"])

    async def test_units_fail_closed_for_conflicts_or_unverified_firmware(self):
        _, values = await self.read([self.measurement("A", 123)], firmware="future")
        self.assertIsNone(values["measurements/power-l1"])
        _, values = await self.read([self.measurement("A", 123, unit="W")], firmware="future")
        self.assertEqual(values["measurements/power-l1"], 123)
        for unit in ("kW", "Wh", "", 18):
            _, values = await self.read([self.measurement("A", 123, unit=unit)])
            self.assertIsNone(values["measurements/power-l1"])
        live = self.measurement("A", 123, unit="W")
        live["values"][0]["unit"] = "kW"
        _, values = await self.read([live])
        self.assertIsNone(values["measurements/power-l1"])
        live = self.measurement("A", 123)
        live["values"][0]["unit"] = "W"
        _, values = await self.read([live], firmware="future")
        self.assertEqual(values["measurements/power-l1"], 123)
