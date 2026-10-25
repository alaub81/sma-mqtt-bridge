"""Bounded counter synchronization never accepts a decreasing household balance."""

import copy
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

import test_wallbox_daily
from test_plant import PlantFixture

from sma_mqtt_bridge.config import load_config
from sma_mqtt_bridge.energy_balances import EnergyBalances, validate_ledger


class CounterTimingTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.config = load_config({"SMAB_STATE_DIR": self.directory.name})
        self.zone = ZoneInfo("Europe/Berlin")
        self.ledger = EnergyBalances(self.config, "a" * 64, self.zone)
        self.wall = datetime(2026, 10, 14, 12, tzinfo=timezone.utc)
        self.signs = {"pv1": 1, "pv2": 1, "import": 1, "export": -1, "charge": -1, "discharge": 1}

    def step(self, seconds, deltas=None, *, stamps=None, name="house", hardware="b" * 64):
        signs = self.signs | ({"wallbox": -1} if name == "housewithoutwallbox" else {})
        values = {key: Decimal(100) + Decimal((deltas or {}).get(key, "0")) for key in signs}
        times = {
            key: self.wall + timedelta(seconds=(stamps or {}).get(key, seconds)) for key in signs
        }
        return self.ledger.observe(
            name,
            values,
            signs,
            hardware,
            self.wall + timedelta(seconds=seconds),
            min(times.values()),
            sample_wall=max(times.values()),
            sample_times=times,
            daily_only=name == "housewithoutwallbox",
        )

    def restart(self):
        self.ledger.persist(0, force=True)
        self.ledger = EnergyBalances(self.config, "a" * 64, self.zone)

    def test_delayed_pv_recovers_without_lower_values_or_baseline_changes(self):
        for name in ("house", "housewithoutwallbox"):
            with self.subTest(name=name):
                self.assertEqual(self.step(0, name=name)[::2], (Decimal(0), "partial"))
                original = copy.deepcopy(self.ledger.data["accounts"][name])
                self.assertEqual(
                    self.step(1, {"charge": ".002"}, stamps={"pv1": 0, "pv2": 0}, name=name),
                    (None, None, "synchronizing"),
                )
                self.assertTrue(self.ledger.force_save)
                self.ledger.persist(1)
                record = self.ledger.committed[name]
                self.assertEqual(record["dailyValue"], "0")
                self.assertEqual(record["last"]["charge"], "100.002")
                self.assertEqual(
                    self.step(180, {"pv1": ".013", "pv2": ".004", "charge": ".006"}, name=name)[
                        ::2
                    ],
                    (Decimal(".011"), "partial"),
                )
                for field in ("dailyBase", "totalBase", "start", "hardware"):
                    self.assertEqual(self.ledger.data["accounts"][name][field], original[field])
                self.assertNotIn(name, self.ledger.synchronizing)
                validate_ledger(self.ledger.data)

    def test_all_current_inputs_and_older_outflows_are_immediately_inconsistent(self):
        for stamps in ({}, {"charge": 0}):
            with self.subTest(stamps=stamps):
                self.ledger.data["accounts"].clear()
                self.step(0)
                self.assertEqual(
                    self.step(1, {"charge": ".002"}, stamps=stamps),
                    (None, None, "inconsistent"),
                )
                self.assertEqual(self.ledger.synchronizing, {})

    def test_positive_but_decreasing_balance_also_waits_without_republishing_the_peak(self):
        self.step(0)
        self.assertEqual(self.step(1, {"pv1": ".010"})[0], Decimal(".010"))
        self.assertEqual(
            self.step(2, {"pv1": ".010", "charge": ".002"}, stamps={"pv1": 1}),
            (None, None, "synchronizing"),
        )
        self.assertEqual(self.ledger.data["accounts"]["house"]["dailyValue"], "0.010")
        self.assertEqual(
            self.step(180, {"pv1": ".013", "charge": ".002"})[::2],
            (Decimal(".011"), "partial"),
        )

    def test_grace_expires_without_new_samples_or_renewal_by_outflows(self):
        self.step(0)
        old_pv = {"pv1": 0, "pv2": 0}
        self.assertEqual(self.step(1, {"charge": ".002"}, stamps=old_pv)[2], "synchronizing")
        self.assertEqual(self.step(120, {"charge": ".003"}, stamps=old_pv)[2], "synchronizing")
        self.assertEqual(self.step(240, {"charge": ".004"}, stamps=old_pv)[2], "synchronizing")
        # The deadline is the first rejected frame plus the configured skew limit.
        self.assertEqual(self.step(241, {"charge": ".004"}, stamps=old_pv)[2], "inconsistent")
        self.assertEqual(self.step(242, {"charge": ".005"}, stamps=old_pv)[2], "inconsistent")
        self.assertEqual(self.ledger.data["accounts"]["house"]["dailyValue"], "0")

    def test_each_lagging_inflow_gets_one_refresh_then_unresolved_balance_is_inconsistent(self):
        self.step(0)
        self.step(1, {"charge": ".002"}, stamps={"pv1": 0, "pv2": 0})
        self.assertEqual(self.step(60, {"charge": ".002"}, stamps={"pv2": 0})[2], "synchronizing")
        self.assertEqual(self.step(61, {"charge": ".002"})[2], "inconsistent")
        self.assertEqual(self.step(62, {"charge": ".003"}, stamps={"pv1": 61})[2], "inconsistent")
        self.assertEqual(self.step(180, {"pv1": ".013", "charge": ".006"})[2], "partial")
        # A genuinely recovered account can wait for a later, separate episode.
        self.assertEqual(
            self.step(181, {"pv1": ".013", "charge": ".008"}, stamps={"pv1": 180})[2],
            "synchronizing",
        )

    def test_restart_does_not_reopen_grace_and_saved_rejected_counter_still_detects_reset(self):
        self.step(0)
        self.step(1, {"charge": ".002"}, stamps={"pv1": 0})
        self.restart()
        self.assertEqual(self.step(2, {"charge": ".003"}, stamps={"pv1": 0})[2], "inconsistent")
        self.assertEqual(self.step(3, {"charge": ".001"}, stamps={"pv1": 0}), (None, None, "reset"))
        self.restart()
        self.assertEqual(self.step(180, {"pv1": ".013", "charge": ".006"}), (None, None, "reset"))

    def test_real_reset_during_grace_blocks_immediately(self):
        for name in ("house", "housewithoutwallbox"):
            with self.subTest(name=name):
                self.step(0, name=name)
                self.step(1, {"charge": ".002"}, stamps={"pv1": 0}, name=name)
                self.assertEqual(self.step(2, {"charge": ".001"}, name=name), (None, None, "reset"))
                self.assertNotIn(name, self.ledger.synchronizing)

    def test_clock_and_hardware_guards_do_not_mutate_pending_state(self):
        self.step(0)
        self.step(10, {"charge": ".002"}, stamps=dict.fromkeys(self.signs, 5) | {"pv1": 0})
        original = copy.deepcopy(self.ledger.data)
        waiting = copy.deepcopy(self.ledger.synchronizing)
        self.assertEqual(
            self.step(9, {"charge": ".002"}, stamps=dict.fromkeys(self.signs, 5)),
            (None, None, "clock-error"),
        )
        self.assertEqual(self.step(11, hardware="c" * 64), (None, None, "configuration-changed"))
        self.assertEqual(self.ledger.data, original)
        self.assertEqual(self.ledger.synchronizing, waiting)

    def test_configuration_and_membership_changes_keep_saved_ledger(self):
        self.step(0)
        self.step(1, {"charge": ".002"}, stamps={"pv1": 0})
        self.restart()
        saved = self.ledger.path.read_bytes()
        self.ledger = EnergyBalances(self.config, "c" * 64, self.zone)
        self.assertEqual(self.step(2), (None, None, "configuration-changed"))
        self.ledger.persist(300, force=True)
        self.assertEqual(self.ledger.path.read_bytes(), saved)
        self.ledger = EnergyBalances(self.config, "a" * 64, self.zone)
        self.assertEqual(
            self.ledger.observe(
                "house",
                {"other": Decimal(100)},
                {"other": 1},
                "b" * 64,
                self.wall + timedelta(seconds=2),
                self.wall,
            ),
            (None, None, "configuration-changed"),
        )
        self.assertEqual(self.ledger.path.read_bytes(), saved)

    def test_midnight_does_not_archive_an_unresolved_day_or_carry_its_wait(self):
        self.wall = datetime(2026, 10, 14, 21, 59, 30, tzinfo=timezone.utc)
        self.step(-60)
        self.ledger.data["accounts"]["house"]["dailyStatus"] = "complete"
        self.step(0, {"pv1": ".010"})
        self.step(1, {"pv1": ".010", "charge": ".002"}, stamps={"pv1": 0})
        daily, total, status = self.step(60, {"pv1": ".013", "charge": ".006"})
        self.assertEqual((daily, total, status), (Decimal(0), None, "inconsistent"))
        record = self.ledger.data["accounts"]["house"]
        self.assertEqual(record["history"], {})
        self.assertEqual(record["date"], "2026-10-15")
        self.assertNotIn("house", self.ledger.synchronizing)

    def test_existing_schema_two_precision_offsets_history_and_other_state_are_preserved(self):
        self.step(0)
        self.ledger.data.update(schemaVersion=2, precisionOffsets={"pv1": ".466"})
        self.ledger.data["accounts"]["house"]["history"] = {"2026-10-13": "8.5"}
        self.ledger.persist(0)
        other = Path(self.directory.name) / "mqtt-topics.json"
        other.write_bytes(b"unrelated fixture state")
        before = copy.deepcopy(self.ledger.data)
        self.step(1, {"charge": ".002"}, stamps={"pv1": 0})
        self.ledger.persist(1)
        self.assertEqual(self.ledger.data["schemaVersion"], 2)
        self.assertEqual(self.ledger.data["signature"], before["signature"])
        self.assertEqual(self.ledger.data["precisionOffsets"], before["precisionOffsets"])
        self.assertEqual(self.ledger.data["accounts"]["house"]["history"], {"2026-10-13": "8.5"})
        validate_ledger(self.ledger.data)
        self.assertEqual(other.read_bytes(), b"unrelated fixture state")

    def test_new_outflow_waits_for_its_older_inflow_without_extending_deadline(self):
        self.step(0)
        self.step(1, {"charge": ".002"}, stamps={"pv1": 0, "pv2": 0})
        self.step(120, {"charge": ".010", "pv1": ".004", "pv2": ".002"}, stamps={"pv2": 119})
        self.assertEqual(
            self.step(180, {"charge": ".010", "pv1": ".004", "pv2": ".002"}, stamps={"pv2": 119})[
                2
            ],
            "synchronizing",
        )
        since, cutoff, waiting = self.ledger.synchronizing["house"]
        self.assertEqual(since, self.wall + timedelta(seconds=1))
        self.assertEqual(cutoff, self.wall + timedelta(seconds=120))
        self.assertIn("pv2", waiting)
        self.assertEqual(
            self.step(181, {"charge": ".010", "pv1": ".004", "pv2": ".008"})[::2],
            (Decimal(".002"), "partial"),
        )

    def test_advancing_cutoff_never_renews_original_timeout(self):
        self.step(0)
        self.step(1, {"charge": ".002"}, stamps={"pv1": 0})
        self.step(239, {"charge": ".010"}, stamps={"pv1": 238})
        self.assertEqual(self.step(241, {"charge": ".020"}, stamps={"pv1": 240})[2], "inconsistent")
        self.assertNotIn("house", self.ledger.synchronizing)
        self.assertEqual(self.ledger.data["accounts"]["house"]["dailyValue"], "0")


