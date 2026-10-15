"""Diagnostic publication flags preserve plant accounting and source availability."""

import asyncio
import unittest
from unittest.mock import AsyncMock

import test_wallbox_daily
from test_plant import PlantFixture
from test_runtime import FakeClient

from sma_mqtt_bridge.homie import HomiePublisher, discovery


class PlantDiagnosticTests(PlantFixture):
    def test_disabled_diagnostics_hide_metadata_and_values_without_affecting_accounting(self):
        enabled = self.engine(ac=True)
        enabled.refresh(100, self.wall)
        before = enabled.ledger.path.read_bytes()
        disabled = self.engine(ac=True, env={"SMAB_PLANT_DIAGNOSTICS_ENABLED": "false"})
        disabled.refresh(100, self.wall)
        self.assertFalse(disabled.ledger.binding_changed)
        self.assertEqual(disabled.ledger.path.read_bytes(), before)
        self.assertEqual(disabled.state.fresh_values(100), enabled.state.fresh_values(100))
        publisher = HomiePublisher(disabled.config, [disabled.state])
        props = publisher.properties([disabled.state])
        self.assertEqual(
            [p.key for p in props if p.node == "diagnostics"], ["diagnostics/plant-status"]
        )
        values, status = publisher.snapshot([disabled.state], now=100)
        enabled_values, enabled_status = HomiePublisher(enabled.config, [enabled.state]).snapshot(
            [enabled.state], now=100
        )
        self.assertEqual(status, enabled_status)
        self.assertEqual(
            {k: v for k, v in values.items() if not k.startswith("diagnostics/")},
            {k: v for k, v in enabled_values.items() if not k.startswith("diagnostics/")},
        )
        self.assertEqual(
            [k for k in values if k.startswith("diagnostics/")], ["diagnostics/plant-status"]
        )
        self.assertIn("diagnostics/power-input-status", disabled.state.fresh_values(100))
        metadata = discovery("homie", "sma-plant", props)
        self.assertEqual(metadata["homie/sma-plant/diagnostics/$properties"], "plantstatus")
        disabled.state.error = True
        self.assertEqual(
            publisher.snapshot([disabled.state], now=100)[0]["diagnostics/plant-status"], "error"
        )

    def test_debug_does_not_reenable_diagnostic_topics(self):
        engine = self.engine(
            env={"SMAB_PLANT_DIAGNOSTICS_ENABLED": "false", "SMAB_PLANT_DEBUG_ENABLED": "true"}
        )
        engine.refresh(100, self.wall)
        publisher = HomiePublisher(engine.config, [engine.state])
        self.assertEqual(
            [p.key for p in publisher.properties([engine.state]) if p.node == "diagnostics"],
            ["diagnostics/plant-status"],
        )

    def test_wallbox_and_plant_flags_are_independent(self):
        fixture = test_wallbox_daily.WallboxDailyTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        for plant_flag, charger_flag in (
            (False, False),
            (False, True),
            (True, False),
            (True, True),
        ):
            with self.subTest(plant=plant_flag, charger=charger_flag):
                engine = fixture.engine(
                    ac=True,
                    env={
                        "SMAB_PLANT_DIAGNOSTICS_ENABLED": str(plant_flag).lower(),
                        "SMAB_ECHARGER_DIAGNOSTICS_ENABLED": str(charger_flag).lower(),
                    },
                )
                engine.refresh(100, fixture.wall)
                publisher = HomiePublisher(engine.config, list(engine.output_states))
                plant_keys = {p.key for p in publisher.properties([engine.state])}
                wallbox_keys = {p.key for p in publisher.properties([engine.wallbox_state])}
                self.assertEqual("diagnostics/power-input-status" in plant_keys, plant_flag)
                self.assertEqual("diagnostics/wallbox-day-status" in wallbox_keys, charger_flag)
                self.assertEqual("diagnostics/wallbox-energy-time" in wallbox_keys, charger_flag)
                self.assertIn("measurements/daily-consumption", wallbox_keys)
                self.assertIn("diagnostics/plant-status", plant_keys)
                self.assertNotIn("diagnostics/wallbox-day-status", plant_keys)
                snapshot, _ = publisher.snapshot([engine.wallbox_state], now=100)
                self.assertEqual("diagnostics/wallbox-day-status" in snapshot, charger_flag)

    def test_device_basic_diagnostic_path_remains_basic(self):
        engine = self.engine(
            env={
                "SMAB_INVERTER1_ADVANCED_CHANNELS_ENABLED": "false",
                "SMAB_INVERTER1_DIAGNOSTICS_ENABLED": "false",
            }
        )
        state = engine.sources["inverter1"]
        self.assertIn("diagnostics/derating-reason", state.property_index())
        publisher = HomiePublisher(engine.config, [state])
        self.assertIn("diagnostics/derating-reason", {p.key for p in publisher.properties([state])})


class PlantDiagnosticRetirementTests(unittest.IsolatedAsyncioTestCase):
    async def test_disabled_diagnostics_retire_both_devices_and_preserve_status(self):
        fixture = test_wallbox_daily.WallboxDailyTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        enabled = fixture.engine(ac=True)
        enabled.refresh(100, fixture.wall)
        saved = enabled.ledger.path.read_bytes()
        disabled = fixture.engine(
            ac=True,
            env={
                "SMAB_PLANT_DIAGNOSTICS_ENABLED": "false",
                "SMAB_ECHARGER_DIAGNOSTICS_ENABLED": "false",
            },
        )
        disabled.refresh(100, fixture.wall)
        old_publisher = HomiePublisher(enabled.config, list(enabled.output_states))
        clients = []

        def factory(*args, **kwargs):
            client = FakeClient(*args, **kwargs)
            clients.append(client)
            return client

        publisher = HomiePublisher(disabled.config, list(disabled.output_states), factory)
        for old_state, state in zip(enabled.output_states, disabled.output_states):
            device = state.device
            old_props = old_publisher.properties([old_state])
            old = set(discovery("homie", device, old_props)) | {
                "homie/" + device + "/" + p.key.replace("-", "") for p in old_props
            }
            new_props = publisher.properties([state])
            current = set(discovery("homie", device, new_props)) | {
                "homie/" + device + "/" + p.key.replace("-", "") for p in new_props
            }
            retired = old - current
            self.assertTrue(retired)
            publisher.owned[device] = old
            publisher.publish_values = AsyncMock()
            await publisher.serve_device(device, [state], asyncio.Event())
            messages = {(topic, value) for topic, value, _ in clients[-1].messages}
            for topic in retired:
                self.assertIn((topic, b""), messages)
                self.assertNotIn(topic, publisher.owned[device])
            self.assertFalse(
                any(topic.endswith("/plantstatus") and value == b"" for topic, value in messages)
            )
        self.assertEqual(disabled.ledger.path.read_bytes(), saved)


if __name__ == "__main__":
    unittest.main()
