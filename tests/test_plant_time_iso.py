"""Profile-driven UTC plant time, with raw epoch seconds independently optional."""

import copy
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock

from sma_mqtt_bridge.adapters.home_manager_modbus import HomeManagerModbusReader
from sma_mqtt_bridge.adapters.modbus import decode
from sma_mqtt_bridge.config import HomeManager
from sma_mqtt_bridge.errors import ConfigError
from sma_mqtt_bridge.home_manager_profile import (
    load_home_manager_profile,
    mappings,
)
from sma_mqtt_bridge.homie import discovery
from tests.test_home_manager_modbus import words


class PlantTimeISOTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.profile = load_home_manager_profile(
            "sma-home-manager-2-modbus", "/nonexistent-fixture-profiles"
        )
        self.iso = next(p for p in self.profile["properties"] if p["id"] == "plant-time-iso")

    def test_utc_conversion_sentinel_and_dst_boundaries(self):
        for seconds in (0, 1, 4294967294, 1774745999, 1774746000, 1792890000):
            actual = decode(words(seconds), self.iso)
            self.assertTrue(actual.endswith("Z"))
            self.assertEqual(datetime.fromisoformat(actual).timestamp(), seconds)
            self.assertEqual(datetime.fromisoformat(actual).tzinfo, timezone.utc)
        self.assertIsNone(decode(words(4294967295), self.iso))

    def test_format_validation_rejects_incompatible_encoding(self):
        for field, value in [
            ("type", "int32"),
            ("scale", 0.001),
            ("datatype", "integer"),
            ("unit", "s"),
            ("minimum", 0),
            ("format", "unknown"),
        ]:
            p = copy.deepcopy(self.profile)
            iso = next(v for v in p["properties"] if v["id"] == "plant-time-iso")
            iso[field] = value
            with self.assertRaises(ConfigError):
                mappings(p["pollers"], p["properties"])

    async def test_same_poll_advanced_off_and_invalid_sample(self):
        for advanced in (False, True):
            reader = HomeManagerModbusReader(
                HomeManager(
                    advanced_channels_enabled=advanced,
                    diagnostics_enabled=False,
                    transaction_delay_seconds=0,
                ),
                self.profile,
            )
            keys = {p.key for p in reader.properties}
            self.assertIn("measurements/plant-time-iso", keys)
            self.assertEqual("measurements/plant-time" in keys, advanced)
            metadata = discovery("homie", "fixture", reader.properties)
            root = "homie/fixture/measurements/planttimeiso"
            self.assertEqual(metadata[root + "/$datatype"], "string")
            self.assertEqual(metadata[root + "/$settable"], "false")
            self.assertNotIn(root + "/$unit", metadata)
            iso_prop = next(p for p in reader.properties if p.id == "plant-time-iso")
            self.assertFalse(iso_prop.required_for_ready)
            reader.connect = AsyncMock(side_effect=lambda: {})
            for poller in reader.pollers:
                reader.next_due[poller["id"]] = float("inf")
            reader.next_due["plant-time"] = 0
            reader.paced_read = AsyncMock(return_value=words(1791910800))
            values = await reader.read()
            self.assertEqual(values["measurements/plant-time-iso"], "2026-10-13T17:00:00Z")
            self.assertEqual("measurements/plant-time" in values, advanced)
            reader.paced_read.assert_awaited_once()
            self.assertEqual(reader.paced_read.call_args.args[0]["start"], 30193)
            reader.next_due["plant-time"] = 0
            reader.paced_read.return_value = words(4294967295)
            values = await reader.read()
            self.assertIsNone(values["measurements/plant-time-iso"])
            self.assertNotIn("measurements/plant-time-iso", await reader.read())
