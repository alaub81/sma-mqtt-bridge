"""Synthetic BYD wire fixtures; no installation captures, identities or live I/O."""

import asyncio
import json
import struct
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import AsyncMock, patch

from sma_mqtt_bridge.adapters.byd import BYDReader, crc16
from sma_mqtt_bridge.byd_profile import load_byd_profile
from sma_mqtt_bridge.byd_values import base_values, detail_values, identity_values, log_values
from sma_mqtt_bridge.config import BYD, load_config
from sma_mqtt_bridge.errors import ConfigError, ProtocolError
from sma_mqtt_bridge.homie import HomiePublisher, discovery
from sma_mqtt_bridge.model import SourceState
from sma_mqtt_bridge.runtime import sources
from sma_mqtt_bridge.translation import load_translation


def profile():
    return load_byd_profile("byd-hvs-4", "/nonexistent-byd-test")


def identity(serial="P03TEST0000000000001"):
    r = [0] * 102
    r[:10] = struct.unpack(">10H", serial.encode().ljust(20, b"\0"))
    r[12:19] = [0x0310, 0x0310, 0x0318, 0x0101, 0x0514, 0x0201, 0]
    return r


def status():
    r = [0] * 25
    r[:9] = [42, 334, 330, 95, 65524, 42000, 27, 23, 24]
    r[14], r[16:21] = 0x0902, [41980, 0x2345, 1, 0x1234, 2]
    return r


