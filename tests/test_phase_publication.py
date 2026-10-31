"""Home Manager phases coalesce publication without changing samples or other topics."""

import asyncio
import tempfile
import unittest
from decimal import Decimal
from unittest.mock import patch

from sma_mqtt_bridge.config import load_config
from sma_mqtt_bridge.errors import ConfigError
from sma_mqtt_bridge.homie import HomiePublisher
from sma_mqtt_bridge.model import Property, SourceState


class PhasePublicationTests(unittest.IsolatedAsyncioTestCase):
    async def exercise(self, interval="5", source="home-manager-phases", changes=None, ticks=7):
        with tempfile.TemporaryDirectory() as tmp:
            config = load_config(
                {
                    "SMAB_STATE_DIR": tmp,
                    "SMAB_HOME_MANAGER_PHASE_PUBLISH_INTERVAL_SECONDS": interval,
                }
            )
            props = (
                Property("measurements", "current-l1", "Current", unit="A"),
                Property("measurements", "power-import", "Grid", unit="W"),
            )
            state = SourceState(source, "meter", props, 30)
            state.update(
                {"measurements/current-l1": "1.001", "measurements/power-import": 100}, now=100
            )
            publisher = HomiePublisher(config, [state])
            clock = [100]
            sent, messages, stop = {}, [], asyncio.Event()

            async def publish(topic, value, **_):
                messages.append((clock[0] - 100, topic, value))

            async def advance(*_):
                clock[0] += 1
                tick = clock[0] - 100
                if tick >= ticks:
                    stop.set()
                    return
                values = {
                    "measurements/current-l1": str(Decimal("1.001") + Decimal(tick) / 1000),
                    "measurements/power-import": 100 + tick,
                }
                if changes:
                    values.update(changes(tick))
                state.update(values, now=clock[0])

            with (
                patch("sma_mqtt_bridge.homie.time.monotonic", side_effect=lambda: clock[0]),
                patch("sma_mqtt_bridge.homie.wait_stop", side_effect=advance),
            ):
                await publisher.publish_values(
                    type("Client", (), {"publish": staticmethod(publish)})(),
                    "homie/meter",
                    [state],
                    stop,
                    sent,
                    0,
                    None,
                )
            return messages, sent

    async def test_default_coalesces_latest_full_precision_without_delaying_totals(self):
        messages, sent = await self.exercise()
        phases = [(t, v) for t, k, v in messages if k.endswith("/currentl1")]
        self.assertEqual(phases, [(0, "1.001"), (5, "1.006")])
        self.assertEqual(sent["homie/meter/measurements/currentl1"], "1.006")
        self.assertEqual(len([1 for _, k, _ in messages if k.endswith("/powerimport")]), 7)

    async def test_disabled_limit_publishes_each_changed_value(self):
        messages, _ = await self.exercise(interval="0")
        self.assertEqual(len([1 for _, k, _ in messages if k.endswith("/currentl1")]), 7)

    async def test_udp_only_owner_is_limited_and_grid_alias_is_not(self):
        messages, _ = await self.exercise(source="home-manager")
        self.assertEqual(len([1 for _, k, _ in messages if k.endswith("/currentl1")]), 2)
        self.assertEqual(len([1 for _, k, _ in messages if k.endswith("/powerdrawn")]), 7)

    async def test_unrelated_device_phase_is_not_limited(self):
        messages, _ = await self.exercise(source="inverter1")
        self.assertEqual(len([1 for _, k, _ in messages if k.endswith("/currentl1")]), 7)

    async def test_return_to_sent_value_does_not_republish_intermediate_value(self):
        messages, _ = await self.exercise(
            changes=lambda t: {"measurements/current-l1": "1.002" if t < 3 else "1.001"}
        )
        self.assertEqual(
            [(t, v) for t, k, v in messages if k.endswith("/currentl1")], [(0, "1.001")]
        )

    async def test_expired_pending_value_is_not_published_and_status_is_immediate(self):
        def change(tick):
            return {
                "measurements/current-l1": None if tick >= 2 else "9.999",
                "measurements/power-import": None if tick >= 2 else 101,
            }

        messages, _ = await self.exercise(changes=change)
        self.assertEqual(
            [(t, v) for t, k, v in messages if k.endswith("/currentl1")], [(0, "1.001")]
        )
        self.assertIn((2, "homie/meter/$state", "alert"), messages)

    async def test_recovery_first_valid_value_does_not_wait_for_previous_limit(self):
        messages, _ = await self.exercise(
            changes=lambda t: {"measurements/current-l1": None if t == 1 else "2.123"}
        )
        self.assertEqual(
            [(t, v) for t, k, v in messages if k.endswith("/currentl1")],
            [(0, "1.001"), (2, "2.123")],
        )

    async def test_new_session_starts_with_immediate_publication(self):
        for _ in range(2):
            messages, _ = await self.exercise(ticks=1)
            self.assertIn((0, "homie/meter/measurements/currentl1", "1.001"), messages)

    def test_config_default_override_and_bounds(self):
        self.assertEqual(load_config({}).home_manager.phase_publish_interval_seconds, 5)
        self.assertEqual(
            load_config(
                {"SMAB_HOME_MANAGER_PHASE_PUBLISH_INTERVAL_SECONDS": "10"}
            ).home_manager.phase_publish_interval_seconds,
            10,
        )
        for v in ("-1", "3601", "nan", "inf"):
            with self.subTest(value=v), self.assertRaises(ConfigError):
                load_config({"SMAB_HOME_MANAGER_PHASE_PUBLISH_INTERVAL_SECONDS": v})
