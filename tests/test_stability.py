"""Watchdog recovery, independent freshness, fail-closed state and process locking."""

import asyncio
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from sma_mqtt_bridge.availability import Availability
from sma_mqtt_bridge.adapters.http import HTTP
from sma_mqtt_bridge.commands import LocalCommands
from sma_mqtt_bridge.config import load_config
from sma_mqtt_bridge.errors import ConfigError, ProtocolTimeout, StateError
from sma_mqtt_bridge.health import atomic_json
from sma_mqtt_bridge.homie import HomiePublisher
from sma_mqtt_bridge.model import Property, SourceState
from sma_mqtt_bridge.portal_commands import PortalCommands
from sma_mqtt_bridge.runtime import reset_reader, run, sources, supervise
from sma_mqtt_bridge.storage import journal_status, state_lock


class StabilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        self.config = load_config({'SMAB_STATE_DIR': self.tmp.name})

    def test_critical_power_expires_despite_fresh_identity_and_energy(self):
        state = SourceState('fixture', 'test-device', (
            Property('identity', 'model', 'Model', 'string', stale_seconds=600),
            Property('measurements', 'energy', 'Energy', stale_seconds=600),
            Property('measurements', 'power', 'Power', stale_seconds=5, required_for_ready=True)), 60)
        state.update({'identity/model': 'Fixture', 'measurements/energy': 10, 'measurements/power': 0}, now=10)
        self.assertEqual(state.status(11), 'ready')
        state.update({'identity/model': 'Fixture', 'measurements/energy': 11}, now=16)
        self.assertEqual(state.status(16), 'stale')
        self.assertEqual(state.missing_critical(16), ['measurements/power'])
        self.assertNotIn('measurements/power', state.fresh_values(16))
        state.update({'measurements/power': 0}, now=17)
        self.assertEqual(state.status(17), 'ready')

    def test_partial_or_invalid_required_values_never_report_ready(self):
        state = SourceState('fixture', 'test-device', (
            Property('measurements', 'a', 'A', required_for_ready=True),
            Property('measurements', 'b', 'B', required_for_ready=True)), 5)
        state.update({'measurements/a': 1}, now=0)
        self.assertEqual(state.status(0), 'stale')
        state.update({'measurements/b': 0}, now=1)
        self.assertEqual(state.status(1), 'ready')
        state.update({'measurements/b': None}, now=2)
        self.assertEqual(state.status(2), 'stale')

    def test_command_feedback_does_not_mask_a_device_outage(self):
        device = SourceState('fixture', 'test-device', (Property('measurements', 'power', 'Power'),), 5)
        command = SourceState('commands', 'test-device', (Property('commands', 'result', 'Result', 'string'),), 5,
                              contributes_availability=False)
        command.update({'commands/result': 'confirmed'}, now=1)
        publisher = HomiePublisher(self.config, [device, command])
        values, status = publisher.snapshot([device, command], now=2)
        self.assertEqual(values['commands/result'], 'confirmed')
        self.assertEqual(status, 'alert')

    def test_readiness_override_is_validated_before_any_device_io(self):
        for value in ('wrong', 'measurements/power,measurements/power', 'measurements/+', ' measurements/power'):
            with self.assertRaises(ConfigError):
                load_config({'SMAB_INVERTER1_READY_PROPERTIES': value})
        config = load_config({'SMAB_ECHARGER_SEMP_ENABLED': 'true', 'SMAB_ECHARGER_HOST': 'fixture.invalid',
                              'SMAB_ECHARGER_SEMP_DEVICE_ID': 'fixture', 'SMAB_MQTT_HOST': 'fixture.invalid',
                              'SMAB_MQTT_TLS': 'false', 'SMAB_ECHARGER_SEMP_READY_PROPERTIES': 'measurements/power'})
        states = sources(config)
        self.assertEqual(states[0][0].required_keys, ('measurements/power',))
        with self.assertRaises(ConfigError):
            sources(replace(config, echarger=replace(config.echarger, semp_ready_properties='measurements/nonexistent')))

    def test_outage_logging_is_bounded_and_recovery_includes_duration(self):
        monitor = Availability('Source fixture', 300)
        with self.assertLogs('sma_mqtt_bridge.availability') as logs:
            monitor.failure()
            monitor.observe('error', 10)
            monitor.failure(timeout=True)
            monitor.observe('error', 20)
            monitor.observe('error', 309)
            monitor.observe('error', 310)
            monitor.success()
            monitor.observe('ready', 315)
        self.assertEqual(len(logs.output), 3)
        self.assertIn('recovered after 305.0s', logs.output[-1])
        self.assertEqual(monitor.snapshot(315)['failures'], 2)
        self.assertEqual(monitor.snapshot(315)['timeouts'], 1)
        self.assertEqual(monitor.snapshot(315)['outageSeconds'], 0)
        self.assertEqual(monitor.snapshot(315)['consecutiveFailures'], 0)

    def test_corrupt_manifests_fail_before_connections_and_preserve_file(self):
        path = self.path / 'mqtt-topics.json'
        invalid = ['null', '{}', '{', '[' * 2000 + '0' + ']' * 2000, '{"schemaVersion":1,"schemaVersion":1}',
                   json.dumps({'schemaVersion': 1, 'prefix': 'homie', 'devices': {'fixture': ['homie/other/$state']}}),
                   json.dumps({'schemaVersion': 1, 'prefix': 'homie', 'devices': {'fixture': ['homie/fixture/#']}}),
                   json.dumps({'schemaVersion': 1, 'prefix': 'homie', 'devices': {'fixture': ['homie/fixture/$state'] * 2}})]
        for text in invalid:
            path.write_text(text)
            with self.assertRaises(StateError):
                HomiePublisher(self.config, [], client_factory=AsyncMock(side_effect=AssertionError))
            self.assertEqual(path.read_text(), text)
        path.write_text(' ' * 100)
        with self.assertRaises(StateError):
            HomiePublisher(replace(self.config, runtime=replace(self.config.runtime, max_state_bytes=10)), [])

    def test_corrupt_and_dangling_journals_remain_blocked(self):
        path = self.path / 'echarger-command-pending.json'
        self.assertIsNone(journal_status(path, 1000))
        for content in ('null', '{}', '{', '{"schemaVersion":1,"schemaVersion":1}',
                        json.dumps({'schemaVersion': 1, 'property': 'plan', 'targets': {}, 'phase': 'mode',
                                    'timestamp': '2026-10-10T00:00:00Z'})):
            path.write_text(content)
            self.assertEqual(journal_status(path, 1000), 'blocked-corrupt')
        path.unlink()
        path.symlink_to(self.path / 'missing')
        self.assertEqual(journal_status(path, 1000), 'blocked-corrupt')
        path.unlink()
        atomic_json(path, {'schemaVersion': 1, 'property': 'led-brightness', 'target': '5190',
                          'timestamp': '2026-10-10T00:00:00Z'})
        self.assertEqual(journal_status(path, 1000), 'blocked-uncertain')

    def test_fifo_state_is_rejected_without_blocking(self):
        path = self.path / 'mqtt-topics.json'
        os.mkfifo(path)
        with self.assertRaises(StateError):
            HomiePublisher(self.config, [])

    def test_manifest_write_limit_preserves_existing_state(self):
        path = self.path / 'mqtt-topics.json'
        publisher = HomiePublisher(self.config, [])
        publisher.owned = {'test-device': {'homie/test-device/$state'}}
        publisher.save_owned()
        before = path.read_bytes()
        publisher.config = replace(self.config, runtime=replace(self.config.runtime, max_state_bytes=10))
        with self.assertRaises(StateError):
            publisher.save_owned()
        self.assertEqual(path.read_bytes(), before)

    def test_state_lock_excludes_a_second_process_and_releases_after_crash(self):
        source = Path(__file__).resolve().parents[1] / 'ressources'
        env = os.environ.copy() | {'PYTHONPATH': str(source)}
        code = ('import sys\nfrom sma_mqtt_bridge.storage import state_lock\n'
                'with state_lock(sys.argv[1]):\n print("locked", flush=True)\n sys.stdin.readline()\n')
        child = subprocess.Popen([sys.executable, '-c', code, self.tmp.name], stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
        try:
            self.assertEqual(child.stdout.readline().strip(), 'locked')
            with self.assertRaises(StateError):
                with state_lock(self.tmp.name):
                    self.fail('A second instance acquired the lock')
        finally:
            child.kill()
            child.communicate(timeout=5)
        with state_lock(self.tmp.name):
            self.assertTrue((self.path / 'bridge.lock').exists())


class AsyncStabilityTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        config = load_config({'SMAB_STATE_DIR': self.tmp.name})
        self.config = replace(config, runtime=replace(config.runtime, read_cycle_timeout_seconds=.01,
                              shutdown_timeout_seconds=.1, reconnect_min_seconds=.001,
                              reconnect_max_seconds=.002, health_interval_seconds=.01))
        self.state = SourceState('fixture', 'test-device', (Property('measurements', 'power', 'Power'),), 5)

    async def test_hung_read_is_cancelled_reset_and_recovers_without_duplicate_reads(self):
        stop, cancelled = asyncio.Event(), asyncio.Event()
        reader, calls = AsyncMock(), 0
        async def read():
            nonlocal calls
            calls += 1
            if calls == 1:
                try:
                    await asyncio.Event().wait()
                finally:
                    cancelled.set()
            self.assertTrue(cancelled.is_set())
            stop.set()
            return {'measurements/power': 0}
        reader.read.side_effect = read
        await asyncio.wait_for(supervise(self.state, reader, 1, self.config, stop), 1)
        self.assertEqual(calls, 2)
        self.assertEqual(reader.close.await_count, 2)
        self.assertEqual(self.state.status(), 'ready')
        self.assertEqual(self.state.monitor.timeouts, 1)
        self.assertEqual(self.state.monitor.consecutive_failures, 0)

    async def test_session_reset_does_not_interrupt_command_owned_lock(self):
        reader = AsyncMock()
        reader.lock = asyncio.Lock()
        async with reader.lock:
            await reset_reader(reader, self.config)
            reader.close.assert_not_awaited()
        await reset_reader(reader, self.config)
        reader.close.assert_awaited_once()

    async def test_http_timeout_is_redacted_counted_and_resets_only_read_session(self):
        http = HTTP(1, 1000)
        http.session = MagicMock()
        http.session.request.side_effect = TimeoutError('fixture sensitive remote detail')
        with self.assertRaises(ProtocolTimeout) as caught:
            await http.request('GET', 'https://fixture.invalid')
        self.assertNotIn('sensitive', str(caught.exception))
        reader, stop = AsyncMock(), asyncio.Event()
        count = 0
        async def read():
            nonlocal count
            count += 1
            if count == 1:
                raise caught.exception
            stop.set()
            return {'measurements/power': 0}
        reader.read.side_effect = read
        await supervise(self.state, reader, 1, self.config, stop)
        self.assertEqual(self.state.monitor.timeouts, 1)
        self.assertEqual(reader.close.await_count, 2)

    async def test_swallowed_watchdog_cancellation_cannot_publish_a_late_sample(self):
        reader, stop = AsyncMock(), asyncio.Event()
        async def read():
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                stop.set()
                return {'measurements/power': 999}
        reader.read.side_effect = read
        await asyncio.wait_for(supervise(self.state, reader, 1, self.config, stop), 1)
        self.assertEqual(self.state.fresh_values(), {})
        self.assertEqual(self.state.monitor.timeouts, 1)

    async def test_zero_portal_interval_never_triggers_read_watchdog(self):
        stop, reader = asyncio.Event(), AsyncMock()
        task = asyncio.create_task(supervise(self.state, reader, 0, self.config, stop))
        await asyncio.sleep(.04)
        self.assertEqual(self.state.monitor.phase, 'idle')
        self.assertEqual(self.state.monitor.failures, 0)
        reader.read.assert_not_awaited()
        stop.set()
        await task

    async def test_corrupt_journals_block_both_command_adapters_before_network(self):
        api = replace(self.config.echarger, enabled=True, commands_enabled=True)
        portal = replace(self.config.portal, enabled=True, commands_enabled=True)
        config = replace(self.config, echarger=api, portal=portal, commands=replace(self.config.commands, enabled=True))
        result = SourceState('result', 'test-device', (Property('commands', 'local-result', 'Local', 'string'),
                             Property('commands', 'portal-result', 'Portal', 'string')), 5)
        for cls, key, payload, topic in ((LocalCommands, 'led-brightness', b'5190', 'commands/local-result'),
                                        (PortalCommands, 'pv-minimum', b'75', 'commands/portal-result')):
            reader = AsyncMock()
            reader.lock = asyncio.Lock()
            name = 'echarger-command-pending.json' if cls is LocalCommands else 'portal-command-pending.json'
            Path(self.tmp.name, name).write_text('null')
            controller = cls(config, self.state, result, reader=reader)
            self.assertEqual(result.fresh_values()[topic], 'blocked-corrupt')
            await controller.handle(key, payload)
            self.assertEqual(result.fresh_values()[topic], 'blocked-corrupt')
            reader.http.request.assert_not_awaited()
            reader.read_device.assert_not_awaited()
            reader.access_token.assert_not_awaited()
            self.assertEqual(controller.journal.read_text(), 'null')

    async def test_second_runtime_is_rejected_before_sources_or_mqtt(self):
        with state_lock(self.tmp.name), patch('sma_mqtt_bridge.runtime.sources', side_effect=AssertionError):
            with self.assertRaises(StateError):
                await run(self.config, publisher_factory=AsyncMock(side_effect=AssertionError))

    async def test_undersized_journal_limit_rejects_before_put(self):
        config = replace(self.config, runtime=replace(self.config.runtime, max_state_bytes=10),
                         commands=replace(self.config.commands, enabled=True),
                         echarger=replace(self.config.echarger, enabled=True, commands_enabled=True))
        result = SourceState('result', 'test-device', (Property('commands', 'local-result', 'Result', 'string'),), 5)
        reader = AsyncMock()
        reader.lock = asyncio.Lock()
        controller = LocalCommands(config, self.state, result, reader=reader)
        controller.catalog = AsyncMock(return_value={'Parameter.Sys.DevSigBri': {
            'editable': True, 'state': 'Confirmed', 'value': '5173', 'possibleValues': ['5173', '5190']}})
        await controller.handle('led-brightness', b'5190')
        self.assertEqual(result.fresh_values()['commands/local-result'], 'rejected')
        reader.http.request.assert_not_awaited()
        self.assertFalse(controller.journal.exists())

    async def test_diagnostics_switch_does_not_disable_internal_watchdog_metrics(self):
        self.state.diagnostics_enabled = False
        self.state.monitor = Availability('Source fixture', 300)
        self.state.monitor.failure(timeout=True)
        publisher = HomiePublisher(self.config, [self.state])
        self.assertTrue(all(p.node != 'diagnostics' for p in publisher.properties([self.state])))
        self.assertEqual(self.state.monitor.snapshot()['timeouts'], 1)
        self.state.diagnostics_enabled = True
        snapshot, _ = publisher.snapshot([self.state])
        self.assertEqual(snapshot['diagnostics/fixture-timeouts'], '1')
        self.assertEqual(snapshot['diagnostics/fixture-missing-critical'], '1')
