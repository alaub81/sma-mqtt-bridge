"""Counter accounting across midnight, DST, gaps, resets and checkpoint failures."""

import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from sma_mqtt_bridge.config import load_config
from sma_mqtt_bridge.energy_balances import EnergyBalances
from sma_mqtt_bridge.errors import StateError


class EnergyBalanceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.config = load_config({"SMAB_STATE_DIR": self.directory.name})
        self.signature = hashlib.sha256(b"fixture").hexdigest()
        self.hardware = hashlib.sha256(b"meter").hexdigest()
        self.zone = ZoneInfo("Europe/Berlin")
        self.ledger = EnergyBalances(self.config, self.signature, self.zone)

    def observe(self, wall, value, *, ledger=None, oldest=None, hardware=None):
        return (ledger or self.ledger).observe(
            "import",
            {"grid/counter": Decimal(value)},
            {"grid/counter": Decimal(1)},
            hardware or self.hardware,
            wall.astimezone(timezone.utc),
            oldest or wall.astimezone(timezone.utc),
        )

    def test_partial_first_day_then_complete_local_day(self):
        before = datetime(2026, 10, 14, 23, 59, 30, tzinfo=self.zone)
        self.assertEqual(self.observe(before, "100"), (None, Decimal(0), "partial"))
        after = before + timedelta(seconds=60)
        self.assertEqual(self.observe(after, "101"), (Decimal(0), Decimal(1), "complete"))
        self.assertEqual(
            self.observe(after + timedelta(hours=1), "103.25"),
            (Decimal("2.25"), Decimal("3.25"), "complete"),
        )

    def test_local_day_is_23_or_25_hours_and_restart_keeps_baseline(self):
        for month, day, expected in ((3, 29, 23), (10, 25, 25)):
            with self.subTest(month=month):
                self.ledger.data["accounts"].clear()
                start = datetime(2026, month, day, tzinfo=self.zone)
                self.observe(start - timedelta(seconds=30), "100")
                self.observe(start + timedelta(seconds=30), "100.1")
                self.ledger.persist(10, force=True)
                restarted = EnergyBalances(self.config, self.signature, self.zone)
                end = start + timedelta(days=1)
                self.assertEqual(
                    (end.astimezone(timezone.utc) - start.astimezone(timezone.utc)).total_seconds(),
                    expected * 3600,
                )
                self.observe(end - timedelta(seconds=30), "123", ledger=restarted)
                daily, _, status = self.observe(
                    end + timedelta(seconds=30), "123.1", ledger=restarted
                )
                self.assertEqual((daily, status), (Decimal(0), "complete"))

    def test_missing_midnight_and_multi_day_outage_never_assign_energy_to_today(self):
        start = datetime(2026, 10, 14, 20, tzinfo=self.zone)
        self.observe(start, "100")
        daily, total, status = self.observe(start + timedelta(hours=12), "110")
        self.assertEqual((daily, total, status), (None, Decimal(10), "gap"))
        daily, total, status = self.observe(start + timedelta(days=3), "120")
        self.assertEqual((daily, total, status), (None, Decimal(20), "gap"))

    def test_old_sample_near_midnight_does_not_prove_boundary_coverage(self):
        before = datetime(2026, 10, 14, 23, 59, tzinfo=self.zone)
        self.observe(before, "100")
        after = before + timedelta(minutes=2)
        daily, _, status = self.observe(after, "101", oldest=before - timedelta(minutes=10))
        self.assertEqual((daily, status), (None, "gap"))

    def test_counter_reset_blocks_lifetime_and_next_day_can_recover_daily(self):
        before = datetime(2026, 10, 14, 23, 58, tzinfo=self.zone)
        self.observe(before, "100")
        self.assertEqual(self.observe(before + timedelta(seconds=10), "1"), (None, None, "reset"))
        self.ledger.persist(1, force=True)
        restarted = EnergyBalances(self.config, self.signature, self.zone)
        self.observe(before + timedelta(minutes=1), "2", ledger=restarted)
        daily, total, status = self.observe(before + timedelta(minutes=3), "3", ledger=restarted)
        self.assertEqual((daily, total, status), (Decimal(0), None, "complete"))

    def test_clock_backwards_and_hardware_replacement_do_not_rebase(self):
        wall = datetime(2026, 10, 14, 12, tzinfo=self.zone)
        self.observe(wall, "100")
        before = json.dumps(self.ledger.data, sort_keys=True)
        self.assertEqual(
            self.observe(wall - timedelta(hours=2), "101"), (None, None, "clock-error")
        )
        self.assertEqual(
            self.observe(
                wall + timedelta(seconds=1), "101", hardware=hashlib.sha256(b"new").hexdigest()
            ),
            (None, None, "configuration-changed"),
        )
        self.assertEqual(before, json.dumps(self.ledger.data, sort_keys=True))
        self.assertEqual(
            self.observe(wall + timedelta(seconds=2), "101"), (None, Decimal(1), "partial")
        )

    def test_checkpoint_throttle_and_forced_transition_before_publication(self):
        wall = datetime(2026, 10, 14, 12, tzinfo=self.zone)
        self.observe(wall, "100")
        with patch("sma_mqtt_bridge.energy_balances.write_state") as write:
            self.ledger.persist(0)
            self.observe(wall + timedelta(seconds=1), "101")
            self.ledger.persist(1)
            self.assertEqual(write.call_count, 1)
            self.ledger.persist(300)
            self.assertEqual(write.call_count, 2)
            self.observe(wall + timedelta(seconds=301), "0")
            self.ledger.persist(301)
            self.assertEqual(write.call_count, 3)

    def test_boundary_entry_is_saved_before_midnight_even_between_checkpoints(self):
        wall = datetime(2026, 10, 14, 23, 55, tzinfo=self.zone)
        self.observe(wall, "100")
        self.ledger.persist(0)
        self.observe(wall + timedelta(minutes=2), "101")
        self.ledger.persist(120)
        restarted = EnergyBalances(self.config, self.signature, self.zone)
        daily, _, status = self.observe(wall + timedelta(minutes=6), "102", ledger=restarted)
        self.assertEqual((daily, status), (Decimal(0), "complete"))

    def test_reused_near_boundary_sample_commits_calendar_transition(self):
        before = datetime(2026, 10, 14, 23, 59, tzinfo=self.zone).astimezone(timezone.utc)
        self.observe(before, "100")
        self.ledger.persist(0)
        after = before + timedelta(minutes=2)
        daily, _, status = self.ledger.observe(
            "import",
            {"grid/counter": Decimal(100)},
            {"grid/counter": Decimal(1)},
            self.hardware,
            after,
            before,
            sample_wall=before,
        )
        self.assertEqual((daily, status), (Decimal(0), "complete"))
        self.ledger.persist(120)
        self.assertEqual(self.ledger.committed["import"]["date"], "2026-10-15")
        self.assertEqual(self.ledger.committed["import"]["dailyValue"], "0")

    def test_extreme_counter_input_cannot_generate_an_unreadable_state(self):
        wall = datetime(2026, 10, 14, 12, tzinfo=self.zone)
        result = self.observe(wall, "1e1000000")
        self.assertEqual(result, (None, None, "invalid"))
        self.assertEqual(self.ledger.data["accounts"], {})

    def test_inconsistent_house_balance_is_not_clamped_and_durable_peak_is_preserved(self):
        wall = datetime(2026, 10, 14, 12, tzinfo=self.zone)
        signs = {"pv": Decimal(1), "export": Decimal(-1)}

        def step(pv, export, seconds):
            return self.ledger.observe(
                "house",
                {"pv": Decimal(pv), "export": Decimal(export)},
                signs,
                self.hardware,
                wall + timedelta(seconds=seconds),
                wall + timedelta(seconds=seconds),
            )

        step("100", "40", 0)
        _, total, _ = step("101", "40.5", 1)
        self.assertEqual(total, Decimal("0.5"))
        self.ledger.persist(1, force=True)
        _, total, status = step("101", "40.7", 2)
        self.assertEqual((total, status), (None, "inconsistent"))
        self.assertEqual(self.ledger.committed["house"]["totalValue"], "0.5")
        _, total, _ = step("102", "40.8", 3)
        self.assertEqual(total, Decimal("1.2"))

    def test_failed_durable_write_keeps_previous_state_and_remains_pending(self):
        wall = datetime(2026, 10, 14, 12, tzinfo=self.zone)
        self.observe(wall, "100")
        self.ledger.persist(0)
        previous = self.ledger.path.read_bytes()
        self.observe(wall + timedelta(seconds=1), "101")
        with patch("sma_mqtt_bridge.health.os.fsync", side_effect=OSError("fixture")):
            with self.assertRaises(OSError):
                self.ledger.persist(1, force=True)
        self.assertEqual(previous, self.ledger.path.read_bytes())
        self.assertTrue(self.ledger.dirty)

    def test_loaded_state_schema_decimal_and_size_limits(self):
        self.observe(datetime(2026, 10, 14, 12, tzinfo=self.zone), "100")
        self.ledger.persist(0)
        original = json.loads(self.ledger.path.read_text())
        for mutate in (
            lambda d: d.update(schemaVersion=True),
            lambda d: d.update(secret="never accepted"),
            lambda d: d["accounts"]["import"]["last"].update({"grid/counter": "NaN"}),
            lambda d: d["accounts"]["import"].update(lastTime="2026-10-14T12:00:00"),
            lambda d: d["accounts"]["import"].update(dailyStatus="invented"),
        ):
            data = json.loads(json.dumps(original))
            mutate(data)
            self.ledger.path.write_text(json.dumps(data))
            with self.assertRaises(StateError):
                EnergyBalances(self.config, self.signature, self.zone)
        Path(self.directory.name, "energy-balances.json").write_text(
            " " * (self.config.runtime.max_state_bytes + 1)
        )
        with self.assertRaises(StateError):
            EnergyBalances(self.config, self.signature, self.zone)
