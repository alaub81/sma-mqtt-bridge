"""U64 energy/duration decoding, model-scoped derating and optional discovery."""

import tempfile
import unittest
from decimal import Decimal

from sma_mqtt_bridge.adapters.modbus import ModbusReader, decode
from sma_mqtt_bridge.config import Inverter
from sma_mqtt_bridge.homie import discovery
from sma_mqtt_bridge.model import SourceState
from sma_mqtt_bridge.profiles import load_profile
from sma_mqtt_bridge.translation import load_translation


def words(prop, raw):
    return [0] * prop["offset"] + [
        (raw >> shift) & 65535 for shift in range(prop["length"] * 16 - 16, -1, -16)
    ]


class InverterCounterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.profiles = [
            load_profile(model, self.tmp.name, require_validated=True)
            for model in ("sma-stp8-0-3av-40", "sma-sbs3-7-10", "sma-sb4-0-1av-41")
        ]

    def test_duration_u64_keeps_seconds_and_precision_above_float_range(self):
        for profile in self.profiles:
            definitions = {p["id"]: p for p in profile["properties"]}
            blocks = {b["id"]: b for b in profile["pollers"]}
            for key, address in (("operating-time", 30521), ("feed-in-time", 30525)):
                prop = definitions[key]
                block = blocks[prop["poller"]]
                self.assertEqual(block["start"] + prop["offset"], address)
                self.assertEqual((prop["type"], prop["unit"], prop["scale"]), ("uint64", "s", 1))
                self.assertEqual(block["function"], 4)
                for raw in (0, 3601, 2**53 + 1):
                    self.assertEqual(decode(words(prop, raw), prop), Decimal(raw))
                self.assertIsNone(decode(words(prop, 2**64 - 1), prop))

    def test_storage_energy_wh_to_kwh_does_not_reuse_legacy_yield_override(self):
        profile = self.profiles[1]
        definitions = {p["id"]: p for p in profile["properties"]}
        block = next(b for b in profile["pollers"] if b["id"] == "battery-energy")
        self.assertEqual(
            (block["function"], block["start"], block["count"], block["intervalSeconds"]),
            (4, 31397, 8, 60),
        )
        for key, offset in (("battery-charge-energy", 0), ("battery-discharge-energy", 4)):
            prop = definitions[key]
            self.assertEqual(prop["offset"], offset)
            self.assertEqual(
                (prop["type"], prop["datatype"], prop["unit"]), ("uint64", "float", "kWh")
            )
            for raw in (0, 1, 1234567, 2**53 + 1):
                self.assertEqual(decode(words(prop, raw), prop), Decimal(raw) / 1000)
            self.assertIsNone(decode(words(prop, 2**64 - 1), prop))
        self.assertEqual(definitions["total-yield"]["scale"], 1)
        for profile in (self.profiles[0], self.profiles[2]):
            self.assertFalse(any(p["id"].endswith("-energy") for p in profile["properties"]))

    def test_derating_codes_are_model_scoped_and_nan_is_not_an_enum_state(self):
        for index, profile in enumerate(self.profiles):
            prop = next(p for p in profile["properties"] if p["id"] == "derating-reason")
            block = next(b for b in profile["pollers"] if b["id"] == prop["poller"])
            self.assertEqual(block["start"] + prop["offset"], 30219)
            self.assertEqual(decode(words(prop, 884), prop), "Keine Abregelung (NoneDrt)")
            self.assertEqual(decode(words(prop, 557), prop), "Übertemperatur (TmpDrt)")
            for raw in (16777213, 4294967295, 999999):
                self.assertIsNone(decode(words(prop, raw), prop))
            self.assertEqual(
                decode(words(prop, 4560), prop),
                "Externe Vorgabe (WSptMaxDrt)" if index == 0 else None,
            )

    def test_groups_readiness_and_read_only_discovery(self):
        labels = load_translation("de", self.tmp.name)
        for index, profile in enumerate(self.profiles):
            reader = ModbusReader(Inverter(), profile)
            topics = discovery("homie", "fixture", reader.properties, labels)
            for key, unit in (("operatingtime", "s"), ("feedintime", "s")):
                root = f"homie/fixture/measurements/{key}"
                self.assertEqual(topics[root + "/$unit"], unit)
                self.assertEqual(topics[root + "/$settable"], "false")
            self.assertEqual(topics["homie/fixture/diagnostics/deratingreason/$settable"], "false")
            basic = ModbusReader(
                Inverter(advanced_channels_enabled=False, diagnostics_enabled=False), profile
            )
            keys = {p.id for p in basic.properties}
            self.assertNotIn("operating-time", keys)
            self.assertNotIn("feed-in-time", keys)
            self.assertNotIn("derating-reason", keys)
            if index == 1:
                self.assertIn("battery-charge-energy", keys)
                self.assertIn("battery-discharge-energy", keys)
            state = SourceState("fixture", "fixture", reader.properties, 60)
            values = {
                "measurements/status": "Ok (Ok)",
                "diagnostics/derating-reason": None,
                "measurements/operating-time": None,
                "measurements/feed-in-time": None,
            }
            if index == 1:
                values["measurements/battery-charge-energy"] = None
            state.update(values, now=10)
            self.assertEqual(state.status(now=10), "ready")
            self.assertFalse(profile["commands"])
