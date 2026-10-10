"""Profile schema, containment, override failures and local identity gates."""

import copy
from pathlib import Path
import tempfile
import unittest

from sma_mqtt_bridge.errors import ConfigError, ProtocolError
from sma_mqtt_bridge.profiles import load_profile, validate_profile, verify_identity
from tests.helpers import validated_profile, write_json


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_bundled_descriptors(self):
        for id in ("sma-stp8-0-3av-40", "sma-sbs3-7-10", "sma-sb4-0-1av-41"):
            self.assertEqual(load_profile(id, self.tmp.name)["validation"]["status"], "identity-only")
            with self.assertRaises(ConfigError):
                load_profile(id, self.tmp.name, require_validated=True)

    def test_host_override_and_file_resolution(self):
        profile = validated_profile()
        write_json(self.tmp.name, "test-inverter.json", profile)
        self.assertEqual(load_profile("test-inverter", self.tmp.name, require_validated=True)["id"], "test-inverter")
        write_json(self.tmp.name, "custom.json", profile)
        self.assertEqual(load_profile("file:custom.json", self.tmp.name)["id"], "test-inverter")

    def test_invalid_override_does_not_fall_back(self):
        Path(self.tmp.name, "sma-stp8-0-3av-40.json").write_text("{}")
        with self.assertRaises(ConfigError):
            load_profile("sma-stp8-0-3av-40", self.tmp.name)

    def test_path_escape_missing_file_and_symlink(self):
        for name in ("file:../outside.json", "file:/outside.json", "../outside", "file:missing.json", "file:a/b.json"):
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
        mutations = [lambda p: p.update(schemaVersion=True), lambda p: p["protocol"].update(type="unknown"),
                     lambda p: p["pollers"][0].update(function=6), lambda p: p["pollers"][0].update(count=126),
                     lambda p: p["properties"][0].update(poller="missing"),
                     lambda p: p["properties"][3].update(length=1),
                     lambda p: p["properties"][3].update(offset=2),
                     lambda p: p["properties"][3].update(scale=float("inf")),
                     lambda p: p["properties"][3].update(byteOrder="guess"),
                     lambda p: p["device"].update(supportedFirmware=[]),
                     lambda p: p["identity"].update(model="absent"),
                     lambda p: p["commands"].append({"set": "all"}),
                     lambda p: p["properties"].append(copy.deepcopy(p["properties"][0]))]
        for mutate in mutations:
            p = copy.deepcopy(original)
            mutate(p)
            with self.subTest(profile=p), self.assertRaises(ConfigError):
                validate_profile(p)

    def test_device_identity_must_match_model_firmware_and_serial(self):
        p = validate_profile(validated_profile())
        values = {"model": "TEST-INVERTER", "firmware": "test-1", "serial": 123}
        verify_identity(p, values, "123")
        for bad in ({"model": "different"}, {"firmware": "future"}, {"serial": 999}, {"model": None}):
            with self.subTest(bad=bad), self.assertRaises(ProtocolError):
                verify_identity(p, values | bad, "123")
