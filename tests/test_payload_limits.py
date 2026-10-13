"""Bound observation expansion before allocation and preserve invalid-sample behavior."""

import tempfile
import unittest
from decimal import Decimal
from unittest.mock import patch

from sma_mqtt_bridge.config import load_config
from sma_mqtt_bridge.errors import ConfigError
from sma_mqtt_bridge.model import Property, SourceState, payload
from sma_mqtt_bridge.runtime import sources


class PayloadLimitTests(unittest.TestCase):
    def test_extreme_exponents_never_reach_fixed_point_formatting(self):
        prop = Property("measurements", "power", "Power")
        for value in ("1e1000000000", "1e-1000000000", "-1e1000000000", "0e-1000000000"):
            with self.subTest(value=value), patch("builtins.format", side_effect=AssertionError):
                self.assertIsNone(payload(value, prop))
        self.assertEqual(payload("0e1000000000", prop), "0")
        self.assertEqual(payload("-0e1000000000", prop), "-0")

    def test_fixed_point_length_boundary_preserves_exact_numeric_payloads(self):
        prop = Property("measurements", "power", "Power")
        for value in ("1e3", "-1e3", "1e-3", "-1e-3", "123.45", "0.000", "-0.00", "1.00", "0"):
            with self.subTest(value=value):
                expected = format(Decimal(value), "f")
                self.assertEqual(payload(value, prop, len(expected)), expected)
                self.assertIsNone(payload(value, prop, len(expected) - 1))
        integer = Property("measurements", "counter", "Counter", "integer")
        self.assertEqual(payload(4500.0, integer, 4), "4500")
        self.assertIsNone(payload(4500, integer, 3))

    def test_utf8_byte_limits_invalid_unicode_and_other_types(self):
        prop = Property("measurements", "text", "Text", "string")
        self.assertEqual(payload("ä", prop, 2), "ä")
        self.assertIsNone(payload("ä", prop, 1))
        self.assertIsNone(payload("\ud800", prop))
        boolean = Property("settings", "enabled", "Enabled", "boolean")
        self.assertEqual(payload(False, boolean, 5), "false")
        self.assertIsNone(payload(False, boolean, 4))
        enum = Property("settings", "mode", "Mode", "enum", format="one,two")
        self.assertEqual(payload("one", enum, 3), "one")
        self.assertIsNone(payload("one", enum, 2))
        self.assertIsNone(payload("other", enum, 10))

    def test_oversized_sample_is_not_fresh_and_never_becomes_zero(self):
        prop = Property("measurements", "power", "Power")
        state = SourceState("fixture", "fixture", (prop,), 10, max_payload_bytes=4)
        state.update({prop.key: 1234}, now=1)
        self.assertEqual(state.status(1), "ready")
        state.update({prop.key: "1e1000000000"}, now=2)
        self.assertEqual(state.fresh_values(2), {})
        self.assertEqual(state.status(2), "stale")
        state.update({prop.key: 0}, now=3)
        self.assertEqual(state.fresh_values(3), {prop.key: "0"})

    def test_configuration_override_validation_and_source_propagation(self):
        from tests.helpers import write_json

        with tempfile.TemporaryDirectory() as directory:
            filename = write_json(directory, "config.json", {"runtime": {"maxPayloadBytes": 8}})
            self.assertEqual(
                load_config({"SMAB_CONFIG_FILE": filename}).runtime.max_payload_bytes, 8
            )
            config = load_config({"SMAB_CONFIG_FILE": filename, "SMAB_MAX_PAYLOAD_BYTES": "16"})
            self.assertEqual(config.runtime.max_payload_bytes, 16)
        for value in ("0", "-1", "1.5", "true", ""):
            with self.subTest(value=value), self.assertRaises(ConfigError):
                load_config({"SMAB_MAX_PAYLOAD_BYTES": value})
        config = load_config(
            {
                "SMAB_MAX_PAYLOAD_BYTES": "16",
                "SMAB_ECHARGER_SEMP_ENABLED": "true",
                "SMAB_ECHARGER_HOST": "fixture.invalid",
                "SMAB_ECHARGER_SEMP_DEVICE_ID": "fixture",
                "SMAB_MQTT_HOST": "fixture.invalid",
                "SMAB_MQTT_TLS": "false",
            }
        )
        self.assertEqual(sources(config)[0][0].max_payload_bytes, 16)
