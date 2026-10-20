"""Offline checks for the explicit, non-deleting InfluxDB migration generator."""

import unittest

from tools.influx2_copy_item import generate


class InfluxMigrationTests(unittest.TestCase):
    def query(self, **overrides):
        args = dict(
            bucket="history",
            org="home",
            old="Old_Item",
            new="New_Item",
            start="2020-01-01T00:00:00Z",
            stop="2026-10-15T15:00:00Z",
        )
        return generate(**(args | overrides))

    def test_default_is_read_only_and_preserves_series_for_counts(self):
        query = self.query()
        self.assertNotIn("|> to(", query)
        self.assertNotIn("delete", query)
        self.assertIn('yield(name: "source_counts")', query)
        self.assertIn('yield(name: "target_last")', query)
        self.assertNotIn("|> group()", query)

    def test_copy_guards_and_preserves_payload(self):
        query = self.query(mode="copy")
        self.assertIn("if exists existing._value and existing._value > 0", query)
        self.assertIn("Unexpected item tag", query)
        self.assertIn("Source interval is empty", query)
        self.assertIn('set(key: "item", value: "New_Item")', query)
        self.assertIn("filter(fn: (r) => not exists r.item)", query)
        self.assertIn('set(key: "_measurement", value: "New_Item")', query)
        self.assertIn('to(bucket: "history", org: "home")', query)
        self.assertNotIn("aggregateWindow", query)
        self.assertNotIn("delete", query)

    def test_invalid_bounds_and_identity_are_rejected(self):
        for override in (
            {"new": "Old_Item"},
            {"new": ""},
            {"stop": "2020-01-01T00:00:00Z"},
            {"start": "2026-10-16T00:00:00Z"},
            {"start": "2020-01-01"},
            {"start": "2020-01-01T00:00:00+02:00"},
            {"mode": "invalid"},
            {"old": "${die(msg: 1)}"},
            {"org": "test\nsecret"},
        ):
            with self.subTest(override=override), self.assertRaises(ValueError):
                self.query(**override)
        self.assertIn('org: "quoted\\"org"', self.query(mode="copy", org='quoted"org'))


if __name__ == "__main__":
    unittest.main()
