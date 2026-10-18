"""Deterministic eCharger timestamp boundaries before changing freshness propagation."""

import asyncio
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from sma_mqtt_bridge.adapters.echarger import (
    NS,
    EChargerReader,
    SempReader,
    current_measurement,
    semp_values,
)
from sma_mqtt_bridge.config import ECharger, load_config
from sma_mqtt_bridge.homie import HomiePublisher
from sma_mqtt_bridge.model import Property, SampleValues, SourceState


class MeasurementFreshnessTests(unittest.TestCase):
    now = datetime(2026, 10, 11, 12, tzinfo=timezone.utc)

    def stamp(self, age):
        return (self.now - timedelta(seconds=age)).isoformat()

    def test_device_age_boundaries_include_zero_and_exact_limit(self):
        for age, accepted in (
            (0, True),
            (179, True),
            (180, True),
            (180.001, False),
            (181, False),
            (-0.001, False),
        ):
            with self.subTest(age=age):
                value = current_measurement(4500, self.stamp(age), 180, self.now)
                self.assertEqual(value, 4500 if accepted else None)
        self.assertEqual(current_measurement(0, self.stamp(0), 180, self.now), 0)

    def test_timestamp_formats_and_invalid_timestamps(self):
        for stamp in ("2026-10-11T12:00:00Z", "2026-10-11T14:00:00+02:00"):
            with self.subTest(stamp=stamp):
                self.assertEqual(current_measurement(4500, stamp, 180, self.now), 4500)
        for stamp in (None, "", "invalid", "2026-10-11T12:00:00", 123, {}):
            with self.subTest(stamp=stamp):
                self.assertIsNone(current_measurement(4500, stamp, 180, self.now))

    def test_partial_semp_reply_ages_channels_individually_and_keeps_settings(self):
        rows = (
            ("Measurement.Metering.GridMs.TotWIn.ChaSta", "4500", 179),
            ("Measurement.ChaSess.WhIn", "1500", 181),
            ("Measurement.Operation.Health", "307", 181),
            ("Measurement.Operation.EVeh.ChaStt", "200113", -1),
            ("Parameter.Chrg.ActChaMod", "4719", 86400),
        )
        body = "".join(
            f"<Parameter><channelId>{channel}</channelId>"
            f"<timestamp>{self.stamp(age)}</timestamp><value>{value}</value></Parameter>"
            for channel, value, age in rows
        )
        values = semp_values(
            f'<Device2EM xmlns="{NS}"><Parameters>{body}</Parameters></Device2EM>', 180, self.now
        )
        self.assertEqual(values["measurements/power"], Decimal("4500"))
        for key in ("session-energy", "health", "vehicle-status"):
            with self.subTest(key=key):
                self.assertIsNone(values["measurements/" + key])
        self.assertEqual(values["settings/charge-mode"], "4719")


