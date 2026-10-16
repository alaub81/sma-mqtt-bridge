"""Phase-specific Sunny Boy decoding, read-only discovery and optional NaN behavior."""

import tempfile
import unittest
from decimal import Decimal

from sma_mqtt_bridge.adapters.modbus import ModbusReader, decode
from sma_mqtt_bridge.config import Inverter, load_config
from sma_mqtt_bridge.homie import HomiePublisher, discovery
from sma_mqtt_bridge.model import SourceState
from sma_mqtt_bridge.profiles import load_profile
from sma_mqtt_bridge.translation import load_translation


class SunnyBoyPhaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.profile = load_profile("sma-sb4-0-1av-41", self.tmp.name, require_validated=True)
        self.reader = ModbusReader(
            Inverter(advanced_channels_enabled=False, diagnostics_enabled=False), self.profile
        )
        self.definitions = {p["id"]: p for p in self.profile["properties"]}

    def test_documented_phase_addresses_scaling_signed_values_and_sentinels(self):
        pollers = {p["id"]: p for p in self.profile["pollers"]}
        for key, address, raw, expected, invalid in (
            ("power-l2", 30779, -123, Decimal(-123), 0x80000000),
            ("power-l3", 30781, 456, Decimal(456), 0x80000000),
            ("volt-g2", 30785, 23012, Decimal("230.12"), 0xFFFFFFFF),
            ("volt-g3", 30787, 23134, Decimal("231.34"), 0xFFFFFFFF),
            ("current-l1", 30977, -5678, Decimal("-5.678"), 0x80000000),
            ("current-l2", 30979, -1234, Decimal("-1.234"), 0x80000000),
            ("current-l3", 30981, 2345, Decimal("2.345"), 0x80000000),
        ):
            with self.subTest(key=key):
                prop = self.definitions[key]
                block = pollers[prop["poller"]]
                self.assertEqual(block["start"] + prop["offset"], address)
                self.assertEqual(block["function"], 4)
                words = [0] * block["count"]
                unsigned = raw & 0xFFFFFFFF
                words[prop["offset"] : prop["offset"] + 2] = [unsigned >> 16, unsigned & 65535]
                self.assertEqual(decode(words, prop), expected)
                words[prop["offset"] : prop["offset"] + 2] = [0, 0]
                self.assertEqual(decode(words, prop), 0)
                words[prop["offset"] : prop["offset"] + 2] = [invalid >> 16, invalid & 65535]
                self.assertIsNone(decode(words, prop))
        self.assertEqual(pollers["power-a"]["count"], 20)
        self.assertEqual(pollers["power-a"]["intervalSeconds"], 3)
        self.assertEqual(pollers["phase-currents"]["intervalSeconds"], 5)
        self.assertEqual(pollers["phase-currents"]["count"], 6)

    def test_shared_current_block_keeps_all_phase_offsets_distinct(self):
        words = [0xFFFF, 0xFB2E, 0, 2345, 0, 6789]
        for key, expected in (
            ("current-l1", Decimal("-1.234")),
            ("current-l2", Decimal("2.345")),
            ("current-l3", Decimal("6.789")),
        ):
            with self.subTest(key=key):
                self.assertEqual(decode(words, self.definitions[key]), expected)

    def test_discovery_preserves_l1_and_adds_read_only_l2_l3_with_optional_filters_off(self):
        labels = load_translation("de", self.tmp.name)
        topics = discovery("homie", "test-sunny-boy", self.reader.properties, labels)
        for suffix, unit, label in (
            ("powerl1", "W", "Leistung Phase L1"),
            ("voltg1", "V", "Netzspannung Phase L1"),
            ("currentl1", "A", "Netzstrom Phase L1"),
            ("powerl2", "W", "Leistung Phase L2"),
            ("powerl3", "W", "Leistung Phase L3"),
            ("voltg2", "V", "Netzspannung Phase L2"),
            ("voltg3", "V", "Netzspannung Phase L3"),
            ("currentl2", "A", "Netzstrom Phase L2"),
            ("currentl3", "A", "Netzstrom Phase L3"),
        ):
            base = "homie/test-sunny-boy/measurements/" + suffix
            self.assertEqual(topics[base + "/$unit"], unit)
            self.assertEqual(topics[base + "/$settable"], "false")
            self.assertEqual(topics[base + "/$name"], label)
        self.assertEqual(self.definitions["power-l1"]["offset"], 8)
        self.assertEqual(self.definitions["volt-g1"]["offset"], 14)
        self.assertFalse(self.profile["commands"])

    def test_inactive_l1_l2_do_not_publish_nan_or_block_ready_l3(self):
        state = SourceState("inverter3", "test-sunny-boy", self.reader.properties, 60)
        state.update(
            {
                "measurements/status": "Ok (Ok)",
                "measurements/power-l1": None,
                "measurements/volt-g1": None,
                "measurements/current-l1": None,
                "measurements/power-l2": None,
                "measurements/volt-g2": None,
                "measurements/current-l2": None,
                "measurements/power-l3": 456,
                "measurements/volt-g3": Decimal("231.34"),
                "measurements/current-l3": Decimal("2.345"),
            },
            now=10,
        )
        config = load_config({"SMAB_STATE_DIR": self.tmp.name})
        values, status = HomiePublisher(config, [state]).snapshot([state], now=10)
        self.assertEqual(status, "ready")
        self.assertEqual(values["measurements/power-l3"], "456")
        self.assertEqual(values["measurements/voltage-l3"], "231.34")
        self.assertEqual(values["measurements/current-l3"], "2.345")
        for key in ("power-l1", "volt-g1", "current-l1", "power-l2", "volt-g2", "current-l2"):
            self.assertNotIn("measurements/" + key, values)
