"""Deterministic Home Manager wire, scheduling, identity and inventory coverage."""

import asyncio
from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path
import struct
import tempfile
import time
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from sma_mqtt_bridge.__main__ import main
from sma_mqtt_bridge.adapters.home_manager_modbus import HomeManagerModbusReader
from sma_mqtt_bridge.adapters.modbus import ModbusException, decode
from sma_mqtt_bridge.config import HomeManager, load_config
from sma_mqtt_bridge.errors import ConfigError, ProtocolError
from sma_mqtt_bridge.home_manager_profile import load_home_manager_profile
from sma_mqtt_bridge.runtime import sources

ROOT = Path(__file__).resolve().parents[1]


def profile():
    return load_home_manager_profile('sma-home-manager-2-modbus', '/nonexistent-fixture-profiles')


def words(value):
    return list(struct.unpack('>HH', struct.pack('>I', value & 0xffffffff)))


def adapter():
    return HomeManagerModbusReader(HomeManager(host='fixture.invalid', serial='123', transport='modbus-tcp',
                                              transaction_delay_seconds=0, after_connection_delay_seconds=0,
                                              reconnect_delay_seconds=0), profile())


class HomeManagerProfileTests(unittest.TestCase):
    def test_complete_documented_read_registers_units_and_scaling(self):
        p = profile()
        core = {(b['unitId'], b['start']) for b in p['pollers']}
        self.assertEqual(core, {(1, a) for a in (30001, 30003, 30005, 30007, 30051, 30053, 30055, 30057, 30193, 43090)}
                         | {(2, a) for a in (30193, 30201, 30581, 30583, 30865, 30867)})
        self.assertEqual({b['start'] for b in p['delegated']['pollers']},
                         {30233, 30825, 30831, 30833, 40200, 40206, 40208, 40216, 40218, 40220,
                          40222, 40224, 40226, 40228, 40230, 40232})
        self.assertTrue(all(b['function'] == 4 for b in p['pollers'] + p['delegated']['pollers']))
        self.assertEqual(p['commands'], [])
        energy = next(v for v in p['properties'] if v['id'] == 'energy-import')
        self.assertEqual(decode(words(3000000000), energy), Decimal('3000000.000'))
        self.assertEqual(energy['unit'], 'kWh')
        self.assertIsNone(decode(words(0xffffffff), energy))
        power = next(v for v in p['properties'] if v['id'] == 'power-import')
        self.assertEqual(decode(words(-10), power), -10)
        self.assertIsNone(decode(words(0x80000000), power))
        cosine = next(v for v in p['delegated']['properties'] if v['id'] == 'cos-phi-setpoint')
        self.assertEqual(decode(words(95), cosine), Decimal('.95'))
        status = next(v for v in p['properties'] if v['id'] == 'plant-status')
        self.assertIsNone(decode(words(16777213), status))
        self.assertEqual(decode(words(455), status), 'warning')

    def test_offline_profile_diagnostic(self):
        with patch('builtins.print') as output:
            self.assertEqual(main(['--check-home-manager-profile', 'sma-home-manager-2-modbus']), 0)
        self.assertFalse(json.loads(output.call_args.args[0])['liveVerified'])

    def test_activation_transport_host_identity_and_interval_precedence(self):
        env = {'SMAB_HOME_MANAGER_ENABLED': 'true', 'SMAB_HOME_MANAGER_TRANSPORT': 'modbus-tcp',
               'SMAB_HOME_MANAGER_HOST': 'fixture.invalid', 'SMAB_HOME_MANAGER_SERIAL': '123',
               'SMAB_MQTT_HOST': 'broker.invalid', 'SMAB_MQTT_TLS': 'false'}
        config = load_config(env)
        source = sources(config)[0]
        self.assertIsInstance(source[1], HomeManagerModbusReader)
        self.assertFalse(source[1].interval_override)
        self.assertEqual(config.home_manager.port, 9522)
        self.assertEqual(config.home_manager.modbus_port, 502)
        configured = load_config(env | {'SMAB_HOME_MANAGER_POLL_INTERVAL_SECONDS': '8'})
        reader = sources(configured)[0][1]
        self.assertEqual(reader.interval(next(b for b in reader.pollers if b['id'] == 'power-import')), 8)
        self.assertEqual(reader.interval(next(b for b in reader.pollers if b['id'] == 'system-time')), 60)
        for changes in ({'SMAB_HOME_MANAGER_HOST': ''}, {'SMAB_HOME_MANAGER_SERIAL': ''},
                        {'SMAB_HOME_MANAGER_TRANSPORT': 'auto'}, {'SMAB_HOME_MANAGER_PROFILE': 'file:missing.json'},
                        {'SMAB_HOME_MANAGER_MODBUS_PORT': '0'}, {'SMAB_HOME_MANAGER_TRANSACTION_DELAY_SECONDS': '-1'}):
            with self.subTest(changes=changes), self.assertRaises(ConfigError):
                load_config(env | changes)
        disabled = load_config({'SMAB_HOME_MANAGER_TRANSPORT': 'modbus-tcp', 'SMAB_HOME_MANAGER_PROFILE': 'file:missing.json'})
        self.assertEqual(sources(disabled), [])
        zero = load_config({'SMAB_HOME_MANAGER_TRANSACTION_DELAY_SECONDS': '0',
                            'SMAB_HOME_MANAGER_AFTER_CONNECTION_DELAY_SECONDS': '0',
                            'SMAB_HOME_MANAGER_RECONNECT_DELAY_SECONDS': '0'})
        self.assertEqual(zero.home_manager.transaction_delay_seconds, 0)

    def test_host_override_invalid_and_traversal_never_fall_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'sma-home-manager-2-modbus.json'
            for mutation in ('unit', 'write', 'identity', 'range', 'nan', 'unknown'):
                p = profile()
                if mutation == 'unit':
                    p['pollers'][0]['unitId'] = 3
                elif mutation == 'write':
                    p['delegated']['pollers'][0]['function'] = 16
                elif mutation == 'identity':
                    p['identity']['serial'] = []
                elif mutation == 'range':
                    p['inventory']['slots'] = 246
                elif mutation == 'nan':
                    p['inventory']['intervalSeconds'] = float('nan')
                else:
                    p['unexpected'] = True
                path.write_text(json.dumps(p))
                with self.subTest(mutation=mutation), self.assertRaises(ConfigError):
                    load_home_manager_profile(p['id'], tmp)
            with self.assertRaises(ConfigError):
                load_home_manager_profile('file:../escape.json', tmp)