def detail():
    d = [0] * 256
    d[:6] = [3331, 3300, 0x2001, 25, 22, 0x3001]
    d[6], d[13] = 0x8001, 0x8000
    d[14:18] = [0x2345, 1, 0x1234, 2]
    d[20], d[23:32] = 4200, [4198, 425, 95, 65524, 0, 0, 0, 0x1603, 0x1803]
    d[45:47] = [0x0209, 0x0209]
    d[48:176] = [3300 + i % 32 for i in range(128)]
    d[176] = 0x6363  # Reserved word must not become two temperature samples.
    d[177:209] = struct.unpack(">32H", bytes([22 + i // 12 for i in range(48)] + [0] * 16))
    return d


def events(code=38):
    raw = bytearray(30)
    raw[:7] = bytes([code, 26, 1, 2, 3, 4, 5])
    raw[7:19] = bytes.fromhex("0100010012400c80031a0501")
    return list(struct.unpack(">15H", raw)) + [0] * 305


def response(function, payload):
    raw = bytes([1, function]) + payload
    return raw + struct.pack("<H", crc16(raw))


class Wire:
    """A fragmented RTU peer with a strict diagnostic selector implementation."""

    def __init__(self, mutate=None, serial="P03TEST0000000000001"):
        self.reader = asyncio.StreamReader()
        self.requests = []
        self.closed = False
        self.pages = {}
        self.mutate = mutate
        self.serial = serial

    def write(self, frame):
        assert crc16(frame) == 0
        self.requests.append(frame)
        function = frame[1]
        address, count = struct.unpack(">HH", frame[2:6])
        if function == 16:
            assert address in (0x550, 0x5A0) and count == 2 and frame[6] == 4
            assert frame[9:11] == bytes.fromhex("8100")
            self.pages[address + 8] = 0
            out = response(16, frame[2:6])
        else:
            if address == 0:
                words = identity(self.serial)
            elif address == 0x500:
                words = status()
            elif address in (0x551, 0x5A1):
                words = [0x8801]
            else:
                assert address in (0x558, 0x5A8)
                i = self.pages[address]
                d = detail() if address == 0x558 else events()
                words = [128] + d[i * 64 : (i + 1) * 64]
                self.pages[address] += 1
            assert len(words) == count
            out = response(3, bytes([2 * count]) + struct.pack(">" + str(count) + "H", *words))
        if self.mutate:
            out = self.mutate(frame, out)
        if out is not None:
            for i in range(0, len(out), 3):
                self.reader.feed_data(out[i : i + 3])

    async def drain(self):
        return None

    def close(self):
        self.closed = True

    async def wait_closed(self):
        return None


class BYDValuesTests(unittest.TestCase):
    def test_crc_known_request_and_byte_order(self):
        self.assertEqual(crc16(bytes.fromhex("010300000066")), 0xE0C5)
        values = base_values(status(), profile())
        self.assertEqual(values["battery/chargeenergy"], 7456.5)
        self.assertEqual(values["battery/dischargeenergy"], 13573.2)
        self.assertEqual(values["battery/current"], -1.2)
        self.assertEqual(values["battery/state"], "charging")
        self.assertEqual(values["battery/power"], -503.76)
        self.assertEqual(values["battery/dischargepower"], 0)

    def test_identity_checks_before_telemetry(self):
        for field, value in ((16, 0x0524), (17, 0x0101), (12, 0x0410), (14, 0x0410)):
            raw = identity()
            raw[field] = value
            with self.subTest(field=field), self.assertRaises(ProtocolError):
                identity_values(raw, profile())
        with self.assertRaises(ProtocolError):
            identity_values(identity(), profile(), "different-test-device")
        raw, p = identity(), profile()
        p["supportedBmuFirmware"] = ["3.15", "3.16"]
        raw[12] = 0x030F
        with self.assertRaises(ProtocolError):
            identity_values(raw, p)

    def test_zero_soc_is_valid_but_invalid_units_and_tables_fail(self):
        r = status()
        r[0] = 0
        self.assertEqual(base_values(r, profile())["battery/soc"], 0)
        for index, value in ((0, 65535), (3, 101), (4, 32767), (5, 65535), (14, 0)):
            r = status()
            r[index] = value
            with self.subTest(index=index), self.assertRaises(ProtocolError):
                base_values(r, profile())

    def test_full_detail_boundaries_firmware_and_module_aggregation(self):
        values = detail_values(detail(), profile(), identity_values(identity(), profile()))
        self.assertEqual(values["tower1module1/temperature01"], 22)
        self.assertEqual(values["tower1module4/temperature12"], 25)
        self.assertNotIn("tower1module4/temperature13", values)
        self.assertEqual(values["tower1module1/cell32voltage"], 3.331)
        self.assertEqual(values["tower1module2/cell01voltage"], 3.3)
        self.assertTrue(values["tower1module4/cell32balancing"])
        self.assertEqual(values["tower1/balancingcount"], 3)
        self.assertEqual(values["tower1module1/balancingcount"], 2)
        self.assertEqual(values["tower1/cellvoltagespread"], 31)
        self.assertEqual(values["tower1/chargeenergy"], 74.565)
        self.assertEqual(values["identity/bmsfirmwarea"], "3.22")
        self.assertEqual(values["identity/bmsfirmwareb"], "3.24")
        self.assertEqual(values["identity/parametertablea"], "9.2")
        for index, value in ((48, 65535), (31, 0), (45, 0), (2, 0)):
            d = detail()
            d[index] = value
            with self.subTest(index=index), self.assertRaises(ProtocolError):
                detail_values(d, profile(), identity_values(identity(), profile()))

    def test_active_fault_bits_remain_distinct_from_availability(self):
        r = status()
        r[13] = 1 << 11
        self.assertEqual(base_values(r, profile())["battery/condition"], "cell-undervoltage")
        d = detail()
        d[47], d[27] = 1 << 4, 1 << 6
        v = detail_values(d, profile(), identity_values(identity(), profile()))
        self.assertEqual(v["diagnostics/tower1errors"], "current-sensor-failure")
        self.assertEqual(v["diagnostics/tower1warnings"], "low-temperature-charging")

    def test_event_scope_unknown_codes_empty_slots_and_payload_limit(self):
        result = log_values(events(), "bmu", 4096)
        event = json.loads(result["events/bmuentry01"])
        self.assertEqual(event["timestamp_device_local"], "2026-01-02T03:04:05")
        self.assertNotIn("Z", event["timestamp_device_local"])
        self.assertEqual(event["values_at_event"]["max_charge_current_a"], 25.6)
        self.assertEqual(result["events/bmuentry02"], "null")
        self.assertEqual(result["diagnostics/bmulogrecords"], 1)
        event = json.loads(log_values(events(250), "bmu", 4096)["events/bmuentry01"])
        self.assertEqual(event["values_at_event"], {})
        self.assertEqual(event["description_reference"], "unknown-event")
        bmu = json.loads(log_values(events(32), "bmu", 4096)["events/bmuentry01"])
        bms = json.loads(log_values(events(32), "tower1", 4096)["events/tower1entry01"])
        self.assertEqual(bmu["description_reference"], "state-change")
        self.assertEqual(bms["description_reference"], "unknown-event")
        with self.assertRaises(ProtocolError):
            log_values(events(), "bmu", 32)
        invalid = events()
        invalid[1] = 0
        with self.assertRaises(ProtocolError):
            log_values(invalid, "bmu", 4096)


class BYDConfigTests(unittest.TestCase):
    def test_default_disabled_and_addresses_do_not_enable_io(self):
        config = load_config(
            {"SMAB_BYD_HOST": "battery.invalid", "SMAB_BYD_PROFILE": "file:missing.json"}
        )
        self.assertFalse(config.has_sources)
        self.assertEqual(sources(config), [])
        self.assertNotIn("byd", config.profiles)

    def test_independent_flags_and_all_four_homie_inventories(self):
        with tempfile.TemporaryDirectory() as tmp:
            for advanced, diagnostics, count in (
                (False, False, 16),
                (True, False, 93),
                (False, True, 394),
                (True, True, 471),
            ):
                c = load_config(
                    {
                        "SMAB_BYD_ENABLED": "true",
                        "SMAB_BYD_HOST": "battery.invalid",
                        "SMAB_MQTT_HOST": "broker.invalid",
                        "SMAB_STATE_DIR": tmp,
                        "SMAB_BYD_ADVANCED_CHANNELS_ENABLED": str(advanced).lower(),
                        "SMAB_BYD_DIAGNOSTICS_ENABLED": str(diagnostics).lower(),
                    }
                )
                state, reader, interval = sources(c)[0]
                state.monitor = object()
                props = HomiePublisher(c, [state]).properties([state])
                self.assertEqual(len(props), count)
                self.assertEqual(interval, 60)
                self.assertFalse(any(p.settable for p in props))
                self.assertEqual(len({p.key for p in props}), count)
                metadata = discovery("homie", "byd-battery", props)
                self.assertEqual(metadata["homie/byd-battery/battery/soc/$unit"], "%")
                if advanced:
                    self.assertEqual(
                        metadata["homie/byd-battery/identity/application/$datatype"], "enum"
                    )
                self.assertTrue(
                    all(
                        p in ("basic", "advanced", "diagnostics")
                        for p in Counter(x.channel_group for x in props)
                    )
                )
                self.assertEqual(bool(reader.stage_keys["detail"]), advanced or diagnostics)
                self.assertEqual(bool(reader.stage_keys["log"]), diagnostics)
                self.assertTrue(
                    all(p.name in load_translation("de", tmp) for p in reader.properties)
                )

    def test_validation_profile_overrides_precedence_and_readiness(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "config.json")
            path.write_text(json.dumps({"byd": {"pollIntervalSeconds": 90, "paused": True}}))
            c = load_config({"SMAB_CONFIG_FILE": str(path), "SMAB_BYD_PAUSED": "false"})
            self.assertFalse(c.byd.paused)
            self.assertEqual(c.byd.poll_interval_seconds, 90)
            for env in (
                {"SMAB_BYD_POLL_INTERVAL_SECONDS": "1"},
                {"SMAB_BYD_PORT": "0"},
                {"SMAB_BYD_DIAGNOSTICS_ENABLED": "yes"},
                {"SMAB_BYD_ENABLED": "true"},
                {"SMAB_BYD_HOMIE_ID": "sma-inverter1"},
            ):
                with self.subTest(env=env), self.assertRaises(ConfigError):
                    load_config(env)
            bad = profile() | {"validation": {"status": "identity-only", "evidence": "fixture"}}
            Path(tmp, "byd-hvs-4.json").write_text(json.dumps(bad))
            with self.assertRaises(ConfigError):
                load_byd_profile("byd-hvs-4", tmp)
            for selector in ("file:../outside.json", "/absolute", "unknown"):
                with self.subTest(selector=selector), self.assertRaises(ConfigError):
                    load_byd_profile(selector, tmp)
            with self.assertRaises(ConfigError):
                sources(
                    load_config(
                        {
                            "SMAB_BYD_ENABLED": "true",
                            "SMAB_BYD_HOST": "battery.invalid",
                            "SMAB_MQTT_HOST": "broker.invalid",
                            "SMAB_BYD_READY_PROPERTIES": "tower1/soc",
                        }
                    )
                )


class BYDWireTests(unittest.IsolatedAsyncioTestCase):
    def reader(self, **kwargs):
        return BYDReader(
            BYD(
                enabled=True,
                host="battery.invalid",
                timeout_seconds=0.03,
                buffer_poll_interval_seconds=0.001,
                buffer_ready_timeout_seconds=0.02,
                **kwargs,
            ),
            profile(),
        )

    async def test_fragmented_full_cycle_and_connections_released(self):
        reader = self.reader(advanced_channels_enabled=True, diagnostics_enabled=True)
        wire = Wire()
        with patch("asyncio.open_connection", new=AsyncMock(return_value=(wire.reader, wire))):
            values = await reader.read()
        self.assertTrue(wire.closed)
        self.assertEqual(set(values), reader.keys)
        self.assertEqual(values["tower1/soc"], 42.5)
        self.assertIn("events/tower1entry20", values)
        self.assertEqual(sum(frame[1] == 16 for frame in wire.requests), 3)
        self.assertTrue(reader.identity_fingerprint)
        second = Wire()
        with patch("asyncio.open_connection", new=AsyncMock(return_value=(second.reader, second))):
            fresh = await reader.read()
        self.assertFalse(any(frame[1] == 16 for frame in second.requests))
        self.assertNotIn("tower1/soc", fresh)
        state = SourceState("byd", "byd-battery", reader.properties, 180)
        state.update(values)
        original_time = state.values["tower1/soc"][1]
        state.update(fresh)
        self.assertEqual(state.values["tower1/soc"][1], original_time)
        self.assertEqual(state.status(), "ready")

    async def test_basic_only_no_selectors_and_disabled_paused_no_io(self):
        reader = self.reader()
        wire = Wire()
        with patch("asyncio.open_connection", new=AsyncMock(return_value=(wire.reader, wire))):
            values = await reader.read()
        self.assertEqual(len(values), 15)
        self.assertEqual(len(wire.requests), 2)
        for settings in (BYD(), BYD(enabled=True, paused=True)):
            with patch("asyncio.open_connection", new=AsyncMock()) as opening:
                self.assertEqual(await BYDReader(settings, profile()).read(), {})
                opening.assert_not_awaited()

    async def test_crc_bad_identity_and_wrong_units_fail_closed(self):
        for mutate in (
            lambda _f, r: r[:-1] + bytes([r[-1] ^ 1]),
            lambda _f, r: response(3, r[2:-2]).replace(b"\x01\x03", b"\x02\x03", 1),
        ):
            reader, wire = self.reader(), Wire(mutate)
            with patch("asyncio.open_connection", new=AsyncMock(return_value=(wire.reader, wire))):
                with self.assertRaises(ProtocolError):
                    await reader.read()
            self.assertTrue(wire.closed)
            self.assertEqual(len(wire.requests), 1)
        reader, wire = self.reader(), Wire(serial="P02TEST0000000000001")
        with patch("asyncio.open_connection", new=AsyncMock(return_value=(wire.reader, wire))):
            with self.assertRaises(ProtocolError):
                await reader.read()
        self.assertEqual(len(wire.requests), 1)

    async def test_truncated_wrong_count_exception_and_oversized_frames_fail_closed(self):
        for mutate in (
            lambda _f, _r: response(0x83, bytes([2])),
            lambda _f, _r: response(3, bytes([2, 0, 0])),
            lambda _f, _r: bytes([1, 3, 255]),
        ):
            reader, wire = self.reader(), Wire(mutate)
            with patch("asyncio.open_connection", new=AsyncMock(return_value=(wire.reader, wire))):
                with self.assertRaises(ProtocolError):
                    await reader.read()
            self.assertTrue(wire.closed)
        reader, wire = self.reader(), Wire(lambda _f, r: r[:-4])
        wire.drain = AsyncMock(side_effect=wire.reader.feed_eof)
        with patch("asyncio.open_connection", new=AsyncMock(return_value=(wire.reader, wire))):
            with self.assertRaises(asyncio.IncompleteReadError):
                await reader.read()
        self.assertTrue(wire.closed)

    async def test_readiness_deadline_and_wrong_selector_ack_do_not_retry(self):
        for mutate in (
            lambda f, r: (
                response(3, bytes([2, 0, 0]))
                if f[1] == 3 and f[2:4] == bytes.fromhex("0551")
                else r
            ),
            lambda f, r: response(16, bytes.fromhex("05510002")) if f[1] == 16 else r,
        ):
            reader, wire = self.reader(advanced_channels_enabled=True), Wire(mutate)
            with patch("asyncio.open_connection", new=AsyncMock(return_value=(wire.reader, wire))):
                values = await reader.read()
            self.assertIsNone(values["tower1/soc"])
            self.assertEqual(sum(f[1] == 16 for f in wire.requests), 1)
            self.assertTrue(wire.closed)

    async def test_detail_expiry_is_independent_of_later_basic_success(self):
        reader = self.reader(advanced_channels_enabled=True)
        wire = Wire()
        with patch("asyncio.open_connection", new=AsyncMock(return_value=(wire.reader, wire))):
            values = await reader.read()
        state = SourceState("byd", "byd-battery", reader.properties, 180)
        state.update(values)
        later = values.observed_at["tower1/soc"] + reader.settings.detail_stale_seconds + 1
        basic = {k: v for k, v in values.items() if k.startswith("battery/")}
        state.update(basic, now=later)
        self.assertEqual(state.status(later), "ready")
        self.assertNotIn("tower1/soc", state.fresh_values(later))
        self.assertEqual(state.fresh_values(later)["battery/soc"], "42")

    async def test_serial_replacement_cannot_inherit_old_optional_samples(self):
        reader = self.reader(advanced_channels_enabled=True)
        first = Wire()
        with patch("asyncio.open_connection", new=AsyncMock(return_value=(first.reader, first))):
            await reader.read()
        old = reader.identity_fingerprint
        second = Wire(serial="P03TEST0000000000002", mutate=lambda f, r: None if f[1] == 16 else r)
        with patch("asyncio.open_connection", new=AsyncMock(return_value=(second.reader, second))):
            result = await reader.read()
        self.assertNotEqual(reader.identity_fingerprint, old)
        self.assertIsNone(result["tower1/soc"])
        self.assertEqual(sum(f[1] == 16 for f in second.requests), 1)

    async def test_overlapping_reads_share_one_serialized_acquisition_path(self):
        reader = self.reader(advanced_channels_enabled=True)
        first, second = Wire(), Wire()
        with patch(
            "asyncio.open_connection",
            new=AsyncMock(side_effect=[(first.reader, first), (second.reader, second)]),
        ):
            a, b = await asyncio.gather(reader.read(), reader.read())
        self.assertIn("tower1/soc", a)
        self.assertNotIn("tower1/soc", b)
        self.assertTrue(first.closed and second.closed)
        self.assertEqual(len(second.requests), 2)

    async def test_failed_base_after_identity_change_keeps_optional_invalidation_pending(self):
        reader = self.reader(advanced_channels_enabled=True)
        first = Wire()
        with patch("asyncio.open_connection", new=AsyncMock(return_value=(first.reader, first))):
            await reader.read()

        def bad_status(frame, raw):
            if frame[1] == 3 and frame[2:4] == bytes.fromhex("0500"):
                words = status()
                words[14] = 0
                return response(3, bytes([50]) + struct.pack(">25H", *words))
            return raw

        second = Wire(serial="P03TEST0000000000002", mutate=bad_status)
        with patch("asyncio.open_connection", new=AsyncMock(return_value=(second.reader, second))):
            with self.assertRaises(ProtocolError):
                await reader.read()
        third = Wire(serial="P03TEST0000000000002", mutate=lambda f, r: None if f[1] == 16 else r)
        with patch("asyncio.open_connection", new=AsyncMock(return_value=(third.reader, third))):
            values = await reader.read()
        self.assertIsNone(values["tower1/soc"])
        self.assertEqual(sum(f[1] == 16 for f in third.requests), 1)

    async def test_optional_failure_invalidates_only_its_group_without_retry(self):
        reader = self.reader(advanced_channels_enabled=True, diagnostics_enabled=True)

        def mutate(frame, raw):
            return raw[:-1] + bytes([raw[-1] ^ 1]) if frame[1] == 16 else raw

        wire = Wire(mutate)
        with patch("asyncio.open_connection", new=AsyncMock(return_value=(wire.reader, wire))):
            values = await reader.read()
        self.assertEqual(values["battery/soc"], 42)
        self.assertIsNone(values["tower1/soc"])
        self.assertEqual(sum(f[1] == 16 for f in wire.requests), 1)
        self.assertGreater(reader.next_due["detail"], 0)
        self.assertTrue(wire.closed)

    async def test_no_non_monitoring_write_or_arbitrary_read(self):
        reader = self.reader()
        for address, unit in ((0x100, 1), (0x550, 0), (0x550, 2), (0x5A0, 2)):
            with self.assertRaises(ProtocolError):
                await reader.select_buffer(address, unit)
        with self.assertRaises(ProtocolError):
            await reader.read_registers(1234, 1)

    async def test_uncertain_selector_timeout_is_not_replayed(self):
        reader = self.reader(advanced_channels_enabled=True)
        wire = Wire(lambda frame, raw: None if frame[1] == 16 else raw)
        with patch("asyncio.open_connection", new=AsyncMock(return_value=(wire.reader, wire))):
            values = await reader.read()
        self.assertIsNone(values["tower1/soc"])
        self.assertEqual(sum(f[1] == 16 for f in wire.requests), 1)
        self.assertTrue(wire.closed)

    async def test_cancellation_closes_connection(self):
        reader = self.reader()
        wire = Wire(lambda _frame, _raw: None)
        with patch("asyncio.open_connection", new=AsyncMock(return_value=(wire.reader, wire))):
            task = asyncio.create_task(reader.read())
            await asyncio.sleep(0)
            await asyncio.sleep(0)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
        self.assertTrue(wire.closed)
