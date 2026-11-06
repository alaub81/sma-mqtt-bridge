"""Homie state repeats have their own cadence; changes and measurements stay prompt."""

import asyncio
import tempfile
import unittest
from unittest.mock import patch

from sma_mqtt_bridge.config import load_config
from sma_mqtt_bridge.errors import ConfigError
from sma_mqtt_bridge.homie import HomiePublisher
from sma_mqtt_bridge.model import Property, SourceState
from tests.helpers import write_json


class StatePublicationTests(unittest.IsolatedAsyncioTestCase):
    async def exercise(self, *, env=None, ticks=22, step=1, change=None, ack_delay=0):
        with tempfile.TemporaryDirectory() as directory:
            config = load_config({"SMAB_STATE_DIR": directory} | (env or {}))
            state = SourceState(
                "fixture",
                "fixture",
                (Property("measurements", "power", "Power", unit="W"),),
                100,
                diagnostics_enabled=False,
            )
            state.update({"measurements/power": 0}, now=0)
            publisher = HomiePublisher(config, [state])
            clock, cycle, messages, waits = [0], [0], [], []
            stop = asyncio.Event()

            async def publish(topic, value, **options):
                messages.append((clock[0], topic, value, options))
                if topic.endswith("/$state"):
                    clock[0] += ack_delay

            async def advance(_stop, seconds):
                waits.append(seconds)
                cycle[0] += 1
                clock[0] += step
                if cycle[0] >= ticks:
                    stop.set()
                    return
                state.update({"measurements/power": cycle[0]}, now=clock[0])
                if change:
                    change(cycle[0], state, clock[0])

            with (
                patch("sma_mqtt_bridge.homie.time.monotonic", side_effect=lambda: clock[0]),
                patch("sma_mqtt_bridge.homie.wait_stop", side_effect=advance),
            ):
                await publisher.publish_values(
                    type("Client", (), {"publish": staticmethod(publish)})(),
                    "homie/fixture",
                    [state],
                    stop,
                    {},
                    0,
                    None,
                )
            return messages, waits

    @staticmethod
    def states(messages):
        return [(time, value) for time, topic, value, _ in messages if topic.endswith("/$state")]

    async def test_default_repeats_at_ten_seconds_while_measurements_keep_changing(self):
        messages, waits = await self.exercise()
        self.assertEqual(self.states(messages), [(0, "ready"), (10, "ready"), (20, "ready")])
        self.assertEqual(
            [(t, v) for t, key, v, _ in messages if key.endswith("/measurements/power")],
            [(t, str(t)) for t in range(22)],
        )
        self.assertEqual(waits, [1] * 22)
        self.assertTrue(all(options == {"qos": 1, "retain": True} for *_, options in messages))

    async def test_error_expiry_and_recovery_are_immediate_and_reset_repeat_deadline(self):
        def change(tick, state, _now):
            if tick == 2:
                state.error = True
            elif tick == 4:
                state.values.clear()

        messages, _ = await self.exercise(ticks=17, change=change)
        self.assertEqual(
            self.states(messages),
            [(0, "ready"), (2, "alert"), (3, "ready"), (4, "alert"), (5, "ready"), (15, "ready")],
        )

    async def test_fractional_override_is_independent_of_health_cadence(self):
        messages, waits = await self.exercise(
            env={
                "SMAB_MQTT_STATE_PUBLISH_INTERVAL_SECONDS": "2.5",
                "SMAB_HEALTH_INTERVAL_SECONDS": "0.25",
            },
            ticks=12,
            step=0.5,
        )
        self.assertEqual(self.states(messages), [(0, "ready"), (2.5, "ready"), (5, "ready")])
        self.assertEqual(waits, [0.25] * 12)

    async def test_one_second_override_preserves_previous_repeat_rate(self):
        messages, _ = await self.exercise(
            env={"SMAB_MQTT_STATE_PUBLISH_INTERVAL_SECONDS": "1"}, ticks=4
        )
        self.assertEqual(self.states(messages), [(t, "ready") for t in range(4)])

    async def test_repeat_deadline_starts_after_publish_acknowledgment(self):
        messages, _ = await self.exercise(ticks=14, ack_delay=2)
        self.assertEqual(self.states(messages), [(0, "ready"), (12, "ready")])

    async def test_fresh_session_publishes_immediately_before_the_interval_has_elapsed(self):
        for _ in range(2):
            messages, _ = await self.exercise(ticks=1)
            self.assertEqual(self.states(messages), [(0, "ready")])

    def test_setting_default_json_and_env_precedence(self):
        self.assertEqual(load_config({}).mqtt.state_publish_interval_seconds, 10)
        with tempfile.TemporaryDirectory() as directory:
            path = write_json(
                directory, "config.json", {"mqtt": {"statePublishIntervalSeconds": 30}}
            )
            env = {"SMAB_CONFIG_FILE": path}
            self.assertEqual(load_config(env).mqtt.state_publish_interval_seconds, 30)
            self.assertEqual(
                load_config(
                    env | {"SMAB_MQTT_STATE_PUBLISH_INTERVAL_SECONDS": "10"}
                ).mqtt.state_publish_interval_seconds,
                10,
            )

    def test_setting_rejects_nonpositive_nonfinite_and_malformed_values(self):
        for value in ("0", "-1", "nan", "inf", "", "true"):
            with self.subTest(value=value), self.assertRaises(ConfigError):
                load_config({"SMAB_MQTT_STATE_PUBLISH_INTERVAL_SECONDS": value})
