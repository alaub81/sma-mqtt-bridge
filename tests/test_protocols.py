"""Deterministic wire-format, auth, timestamp, identity and missing-value cases."""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
import struct
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from sma_mqtt_bridge.adapters.echarger import NS, SempReader, parameter_catalog, semp_values, settings_values, validate_semp_identity
from sma_mqtt_bridge.adapters.http import HTTP, json_data
from sma_mqtt_bridge.adapters.meter import parse_telegram
from sma_mqtt_bridge.adapters.modbus import ModbusReader, decode
from sma_mqtt_bridge.adapters.portal import PortalReader, authorization_code, login_action, portal_values
from sma_mqtt_bridge.config import ECharger, Inverter, Portal
from sma_mqtt_bridge.errors import AuthenticationError, ProtocolError
from sma_mqtt_bridge.profiles import validate_profile
from tests.helpers import validated_profile


class DecodeTests(unittest.TestCase):
    def test_signed_scaling_sentinels_and_byte_order(self):
        p = validated_profile()["properties"][-1]
        self.assertEqual(decode([0xffff, 0xff9c], p), Decimal('-10.0'))
        self.assertIsNone(decode([0x8000, 0], p))
        self.assertEqual(decode([100, 0], p | {"wordOrder": "little"}), Decimal('10.0'))
        self.assertEqual(decode([0, 0x6400], p | {"byteOrder": "little"}), Decimal('10.0'))
        with self.assertRaises(ProtocolError):
            decode([1], p)

    def test_float_nan_and_unknown_map(self):
        p = validated_profile()["properties"][-1] | {"type": "float32", "invalid": []}
        self.assertIsNone(decode([0x7fc0, 0], p))
        self.assertEqual(decode([0x3f80, 0], p), Decimal('.10'))
        p = validated_profile()["properties"][0]
        self.assertEqual(decode([1, 2, 3], p), "TEST-INVERTER")
        self.assertIsNone(decode([9, 2, 3], p))

    def test_sma_firmware_bcd_and_binary_build(self):
        p = validated_profile()["properties"][-1] | {"type": "uint32", "datatype": "string",
                                                       "scale": 1, "format": "sma-firmware", "invalid": [4294967295]}
        self.assertEqual(decode([0x0410, 0x0a04], p), "4.10.10.R")
        self.assertEqual(decode([0x0407, 0x1f04], p), "4.07.31.R")
        self.assertIsNone(decode([0x04fa, 0x0104], p))
        self.assertIsNone(decode([0xffff, 0xffff], p))

    def test_meter_unsigned_energy_scaling_serial_selection(self):
        header = bytearray(28)
        header[:4], header[16:18], header[20:24], header[24:28] = b'SMA\0', b'\x60\x69', struct.pack('>I', 123), struct.pack('>I', 100)
        frame = bytes(header) + struct.pack('>II', 0x00010400, 12345) + struct.pack('>IQ', 0x00010800, 3600000000) + b'\0' * 4
        stamp, values = parse_telegram(frame, '123')
        self.assertEqual(stamp, 100)
        self.assertEqual(values['measurements/power-import'], Decimal('1234.5'))
        self.assertEqual(values['measurements/energy-import'], 1000)
        self.assertNotIn('measurements/power-export', values)
        self.assertIsNone(parse_telegram(frame, '999'))
        for bad in (frame[:20], frame[:-5], b'BAD' + frame[3:], frame[:16] + b'\x60\x68' + frame[18:]):
            with self.subTest(bad=bad), self.assertRaises(ProtocolError):
                parse_telegram(bad, '123')

    def test_semp_identity_and_stale_values(self):
        identity = f'<Device2EM xmlns="{NS}"><DeviceInfo><Identification><DeviceId>fixture</DeviceId><DeviceSerial>123</DeviceSerial></Identification></DeviceInfo></Device2EM>'
        validate_semp_identity(identity, 'fixture', '123')
        with self.assertRaises(ProtocolError):
            validate_semp_identity(identity, 'different')
        xml = f'<Device2EM xmlns="{NS}"><Parameters><Parameter><channelId>Measurement.ChaSess.WhIn</channelId><timestamp>2026-10-10T10:00:00Z</timestamp><value>1500</value></Parameter></Parameters></Device2EM>'
        current = datetime(2026, 10, 10, 10, 0, 10, tzinfo=timezone.utc)
        self.assertEqual(semp_values(xml, 30, current)['measurements/session-energy'], Decimal('1.5'))
        self.assertIsNone(semp_values(xml, 5, current)['measurements/session-energy'])
        self.assertIsNone(semp_values(xml.replace('<value>1500', '<value>NaN'), 30, current)['measurements/session-energy'])
        with self.assertRaises(ProtocolError):
            semp_values('<!DOCTYPE x>' + xml, 30)
        with self.assertRaises(ProtocolError):
            semp_values(xml.replace(NS, 'unknown'), 30)

    def test_local_metadata_identity_and_unverified_unit(self):
        reply = [{'componentId': 'IGULD:SELF', 'values': [
            {'channelId': 'Parameter.Nameplate.SerNum', 'value': '123'},
            {'channelId': 'Parameter.Nameplate.ModelStr', 'value': 'EVC22-3AC-20'},
            {'channelId': 'Parameter.Chrg.Plan.En', 'value': 3},
            {'channelId': 'Parameter.Chrg.ChrgApv', 'value': '5172'}]}]
        catalog = parameter_catalog(reply, '123')
        self.assertIsNone(settings_values(catalog)['settings/plan-energy'])
        self.assertIs(settings_values(catalog)['settings/charging-release'], True)
        catalog['Parameter.Chrg.Plan.En']['unit'] = 'kWh'
        self.assertEqual(settings_values(catalog)['settings/plan-energy'], 3)
        with self.assertRaises(ProtocolError):
            parameter_catalog(reply, '999')

    def test_semp_settings_raw_units_and_stale_setpoints(self):
        channels = {'Parameter.Chrg.Plan.En': '3', 'Parameter.Chrg.StpWhenFlTm': '5',
                    'Parameter.Chrg.ChrgLok': '1129', 'Parameter.Chrg.CblLok': '308',
                    'Setpoint.PlantControl.PCC.ChrgActCnt': '1'}
        body = ''.join(f'<Parameter><channelId>{k}</channelId><timestamp>2026-10-10T10:00:00Z</timestamp><value>{v}</value></Parameter>'
                       for k, v in channels.items())
        xml = f'<Device2EM xmlns="{NS}"><Parameters>{body}</Parameters></Device2EM>'
        values = semp_values(xml, 30, datetime(2026, 10, 10, 10, 1, tzinfo=timezone.utc))
        self.assertIs(values['settings/approval-required'], True)
        self.assertIs(values['settings/cable-lock'], True)
        self.assertIsNone(values['settings/plan-energy'])
        self.assertIsNone(values['settings/stop-delay'])
        self.assertEqual(values['parameters/chrg-plan-en-raw'], 3)
        self.assertEqual(values['parameters/chrg-stpwhenfltm-raw'], 5)
        self.assertIsNone(values['control/active-charging-count'])
        adapter = SempReader(ECharger(), 10000)
        self.assertEqual(len({p.key for p in adapter.properties}), len(adapter.properties))
        self.assertTrue(set(values).issubset({p.key for p in adapter.properties}))
        shared = SempReader(ECharger(), 10000, include_settings=False)
        self.assertFalse(any(p.node == 'settings' for p in shared.properties))

    def test_portal_nullable_preference_rights_and_identity(self):
        reply = {'plantId': 'fixture-plant', 'deviceId': 'fixture-device', 'productTagId': 19143,
                 'consumerTypes': ['EVehicle'], '_links': {'ui_Edit_OptionalEnergyDemand': []},
                 'optionalEnergyDemand': {'isOptionalConsumer': True, 'minPvPercentage': 65,
                                         'pvSurplusOnly': None, 'usePriceLimit': False, 'priceLimit': None}}
        values = portal_values(reply, 'fixture-plant', 'fixture-device')
        self.assertEqual(values['portal/grid-share'], 35)
        self.assertTrue(values['portal/writable'])
        self.assertEqual(values['portal/setting-mode'], 'Mindest-PV-Anteil')
        for pv in (None, True, 100.5, -1, 101):
            with self.subTest(pv=pv), self.assertRaises(ProtocolError):
                portal_values(reply | {'optionalEnergyDemand': reply['optionalEnergyDemand'] | {'minPvPercentage': pv}}, 'fixture-plant', 'fixture-device')
        with self.assertRaises(ProtocolError):
            portal_values(reply, 'wrong-plant', 'fixture-device')

    def test_pkce_redirect_and_login_origin_guard(self):
        base = 'https://login.sma.energy/auth/realms/SMA'
        form = '<form id="kc-form-login" action="/auth/realms/SMA/login-actions/authenticate?x=1&amp;y=2">'
        self.assertEqual(login_action(form, base), base + '/login-actions/authenticate?x=1&y=2')
        for html in (form.replace('/auth/realms/SMA/login-actions/', 'https://evil.invalid/'),
                     form + '<input name="otp" type="text">', 'changed login form'):
            with self.subTest(html=html), self.assertRaises(AuthenticationError):
                login_action(html, base)
        redirect = 'https://ennexos.sunnyportal.com/dashboard/initialize'
        self.assertEqual(authorization_code(redirect + '?code=fixture&state=abc', redirect, 'abc'), 'fixture')
        for query in ('?code=x&state=wrong', '?code=x&state=abc&state=abc', '?code=x&state=abc#fragment'):
            with self.subTest(query=query), self.assertRaises(AuthenticationError):
                authorization_code(redirect + query, redirect, 'abc')

    def test_json_protocol_rejects_duplicates_and_nonfinite(self):
        for text in ('{"a":1,"a":2}', '{"value":NaN}', 'login HTML'):
            with self.subTest(text=text), self.assertRaises(ProtocolError):
                json_data(text)