class HomeManagerProtocolTests(unittest.IsolatedAsyncioTestCase):
    def session(self, bad_serial=False):
        reader = adapter()
        writer = MagicMock()
        writer.wait_closed = AsyncMock()
        identity = {'model': 9343, 'serial': 124 if bad_serial else 123, 'serial-copy': 123,
                    'device-class': 8128, 'manufacturer': 461}
        requests = []
        async def read(stream, output, poller):
            requests.append((poller['unitId'], poller['start']))
            if poller['id'] in identity:
                return words(identity[poller['id']])
            return [0] * poller['count']
        reader.read_block = AsyncMock(side_effect=read)
        return reader, writer, requests

    async def test_identity_before_measurements_persistent_session_and_no_write(self):
        reader, writer, requests = self.session()
        with patch('asyncio.open_connection', AsyncMock(return_value=(object(), writer))) as connect:
            result = await reader.read()
            await reader.read()
        self.assertEqual(connect.await_count, 1)
        self.assertTrue(all(unit == 1 for unit, _ in requests[:5]))
        self.assertEqual(result['identity/serial'], 123)
        self.assertIn('measurements/power-import', result)
        self.assertFalse(writer.close.called)
        await reader.close()
        writer.close.assert_called_once()
        reader, writer, requests = self.session(bad_serial=True)
        with patch('asyncio.open_connection', AsyncMock(return_value=(object(), writer))), self.assertRaises(ProtocolError):
            await reader.read()
        self.assertTrue(all(unit == 1 for unit, _ in requests))
        writer.close.assert_called_once()

    async def test_rejected_register_is_unavailable_and_other_values_continue(self):
        reader, writer, _ = self.session()
        original = reader.read_block.side_effect
        async def reject(stream, output, poller):
            if poller['unitId'] == 2 and poller['start'] == 30865:
                raise ModbusException(2)
            return await original(stream, output, poller)
        reader.read_block.side_effect = reject
        with patch('asyncio.open_connection', AsyncMock(return_value=(object(), writer))):
            first = await reader.read()
            second = await reader.read()
        self.assertIsNone(first['measurements/power-import'])
        self.assertEqual(first['diagnostics/modbus-rejected-blocks'], 1)
        self.assertEqual(second['measurements/power-export'], 0)
        self.assertFalse(writer.close.called)
        await reader.close()

    async def test_assignment_boundaries_dynamic_parameters_and_retirement(self):
        reader = adapter()
        self.assertEqual(sum(p['count'] for p in reader.inventory_pollers), 980)
        self.assertLessEqual(max(p['count'] for p in reader.inventory_pollers), 125)
        self.assertEqual(reader.inventory_pollers[-1]['start'] + reader.inventory_pollers[-1]['count'], 43089)
        poller = reader.inventory_pollers[0]
        block = [65535] * poller['count']
        block[:8] = [158, 0, 1234, 7, 158, 0, 2345, 255]
        values = reader.inventory_values(poller, block)
        self.assertEqual(values['device-1/serial'], 1234)
        self.assertEqual(values['device-2/unit-id'], 255)
        self.assertIn('device-1/cos-phi-setpoint', {p.key for p in reader.properties})
        self.assertNotIn('device-2/cos-phi-setpoint', {p.key for p in reader.properties})
        delegated = [p for p in reader.pollers if 'assignedSlot' in p]
        self.assertEqual(len(delegated), 16)
        self.assertTrue(all(p['unitId'] == 7 for p in delegated))
        reader.inventory_values(poller, [65535] * poller['count'])
        self.assertFalse(any(p.key.startswith('device-') for p in reader.properties))
        self.assertFalse(any('assignedSlot' in p for p in reader.pollers))

    async def test_duplicate_unit_uses_first_slot_and_expired_assignment_is_not_polled(self):
        reader, writer, _ = self.session()
        with patch('asyncio.open_connection', AsyncMock(return_value=(object(), writer))):
            await reader.read()
        poller = reader.inventory_pollers[0]
        block = [65535] * poller['count']
        block[:8] = [158, 0, 1234, 7, 158, 0, 2345, 7]
        reader.inventory_values(poller, block)
        delegated = [p for p in reader.pollers if 'assignedSlot' in p]
        self.assertEqual({p['assignedSlot'] for p in delegated}, {0})
        reader.assignment_received = {slot: time.monotonic() - 1000 for slot in reader.assignments}
        await reader.read()
        self.assertEqual(reader.assignments, {})
        await reader.close()

    async def test_timeout_closes_session_and_reconnect_verifies_identity(self):
        reader, writer, requests = self.session()
        reader.settings = replace(reader.settings, timeout_seconds=.01)
        original = reader.read_block.side_effect
        async def timeout(stream, output, poller):
            if poller['unitId'] == 2:
                await asyncio.sleep(10)
            return await original(stream, output, poller)
        reader.read_block.side_effect = timeout
        with patch('asyncio.open_connection', AsyncMock(return_value=(object(), writer))):
            with self.assertRaises(asyncio.TimeoutError):
                await reader.read()
            reader.read_block.side_effect = original
            await reader.read()
        self.assertEqual(sum(start == 30053 for _, start in requests), 2)
        self.assertTrue(writer.close.called)
        await reader.close()

    async def test_wire_unit_override_and_exception_correlation(self):
        reader = adapter()
        stream = asyncio.StreamReader()
        stream.feed_data(struct.pack('>HHHB', 1, 0, 7, 2) + bytes([4, 4, 0, 0, 0, 100]))
        writer = MagicMock()
        writer.drain = AsyncMock()
        poller = next(p for p in reader.pollers if p['id'] == 'power-import')
        self.assertEqual(await reader.read_block(stream, writer, poller), [0, 100])
        self.assertEqual(writer.write.call_args[0][0][6], 2)
        self.assertEqual(writer.write.call_args[0][0][7], 4)
        for tx, unit, function in ((99, 2, 0x84), (2, 1, 0x84), (2, 2, 0x83)):
            reader.transaction = 1
            stream = asyncio.StreamReader()
            stream.feed_data(struct.pack('>HHHB', tx, 0, 3, unit) + bytes([function, 2]))
            with self.assertRaises(ProtocolError):
                await reader.read_block(stream, writer, poller)

    async def test_fast_power_read_wins_over_due_delegated_inventory(self):
        reader, writer, requests = self.session()
        with patch('asyncio.open_connection', AsyncMock(return_value=(object(), writer))):
            await reader.read()
        block = [65535] * reader.inventory_pollers[0]['count']
        block[:4] = [158, 0, 1234, 7]
        reader.inventory_values(reader.inventory_pollers[0], block)
        now = time.monotonic()
        reader.next_due = {p['id']: now + 1000 for p in reader.pollers}
        delegated = next(p for p in reader.pollers if 'assignedSlot' in p)
        reader.next_due[delegated['id']] = now - 1
        reader.next_due['power-import'] = now - 1
        requests.clear()
        await reader.read()
        self.assertEqual(requests, [(2, 30865)])
        reader.next_due['power-import'] = now + 1000
        result = await reader.read()
        self.assertEqual(requests[-1], (7, 30233))
        self.assertEqual(result['device-1/permanent-power-limit'], 0)
        await reader.close()

    async def test_pacing_and_connect_delay_are_explicit(self):
        reader, writer, _ = self.session()
        reader.home_settings = replace(reader.home_settings, transaction_delay_seconds=.2, after_connection_delay_seconds=3)
        with patch('asyncio.open_connection', AsyncMock(return_value=(object(), writer))), patch('asyncio.sleep', AsyncMock()) as sleep:
            await reader.read()
        self.assertEqual(sleep.await_args_list[0].args, (3,))
        self.assertTrue(any(0 < call.args[0] <= .2 for call in sleep.await_args_list))
        await reader.close()