class RemainingLifetimeTests(unittest.TestCase):
    now = MeasurementFreshnessTests.now
    stamp = MeasurementFreshnessTests.stamp

    def reply(self, rows):
        body = "".join(
            f"<Parameter><channelId>{channel}</channelId>"
            f"<timestamp>{self.stamp(age)}</timestamp><value>{value}</value></Parameter>"
            for channel, value, age in rows
        )
        with patch("sma_mqtt_bridge.adapters.echarger.time.monotonic", return_value=1000):
            return semp_values(
                f'<Device2EM xmlns="{NS}"><Parameters>{body}</Parameters></Device2EM>',
                180,
                self.now,
            )

    def state(self, values):
        props = tuple(
            Property(
                key.split("/")[0],
                key.split("/")[1],
                key,
                "string"
                if key
                in {"measurements/vehicle-status", "measurements/health", "settings/charge-mode"}
                else "float",
            )
            for key in values
        )
        return SourceState("semp", "fixture", props, 180, ready_properties=("measurements/power",))

    def test_near_limit_does_not_restart_lifetime_and_preserves_last_known(self):
        for age in (179, 180):
            values = self.reply([("Measurement.Metering.GridMs.TotWIn.ChaSta", "0", age)])
            state = self.state(values)
            state.update(values, now=1000)
            self.assertEqual(state.fresh_values(1000)["measurements/power"], "0")
            self.assertEqual(state.status(1000), "ready")
            self.assertNotIn("measurements/power", state.fresh_values(1002))
            self.assertEqual(state.status(1002), "stale")
            self.assertEqual(state.values["measurements/power"][0], "0")

    def test_processing_delay_consumes_remaining_time_without_hiding_missing_power(self):
        values = self.reply(
            [
                ("Measurement.Metering.GridMs.TotWIn.ChaSta", "4500", 179),
                ("Parameter.Chrg.ActChaMod", "4719", 86400),
            ]
        )
        state = self.state(values)
        state.update(values, now=1002)
        self.assertNotIn("measurements/power", state.fresh_values(1002))
        self.assertEqual(state.fresh_values(1002)["settings/charge-mode"], "4719")
        self.assertEqual(state.status(1002), "stale")

    def test_new_timestamp_refreshes_equal_value_and_partial_reply_keeps_old_deadline(self):
        channel = "Measurement.Metering.GridMs.TotWIn.ChaSta"
        state = self.state(self.reply([(channel, "0", 179)]))
        state.update(self.reply([(channel, "0", 179)]), now=1000)
        state.update({"settings/charge-mode": "4719"}, now=1001)
        self.assertNotIn("measurements/power", state.fresh_values(1002))
        state.update(self.reply([(channel, "0", 0)]), now=1002)
        self.assertEqual(state.fresh_values(1002)["measurements/power"], "0")
        self.assertNotIn("measurements/power", state.fresh_values(1181))

    def test_vehicle_aliases_and_setpoints_keep_independent_ages(self):
        values = self.reply(
            [
                ("Measurement.Metering.GridMs.TotWIn.ChaSta", "1", 0),
                ("Measurement.Operation.EVeh.ChaStt", "200113", 179),
                ("Setpoint.PlantControl.PCC.ChrgActCnt", "1", 170),
            ]
        )
        state = self.state(values)
        state.update(values, now=1000)
        fresh = state.fresh_values(1002)
        self.assertNotIn("measurements/vehicle-status", fresh)
        self.assertNotIn("measurements/vehicle-status-code", fresh)
        self.assertIn("control/active-charging-count", fresh)
        self.assertNotIn("control/active-charging-count", state.fresh_values(1011))
        self.assertEqual(state.status(1011), "ready")

    def test_repeated_old_timestamp_keeps_deadline_and_monotonic_clock_controls_expiry(self):
        channel = "Measurement.Metering.GridMs.TotWIn.ChaSta"
        values = self.reply([(channel, "0", 100)])
        state = self.state(values)
        state.update(values, now=1000)
        body = (
            f'<Device2EM xmlns="{NS}"><Parameters><Parameter>'
            f"<channelId>{channel}</channelId><value>0</value>"
            f"<timestamp>{self.stamp(100)}</timestamp>"
            "</Parameter></Parameters></Device2EM>"
        )
        with patch("sma_mqtt_bridge.adapters.echarger.time.monotonic", return_value=1060):
            repeated = semp_values(body, 180, self.now + timedelta(seconds=60))
        state.update(repeated, now=1060)
        self.assertIn("measurements/power", state.fresh_values(1080))
        with patch("sma_mqtt_bridge.model.time.monotonic", return_value=1080.001):
            self.assertNotIn("measurements/power", state.fresh_values())
        self.assertEqual(state.last_success, 1060)

    def test_property_specific_limit_and_invalid_metadata_fail_closed(self):
        values = self.reply([("Measurement.Metering.GridMs.TotWIn.ChaSta", "0", 10)])
        values = SampleValues(
            {"measurements/power": values["measurements/power"]}, values.observed_at
        )
        state = SourceState(
            "semp",
            "fixture",
            (Property("measurements", "power", "Power", stale_seconds=15),),
            180,
        )
        state.update(values, now=1000)
        self.assertIn("measurements/power", state.fresh_values(1005))
        self.assertNotIn("measurements/power", state.fresh_values(1005.001))
        for observed in (float("nan"), float("inf"), 1001):
            values.observed_at["measurements/power"] = observed
            state.update(values, now=1000)
            self.assertNotIn("measurements/power", state.fresh_values(1000))

    def test_session_health_and_plain_adapters_keep_existing_receipt_lifetime(self):
        values = self.reply(
            [
                ("Measurement.Metering.GridMs.TotWIn.ChaSta", "1", 0),
                ("Measurement.ChaSess.WhIn", "1500", 179),
                ("Measurement.Operation.Health", "307", 179),
            ]
        )
        state = self.state(values)
        state.update(values, now=1000)
        self.assertIn("measurements/session-energy", state.fresh_values(1002))
        self.assertIn("measurements/health", state.fresh_values(1002))
        stale = self.reply(
            [
                ("Measurement.ChaSess.WhIn", "1500", 181),
                ("Measurement.Operation.Health", "307", 181),
            ]
        )
        state.update(stale, now=1003)
        self.assertNotIn("measurements/session-energy", state.fresh_values(1003))
        self.assertNotIn("measurements/health", state.fresh_values(1003))
        for source in ("modbus", "meter", "portal"):
            plain = self.state({"measurements/power": 1})
            plain.id = source
            plain.update({"measurements/power": 1}, now=1000)
            self.assertIn("measurements/power", plain.fresh_values(1180))
            self.assertNotIn("measurements/power", plain.fresh_values(1180.001))


