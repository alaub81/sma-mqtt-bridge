"""Offline runtime, freshness, Homie lifecycle and shutdown regressions."""

import asyncio
from dataclasses import replace
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from sma_mqtt_bridge.config import load_config
from sma_mqtt_bridge.errors import AuthenticationError
from sma_mqtt_bridge.health import atomic_json, healthy, heartbeat
from sma_mqtt_bridge.homie import HomiePublisher, backoff, discovery
from sma_mqtt_bridge.model import Property, SourceState
from sma_mqtt_bridge.runtime import run, sources, supervise


class ModelTests(unittest.TestCase):
    def state(self):
        return SourceState('fixture', 'test-device', (Property('measurements', 'power', 'Power', unit='W'),), 5)

    def test_missing_stale_and_invalid_values_never_become_zero(self):
        state = self.state()
        self.assertEqual(state.status(0), 'init')
        self.assertEqual(state.fresh_values(0), {})
        state.update({'measurements/power': 0}, now=10)
        self.assertEqual(state.fresh_values(11), {'measurements/power': '0'})
        self.assertEqual(state.fresh_values(16), {})
        self.assertEqual(state.status(16), 'stale')
        state.update({'measurements/power': None}, now=17)
        self.assertEqual(state.fresh_values(17), {})
        state.update({'measurements/power': float('nan')}, now=18)
        self.assertEqual(state.fresh_values(18), {})

    def test_partial_update_does_not_refresh_older_properties(self):
        state = SourceState('fixture', 'test-device', (Property('measurements', 'a', 'A'), Property('measurements', 'b', 'B')), 5)
        state.update({'measurements/a': 1, 'measurements/b': 2}, now=10)
        state.update({'measurements/a': 3}, now=14)
        self.assertEqual(state.fresh_values(16), {'measurements/a': '3'})

    def test_slow_poller_expiry_does_not_extend_power_freshness(self):
        state = SourceState('fixture', 'test-device',
                            (Property('measurements', 'power', 'Power', stale_seconds=60),
                             Property('measurements', 'energy', 'Energy', stale_seconds=360)), 60)
        state.update({'measurements/power': 1, 'measurements/energy': 2}, now=0)
        self.assertEqual(state.fresh_values(180), {'measurements/energy': '2'})
        self.assertEqual(state.fresh_values(361), {})

    def test_homie_retained_metadata_read_only(self):
        metadata = discovery('homie', 'test-device', self.state().properties)
        self.assertEqual(metadata['homie/test-device/$homie'], '4.0.0')
        self.assertEqual(metadata['homie/test-device/$nodes'], 'measurements')
        self.assertEqual(metadata['homie/test-device/measurements/power/$unit'], 'W')
        self.assertEqual(metadata['homie/test-device/measurements/power/$settable'], 'false')
        self.assertFalse(any(t.endswith('/set') for t in metadata))

    def test_heartbeat_atomic_freshness_and_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'heartbeat.json'
            atomic_json(path, {'schemaVersion': 2, 'status': 'running', 'pid': os.getpid(), 'monotonic': 10})
            self.assertTrue(healthy(tmp, 5, 14))
            self.assertFalse(healthy(tmp, 5, 16))
            self.assertFalse(healthy(tmp, 5, 9))
            atomic_json(path, {'status': 'stopped'})
            self.assertFalse(healthy(tmp, 5, 14))
            self.assertFalse(path.with_name(path.name + '.tmp').exists())

    def test_heartbeat_rejects_dead_process_old_schema_and_invalid_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'heartbeat.json'
            valid = {'schemaVersion': 2, 'status': 'running', 'pid': os.getpid(), 'monotonic': 10}
            for change in ({'schemaVersion': 1}, {'pid': 0}, {'pid': True}, {'pid': 10 ** 100},
                           {'monotonic': True}, {'monotonic': 10 ** 1000}):
                atomic_json(path, valid | change)
                self.assertFalse(healthy(tmp, 5, 14))
            atomic_json(path, valid)
            with patch('sma_mqtt_bridge.health.os.kill', side_effect=ProcessLookupError):
                self.assertFalse(healthy(tmp, 5, 14))
            with patch('sma_mqtt_bridge.health.time.time', return_value=-100000):
                self.assertTrue(healthy(tmp, 5, 14))

    def test_health_is_liveness_even_when_source_and_mqtt_are_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = load_config({'SMAB_STATE_DIR': tmp})
            state = self.state()
            state.error = True
            heartbeat(config, [state], {'test-device': False})
            self.assertTrue(healthy(tmp, 5))
            data = __import__('json').loads((Path(tmp) / 'heartbeat.json').read_text())
            self.assertEqual(data['sources'], {'fixture': 'error'})
            self.assertEqual(data['mqtt'], {'test-device': False})

    def test_bounded_backoff(self):
        for attempt in range(100):
            delay = backoff(attempt, 1, 60, .5)
            self.assertGreaterEqual(delay, 1)
            self.assertLessEqual(delay, 60)

    def test_disabled_sources_create_no_sessions(self):
        with patch('sma_mqtt_bridge.runtime.ModbusReader', side_effect=AssertionError), patch('sma_mqtt_bridge.runtime.MeterReader', side_effect=AssertionError), patch('sma_mqtt_bridge.runtime.EChargerReader', side_effect=AssertionError), patch('sma_mqtt_bridge.runtime.PortalReader', side_effect=AssertionError):
            self.assertEqual(sources(load_config({})), [])