class PlantCounterTimingTests(PlantFixture):
    def test_cached_frame_expires_grace_without_refreshing_the_confirmed_energy(self):
        engine = self.engine(
            ac=True,
            env={
                "SMAB_PLANT_PUBLISH_PARTIAL_DAY": "true",
                "SMAB_PLANT_MAX_SKEW_SECONDS": "10",
                "SMAB_PLANT_CHECKPOINT_INTERVAL_SECONDS": "300",
            },
        )
        engine.refresh(100, self.wall)
        energy = engine.ledger.committed["house"]["dailyValue"]
        charge = engine.groups["battery"][0]["batterychargeenergy"]
        engine.sources[charge.source].update({charge.key: "40.002"}, now=101)
        engine.refresh(101, self.wall + timedelta(seconds=1))
        values = engine.state.fresh_values(101)
        self.assertEqual(values["diagnostics/house-energy-status"], "synchronizing")
        self.assertNotIn("house/daily-consumption", values)
        self.assertNotIn(
            "house/dailyconsumption", values["diagnostics/valid-properties"].split(",")
        )
        self.assertNotIn("house/daily-consumption", engine.state.values)
        self.assertEqual(engine.ledger.committed["house"]["dailyValue"], energy)
        self.assertEqual(engine.ledger.last_save, 101)
        engine.refresh(111, self.wall + timedelta(seconds=11))
        self.assertEqual(
            engine.state.fresh_values(111)["diagnostics/house-energy-status"], "inconsistent"
        )
        self.fill(
            engine,
            112,
            {
                "inverter1": {"totalyield": "100.013"},
                "inverter3": {"totalyield": "200.004"},
                "inverter2": {"batterychargeenergy": "40.006"},
            },
        )
        engine.refresh(112, self.wall + timedelta(seconds=12))
        self.assertEqual(
            engine.state.fresh_values(112)["diagnostics/house-energy-status"], "partial"
        )
        # Checkpoint publication remains separate from calculation eligibility.
        self.assertEqual(engine.state.fresh_values(112)["house/daily-consumption"], "0")
        engine.ledger.persist(112, force=True)
        engine.refresh(113, self.wall + timedelta(seconds=13))
        self.assertEqual(
            Decimal(engine.state.fresh_values(113)["house/daily-consumption"]), Decimal(".011")
        )

    def test_missing_stale_skewed_or_failed_sources_cannot_use_grace(self):
        for failure in ("missing", "stale", "skew", "error"):
            with self.subTest(failure=failure):
                engine = self.engine(ac=True, env={"SMAB_PLANT_MAX_SKEW_SECONDS": "10"})
                engine.ledger.data["accounts"].clear()
                engine.refresh(100, self.wall)
                charge = engine.groups["battery"][0]["batterychargeenergy"]
                engine.sources[charge.source].update({charge.key: "40.002"}, now=101)
                engine.refresh(101, self.wall + timedelta(seconds=1))
                source = engine.sources["inverter1"]
                key = engine.groups["pv"][0]["totalyield"].key
                if failure == "missing":
                    source.values.pop(key)
                elif failure == "stale":
                    source.values[key] = (source.values[key][0], -1000)
                elif failure == "skew":
                    source.values[key] = (source.values[key][0], 89)
                else:
                    source.error = True
                engine.refresh(102, self.wall + timedelta(seconds=2))
                self.assertEqual(
                    engine.state.fresh_values(102)["diagnostics/house-energy-status"], "unavailable"
                )
                self.assertNotIn("house/daily-consumption", engine.state.fresh_values(102))


