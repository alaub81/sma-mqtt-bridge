"""Consistent grid-power MQTT names without profile or energy-state migration."""

import asyncio
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from test_plant import PlantFixture
from test_runtime import FakeClient

from sma_mqtt_bridge.adapters.home_manager_modbus import HomeManagerModbusReader
from sma_mqtt_bridge.adapters.meter import MeterReader
from sma_mqtt_bridge.config import HomeManager, load_config
from sma_mqtt_bridge.home_manager_profile import load_home_manager_profile
from sma_mqtt_bridge.homie import HomiePublisher
from sma_mqtt_bridge.model import Property, SourceState


class HomeManagerPowerNamesTests(unittest.TestCase):
    def test_both_transports_match_inverter_names_units_and_keep_internal_readiness(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = load_config({"SMAB_STATE_DIR": tmp, "SMAB_LANGUAGE": "de"})
            profile = load_home_manager_profile("sma-home-manager-2-modbus", tmp)
            for reader in (
                MeterReader(HomeManager(advanced_channels_enabled=True, diagnostics_enabled=True)),
                HomeManagerModbusReader(
                    HomeManager(advanced_channels_enabled=True, diagnostics_enabled=True), profile
                ),
            ):
                state = SourceState("home-manager", "meter", reader.properties, 30)
                old_keys = {p.key for p in reader.properties}
                state.update(
                    {"measurements/power-import": 120, "measurements/power-export": 0}, now=100
                )
                publisher = HomiePublisher(config, [state])
                props = publisher.properties([state])
                by_key = {p.key: p for p in props}
                self.assertIn("measurements/power-drawn", by_key)
                self.assertIn("measurements/power-grid-feed-in", by_key)
                self.assertNotIn("measurements/power-import", by_key)
                self.assertNotIn("measurements/power-export", by_key)
                for key in ("measurements/power-drawn", "measurements/power-grid-feed-in"):
                    self.assertEqual(by_key[key].unit, "W")
                    self.assertEqual(by_key[key].channel_group, "basic")
                    self.assertFalse(by_key[key].settable)
                values, status = publisher.snapshot([state], now=100)
                self.assertEqual(status, "ready")
                self.assertEqual(values["measurements/power-drawn"], "120")
                self.assertEqual(values["measurements/power-grid-feed-in"], "0")
                self.assertNotIn("measurements/power-import", values)
                self.assertNotIn("measurements/power-export", values)
                self.assertEqual({p.key for p in reader.properties}, old_keys)
                self.assertEqual(
                    state.required_keys, ("measurements/power-import", "measurements/power-export")
                )
                metadata = publisher.metadata("meter", props)
                self.assertIn("homie/meter/measurements/powerdrawn/$unit", metadata)
                self.assertIn("homie/meter/measurements/powergridfeedin/$unit", metadata)
                self.assertEqual(
                    metadata["homie/meter/measurements/powerdrawn/$name"], "Bezogene Leistung"
                )
                self.assertEqual(
                    metadata["homie/meter/measurements/powergridfeedin/$name"],
                    "Netzeinspeiseleistung",
                )
                state.error = True
                self.assertEqual(publisher.snapshot([state], now=100)[1], "alert")

    def test_other_sources_and_delegated_properties_are_not_renamed(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = load_config({"SMAB_STATE_DIR": tmp})
            for source in ("inverter1", "api", "fixture"):
                state = SourceState(
                    source, "fixture", (Property("measurements", "power-import", "Fixture"),), 30
                )
                state.update({"measurements/power-import": 10}, now=100)
                publisher = HomiePublisher(config, [state])
                self.assertIn(
                    "measurements/power-import", {p.key for p in publisher.properties([state])}
                )
                self.assertIn("measurements/power-import", publisher.snapshot([state], now=100)[0])
            state = SourceState(
                "home-manager",
                "fixture",
                (Property("device-1", "power-import", "Delegated fixture"),),
                30,
            )
            self.assertEqual(
                HomiePublisher(config, [state]).properties([state])[0].key, "device-1/power-import"
            )


class PlantPowerNameContinuityTests(PlantFixture):
    def test_publication_preserves_energy_ledger_house_power_and_earnings(self):
        engine = self.engine(ac=True, env={"SMAB_PLANT_FEED_IN_TARIFF_PER_KWH": "0.1"})
        engine.refresh(100, self.wall)
        before = engine.ledger.path.read_bytes()
        state = engine.sources["home-manager"]
        publisher = HomiePublisher(engine.config, [state, engine.state])
        publisher.properties([state])
        values, _ = publisher.snapshot([state], now=100)
        self.assertEqual(values["measurements/power-drawn"], "600")
        self.assertEqual(values["measurements/power-grid-feed-in"], "800")
        self.assertEqual(engine.state.fresh_values(100)["house/consumption"], "4600")
        self.assertEqual(engine.state.fresh_values(100)["pv/total-earnings"], "6.00")
        self.assertEqual(engine.ledger.path.read_bytes(), before)
        restarted = self.engine(ac=True)
        self.assertFalse(restarted.ledger.binding_changed)
        self.assertEqual(restarted.ledger.path.read_bytes(), before)


class HomeManagerPowerRetirementTests(unittest.IsolatedAsyncioTestCase):
    async def test_old_topics_retire_and_new_values_publish_on_actual_stack(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = load_config({"SMAB_STATE_DIR": tmp})
            state = SourceState(
                "home-manager",
                "meter",
                MeterReader(
                    HomeManager(advanced_channels_enabled=True, diagnostics_enabled=True)
                ).properties,
                30,
            )
            state.update({"measurements/power-import": 120, "measurements/power-export": 0})
            client = FakeClient()
            publisher = HomiePublisher(config, [state], lambda *a, **k: client)
            roots = ["homie/meter/measurements/" + name for name in ("powerimport", "powerexport")]
            old = {
                root + suffix
                for root in roots
                for suffix in ("", "/$name", "/$unit", "/$datatype", "/$retained", "/$settable")
            }
            publisher.owned = {"meter": old}
            publisher.save_owned()
            publisher = HomiePublisher(config, [state], lambda *a, **k: client)
            publisher.publish_values = AsyncMock()
            await publisher.serve_device("meter", [state], asyncio.Event())
            messages = {(topic, value) for topic, value, _ in client.messages}
            for topic in old:
                self.assertIn((topic, b""), messages)
                self.assertNotIn(topic, publisher.owned["meter"])
            stop = asyncio.Event()

            async def finish(*_args):
                stop.set()

            with patch("sma_mqtt_bridge.homie.wait_stop", side_effect=finish):
                await HomiePublisher.publish_values(
                    publisher, client, "homie/meter", [state], stop, {}, 0, None
                )
            messages = {(topic, value) for topic, value, _ in client.messages}
            self.assertIn(("homie/meter/measurements/powerdrawn", "120"), messages)
            self.assertIn(("homie/meter/measurements/powergridfeedin", "0"), messages)
            self.assertFalse(any(topic in roots and value != b"" for topic, value in messages))


if __name__ == "__main__":
    unittest.main()
