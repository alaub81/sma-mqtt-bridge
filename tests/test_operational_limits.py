"""Effective-limit redaction and virtual twelve-hour outage/recovery evidence."""

import json
import unittest

from sma_mqtt_bridge.availability import Availability
from sma_mqtt_bridge.config import load_config
from sma_mqtt_bridge.model import Property, SourceState
from sma_mqtt_bridge.operational_limits import summary


class OperationalLimitsTests(unittest.TestCase):
    def test_summary_excludes_private_identity_and_credentials(self):
        config = load_config(
            {
                "SMAB_MQTT_HOST": "private-broker.invalid",
                "SMAB_MQTT_PASSWORD": "private-password",
            }
        )
        result = summary(config)
        self.assertEqual(result["sources"], [])
        self.assertEqual(result["runtime"]["read_cycle_timeout_seconds"], 120)
        self.assertNotIn("private", json.dumps(result))

    def test_twelve_hour_partial_samples_and_outage_recover_independently(self):
        props = (
            Property("measurements", "power", "Power", required_for_ready=True),
            Property("measurements", "energy", "Energy"),
        )
        failed = SourceState("fixture", "fixture", props, 60)
        healthy = SourceState("other", "other", props, 60)
        monitor = Availability("Source fixture", 300)
        failed.update({"measurements/power": 7, "measurements/energy": 1}, now=0)
        monitor.observe("ready", now=0)
        with self.assertLogs("sma_mqtt_bridge.availability") as logs:
            for now in range(30, 43201, 30):
                healthy.update({"measurements/power": 0}, now=now)
                failed.update({"measurements/energy": now}, now=now)
                self.assertEqual(healthy.status(now), "ready")
                if now > 60:
                    self.assertEqual(failed.status(now), "stale")
                    self.assertNotIn("measurements/power", failed.fresh_values(now))
                    monitor.observe("stale", now=now)
            self.assertEqual(failed.values["measurements/power"][0], "7")
            failed.update({"measurements/power": 0}, now=43230)
            monitor.success()
            monitor.observe(failed.status(43230), now=43230)
        self.assertLessEqual(len(logs.output), 146)
        self.assertIn("recovered after 43140.0s", logs.output[-1])
        self.assertEqual(monitor.snapshot(43230)["outageSeconds"], 0)
        self.assertEqual(failed.status(43230), "ready")


class RepeatedOutageTests(unittest.IsolatedAsyncioTestCase):
    async def test_repeated_timeouts_retry_serially_and_recover(self):
        import asyncio
        from unittest.mock import AsyncMock, patch

        from sma_mqtt_bridge.runtime import supervise

        config = load_config({})
        state = SourceState("fixture", "fixture", (Property("measurements", "power", "Power"),), 60)
        stop = asyncio.Event()
        reader = AsyncMock()
        calls = 0

        async def read():
            nonlocal calls
            calls += 1
            if calls <= 60:
                raise TimeoutError
            stop.set()
            return {"measurements/power": 0}

        reader.read.side_effect = read
        with patch("sma_mqtt_bridge.runtime.wait_stop", new_callable=AsyncMock) as wait:
            with self.assertLogs("sma_mqtt_bridge.availability"):
                await supervise(state, reader, 30, config, stop)
        self.assertEqual(calls, 61)
        self.assertEqual(reader.close.await_count, 61)
        self.assertEqual(state.monitor.timeouts, 60)
        self.assertEqual(state.monitor.consecutive_failures, 0)
        self.assertEqual(state.status(), "ready")
        delays = [call.args[1] for call in wait.await_args_list[:-1]]
        self.assertEqual(len(delays), 60)
        self.assertTrue(all(1 <= delay <= 60 for delay in delays))
