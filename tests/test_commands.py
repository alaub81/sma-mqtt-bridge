"""Offline command gating, exact payloads, readback and uncertain-write persistence."""

import asyncio
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock

from sma_mqtt_bridge.commands import LOCAL_COMMANDS, LocalCommands, command_target
from sma_mqtt_bridge.adapters.echarger import settings_values
from sma_mqtt_bridge.config import load_config
from sma_mqtt_bridge.errors import ProtocolError
from sma_mqtt_bridge.homie import HomiePublisher, discovery
from sma_mqtt_bridge.model import Property, SourceState


def catalog(value='5191', editable=True, state='Confirmed'):
    return {'Parameter.Sys.DevSigBri': {'value': value, 'state': state, 'editable': editable,
                                      'possibleValues': ['5191', '5190', '5173']}}


class CommandsTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        config = load_config({'SMAB_STATE_DIR': self.tmp.name})
        self.config = replace(config, echarger=replace(config.echarger, enabled=True, commands_enabled=True),
                              commands=replace(config.commands, enabled=True, readback_timeout_seconds=.02,
                                               readback_interval_seconds=.001))
        self.api = SourceState('api', 'sma-echarger', (Property('settings', 'led-brightness', 'LED', 'enum', format='5191,5190,5173'),), 180)
        self.result = SourceState('commands', 'sma-echarger', (Property('commands', 'local-result', 'Result', 'string'),), 180)
        self.controller = LocalCommands(self.config, self.api, self.result)
        self.controller.catalog = AsyncMock(side_effect=[catalog(), catalog('5190')])
        self.controller.reader.access_token = AsyncMock(return_value='fixture-token')
        self.controller.reader.http.request = AsyncMock(return_value=(200, {}, ''))

    def status(self):
        return self.result.fresh_values()['commands/local-result']

    async def test_one_put_and_only_confirmed_readback_updates_state(self):
        await self.controller.handle('led-brightness', b'5190')
        request = self.controller.reader.http.request
        request.assert_awaited_once()
        args, kwargs = request.call_args
        self.assertEqual(args[0], 'PUT')
        self.assertTrue(args[1].endswith('/api/v1/parameters/IGULD:SELF'))
        target = kwargs['json']['values'][0]
        self.assertEqual(target['channelId'], 'Parameter.Sys.DevSigBri')
        self.assertEqual(target['value'], '5190')
        self.assertTrue(target['timestamp'].endswith('Z'))
        self.assertEqual(self.status(), 'confirmed')
        self.assertEqual(self.api.fresh_values()['settings/led-brightness'], '5190')
        self.assertFalse(self.controller.journal.exists())
        await self.controller.close()

    async def test_retained_disabled_invalid_and_read_only_commands_never_write(self):
        for key, data, retained in [('led-brightness', b'5190', True), ('power', b'1000', False),
                                    ('led-brightness', b'bad', False), ('led-brightness', b'\xff', False),
                                    ('led-brightness', b'x' * 65, False)]:
            self.controller.catalog.side_effect = None
            self.controller.catalog.return_value = catalog()
            # Pylint also infers the two-argument replacement in a separate test.
            await self.controller.handle(key, data, retained)  # pylint: disable=too-many-function-args
            self.controller.reader.http.request.assert_not_awaited()
        self.controller.config = replace(self.config, commands=replace(self.config.commands, enabled=False))
        await self.controller.handle('led-brightness', b'5190')
        self.assertEqual(self.status(), 'rejected-disabled')
        self.controller.reader.http.request.assert_not_awaited()
        await self.controller.close()

    async def test_metadata_rights_choices_and_target_mode_guard(self):
        for entry in [catalog(editable=False), catalog(state='Pending'),
                      {'Parameter.Sys.DevSigBri': catalog()['Parameter.Sys.DevSigBri'] | {'possibleValues': ['5191']}}]:
            self.controller.catalog.side_effect = None
            self.controller.catalog.return_value = entry
            await self.controller.handle('led-brightness', b'5190')
            self.assertEqual(self.status(), 'rejected')
        with self.assertRaises(ProtocolError):
            command_target('charge-mode', '4720', {'Parameter.Chrg.ActChaMod': {
                'state': 'Confirmed', 'editable': True, 'possibleValues': ['4720']}})
        for key in ['plan-energy', 'plan-end', 'stop-delay']:
            self.assertNotIn(key, LOCAL_COMMANDS)
        self.controller.reader.http.request.assert_not_awaited()
        await self.controller.close()

    async def test_equal_target_is_idempotent_without_write(self):
        self.controller.catalog.side_effect = None
        self.controller.catalog.return_value = catalog('5190')
        await self.controller.handle('led-brightness', b'5190')
        self.assertEqual(self.status(), 'already-confirmed')
        self.controller.reader.http.request.assert_not_awaited()
        await self.controller.close()

    async def test_uncertain_response_persists_across_new_controller(self):
        self.controller.reader.http.request.side_effect = ProtocolError('fixture response lost')
        await self.controller.handle('led-brightness', b'5190')
        self.assertEqual(self.status(), 'uncertain')
        self.assertTrue(self.controller.journal.exists())
        self.assertEqual(self.controller.journal.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.api.fresh_values(), {})
        newer = LocalCommands(self.config, self.api, self.result)
        newer.catalog = AsyncMock()
        await newer.handle('led-brightness', b'5190')
        self.assertEqual(self.status(), 'blocked-uncertain')
        newer.catalog.assert_not_awaited()
        await newer.close()
        await self.controller.close()

    async def test_pending_poll_preserves_retained_observation_and_uncertain_guard(self):
        self.addAsyncCleanup(self.controller.close)
        key = 'settings/led-brightness'
        self.api.update({key: settings_values(catalog())[key]})
        publisher = HomiePublisher(self.config, [self.api, self.result])
        stop, retained, sent = asyncio.Event(), {}, {}
        async def publish(topic, value, **kwargs):
            self.assertTrue(kwargs['retain'])
            retained[topic] = value
            stop.set()
        client = AsyncMock()
        client.publish.side_effect = publish
        base = self.config.mqtt.homie_prefix + '/sma-echarger'
        topic = base + '/settings/ledbrightness'
        async def cycle():
            stop.clear()
            await publisher.publish_values(client, base, [self.api, self.result], stop, sent, 0, None)
        await cycle()
        self.assertEqual(retained[topic], '5191')
        self.controller.reader.http.request.side_effect = ProtocolError('fixture response lost')
        await self.controller.handle('led-brightness', b'5190')
        self.assertEqual(self.status(), 'uncertain')
        self.api.update({key: settings_values(catalog('5190', state='Pending'))[key]})
        self.assertNotIn(key, self.api.fresh_values())
        await cycle()
        self.assertEqual(retained[topic], '5191')
        self.assertTrue(self.controller.journal.exists())
        self.api.update({key: settings_values(catalog('5190'))[key]})
        await cycle()
        self.assertEqual(retained[topic], '5190')
        self.assertEqual(self.status(), 'uncertain')
        await self.controller.handle('led-brightness', b'5190')
        self.assertEqual(self.status(), 'blocked-uncertain')
        self.controller.reader.http.request.assert_awaited_once()
        self.assertTrue(self.controller.journal.exists())

    async def test_http_success_with_unconfirmed_readback_is_uncertain(self):
        self.controller.catalog.side_effect = None
        self.controller.catalog.return_value = catalog()
        await self.controller.handle('led-brightness', b'5190')
        self.assertEqual(self.status(), 'uncertain')
        self.controller.reader.http.request.assert_awaited_once()
        self.assertEqual(self.api.fresh_values(), {})
        await self.controller.close()

    async def test_busy_and_cancelled_write_never_retries(self):
        started = asyncio.Event()
        async def pending(*args, **kwargs):
            started.set()
            await asyncio.Event().wait()
        self.controller.reader.http.request.side_effect = pending
        task = asyncio.create_task(self.controller.handle('led-brightness', b'5190'))
        await started.wait()
        await self.controller.handle('led-brightness', b'5173')
        self.assertEqual(self.status(), 'rejected-busy')
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertEqual(self.status(), 'uncertain')
        self.controller.reader.http.request.assert_awaited_once()
        await self.controller.close()

    def test_boolean_choices_and_measurement_discovery(self):
        entry = {'Parameter.Chrg.ChrgApv': {'editable': True, 'state': 'Confirmed', 'possibleValues': ['5171', '5172']}}
        self.assertEqual(command_target('charging-release', 'true', entry)[1], '5172')
        self.assertEqual(command_target('charging-release', 'false', entry)[1], '5171')
        with self.assertRaises(ProtocolError):
            command_target('charging-release', 'ON', entry)
        metadata = discovery('homie', 'sma-echarger', (Property('settings', 'charging-release', 'Release', 'boolean', settable=True), Property('measurements', 'power', 'Power')))
        self.assertEqual(metadata['homie/sma-echarger/settings/chargingrelease/$settable'], 'true')
        self.assertEqual(metadata['homie/sma-echarger/measurements/power/$settable'], 'false')

    async def test_http_put_transport_never_retries_lost_response(self):
        from sma_mqtt_bridge.adapters.http import HTTP
        writes = []
        async def server(reader, writer):
            try:
                while True:
                    header = await reader.readuntil(b'\r\n\r\n')
                    length = next((int(line.split(b':', 1)[1]) for line in header.split(b'\r\n') if line.lower().startswith(b'content-length:')), 0)
                    await reader.readexactly(length)
                    if header.startswith(b'PUT '):
                        writes.append(header)
                        return
                    writer.write(b'HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\n{}')
                    await writer.drain()
            except asyncio.IncompleteReadError:
                pass
            finally:
                writer.close()
                await writer.wait_closed()
        listener = await asyncio.start_server(server, '127.0.0.1', 0)
        http = HTTP(1, 1000, allow_put=True)
        try:
            url = 'http://127.0.0.1:' + str(listener.sockets[0].getsockname()[1])
            await http.request('GET', url)
            with self.assertRaises(ProtocolError):
                await http.request('PUT', url, json={'values': []})
            self.assertEqual(len(writes), 1)
        finally:
            await http.close()
            listener.close()
            await listener.wait_closed()
        self.assertFalse(Path(self.tmp.name, 'echarger-command-pending.json').exists())

    async def test_config_requires_independent_activation_gates(self):
        from sma_mqtt_bridge.errors import ConfigError
        env = {'SMAB_COMMANDS_ENABLED': 'true', 'SMAB_ECHARGER_COMMANDS_ENABLED': 'true',
               'SMAB_ECHARGER_ENABLED': 'true', 'SMAB_ECHARGER_HOST': 'fixture.invalid',
               'SMAB_ECHARGER_USERNAME': 'fixture', 'SMAB_ECHARGER_PASSWORD': 'fixture',
               'SMAB_ECHARGER_EXPECTED_SERIAL': '123', 'SMAB_ECHARGER_TLS_VERIFY': 'false',
               'SMAB_MQTT_HOST': 'fixture.invalid', 'SMAB_MQTT_TLS': 'false'}
        config = load_config(env)
        self.assertTrue(config.commands.enabled)
        for change in [{'SMAB_ECHARGER_ENABLED': 'false'}, {'SMAB_ECHARGER_COMMANDS_ENABLED': 'false'},
                       {'SMAB_PORTAL_COMMANDS_ENABLED': 'true'}, {'SMAB_INVERTER1_COMMANDS_ENABLED': 'true'}]:
            with self.subTest(change=change), self.assertRaises(ConfigError):
                load_config(env | change)

    async def test_homie_retained_unknown_and_busy_messages(self):
        from types import SimpleNamespace
        from sma_mqtt_bridge.homie import HomiePublisher
        base = 'homie/sma-echarger'
        blocker = asyncio.Event()
        handled = []
        async def handle(key, data):
            handled.append((key, data))
            await blocker.wait()
        controller = self.controller
        controller.handle = handle
        async def incoming():
            for topic, data, retained in [
                (base + '/settings/ledbrightness/set', b'5173', True),
                (base + '/measurements/power/set', b'1', False),
                (base + '/settings/ledbrightness/set', b'5190', False),
                (base + '/settings/ledbrightness/set', b'5173', False),
            ]:
                yield SimpleNamespace(topic=topic, payload=data, retain=retained)
                await asyncio.sleep(0)
            await blocker.wait()
        publisher = HomiePublisher(self.config, [])
        publisher.command_controller = controller
        props = (Property('settings', 'led-brightness', 'LED', settable=True),)
        client = SimpleNamespace(messages=incoming())
        consumer = asyncio.create_task(publisher.receive_commands(client, base, props))
        await asyncio.sleep(.01)
        self.assertEqual(handled, [('led-brightness', b'5190')])
        self.assertEqual(self.status(), 'rejected-busy')
        consumer.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await consumer
        await controller.close()

    async def test_runtime_registers_only_allowlist_without_startup_write(self):
        from unittest.mock import patch
        from sma_mqtt_bridge.runtime import run
        config = replace(self.config, runtime=replace(self.config.runtime, health_interval_seconds=.001))
        reader = self.controller.reader
        reader.read = AsyncMock(return_value={'settings/led-brightness': '5191'})
        captured = []
        stop = asyncio.Event()
        class Publisher:
            status = {}
            def __init__(self, config, states):
                self.states = states
                captured.append(self)
            async def run(self, stop):
                await asyncio.sleep(.01)
                stop.set()
        with patch('sma_mqtt_bridge.runtime.sources', return_value=[(self.api, reader, 60)]):
            await run(config, stop=stop, publisher_factory=Publisher)
        self.assertTrue(self.api.properties[0].settable)
        self.assertIsNotNone(captured[0].command_controller)
        reader.http.request.assert_not_awaited()
        self.assertFalse(self.controller.journal.exists())
