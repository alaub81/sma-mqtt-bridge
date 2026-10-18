"""Evidence-backed phase mappings and consistent inverter publication metadata."""

import hashlib
import json
import tempfile
import unittest
from decimal import Decimal

from sma_mqtt_bridge.adapters.modbus import ModbusReader, decode
from sma_mqtt_bridge.config import Inverter, load_config
from sma_mqtt_bridge.homie import HomiePublisher, discovery
from sma_mqtt_bridge.model import SourceState
from sma_mqtt_bridge.plant import energy_binding_profile
from sma_mqtt_bridge.profiles import load_profile


class InverterTopicParityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = load_config({"SMAB_STATE_DIR": self.tmp.name})

    def profile(self, selector):
        return load_profile(selector, self.tmp.name, require_validated=True)

    def test_exact_additions_preserve_released_energy_identity_without_mutating_profiles(self):
        released = {
            "sma-stp8-0-3av-40": "4c5a70806736f5879e21c4602cc7098a120ea327eb0848d9b2670098feffe19f",
            "sma-sbs3-7-10": "acccc29aebc0e8a0ad77400e939750243feb2bda59dc1bec6c870ce495a4119a",
            "sma-sb4-0-1av-41": "c3f3835aa814b8fbd0de12da08d3d4ebec0ccdeb38d9dd46aed03cf9b1c5534e",
        }
        for selector, expected in released.items():
            with self.subTest(profile=selector):
                profile = self.profile(selector)
                original = json.dumps(profile, sort_keys=True)
                binding = energy_binding_profile(profile)
                digest = hashlib.sha256(json.dumps(binding, sort_keys=True).encode()).hexdigest()
                self.assertEqual(digest, expected)
                self.assertEqual(json.dumps(profile, sort_keys=True), original)
                # An unrecognized edit must still change the energy identity.
                for key in (
                    "total-yield",
                    "power-l1",
                ):
                    modified = json.loads(original)
                    next(p for p in modified["properties"] if p["id"] == key)["scale"] = 2
                    changed = energy_binding_profile(modified)
                    digest = hashlib.sha256(
                        json.dumps(changed, sort_keys=True).encode()
                    ).hexdigest()
                    self.assertNotEqual(digest, expected)

    def test_phase_addresses_scaling_sentinels_and_unchanged_read_intervals(self):
        for selector, phases in (("sma-stp8-0-3av-40", (1, 2, 3)), ("sma-sbs3-7-10", (1,))):
            profile = self.profile(selector)
            blocks = {p["id"]: p for p in profile["pollers"]}
            definitions = {p["id"]: p for p in profile["properties"]}
            for phase in phases:
                for key, address, raw, expected, sentinel in (
                    (f"power-l{phase}", 30775 + 2 * phase, -123, -123, 0x80000000),
                    (f"volt-g{phase}", 30781 + 2 * phase, 23123, Decimal("231.23"), 0xFFFFFFFF),
                ):
                    with self.subTest(profile=selector, key=key):
                        prop = definitions[key]
                        block = blocks[prop["poller"]]
                        self.assertEqual(block["start"] + prop["offset"], address)
                        self.assertEqual(block["function"], 4)
                        self.assertEqual(block["intervalSeconds"], 3 if len(phases) == 3 else 5)
                        words = [0] * block["count"]
                        for value, result in ((raw, expected), (0, 0), (sentinel, None)):
                            unsigned = value & 0xFFFFFFFF
                            words[prop["offset"] : prop["offset"] + 2] = [
                                unsigned >> 16,
                                unsigned & 65535,
                            ]
                            self.assertEqual(decode(words, prop), result)
            if len(phases) == 3:
                self.assertEqual(blocks["power-a"]["start"], 30769)
                self.assertEqual(blocks["power-a"]["count"], 20)
            else:
                self.assertEqual(blocks["ac-power"]["count"], 4)

    def test_pv_public_topic_metadata_matches_with_optional_groups_disabled(self):
        inventories = []
        for slot, selector in ((1, "sma-stp8-0-3av-40"), (3, "sma-sb4-0-1av-41")):
            reader = ModbusReader(
                Inverter(advanced_channels_enabled=False, diagnostics_enabled=False),
                self.profile(selector),
            )
            state = SourceState(f"inverter{slot}", "fixture", reader.properties, 60)
            props = HomiePublisher(self.config, [state]).properties([state])
            inventories.append(
                {
                    p.key: (p.unit, p.datatype, p.channel_group, p.settable)
                    for p in props
                    if p.node != "diagnostics"
                }
            )
            topics = discovery("homie", "fixture", props)
            for phase in (1, 2, 3):
                for prefix, unit in (("powerl", "W"), ("voltagel", "V"), ("currentl", "A")):
                    base = f"homie/fixture/measurements/{prefix}{phase}"
                    self.assertEqual(topics[base + "/$unit"], unit)
                    self.assertEqual(topics[base + "/$settable"], "false")
            state.update({"measurements/status": "Ok (Ok)", "measurements/power-l1": None}, now=10)
            self.assertEqual(state.status(10), "ready")
        self.assertEqual(inventories[0], inventories[1])

    def test_storage_meter_block_and_supported_l1_are_read_only_optional_measurements(self):
        profile = self.profile("sma-sbs3-7-10")
        reader = ModbusReader(Inverter(), profile)
        definitions = {p["id"]: p for p in profile["properties"]}
        blocks = {p["id"]: p for p in profile["pollers"]}
        for key, address, expected in (
            ("power-drawn", 30865, 321),
            ("power-grid-feed-in", 30867, 654),
        ):
            prop = definitions[key]
            block = blocks[prop["poller"]]
            self.assertEqual(block["start"] + prop["offset"], address)
            self.assertEqual(block["count"], 4)
            self.assertEqual(block["intervalSeconds"], 5)
            self.assertEqual(decode([0, 321, 0, 654], prop), expected)
            self.assertEqual(decode([0, 0, 0, 0], prop), 0)
            self.assertIsNone(decode([0x8000, 0, 0x8000, 0], prop))
        state = SourceState("inverter2", "fixture", reader.properties, 60)
        props = HomiePublisher(self.config, [state]).properties([state])
        topics = discovery("homie", "fixture", props)
        for key, unit in (
            ("powerl1", "W"),
            ("voltagel1", "V"),
            ("powerdrawn", "W"),
            ("powergridfeedin", "W"),
        ):
            base = f"homie/fixture/measurements/{key}"
            self.assertEqual(topics[base + "/$unit"], unit)
            self.assertEqual(topics[base + "/$settable"], "false")
        self.assertNotIn("power-l2", definitions)
        self.assertNotIn("volt-g2", definitions)
        state.update({"measurements/status": "Ok (Ok)"}, now=10)
        self.assertEqual(state.status(10), "ready")