class FakeClient:
    def __init__(self, *args, **kwargs):
        self.kwargs, self.messages = kwargs, []
        self.stop = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def publish(self, topic, payload, **kwargs):
        self.messages.append((topic, payload, kwargs))
        if topic.endswith('/$state') and payload == 'ready' and self.stop is not None:
            self.stop.set()


class AsyncRuntimeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = load_config({'SMAB_STATE_DIR': self.tmp.name})
        self.config = replace(self.config, runtime=replace(self.config.runtime, health_interval_seconds=.01, shutdown_timeout_seconds=.1))

    async def test_homie_will_retirement_and_graceful_shutdown(self):
        state = SourceState('fixture', 'test-device', (Property('measurements', 'power', 'Power'),), 5)
        state.update({'measurements/power': 12})
        stop = asyncio.Event()
        clients = []
        def factory(*args, **kwargs):
            client = FakeClient(*args, **kwargs)
            client.stop = stop
            clients.append(client)
            return client
        publisher = HomiePublisher(self.config, [state], factory)
        publisher.owned = {'test-device': {'homie/test-device/measurements/retired', 'homie/test-device/measurements/power'}}
        await publisher.run(stop)
        client = clients[0]
        self.assertEqual(client.kwargs['will'].topic, 'homie/test-device/$state')
        self.assertEqual(client.kwargs['will'].payload, 'lost')
        self.assertIn(('homie/test-device/measurements/retired', b''), [(t, p) for t, p, _ in client.messages])
        self.assertIn(('homie/test-device/measurements/power', '12'), [(t, p) for t, p, _ in client.messages])
        self.assertEqual(client.messages[-1][1], 'disconnected')
        self.assertTrue(all(k['retain'] for _, _, k in client.messages))

    async def test_dynamic_inventory_discovery_retirement_and_manifest(self):
        state = SourceState('home-manager', 'test-device', (Property('measurements', 'power', 'Power'),), 5)
        state.update({'measurements/power': 12})
        stop = asyncio.Event()
        client = FakeClient()
        initial = None
        publisher = HomiePublisher(self.config, [state])
        metadata = discovery('homie', 'test-device', state.properties)
        publisher.owned = {'test-device': set(metadata) | {'homie/test-device/measurements/power'}}
        changed = False
        async def publish(topic, payload, **kwargs):
            nonlocal changed
            client.messages.append((topic, payload, kwargs))
            if topic.endswith('/$state') and payload == 'ready' and not changed:
                changed = True
                state.properties = (Property('device-1', 'serial', 'Assigned serial', 'integer'),)
                state.values.clear()
                state.update({'device-1/serial': 123})
            if topic.endswith('/device-1/serial') and payload == '123':
                stop.set()
        client.publish = publish
        await publisher.publish_values(client, 'homie/test-device', [state], stop, {}, 0, None, initial)
        messages = [(t, p) for t, p, _ in client.messages]
        self.assertIn(('homie/test-device/measurements/power/$name', b''), messages)
        self.assertIn(('homie/test-device/device-1/serial/$settable', 'false'), messages)
        self.assertIn(('homie/test-device/$nodes', 'device-1,diagnostics'), messages)
        self.assertNotIn('homie/test-device/measurements/power', publisher.owned['test-device'])
        self.assertIn('homie/test-device/device-1/serial', publisher.owned['test-device'])
        saved = __import__('json').loads((Path(self.tmp.name) / 'mqtt-topics.json').read_text())
        self.assertIn('homie/test-device/device-1/serial', saved['devices']['test-device'])

    async def test_fully_disabled_device_is_retired(self):
        clients = []
        def factory(*args, **kwargs):
            c = FakeClient(*args, **kwargs)
            clients.append(c)
            return c
        publisher = HomiePublisher(self.config, [], factory)
        publisher.owned = {'old-device': {'homie/old-device/$homie', 'homie/old-device/$state'}}
        await publisher.run(asyncio.Event())
        self.assertTrue(all(payload == b'' for _, payload, _ in clients[0].messages))
        self.assertNotIn('old-device', publisher.owned)

    async def test_zero_portal_interval_performs_no_automatic_login(self):
        reader = AsyncMock()
        stop = asyncio.Event()
        state = SourceState('portal', 'test-device', (), 5)
        task = asyncio.create_task(supervise(state, reader, 0, self.config, stop))
        await asyncio.sleep(.01)
        reader.read.assert_not_awaited()
        stop.set()
        await task
        reader.close.assert_awaited_once()

    async def test_authentication_failure_blocks_retry_storm(self):
        reader = AsyncMock()
        reader.read.side_effect = AuthenticationError('Fixture authentication denied')
        state = SourceState('api', 'test-device', (), 5)
        stop = asyncio.Event()
        task = asyncio.create_task(supervise(state, reader, .01, self.config, stop))
        await asyncio.sleep(.03)
        self.assertEqual(reader.read.await_count, 1)
        self.assertEqual(state.status(), 'error')
        stop.set()
        await task

    async def test_main_loop_heartbeat_and_bounded_shutdown(self):
        stop = asyncio.Event()
        class FakePublisher:
            status = {}
            def __init__(self, *args):
                pass
            async def run(self, stop):
                await stop.wait()
        task = asyncio.create_task(run(self.config, stop=stop, publisher_factory=FakePublisher))
        await asyncio.sleep(.03)
        self.assertTrue(healthy(self.tmp.name, 5))
        stop.set()
        await asyncio.wait_for(task, .5)
        self.assertFalse(healthy(self.tmp.name, 5))

    async def test_mqtt_failure_rebuilds_client_and_reannounces(self):
        import aiomqtt
        state = SourceState('fixture', 'test-device', (Property('measurements', 'power', 'Power'),), 5)
        state.update({'measurements/power': 10})
        stop, clients = asyncio.Event(), []
        def factory(*args, **kwargs):
            client = FakeClient(*args, **kwargs)
            if not clients:
                client.publish = AsyncMock(side_effect=aiomqtt.MqttError('fixture failure'))
            else:
                client.stop = stop
            clients.append(client)
            return client
        config = replace(self.config, runtime=replace(self.config.runtime, reconnect_min_seconds=.001, reconnect_max_seconds=.002))
        publisher = HomiePublisher(config, [state], factory)
        await asyncio.wait_for(publisher.run(stop), .5)
        self.assertEqual(len(clients), 2)
        self.assertTrue(any(t.endswith('/$homie') for t, _, _ in clients[1].messages))

    async def test_stale_retained_measurement_is_deleted(self):
        state = SourceState('fixture', 'test-device', (Property('measurements', 'power', 'Power'),), 5)
        state.update({'measurements/power': 10})
        stop, clients = asyncio.Event(), []
        class ExpiringClient(FakeClient):
            async def publish(self, topic, payload, **kwargs):
                await super().publish(topic, payload, **kwargs)
                if topic.endswith('/$state') and payload == 'ready':
                    state.values = {k: (v, received - 10) for k, (v, received) in state.values.items()}
                if topic.endswith('/$state') and payload == 'alert':
                    stop.set()
        def factory(*args, **kwargs):
            client = ExpiringClient(*args, **kwargs)
            clients.append(client)
            return client
        publisher = HomiePublisher(self.config, [state], factory)
        await asyncio.wait_for(publisher.run(stop), .5)
        power = [(p, k) for t, p, k in clients[0].messages if t.endswith('/measurements/power')]
        self.assertEqual([p for p, _ in power], [b'', '10', b''])

    async def test_unacknowledged_shutdown_aborts_transport_for_will(self):
        from sma_mqtt_bridge.homie import mqtt_session
        from unittest.mock import MagicMock
        client = FakeClient()
        client._client = MagicMock()
        with self.assertRaises(asyncio.TimeoutError):
            async with mqtt_session(client, .1, .1):
                raise asyncio.TimeoutError
        client._client.socket().shutdown.assert_called()

    async def test_source_failure_does_not_stop_independent_supervisor(self):
        failing, working = AsyncMock(), AsyncMock()
        failing.read.side_effect = OSError('Uncontrolled fixture error')
        working.read.return_value = {'measurements/power': 42}
        bad = SourceState('bad', 'bad-device', (Property('measurements', 'power', 'Power'),), 5)
        good = SourceState('good', 'good-device', (Property('measurements', 'power', 'Power'),), 5)
        stop = asyncio.Event()
        tasks = [asyncio.create_task(supervise(s, r, .01, self.config, stop)) for s, r in ((bad, failing), (good, working))]
        await asyncio.sleep(.03)
        self.assertEqual(good.status(), 'ready')
        self.assertEqual(bad.status(), 'error')
        stop.set()
        await asyncio.gather(*tasks)

    async def test_manifest_cleans_up_previous_prefix_after_restart(self):
        atomic_json(Path(self.tmp.name) / 'mqtt-topics.json', {'schemaVersion': 1, 'prefix': 'previous',
                    'devices': {'old-device': ['previous/old-device/$homie']}})
        clients = []
        def factory(*args, **kwargs):
            c = FakeClient(*args, **kwargs)
            clients.append(c)
            return c
        publisher = HomiePublisher(self.config, [], factory)
        await publisher.run(asyncio.Event())
        self.assertEqual(clients[0].messages[0][0], 'previous/old-device/$homie')
        self.assertEqual(clients[0].messages[0][1], b'')

    async def test_source_recovers_after_outage(self):
        state = SourceState('fixture', 'test-device', (Property('measurements', 'power', 'Power'),), 5)
        stop = asyncio.Event()
        reader = AsyncMock()
        reader.read.side_effect = [OSError('fixture outage'), {'measurements/power': 42}]
        config = replace(self.config, runtime=replace(self.config.runtime, reconnect_min_seconds=.001,
                                                    reconnect_max_seconds=.002))
        async def delay(*args):
            if state.last_success is not None:
                stop.set()
        with patch('sma_mqtt_bridge.runtime.wait_stop', side_effect=delay):
            await supervise(state, reader, .01, config, stop)
        self.assertEqual(reader.read.await_count, 2)
        self.assertEqual(state.status(), 'ready')
        reader.close.assert_awaited_once()

    async def test_runtime_rejects_cancelled_or_silently_stopped_publisher(self):
        state = SourceState('fixture', 'test-device', (), 5)
        for cancelled in (False, True):
            reader = AsyncMock()
            reader.read.side_effect = OSError('fixture outage')
            class BrokenPublisher:
                status = {}
                def __init__(self, *args):
                    pass
                async def run(self, stop):
                    if cancelled:
                        raise asyncio.CancelledError
            with patch('sma_mqtt_bridge.runtime.sources', return_value=[(state, reader, 1)]):
                with self.assertRaisesRegex(RuntimeError, 'supervisor'):
                    await asyncio.wait_for(run(self.config, publisher_factory=BrokenPublisher), .5)
            self.assertFalse(healthy(self.tmp.name, 5))
            reader.close.assert_awaited_once()

    async def test_mqtt_failure_cleans_up_other_device_sessions(self):
        states = [SourceState('fixture', d, (), 5) for d in ('a', 'b')]
        publisher = HomiePublisher(self.config, states)
        started, closed = asyncio.Event(), asyncio.Event()
        async def serve(device, states, stop):
            if device == 'a':
                await started.wait()
                raise RuntimeError('fixture failure')
            try:
                started.set()
                await asyncio.Event().wait()
            finally:
                closed.set()
        publisher.serve_device = serve
        with self.assertRaises(RuntimeError):
            await publisher.run(asyncio.Event())
        self.assertTrue(closed.is_set())