class AsyncProtocolTests(unittest.IsolatedAsyncioTestCase):
    def reader(self):
        return ModbusReader(Inverter(host='fixture.invalid', unit_id=4), validate_profile(validated_profile()))

    async def test_modbus_wire_validation(self):
        adapter = self.reader()
        reader = asyncio.StreamReader()
        reader.feed_data(struct.pack('>HHHB', 1, 0, 7, 4) + bytes([4, 4, 0, 0, 0, 100]))
        writer = MagicMock()
        writer.drain = AsyncMock()
        writer.wait_closed = AsyncMock()
        self.assertEqual(await adapter.read_block(reader, writer, adapter.profile['pollers'][1]), [0, 100])
        sent = writer.write.call_args[0][0]
        self.assertEqual(sent[-5:], struct.pack('>BHH', 4, 10, 2))
        for header, body in ((struct.pack('>HHHB', 99, 0, 6, 4), b''),
                             (struct.pack('>HHHB', 1, 0, 3, 4), bytes([0x84, 2])),
                             (struct.pack('>HHHB', 1, 0, 7, 4), bytes([3, 4, 0, 0, 0, 100]))):
            adapter = self.reader()
            reader = asyncio.StreamReader()
            reader.feed_data(header + body)
            with self.assertRaises(ProtocolError):
                await adapter.read_block(reader, writer, adapter.profile['pollers'][1])

    async def test_identity_gate_precedes_measurements(self):
        adapter = self.reader()
        writer = MagicMock()
        writer.drain = AsyncMock()
        writer.wait_closed = AsyncMock()
        with patch('asyncio.open_connection', AsyncMock(return_value=(object(), writer))), patch.object(adapter, 'read_block', AsyncMock(return_value=[9, 2, 123])) as read:
            with self.assertRaises(ProtocolError):
                await adapter.read()
        self.assertEqual(read.await_count, 1)
        self.assertEqual(read.call_args[0][2]['id'], 'identity')
        writer.close.assert_called_once()

    async def test_per_poller_intervals_and_explicit_override(self):
        adapter = self.reader()
        self.assertEqual(adapter.interval(adapter.profile['pollers'][1]), 3)
        adapter.interval_override = True
        self.assertEqual(adapter.interval(adapter.profile['pollers'][1]), 10)

    async def test_modbus_timeout(self):
        adapter = self.reader()
        adapter.settings = Inverter(timeout_seconds=.01)
        async def stall(*args):
            await asyncio.sleep(10)
        with patch('asyncio.open_connection', stall), self.assertRaises(asyncio.TimeoutError):
            await adapter.read()

    async def test_http_cannot_write(self):
        http = HTTP(1, 100)
        with self.assertRaises(ProtocolError):
            await http.request('PUT', 'https://fixture.invalid')
        self.assertIsNone(http.session)

    async def test_portal_token_refresh_and_one_read_retry(self):
        adapter = PortalReader(Portal(plant_id='fixture-plant', device_id='fixture-device'), 1000)
        adapter.refresh = 'fixture-refresh'
        adapter.http.request = AsyncMock(return_value=(200, {}, '{"access_token":"fixture-token","expires_in":120}'))
        self.assertEqual(await adapter.access_token(), 'fixture-token')
        self.assertEqual(adapter.http.request.call_args[1]['data']['grant_type'], 'refresh_token')
        await adapter.access_token()
        self.assertEqual(adapter.http.request.await_count, 1)

    async def test_portal_html_success_is_not_authentication(self):
        adapter = PortalReader(Portal(), 1000)
        adapter.http.request = AsyncMock(return_value=(200, {}, '<input name="otp">'))
        with self.assertRaises(AuthenticationError):
            await adapter.access_token()

    async def test_full_local_api_read_is_scoped_and_read_only(self):
        from sma_mqtt_bridge.adapters.echarger import EChargerReader
        from sma_mqtt_bridge.config import ECharger
        import json
        timestamp = datetime.now(timezone.utc).isoformat()
        adapter = EChargerReader(ECharger(host='fixture.invalid', username='fixture-account', password='fixture-password', expected_serial='123'), 10000)
        adapter.http.get_json = AsyncMock(side_effect=[
            {'access_token': 'fixture-token', 'expires_in': 120},
            [{'componentId': 'IGULD:SELF', 'values': [
                {'channelId': 'Parameter.Nameplate.SerNum', 'value': '123'},
                {'channelId': 'Parameter.Nameplate.ModelStr', 'value': 'EVC22-3AC-20'},
                {'channelId': 'Parameter.Chrg.ActChaMod', 'value': '4719'}]}],
            [{'channelId': 'Measurement.GridMs.A.phsA', 'values': [{'value': 4.5, 'timestamp': timestamp}]},
             {'channelId': 'Measurement.GridMs.A.phsB', 'values': [{'value': 5, 'timestamp': '2000-01-01T00:00:00Z'}]}],
        ])
        values = await adapter.read()
        self.assertEqual(values['settings/charge-mode'], '4719')
        self.assertEqual(values['measurements/current-l1'], Decimal('4.5'))
        self.assertIsNone(values['measurements/current-l2'])
        calls = adapter.http.get_json.call_args_list
        self.assertTrue(all(c.args[0] == 'POST' for c in calls))
        self.assertEqual(calls[1].kwargs['json'], {'queryItems': [{'componentId': 'IGULD:SELF'}]})
        self.assertNotIn('fixture-password', json.dumps(values, default=str))
        await adapter.close()

    async def test_full_portal_pkce_login_and_device_read(self):
        import json
        from urllib.parse import parse_qs, urlsplit
        settings = Portal(username='fixture-account', password='fixture-password', plant_id='fixture-plant', device_id='fixture-device')
        adapter = PortalReader(settings, 10000)
        reply = {'plantId': 'fixture-plant', 'deviceId': 'fixture-device', 'productTagId': 19143,
                 'consumerTypes': ['EVehicle'], 'optionalEnergyDemand': {'isOptionalConsumer': True,
                 'minPvPercentage': 70, 'pvSurplusOnly': None, 'usePriceLimit': False, 'priceLimit': None}}
        state = None
        async def request(method, url, **kwargs):
            nonlocal state
            if '/protocol/openid-connect/auth?' in url:
                state = parse_qs(urlsplit(url).query)['state'][0]
                self.assertEqual(parse_qs(urlsplit(url).query)['code_challenge_method'], ['S256'])
                return 200, {}, '<form id="kc-form-login" action="/auth/realms/SMA/login-actions/authenticate">'
            if '/login-actions/' in url:
                self.assertEqual(kwargs['data']['username'], 'fixture-account')
                return 302, {'Location': adapter.redirect + '?code=fixture-code&state=' + state}, ''
            if url == adapter.token_url:
                self.assertEqual(kwargs['data']['grant_type'], 'authorization_code')
                self.assertIn('code_verifier', kwargs['data'])
                return 200, {}, '{"access_token":"fixture-token","expires_in":120,"refresh_token":"fixture-refresh"}'
            self.assertEqual(method, 'GET')
            self.assertEqual(kwargs['token'], 'fixture-token')
            return 200, {}, json.dumps(reply)
        adapter.http.request = AsyncMock(side_effect=request)
        values = await adapter.read()
        self.assertEqual(values['portal/pv-minimum'], 70)
        self.assertEqual(values['portal/grid-share'], 30)
        self.assertFalse(values['portal/writable'])
        self.assertEqual(adapter.http.request.await_count, 4)
        self.assertFalse(any('/optionalenergydemand' in c.args[1] for c in adapter.http.request.call_args_list))
        await adapter.close()
