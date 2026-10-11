"""Migration extraction refuses uncertain syntax and never exports private fields."""

import json
import unittest
from pathlib import Path

from sma_mqtt_bridge.errors import ConfigError
from sma_mqtt_bridge.profiles import validate_profile
from tests.inventory_things import InventoryError, inventory

SOURCE = """// Commented declarations must not become extra channels.
Bridge modbus:tcp:inverter1 "PRIVATE LABEL" [ host="private://address", port=502, id=3, connectMaxTries=3 ] {
    Bridge poller power "Power" [ start=30769, length=20, refresh=3000, type="input" ] {
        Thing data current "Current" [ readStart="30769", readValueType="int32", readTransform="JS(smalimit1000.js)" ]
        // Thing data unused "Ignored" [ readStart="30769", readValueType="uint32" ]
        Thing data voltage "Voltage" [ readStart="30771", readValueType="uint32" ]
    }
}
"""


class InventoryTests(unittest.TestCase):
    def test_preserves_ranges_types_intervals_and_transform_without_private_fields(self):
        result = inventory([SOURCE])
        encoded = json.dumps(result)
        self.assertNotIn("PRIVATE LABEL", encoded)
        self.assertNotIn("private://address", encoded)
        self.assertNotIn('"host"', encoded)
        self.assertFalse(result["pollingAuthorized"])
        poller = result["devices"][0]["pollers"][0]
        self.assertEqual(
            (poller["function"], poller["start"], poller["count"], poller["intervalSeconds"]),
            (4, 30769, 20, 3),
        )
        self.assertEqual(len(poller["channels"]), 2)
        self.assertEqual(poller["channels"][0]["readTransform"], "JS(smalimit1000.js)")
        self.assertEqual(poller["channels"][1]["offset"], 2)
        self.assertEqual(poller["channels"][1]["type"], "uint32")
        with self.assertRaises(ConfigError):
            validate_profile(result)

    def test_unsafe_or_unhandled_exports_fail_without_echoing_source(self):
        cases = [
            SOURCE + "}",
            SOURCE[:-2],
            SOURCE.replace("id=3", "id=0"),
            SOURCE.replace('type="input"', 'type="holding"'),
            SOURCE.replace("refresh=3000", "refresh=0"),
            SOURCE.replace("length=20", "length=126"),
            SOURCE.replace('readStart="30771"', 'readStart="30788"'),
            SOURCE.replace('readValueType="uint32"', 'readValueType="uint64"'),
            SOURCE.replace('readValueType="uint32"', 'readValueType="uint32", writeStart="30771"'),
            SOURCE.replace("smalimit1000.js", "unknown-private.js"),
            SOURCE.replace("port=502", "port=502, port=503"),
            SOURCE.replace("private://address", 'broken"quote'),
        ]
        for source in cases:
            with self.subTest(), self.assertRaises(InventoryError) as caught:
                inventory([source])
            self.assertNotIn("private", str(caught.exception).lower())
        with self.assertRaises(InventoryError):
            inventory([SOURCE, SOURCE])
        with self.assertRaises(InventoryError):
            inventory(["// Empty export"])

    def test_public_evidence_preserves_all_41_channels_and_19_pollers(self):
        root = Path(__file__).resolve().parents[1]
        path = root / "reference/inverter-things-inventory.json"
        # Public tooling evidence is excluded from runtime images. Transport tests
        # run there too, so the same public file is supplied by the test mounts.
        data = json.loads(path.read_text())
        self.assertEqual(data["status"], "migration-evidence-only")
        self.assertFalse(data["pollingAuthorized"])
        self.assertEqual([len(d["pollers"]) for d in data["devices"]], [6, 7, 6])
        counts = [sum(len(p["channels"]) for p in d["pollers"]) for d in data["devices"]]
        self.assertEqual(counts, [14, 11, 16])


if __name__ == "__main__":
    unittest.main()