class WallboxCounterTimingTests(unittest.TestCase):
    def fixture(self):
        fixture = test_wallbox_daily.WallboxDailyTests()
        fixture.setUp()
        fixture.wall = datetime(2026, 10, 14, 12, tzinfo=timezone.utc)
        self.addCleanup(fixture.doCleanups)
        engine = fixture.engine(ac=True, env={"SMAB_PLANT_PUBLISH_PARTIAL_DAY": "true"})
        engine.refresh(100, fixture.wall)
        return fixture, engine

    def test_delayed_wallbox_outflow_only_synchronizes_the_excluded_house_balance(self):
        fixture, engine = self.fixture()
        engine.sources["api"].update({"measurements/total-energy": "1000.002"}, now=101)
        engine.refresh(101, fixture.wall + timedelta(seconds=1))
        values = fixture.output_values(engine, 101)
        self.assertEqual(values["diagnostics/house-energy-status"], "partial")
        self.assertEqual(values["diagnostics/wallbox-day-status"], "partial")
        self.assertEqual(values["diagnostics/house-without-wallbox-day-status"], "synchronizing")
        self.assertEqual(Decimal(values["measurements/daily-consumption"]), Decimal(".002"))
        self.assertNotIn("house/daily-consumption-without-wallbox", values)
        fixture.fill(
            engine,
            180,
            {
                "inverter1": {"totalyield": "100.013"},
                "inverter3": {"totalyield": "200.004"},
                "inverter2": {"batterychargeenergy": "40.006"},
            },
            energy="1000.002",
        )
        engine.refresh(180, fixture.wall + timedelta(seconds=80))
        values = fixture.output_values(engine, 180)
        self.assertEqual(Decimal(values["house/daily-consumption"]), Decimal(".011"))
        self.assertEqual(
            Decimal(values["house/daily-consumption-without-wallbox"]), Decimal(".009")
        )

    def test_failed_entry_checkpoint_never_publishes_synchronization(self):
        fixture, engine = self.fixture()
        original = engine.ledger.path.read_bytes()
        engine.sources["api"].update({"measurements/total-energy": "1000.002"}, now=101)
        with patch("sma_mqtt_bridge.energy_balances.write_state", side_effect=OSError("fixture")):
            with self.assertRaises(OSError):
                engine.refresh(101, fixture.wall + timedelta(seconds=1))
        self.assertEqual(engine.ledger.path.read_bytes(), original)
        self.assertEqual(
            fixture.output_values(engine, 101)["diagnostics/house-without-wallbox-day-status"],
            "partial",
        )
        self.assertTrue(engine.ledger.force_save)


if __name__ == "__main__":
    unittest.main()
