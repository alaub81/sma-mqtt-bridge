"""Profile schema, containment, override failures and local identity gates."""

import copy
import json
import tempfile
import unittest
from pathlib import Path

from sma_mqtt_bridge.adapters.modbus import decode
from sma_mqtt_bridge.errors import ConfigError, ProtocolError
from sma_mqtt_bridge.profiles import load_profile, validate_profile, verify_identity
from tests.helpers import validated_profile, write_json


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_bundled_profiles(self):
        for id in ("sma-stp8-0-3av-40", "sma-sbs3-7-10", "sma-sb4-0-1av-41"):
            profile = load_profile(id, self.tmp.name, require_validated=True)
            self.assertEqual(profile["validation"]["status"], "validated")
            self.assertFalse(profile["commands"])

    def test_identity_only_descriptor_remains_blocked(self):
        profile = validated_profile()
        profile.pop("identity")
        profile.update(pollers=[], properties=[])
        profile["validation"]["status"] = "identity-only"
        write_json(self.tmp.name, "test-inverter.json", profile)
        with self.assertRaisesRegex(ConfigError, "identity-only"):
            load_profile("test-inverter", self.tmp.name, require_validated=True)

    def test_existing_ranges_intervals_and_model_specific_energy_units(self):
        root = Path(__file__).resolve().parents[1]
        inventory = json.loads((root / "reference/inverter-things-inventory.json").read_text())
        for device, selector, unit in zip(
            inventory["devices"],
            ("sma-stp8-0-3av-40", "sma-sbs3-7-10", "sma-sb4-0-1av-41"),
            ("kWh", "kWh", "kWh"),
        ):
            p = load_profile(selector, self.tmp.name, require_validated=True)
            self.assertEqual(
                [
                    (b["function"], b["start"], b["count"], b["intervalSeconds"])
                    for b in p["pollers"][1 : 1 + len(device["pollers"])]
                ],
                [
                    (b["function"], b["start"], b["count"], b["intervalSeconds"])
                    for b in device["pollers"]
                ],
            )
            self.assertEqual(
                len(p["properties"])
                - 3
                - {
                    "sma-stp8-0-3av-40": 7,
                    "sma-sbs3-7-10": 8,
                    "sma-sb4-0-1av-41": 7,
                }[selector],
                sum(len(b["channels"]) for b in device["pollers"]),
            )
            for energy_id in ("day-yield", "total-yield"):
                energy = next(x for x in p["properties"] if x["id"] == energy_id)
                self.assertEqual(energy["unit"], unit)
                self.assertEqual(energy["datatype"], "integer")
                self.assertEqual(energy["scale"], 1)
                self.assertEqual(decode([0] * energy["offset"] + [0, 2], energy), 2)
            prop = next(x for x in p["properties"] if x["id"] == "total-yield")
            self.assertEqual(prop["unit"], unit)
            self.assertEqual(prop["type"], "uint32")
            words = [0] * prop["offset"] + [0x8000, 1]
            self.assertEqual(decode(words, prop), 2147483649)
            self.assertIsNone(decode([0] * prop["offset"] + [0xFFFF, 0xFFFF], prop))
            if selector == "sma-sb4-0-1av-41":
                device_type = next(x for x in p["properties"] if x["id"] == "type")
                self.assertEqual(device_type["datatype"], "integer")
                self.assertEqual(decode([0, 9403], device_type), 9403)

    def test_host_override_and_file_resolution(self):
        profile = validated_profile()
        write_json(self.tmp.name, "test-inverter.json", profile)
        self.assertEqual(
            load_profile("test-inverter", self.tmp.name, require_validated=True)["id"],
            "test-inverter",
        )
        write_json(self.tmp.name, "custom.json", profile)
        self.assertEqual(load_profile("file:custom.json", self.tmp.name)["id"], "test-inverter")

    def test_invalid_override_does_not_fall_back(self):
        Path(self.tmp.name, "sma-stp8-0-3av-40.json").write_text("{}")
        with self.assertRaises(ConfigError):
            load_profile("sma-stp8-0-3av-40", self.tmp.name)

    def test_path_escape_missing_file_and_symlink(self):
        for name in (
            "file:../outside.json",
            "file:/outside.json",
            "../outside",
            "file:missing.json",
            "file:a/b.json",
        ):
            with self.subTest(name=name), self.assertRaises(ConfigError):
                load_profile(name, self.tmp.name)
        Path(self.tmp.name, "escape.json").symlink_to("/not/present")
        with self.assertRaises(ConfigError):
            load_profile("file:escape.json", self.tmp.name)

    def test_id_match(self):
        write_json(self.tmp.name, "wrong.json", validated_profile())
        with self.assertRaises(ConfigError):
            load_profile("wrong", self.tmp.name)

    def test_strict_mapping_schema(self):
        original = validated_profile()
        mutations = [
            lambda p: p.update(schemaVersion=True),
            lambda p: p["protocol"].update(type="unknown"),
            lambda p: p["pollers"][0].update(function=6),
            lambda p: p["pollers"][0].update(count=126),
            lambda p: p["properties"][0].update(poller="missing"),
            lambda p: p["properties"][3].update(length=1),
            lambda p: p["properties"][3].update(offset=2),
            lambda p: p["properties"][3].update(scale=float("inf")),
            lambda p: p["properties"][3].update(byteOrder="guess"),
            lambda p: p["device"].update(supportedFirmware=[]),
            lambda p: p["identity"].update(model="absent"),
            lambda p: p["commands"].append({"set": "all"}),
            lambda p: p["properties"].append(copy.deepcopy(p["properties"][0])),
        ]
        for mutate in mutations:
            p = copy.deepcopy(original)
            mutate(p)
            with self.subTest(profile=p), self.assertRaises(ConfigError):
                validate_profile(p)

    def test_device_identity_must_match_model_firmware_and_serial(self):
        p = validate_profile(validated_profile())
        values = {"model": "TEST-INVERTER", "firmware": "test-1", "serial": 123}
        verify_identity(p, values, "123")
        for bad in (
            {"model": "different"},
            {"firmware": "future"},
            {"serial": 999},
            {"model": None},
        ):
            with self.subTest(bad=bad), self.assertRaises(ProtocolError):
                verify_identity(p, values | bad, "123")
