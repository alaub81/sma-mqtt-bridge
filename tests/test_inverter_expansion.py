"""Small inverter expansion with fixed identity, signed values and read-only discovery."""

import tempfile
import unittest
from decimal import Decimal

from sma_mqtt_bridge.adapters.modbus import ModbusReader, decode
from sma_mqtt_bridge.config import Inverter
from sma_mqtt_bridge.homie import discovery
from sma_mqtt_bridge.model import SourceState
from sma_mqtt_bridge.profiles import load_profile
from sma_mqtt_bridge.translation import load_translation


class InverterExpansionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def profiles(self):
        for selector in ("sma-stp8-0-3av-40", "sma-sbs3-7-10", "sma-sb4-0-1av-41"):
            yield load_profile(selector, self.tmp.name, require_validated=True)

    def test_limits_and_type_match_sunny_boy_and_stay_read_only_advanced(self):
        for profile, model in zip(self.profiles(), (9347, 9356, 9403)):
            definitions = {p["id"]: p for p in profile["properties"]}
            blocks = {b["id"]: b for b in profile["pollers"]}
            for key, address, raw in (
                ("type", 30053, model),
                ("max-power", 30231, 8000),
                ("set-max-power", 30233, 7000),
            ):
                prop = definitions[key]
                self.assertEqual(blocks[prop["poller"]]["start"] + prop["offset"], address)
                self.assertEqual(prop["channelGroup"], "advanced")
                self.assertEqual(decode([0] * prop["offset"] + [0, raw], prop), raw)
                self.assertIsNone(decode([0] * prop["offset"] + [65535, 65535], prop))
            all_reader = ModbusReader(Inverter(), profile)
            topics = discovery("homie", "fixture", all_reader.properties)
            for key in ("type", "maxpower", "setmaxpower"):
                self.assertEqual(topics[f"homie/fixture/measurements/{key}/$settable"], "false")
            self.assertFalse(profile["commands"])

    def test_documented_small_measurement_blocks_units_and_signed_decoding(self):
        for index, profile in enumerate(self.profiles(), 1):
            definitions = {p["id"]: p for p in profile["properties"]}
            blocks = {b["id"]: b for b in profile["pollers"]}
            cases = [("frequency", 30803, 5012, Decimal("50.12"), "Hz")]
            for phase in (1, 2, 3) if index == 1 else (1,) if index == 2 else (2, 3):
                cases.append(
                    (f"current-l{phase}", 30977 + 2 * (phase - 1), -1234, Decimal("-1.234"), "A")
                )
            if index == 2:
                cases += [
                    ("active-power", 30775, -321, Decimal(-321), "W"),
                    ("battery-current", 30843, -1234, Decimal("-1.234"), "A"),
                    ("battery-voltage", 30851, 45678, Decimal("456.78"), "V"),
                ]
            if index == 3:
                cases += [
                    ("current-b-input", 30957, 1234, Decimal("1.234"), "A"),
                    ("voltage-b-input", 30959, 34567, Decimal("345.67"), "V"),
                    ("power-b-input", 30961, 4321, Decimal(4321), "W"),
                ]
            for key, address, raw, expected, unit in cases:
                with self.subTest(profile=profile["id"], key=key):
                    prop = definitions[key]
                    block = blocks[prop["poller"]]
                    self.assertEqual(block["start"] + prop["offset"], address)
                    self.assertEqual(block["function"], 4)
                    self.assertEqual(block["intervalSeconds"], 5)
                    self.assertEqual(prop["unit"], unit)
                    unsigned = raw & 0xFFFFFFFF
                    self.assertEqual(
                        decode([0] * prop["offset"] + [unsigned >> 16, unsigned & 65535], prop),
                        expected,
                    )
                    self.assertEqual(decode([0] * prop["offset"] + [0, 0], prop), 0)
                    invalid = 0x80000000 if prop["type"] == "int32" else 0xFFFFFFFF
                    self.assertIsNone(
                        decode([0] * prop["offset"] + [invalid >> 16, invalid & 65535], prop)
                    )

    def test_basic_reads_survive_filters_and_optional_nan_does_not_block_ready(self):
        labels = load_translation("de", self.tmp.name)
        for index, profile in enumerate(self.profiles(), 1):
            reader = ModbusReader(
                Inverter(advanced_channels_enabled=False, diagnostics_enabled=False), profile
            )
            keys = {p.id for p in reader.properties}
            self.assertIn("frequency", keys)
            for key in ("type", "max-power", "set-max-power"):
                self.assertNotIn(key, keys)
            if index == 2:
                self.assertTrue({"active-power", "battery-current", "battery-voltage"} <= keys)
                self.assertNotIn("current-l2", keys)
                self.assertNotIn("current-l3", keys)
            if index == 3:
                self.assertNotIn("current-l1", keys)
                self.assertTrue({"current-b-input", "voltage-b-input", "power-b-input"} <= keys)
            topics = discovery("homie", "fixture", reader.properties, labels)
            if index == 3:
                for key in ("currentbinput", "voltagebinput", "powerbinput"):
                    self.assertEqual(topics[f"homie/fixture/measurements/{key}/$settable"], "false")
            self.assertEqual(topics["homie/fixture/measurements/frequency/$name"], "Netzfrequenz")
            state = SourceState("fixture", "fixture", reader.properties, 60)
            state.update({"measurements/status": "Ok (Ok)", "measurements/frequency": None}, now=10)
            self.assertEqual(state.status(now=10), "ready")
            self.assertNotIn("measurements/frequency", state.fresh_values(now=10))
