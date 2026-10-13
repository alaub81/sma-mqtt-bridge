"""Deterministic virtual-time supervision, watchdog and MQTT fault sequences."""

import asyncio
import json
import tempfile
import unittest
from collections import Counter
from dataclasses import replace
from pathlib import Path
from unittest.mock import AsyncMock, patch

import aiomqtt

from sma_mqtt_bridge.config import load_config
from sma_mqtt_bridge.errors import ProtocolTimeout
from sma_mqtt_bridge.homie import HomiePublisher, backoff
from sma_mqtt_bridge.model import Property, SampleValues, SourceState
from sma_mqtt_bridge.runtime import supervise

# Bound fixture deadlocks while allowing asyncio debug overhead under CI QEMU.
# This wall-clock guard is independent of virtual time and production watchdogs.
VIRTUAL_SEQUENCE_TIMEOUT_SECONDS = 120


class VirtualClock:
    def __init__(self):
        self.now = 1000.0

    def monotonic(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def deterministic_backoff(attempt, minimum, maximum):
    return backoff(attempt, minimum, maximum, random_value=0.5)


class LongOutageTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.config = load_config({"SMAB_STATE_DIR": self.directory.name, "SMAB_MQTT_TLS": "false"})
        self.clock = VirtualClock()
        # Patch module bindings, not time.monotonic itself: asyncio's timer must stay real.
        for module in ("model", "availability", "runtime", "homie"):
            self.enterContext(patch(f"sma_mqtt_bridge.{module}.time", self.clock))
        for module in ("runtime", "homie"):
            self.enterContext(patch(f"sma_mqtt_bridge.{module}.backoff", deterministic_backoff))
        self.props = (
            Property("measurements", "power", "Power", required_for_ready=True),
            Property("measurements", "energy", "Energy"),
        )

    async def test_twelve_hours_mixed_read_faults_keep_other_supervisor_ready(self):
        failed = SourceState("failed", "fixture", self.props, 60)
        healthy = SourceState("healthy", "other", self.props, 60)
        failed.update({"measurements/power": 7, "measurements/energy": 1})
        stop, ticks = asyncio.Event(), asyncio.Queue()
        bad_reader, good_reader = AsyncMock(), AsyncMock()
        healthy_ack = None
        phases, waits = Counter(), []
        active, peak = 0, 0
        timeout_count = 0

        async def bad_read():
            nonlocal active, peak, timeout_count
            active += 1
            peak = max(peak, active)
            try:
                elapsed = self.clock.now - 1000
                if elapsed < 3600:
                    phases["normal"] += 1
                    return {"measurements/power": 7, "measurements/energy": elapsed}
                if elapsed < 10800:
                    phases["partial"] += 1
                    return {"measurements/energy": elapsed}
                if elapsed < 25200:
                    phases["timeout"] += 1
                    timeout_count += 1
                    self.clock.advance(10)
                    raise ProtocolTimeout("Synthetic read timeout")
                if elapsed < 32400:
                    phases["late-sample"] += 1
                    # A successful slow response cannot refresh an almost-expired device sample.
                    observed = self.clock.now - 59
                    self.clock.advance(5)
                    return SampleValues(
                        {"measurements/power": 999, "measurements/energy": elapsed},
                        {"measurements/power": observed},
                    )
                if elapsed < 39600:
                    phases["connection-error"] += 1
                    raise OSError("Synthetic disconnected device")
                phases["recovered"] += 1
                return {"measurements/power": 0, "measurements/energy": elapsed}
            finally:
                active -= 1

        async def good_read():
            nonlocal healthy_ack
            healthy_ack = await ticks.get()
            return {"measurements/power": 0, "measurements/energy": self.clock.now}

        async def wait(event, delay):
            nonlocal healthy_ack
            if asyncio.current_task().get_name() == "healthy-fixture":
                healthy_ack.set_result(None)
                return
            self.assertLessEqual(delay, 60)
            waits.append(delay)
            elapsed = self.clock.now - 1000
            if 10900 < elapsed < 25100 or 32500 < elapsed < 39500:
                self.assertEqual(failed.status(), "error")
            if 10900 < elapsed < 25100:
                self.assertEqual(failed.values["measurements/power"][0], "7")
            if 3700 < elapsed < 10700 or 25300 < elapsed < 32300:
                self.assertEqual(failed.status(), "stale")
                self.assertNotIn("measurements/power", failed.fresh_values())
            self.clock.advance(delay)
            ack = asyncio.get_running_loop().create_future()
            await ticks.put(ack)
            await ack
            self.assertEqual(healthy.status(), "ready")
            self.assertEqual(healthy.fresh_values()["measurements/power"], "0")
            self.assertLessEqual(len(failed.values), len(self.props))
            if self.clock.now - 1000 >= 43200:
                stop.set()
                # Release the healthy read waiting for the next tick so both supervisors close.
                await ticks.put(asyncio.get_running_loop().create_future())

        bad_reader.read.side_effect, good_reader.read.side_effect = bad_read, good_read
        with (
            patch("sma_mqtt_bridge.runtime.wait_stop", side_effect=wait),
            self.assertLogs("sma_mqtt_bridge.availability") as logs,
        ):
            tasks = [
                asyncio.create_task(supervise(failed, bad_reader, 30, self.config, stop)),
                asyncio.create_task(
                    supervise(healthy, good_reader, 30, self.config, stop), name="healthy-fixture"
                ),
            ]
            try:
                await asyncio.wait_for(asyncio.gather(*tasks), VIRTUAL_SEQUENCE_TIMEOUT_SECONDS)
            finally:
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
        self.assertEqual(
            set(phases),
            {"normal", "partial", "timeout", "late-sample", "connection-error", "recovered"},
        )
        self.assertEqual(peak, 1)
        self.assertEqual(active, 0)
        self.assertEqual(bad_reader.close.await_count, timeout_count + 1)
        self.assertEqual(good_reader.close.await_count, 1)
        self.assertEqual(failed.monitor.timeouts, timeout_count)
        self.assertEqual(failed.monitor.consecutive_failures, 0)
        self.assertEqual(failed.monitor.snapshot()["outageSeconds"], 0)
        self.assertEqual(failed.status(), "ready")
        self.assertEqual(failed.fresh_values()["measurements/power"], "0")
        self.assertGreater(len(waits), 500)
        self.assertLess(len(logs.output), 170)

    async def test_twenty_four_watchdog_cancellations_release_each_read_before_retry(self):
        config = replace(
            self.config, runtime=replace(self.config.runtime, read_cycle_timeout_seconds=0.001)
        )
        state = SourceState("fixture", "fixture", self.props, 60)
        stop, reader = asyncio.Event(), AsyncMock()
        calls, active, cancelled = 0, 0, 0

        async def read():
            nonlocal calls, active, cancelled
            self.assertEqual(active, 0)
            calls += 1
            active += 1
            try:
                if calls <= 24:
                    try:
                        await asyncio.Event().wait()
                    except asyncio.CancelledError:
                        cancelled += 1
                        self.clock.advance(1800)
                        raise
                stop.set()
                return {"measurements/power": 0}
            finally:
                active -= 1

        async def wait(_stop, delay):
            self.assertEqual(active, 0)
            self.clock.advance(delay)

        reader.read.side_effect = read
        with (
            patch("sma_mqtt_bridge.runtime.wait_stop", side_effect=wait),
            self.assertLogs("sma_mqtt_bridge.availability"),
        ):
            await asyncio.wait_for(supervise(state, reader, 30, config, stop), 5)
        self.assertEqual((calls, cancelled, active), (25, 24, 0))
        self.assertEqual(reader.close.await_count, 25)
        self.assertEqual(state.monitor.timeouts, 24)
        self.assertEqual(state.monitor.consecutive_failures, 0)
        self.assertEqual(state.status(), "ready")
        self.assertGreaterEqual(self.clock.now - 1000, 43200)

    async def test_twelve_hour_broker_faults_cleanup_sessions_preserve_state_and_recover(self):
        state = SourceState("fixture", "fixture", self.props, 60)
        state.update({"measurements/power": 1})
        stop = asyncio.Event()
        retained = {"homie/fixture/measurements/power": "1"}
        stats = Counter()
        journal = Path(self.directory.name) / "echarger-command-pending.json"
        journal.write_text('{"schemaVersion":1,"property":"fixture","target":"1"}\n')
        original_journal = journal.read_bytes()
        clock, test = self.clock, self

        class Client:
            def __init__(self, *_args, **kwargs):
                test.assertEqual(kwargs["will"].payload, "lost")
                test.assertTrue(kwargs["will"].retain)
                test.assertEqual(
                    kwargs["max_queued_outgoing_messages"], test.config.mqtt.max_queue_messages
                )
                stats["attempts"] += 1

            async def __aenter__(self):
                if clock.now - 1000 < 36000:
                    raise aiomqtt.MqttError("Synthetic unavailable broker")
                stats["active"] += 1
                stats["peak"] = max(stats["peak"], stats["active"])
                return self

            async def __aexit__(self, *_args):
                stats["active"] -= 1
                stats["closed"] += 1

            async def publish(self, topic, value, **kwargs):
                test.assertTrue(kwargs["retain"])
                if topic.endswith("/measurements/power") and clock.now - 1000 < 43200:
                    # The broker receives a retained message but its ACK is lost/delayed.
                    retained[topic] = value
                    stats["lost-acks"] += 1
                    clock.advance(300)
                    raise TimeoutError("Synthetic acknowledgement timeout")
                retained[topic] = value
                if topic.endswith("/$state") and value == "ready":
                    stop.set()

        publisher = HomiePublisher(self.config, [state], client_factory=Client)
        publisher.owned = {"fixture": {"homie/fixture/measurements/obsolete"}}
        publisher.save_owned()
        publisher.command_controller = AsyncMock()
        original_tasks = set(asyncio.all_tasks())

        async def wait(_stop, delay):
            if _stop.is_set():
                return
            self.assertTrue(1 <= delay <= 60)
            self.assertEqual(stats["active"], 0)
            self.clock.advance(delay)
            state.update({"measurements/power": 0, "measurements/energy": self.clock.now})
            self.assertEqual(state.status(), "ready")

        with (
            patch("sma_mqtt_bridge.homie.wait_stop", side_effect=wait),
            self.assertLogs("sma_mqtt_bridge.availability") as logs,
        ):
            await asyncio.wait_for(
                publisher.serve_device("fixture", [state], stop), VIRTUAL_SEQUENCE_TIMEOUT_SECONDS
            )
        self.assertGreater(stats["attempts"], 500)
        self.assertGreater(stats["lost-acks"], 20)
        self.assertEqual(stats["closed"], stats["lost-acks"] + 1)
        self.assertEqual((stats["active"], stats["peak"]), (0, 1))
        self.assertEqual(retained["homie/fixture/measurements/power"], "0")
        self.assertEqual(retained["homie/fixture/$state"], "disconnected")
        self.assertEqual(retained["homie/fixture/measurements/obsolete"], b"")
        self.assertNotIn("homie/fixture/measurements/obsolete", publisher.owned["fixture"])
        manifest = json.loads((Path(self.directory.name) / "mqtt-topics.json").read_text())
        self.assertEqual(set(manifest["devices"]["fixture"]), publisher.owned["fixture"])
        self.assertEqual(journal.read_bytes(), original_journal)
        publisher.command_controller.handle.assert_not_awaited()
        self.assertEqual(publisher.monitors["fixture"].timeouts, stats["lost-acks"])
        self.assertEqual(publisher.monitors["fixture"].consecutive_failures, 0)
        self.assertEqual(publisher.monitors["fixture"].snapshot()["outageSeconds"], 0)
        self.assertLess(len(logs.output), 170)
        self.assertEqual(set(asyncio.all_tasks()), original_tasks)
