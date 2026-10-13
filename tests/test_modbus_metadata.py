"""Preserve mapped formats, readiness and lifetimes at Modbus adapter boundaries."""

import unittest

from sma_mqtt_bridge.adapters.home_manager_modbus import HomeManagerModbusReader
from sma_mqtt_bridge.adapters.modbus import ModbusReader
from sma_mqtt_bridge.config import HomeManager, Inverter
from sma_mqtt_bridge.home_manager_profile import load_home_manager_profile, mappings
from sma_mqtt_bridge.homie import discovery
from sma_mqtt_bridge.profiles import validate_profile
from tests.helpers import validated_profile


class ModbusMetadataTests(unittest.TestCase):
    def test_inverter_keeps_enum_order_and_omits_non_enum_formats(self):
        raw = validated_profile()
        base = raw["properties"][-1]
        for datatype, mapping in (
            ("enum", {"1": "second", "2": "first", "3": "second"}),
            ("boolean", {"1": "true", "2": "false"}),
            ("string", {"1": "text", "2": "other"}),
        ):
            raw["properties"].append(
                base
                | {
                    "id": datatype,
                    "datatype": datatype,
                    "unit": "",
                    "valueMap": mapping,
                    "requiredForReady": True,
                }
            )
        reader = ModbusReader(Inverter(stale_seconds=1), validate_profile(raw))
        properties = {p.key: p for p in reader.properties}
        topics = discovery("fixture", "fixture", reader.properties)
        self.assertEqual(properties["measurements/enum"].format, "second,first")
        self.assertEqual(topics["fixture/fixture/measurements/enum/$format"], "second,first")
        for datatype in ("enum", "boolean", "string"):
            p = properties["measurements/" + datatype]
            self.assertEqual(p.datatype, datatype)
            self.assertEqual(p.stale_seconds, 6)
            self.assertTrue(p.required_for_ready)
            self.assertFalse(p.settable)
            if datatype != "enum":
                self.assertEqual(p.format, "")
                self.assertNotIn("fixture/fixture/measurements/" + datatype + "/$format", topics)

    def test_delegated_maps_keep_formats_without_becoming_required(self):
        profile = load_home_manager_profile(
            "sma-home-manager-2-modbus", "/nonexistent-fixture-profiles"
        )
        base = profile["delegated"]["properties"][0]
        profile["delegated"]["properties"].extend(
            [
                base
                | {
                    "id": "fixture-boolean",
                    "datatype": "boolean",
                    "unit": "",
                    "valueMap": {"1": "true", "2": "false"},
                    "requiredForReady": True,
                },
                base
                | {
                    "id": "fixture-string",
                    "datatype": "string",
                    "unit": "",
                    "valueMap": {"1": "second", "2": "first", "3": "second"},
                },
            ]
        )
        mappings(**profile["delegated"], delegated=True)
        reader = HomeManagerModbusReader(HomeManager(stale_seconds=1), profile)
        reader.assignments = {0: (158, 1234, 7), 1: (158, 2345, 7)}
        reader.refresh_properties()
        properties = {p.key: p for p in reader.properties}
        topics = discovery("fixture", "fixture", reader.properties)
        for datatype, expected in (("boolean", "true,false"), ("string", "second,first")):
            p = properties["device-1/fixture-" + datatype]
            self.assertEqual(p.node, "device-1")
            self.assertEqual(p.format, expected)
            self.assertFalse(p.required_for_ready)
            self.assertFalse(p.settable)
            self.assertEqual(
                topics["fixture/fixture/device1/fixture" + datatype + "/$format"], expected
            )
            self.assertNotIn("device-2/fixture-" + datatype, properties)

    def test_metadata_lifetime_keeps_interval_override_and_stale_floor(self):
        profile = validate_profile(validated_profile())
        for override, stale, expected in (
            (False, 1, 6),
            (True, 1, 34),
            (True, 1000, 1000),
        ):
            reader = ModbusReader(
                Inverter(poll_interval_seconds=17, stale_seconds=stale), profile, override
            )
            with self.subTest(override=override, stale=stale):
                power = next(p for p in reader.properties if p.key == "measurements/power")
                self.assertEqual(power.stale_seconds, expected)
                self.assertEqual(power.unit, "W")
                self.assertEqual(power.name, "Power")
