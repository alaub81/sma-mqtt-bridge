"""Shared JSON acceptance and caller-specific, redacted rejection boundaries."""

import tempfile
import unittest
from pathlib import Path

from sma_mqtt_bridge.adapters.http import json_data
from sma_mqtt_bridge.config import read_json
from sma_mqtt_bridge.errors import ConfigError, ProtocolError, StateError
from sma_mqtt_bridge.storage import read_state


class JsonParsingTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "fixture.json"

    def test_valid_values_and_repeated_keys_in_separate_objects(self):
        cases = (
            (
                '{"rows":[{"value":0},{"value":-1}],"empty":{}}',
                {"rows": [{"value": 0}, {"value": -1}], "empty": {}},
            ),
            ('{"label":"Gr\\u00f6\\u00dfe","literal":"NaN"}', {"label": "Größe", "literal": "NaN"}),
            (
                "[null,true,false,1.25,-0.5,9223372036854775808]",
                [None, True, False, 1.25, -0.5, 9223372036854775808],
            ),
            ("null", None),
            ("0", 0),
        )
        for text, expected in cases:
            with self.subTest(text=text):
                self.path.write_text(text, encoding="utf-8")
                self.assertEqual(json_data(text), expected)
                self.assertEqual(read_json(self.path), expected)
                self.assertEqual(read_state(self.path, 4096), expected)

    def test_ambiguous_and_malformed_data_keep_caller_errors_without_contents(self):
        cases = (
            '{"fixture-secret":1,"fixture-secret":2}',
            '{"rows":[{"fixture-secret":1,"fixture-secret":2}]}',
            '{"fixture-secret":1,"fixture-\\u0073ecret":2}',
            '{"fixture-secret":NaN}',
            '{"fixture-secret":Infinity}',
            '{"rows":[{"fixture-secret":-Infinity}]}',
            '{"fixture-secret":1,}',
            "<html>fixture-secret</html>",
            "",
        )
        for text in cases:
            self.path.write_text(text, encoding="utf-8")
            callers = (
                (
                    lambda text=text: json_data(text),
                    ProtocolError,
                    "Invalid JSON protocol response",
                ),
                (
                    lambda: read_json(self.path),
                    ConfigError,
                    "Cannot read a valid JSON configuration/profile file",
                ),
                (
                    lambda: read_state(self.path, 4096),
                    StateError,
                    "Persistent state is corrupt; manual reconciliation required",
                ),
            )
            for call, error_type, message in callers:
                with self.subTest(text=text, caller=error_type.__name__):
                    with self.assertRaises(error_type) as raised:
                        call()
                    self.assertEqual(str(raised.exception), message)
                    self.assertTrue(raised.exception.__suppress_context__)

    def test_invalid_utf8_keeps_file_and_protocol_rejections(self):
        data = b'{"fixture-secret":"\xff"}'
        self.path.write_bytes(data)
        for call, error_type in (
            (lambda: json_data(data), ProtocolError),
            (lambda: read_json(self.path), ConfigError),
            (lambda: read_state(self.path, 4096), StateError),
        ):
            with self.subTest(caller=error_type.__name__), self.assertRaises(error_type):
                call()