class ReaderLifetimeTests(unittest.IsolatedAsyncioTestCase):
    now = MeasurementFreshnessTests.now
    stamp = MeasurementFreshnessTests.stamp

    async def read_api(self, rows, include_base=True):
        reader = EChargerReader(
            ECharger(
                expected_serial="123", advanced_channels_enabled=False, diagnostics_enabled=False
            ),
            10000,
            include_base=include_base,
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
            {"channelId": c, "values": [{"value": v, "time": self.stamp(age)}]}
            for c, v, age in rows
        ]
        reader.http.get_json = AsyncMock(side_effect=[catalog, live])
        with (
            patch("sma_mqtt_bridge.adapters.echarger.datetime") as wall,
            patch("sma_mqtt_bridge.adapters.echarger.time.monotonic", return_value=1000),
        ):
            wall.now.return_value = self.now
            wall.fromisoformat.side_effect = datetime.fromisoformat
            values = await reader.read()
        self.assertEqual(reader.http.get_json.await_count, 2)
        state = SourceState("api", "fixture", reader.properties, 180)
        await reader.close()
        return values, state

    async def test_api_channel_ages_scaling_aliases_and_conservative_exclusions(self):
        values, state = await self.read_api(
            [
                ("Measurement.Metering.GridMs.TotWIn.ChaSta", "0", 179),
                ("Measurement.Metering.GridMs.TotWhIn.ChaSta", "1500", 179),
                ("Measurement.GridMs.A.phsA", "1.25", 179),
                ("Measurement.GridMs.PhV.phsA", "230", 179),
                ("Measurement.Operation.EVeh.ChaStt", "200113", 179),
                ("Measurement.ChaSess.WhIn", "1500", 179),
                ("Measurement.GridMs.W.phsA", "123.5", 179),
            ]
        )
        state.update(values, now=1000)
        self.assertEqual(state.fresh_values(1000)["measurements/total-energy"], "1.5")
        for key in ("power", "total-energy", "current-l1", "vehicle-status", "vehicle-status-code"):
            self.assertNotIn("measurements/" + key, state.fresh_values(1002))
        for key in ("voltage-l1", "session-energy", "power-l1"):
            self.assertIn("measurements/" + key, state.fresh_values(1002))
        self.assertEqual(state.status(1002), "stale")
        delayed = SourceState("api", "fixture", state.properties, 180)
        delayed.update(values, now=1002)
        self.assertNotIn("measurements/current-l1", delayed.fresh_values(1002))
        self.assertEqual(delayed.status(1002), "stale")

    async def test_api_session_observation_preserves_source_time_without_expanding_base_inventory(
        self,
    ):
        for include_base in (False, True):
            values, state = await self.read_api(
                [
                    ("Measurement.Metering.GridMs.TotWIn.ChaSta", "3000", 3),
                    ("Measurement.Operation.EVeh.ChaStt", "200113", 2),
                    ("Measurement.ChaSess.WhIn", "1500", 1),
                ],
                include_base=include_base,
            )
            sample = values.session_observation
            self.assertEqual(sample.energy, Decimal("1.5"))
            self.assertEqual(sample.energy_time.isoformat(), self.stamp(1).replace("Z", "+00:00"))
            self.assertEqual(sample.observed_at, 997)
            self.assertEqual("measurements/session-energy" in values, include_base)
            self.assertFalse(any(p.node == "session" for p in state.properties))

    async def test_api_total_energy_fallback_uses_selected_channel_not_primary_age(self):
        rows = [
            ("Measurement.Metering.GridMs.TotWhIn.ChaSta", "NaN", 179),
            ("Measurement.Metering.GridMs.TotWhIn", "2000", 179),
        ]
        values, state = await self.read_api(rows, include_base=False)
        state.update(values, now=1000)
        self.assertEqual(state.fresh_values(1002)["measurements/total-energy"], "2")
        self.assertNotIn("measurements/power", values)
        self.assertNotIn("measurements/vehicle-status-code", values)
        values, state = await self.read_api(
            [
                ("Measurement.Metering.GridMs.TotWhIn.ChaSta", "1500", 179),
                ("Measurement.Metering.GridMs.TotWhIn", "2000", 0),
            ],
            include_base=False,
        )
        state.update(values, now=1000)
        self.assertEqual(state.fresh_values(1000)["measurements/total-energy"], "1.5")
        self.assertNotIn("measurements/total-energy", state.fresh_values(1002))

    async def test_semp_reader_filter_keeps_timing_and_api_independence(self):
        reader = SempReader(
            ECharger(
                semp_device_id="fixture", advanced_channels_enabled=True, diagnostics_enabled=True
            ),
            10000,
            include_settings=False,
        )
        identity = f'<Device2EM xmlns="{NS}"><DeviceInfo><Identification><DeviceId>fixture</DeviceId></Identification></DeviceInfo></Device2EM>'
        body = f'<Device2EM xmlns="{NS}"><Parameters><Parameter><channelId>Measurement.Metering.GridMs.TotWIn.ChaSta</channelId><value>0</value><timestamp>{self.stamp(179)}</timestamp></Parameter></Parameters></Device2EM>'
        reader.http.request = AsyncMock(side_effect=[(200, {}, identity), (200, {}, body)])
        with (
            patch("sma_mqtt_bridge.adapters.echarger.datetime") as wall,
            patch("sma_mqtt_bridge.adapters.echarger.time.monotonic", return_value=1000),
        ):
            wall.now.return_value = self.now
            wall.fromisoformat.side_effect = datetime.fromisoformat
            values = await reader.read()
        self.assertFalse(any(k.startswith("settings/") for k in values))
        semp = SourceState("semp", "fixture", reader.properties, 180)
        semp.update(values, now=1000)
        api_values, api = await self.read_api(
            [
                ("Measurement.GridMs.A.phsA", "0", 0),
                ("Measurement.GridMs.PhV.phsA", "230", 0),
            ],
            include_base=False,
        )
        api.update(api_values, now=1000)
        self.assertEqual(semp.status(1002), "stale")
        self.assertEqual(api.status(1002), "ready")
        api_values, api = await self.read_api(
            [
                ("Measurement.GridMs.A.phsA", "0", 179),
                ("Measurement.GridMs.PhV.phsA", "230", 0),
            ],
            include_base=False,
        )
        api.update(api_values, now=1000)
        with patch("sma_mqtt_bridge.adapters.echarger.time.monotonic", return_value=1000):
            fresh = semp_values(body.replace(self.stamp(179), self.stamp(0)), 180, self.now)
        fresh = type(fresh)(
            {k: v for k, v in fresh.items() if not k.startswith("settings/")}, fresh.observed_at
        )
        semp.update(fresh, now=1000)
        self.assertEqual(semp.status(1002), "ready")
        self.assertEqual(api.status(1002), "stale")
        await reader.close()

    async def test_expiry_and_restart_do_not_republish_or_delete_retained_measurement(self):
        values, state = await self.read_api(
            [
                ("Measurement.Metering.GridMs.TotWIn.ChaSta", "4500", 179),
            ]
        )
        state.ready_properties = ("measurements/power",)
        state.update(values, now=1000)
        with tempfile.TemporaryDirectory() as directory:
            publisher = HomiePublisher(load_config({"SMAB_STATE_DIR": directory}), [state])
            client = SimpleNamespace(publish=AsyncMock())
            stop = asyncio.Event()
            with patch("sma_mqtt_bridge.model.time.monotonic", return_value=1000):

                async def advance(*_):
                    stop.set()

                with patch("sma_mqtt_bridge.homie.wait_stop", side_effect=advance):
                    await publisher.publish_values(
                        client, "homie/fixture", [state], stop, {}, 0, None
                    )
            self.assertTrue(
                any(
                    c.args == ("homie/fixture/measurements/power", "4500") and c.kwargs["retain"]
                    for c in client.publish.await_args_list
                )
            )
            for current in (state, SourceState("api", "fixture", state.properties, 180)):
                client.publish.reset_mock()
                stop.clear()
                with (
                    patch("sma_mqtt_bridge.model.time.monotonic", return_value=1002),
                    patch("sma_mqtt_bridge.homie.wait_stop", side_effect=advance),
                ):
                    await publisher.publish_values(
                        client, "homie/fixture", [current], stop, {}, 0, None
                    )
                self.assertFalse(
                    any(
                        c.args[0] == "homie/fixture/measurements/power"
                        for c in client.publish.await_args_list
                    )
                )
