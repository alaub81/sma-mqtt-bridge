"""Portal refresh wakes serialized reads without preference writes or replay."""

import asyncio
import tempfile
import unittest
from dataclasses import replace
from unittest.mock import AsyncMock, patch

from sma_mqtt_bridge.config import load_config
from sma_mqtt_bridge.errors import AuthenticationError
from sma_mqtt_bridge.homie import discovery
from sma_mqtt_bridge.model import Property, SourceState
from sma_mqtt_bridge.portal_commands import CommandRouter
from sma_mqtt_bridge.portal_refresh import PortalRefresh
from sma_mqtt_bridge.runtime import run_locked, supervise


class PortalRefreshTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.config = load_config({"SMAB_STATE_DIR": directory.name, "SMAB_MQTT_TLS": "false"})
        self.state = SourceState(
            "portal", "fixture", (Property("portal", "pv-minimum", "PV"),), 1800
        )
        self.result = SourceState(
            "portal-refresh",
            "fixture",
            (Property("portal", "refresh", "Refresh", "string"),),
            1800,
            contributes_availability=False,
        )
        self.refresh = PortalRefresh(self.result)
        self.stop = asyncio.Event()

    async def until(self, predicate):
        async with asyncio.timeout(1):
            while not predicate():
                await asyncio.sleep(0)

    async def start(self, reader, interval, initial=False):
        task = asyncio.create_task(
            supervise(self.state, reader, interval, self.config, self.stop, initial, self.refresh)
        )

        async def cleanup():
            self.stop.set()
            await asyncio.wait_for(task, 1)

        self.addAsyncCleanup(cleanup)
        return task

    async def test_zero_interval_no_startup_read_retained_or_invalid_replay(self):
        reader = AsyncMock()
        reader.read.return_value = {"portal/pv-minimum": 80}
        await self.start(reader, 0)
        await asyncio.sleep(0)
        for payload in (b"REFRESH", b"80", b"", "refresh"):
            await self.refresh.handle("refresh", payload)
        await self.refresh.handle("refresh", b"refresh", retained=True)
        reader.read.assert_not_awaited()
        self.assertFalse(self.refresh.event.is_set())
        router = CommandRouter(refresh=self.refresh)
        await router.handle("refresh", b"refresh")
        await self.until(lambda: reader.read.await_count == 1 and not self.refresh.reading)
        self.assertEqual(self.state.fresh_values()["portal/pv-minimum"], "80")
        self.assertEqual(self.result.fresh_values()["portal/refresh"], "completed")
        await asyncio.sleep(0)
        self.assertEqual(reader.read.await_count, 1)

    async def test_periodic_wait_wakes_and_clicks_during_read_are_coalesced(self):
        reader, entered, release = AsyncMock(), asyncio.Event(), asyncio.Event()
        calls = 0

        async def read():
            nonlocal calls
            calls += 1
            if calls == 2:
                entered.set()
                await release.wait()
            return {"portal/pv-minimum": 70 + calls}

        reader.read.side_effect = read
        await self.start(reader, 900)
        await self.until(lambda: calls == 1 and not self.refresh.reading)
        await self.refresh.handle("refresh", b"refresh")
        await asyncio.wait_for(entered.wait(), 1)
        for _ in range(20):
            await self.refresh.handle("refresh", b"refresh")
        release.set()
        await self.until(lambda: not self.refresh.reading)
        await asyncio.sleep(0)
        self.assertEqual(calls, 2)
        self.assertFalse(self.refresh.event.is_set())
        self.assertEqual(self.state.fresh_values()["portal/pv-minimum"], "72")

    async def test_auth_failure_blocks_refresh_until_restart(self):
        reader = AsyncMock()
        reader.read.side_effect = AuthenticationError("fixture")
        await self.start(reader, 0)
        await self.refresh.handle("refresh", b"refresh")
        await self.until(lambda: self.refresh.blocked)
        for _ in range(10):
            await self.refresh.handle("refresh", b"refresh")
        self.assertFalse(self.refresh.event.is_set())
        self.assertEqual(reader.read.await_count, 1)
        self.assertEqual(self.result.fresh_values()["portal/refresh"], "auth-blocked")

    async def test_transient_failure_preserves_value_and_backoff(self):
        reader = AsyncMock()
        self.state.update({"portal/pv-minimum": 65})
        reader.read.side_effect = [OSError("fixture"), {"portal/pv-minimum": 75}]
        waits = []

        async def retry(stop, delay):
            waits.append(delay)
            self.assertEqual(self.state.values["portal/pv-minimum"][0], "65")
            self.assertEqual(self.result.fresh_values()["portal/refresh"], "failed")
            await self.refresh.handle("refresh", b"refresh")

        with patch("sma_mqtt_bridge.runtime.wait_stop", retry):
            await self.start(reader, 0)
            await self.refresh.handle("refresh", b"refresh")
            await self.until(lambda: reader.read.await_count == 2 and not self.refresh.reading)
        self.assertEqual(len(waits), 1)
        self.assertEqual(self.state.fresh_values()["portal/pv-minimum"], "75")

    async def test_runtime_exposes_refresh_without_any_write_gates(self):
        config = replace(self.config, portal=replace(self.config.portal, enabled=True))
        reader = AsyncMock()
        reader.read.return_value = {"portal/pv-minimum": 85}
        test = self

        class Publisher:
            def __init__(self, config, states):
                self.states, self.status = states, {}
                self.command_controller = None

            async def run(self, stop):
                props = [p for s in self.states for p in s.properties if p.settable]
                test.assertEqual([p.key for p in props], ["portal/refresh"])
                await self.command_controller.handle("refresh", b"refresh")
                await test.until(lambda: test.state.fresh_values().get("portal/pv-minimum") == "85")
                stop.set()

        with patch("sma_mqtt_bridge.runtime.sources", return_value=[(self.state, reader, 0)]):
            await asyncio.wait_for(
                run_locked(config, stop=self.stop, publisher_factory=Publisher), 1
            )
        reader.read.assert_awaited_once()
        reader.close.assert_awaited_once()

    async def test_disabled_portal_has_no_refresh_or_command_consumer(self):
        test = self

        class Publisher:
            def __init__(self, config, states):
                self.command_controller = None
                self.status = {}
                test.assertFalse(any(p.settable for s in states for p in s.properties))

            async def run(self, stop):
                test.assertIsNone(self.command_controller)
                stop.set()

        with patch("sma_mqtt_bridge.runtime.sources", return_value=[]):
            await asyncio.wait_for(
                run_locked(self.config, stop=self.stop, publisher_factory=Publisher), 1
            )

    async def test_deadline_cancels_read_and_uses_existing_session_reset(self):
        reader = AsyncMock()
        config = replace(
            self.config,
            runtime=replace(self.config.runtime, read_cycle_timeout_seconds=0.001),
        )
        cancelled = asyncio.Event()

        async def read():
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()

        async def backoff(stop, delay):
            stop.set()

        reader.read.side_effect = read
        with (
            patch("sma_mqtt_bridge.runtime.reset_reader", new_callable=AsyncMock) as reset,
            patch("sma_mqtt_bridge.runtime.wait_stop", backoff),
        ):
            await supervise(self.state, reader, 0, config, self.stop, True, self.refresh)
        self.assertTrue(cancelled.is_set())
        reset.assert_awaited_once_with(reader, config)
        self.assertEqual(self.result.fresh_values()["portal/refresh"], "failed")
        self.assertFalse(self.refresh.reading)
        props = (Property("portal", "refresh", "Refresh", "string", settable=True),)
        metadata = discovery("homie", "fixture", props)
        self.assertEqual(metadata["homie/fixture/portal/refresh/$datatype"], "string")
        self.assertEqual(metadata["homie/fixture/portal/refresh/$settable"], "true")
