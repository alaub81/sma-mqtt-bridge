"""Joint frame evidence and independent power/energy time guards."""

import json
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from test_plant import PlantFixture

from sma_mqtt_bridge.errors import ConfigError


class PlantTimingTests(PlantFixture):
    def test_same_latest_sample_with_wall_mapping_jitter_is_not_clock_error(self):
        engine = self.engine(ac=True)
        ref = engine.groups["pv"][0]["totalyield"]
        engine.sources[ref.source].values[ref.key] = ("100", 99)
        engine.refresh(100, self.wall)
        original = engine.ledger.data["accounts"]["house"]["lastTime"]
        # Only an older contributor catches up; the latest observation is unchanged.
        ref = engine.groups["pv"][0]["totalyield"]
        engine.sources[ref.source].values[ref.key] = ("100", 99.5)
        engine.refresh(101, self.wall + timedelta(seconds=0.9999))
        self.assertNotEqual(
            engine.state.values["diagnostics/house-energy-status"][0], "clock-error"
        )
        self.assertEqual(engine.ledger.data["accounts"]["house"]["lastTime"], original)
        engine.refresh(102, self.wall + timedelta(seconds=1.9998))
        self.assertNotEqual(
            engine.state.values["diagnostics/house-energy-status"][0], "clock-error"
        )

    def test_actual_wall_rollback_remains_blocked(self):
        engine = self.engine(ac=True)
        engine.refresh(100, self.wall)
        engine.refresh(101, self.wall - timedelta(seconds=1))
        self.assertEqual(engine.state.values["diagnostics/house-energy-status"][0], "clock-error")

    def test_power_skew_does_not_change_energy_guard_and_recovers(self):
        engine = self.engine(ac=True, env={"SMAB_PLANT_POWER_MAX_SKEW_SECONDS": "5"})
        ref = engine.groups["pv"][0]["activepower"]
        engine.sources[ref.source].values[ref.key] = ("2000", 94)
        engine.refresh(100, self.wall)
        self.assertNotIn("house/consumption", engine.state.fresh_values(100))
        self.assertEqual(engine.state.values["diagnostics/house-energy-status"][0], "partial")
        self.assertIn("sample-skew", engine.state.values["diagnostics/power-input-status"][0])
        engine.sources[ref.source].update({ref.key: 2000}, now=100)
        engine.refresh(100, self.wall)
        self.assertIn("house/consumption", engine.state.fresh_values(100))
        # Publishing between refreshes must enforce the same W-only guard.
        engine.sources[ref.source].update({ref.key: 2100}, now=106)
        self.assertNotIn("house/consumption", engine.state.fresh_values(106))

    def test_recorder_captures_same_frame_and_critical_staleness(self):
        engine = self.engine(ac=True, env={"SMAB_PLANT_RECORDER_ENABLED": "true"})
        engine.refresh(100, self.wall)
        row = json.loads(engine.recorder.path.read_text().splitlines()[-1])
        terms = row["powerRecipes"]["house/consumption"]
        expected = sum(
            Decimal(row["inputs"][term["input"]]["value"]) * term["sign"] for term in terms
        )
        self.assertEqual(Decimal(row["outputs"]["house/consumption"]["candidate"]), expected)
        self.assertEqual(
            row["outputs"]["house/consumption"]["candidate"],
            row["outputs"]["house/consumption"]["available"],
        )
        engine.refresh(1000, self.wall + timedelta(seconds=900))
        row = json.loads(engine.recorder.path.read_text().splitlines()[-1])
        self.assertTrue(row["sources"]["inverter1"]["missingCritical"])
        self.assertEqual(row["sources"]["inverter1"]["status"], "stale")
        self.assertIsNone(row["outputs"]["house/consumption"]["available"])
        self.assertNotIn("hardware", engine.recorder.path.read_text())

    def test_recorder_is_disabled_by_default_and_storage_failure_is_nonfatal(self):
        engine = self.engine(ac=True)
        engine.refresh(100, self.wall)
        self.assertFalse(engine.recorder.path.exists())
        engine.recorder.enabled = True
        with (
            patch.object(engine.recorder, "append", side_effect=OSError),
            self.assertLogs("sma_mqtt_bridge.plant_recorder", "WARNING"),
        ):
            engine.refresh(101, self.wall + timedelta(seconds=1))
        self.assertIn("house/consumption", engine.state.fresh_values(101))

    def test_recorder_rotates_and_rejects_symlink(self):
        engine = self.engine(ac=True, env={"SMAB_PLANT_RECORDER_ENABLED": "true"})
        engine.recorder.max_bytes = 30000
        for second in range(10):
            engine.refresh(100 + second, self.wall + timedelta(seconds=second))
        self.assertTrue(engine.recorder.path.with_suffix(".jsonl.1").exists())
        self.assertLessEqual(engine.recorder.path.stat().st_size, 30000)
        engine.recorder.path.unlink()
        target = engine.recorder.path.parent / "untouched"
        target.write_text("original")
        engine.recorder.path.symlink_to(target)
        with self.assertLogs("sma_mqtt_bridge.plant_recorder", "WARNING"):
            engine.refresh(111, self.wall + timedelta(seconds=11))
        self.assertEqual(target.read_text(), "original")

    def test_invalid_limits_fail_before_connections(self):
        for env in (
            {"SMAB_PLANT_POWER_MAX_SKEW_SECONDS": "-1"},
            {"SMAB_PLANT_POWER_MAX_SKEW_SECONDS": "3601"},
            {"SMAB_PLANT_RECORDER_MAX_BYTES": "0"},
        ):
            with self.subTest(env=env), self.assertRaises(ConfigError):
                self.engine(env=env)

    def test_negative_power_frame_makes_plant_stale_without_energy_clock_error(self):
        engine = self.engine(ac=True)
        engine.refresh(100, self.wall)
        self.assertEqual(engine.state.status(100), "ready")
        ref = engine.grid["powerexport"]
        engine.sources[ref.source].update({ref.key: 9000}, now=101)
        engine.refresh(101, self.wall + timedelta(seconds=1))
        self.assertEqual(engine.state.status(101), "stale")
        self.assertIn("negative-balance", engine.state.values["diagnostics/power-input-status"][0])
        self.assertNotEqual(
            engine.state.values["diagnostics/house-energy-status"][0], "clock-error"
        )

    def test_synchronizing_unchanged_frame_survives_clock_mapping_jitter(self):
        engine = self.engine(ac=True)
        engine.refresh(100, self.wall)
        ref = engine.groups["battery"][0]["batterychargeenergy"]
        engine.sources[ref.source].update({ref.key: "40.002"}, now=101)
        engine.refresh(101, self.wall + timedelta(seconds=1))
        self.assertEqual(engine.state.values["diagnostics/house-energy-status"][0], "synchronizing")
        engine.refresh(102, self.wall + timedelta(seconds=1.9999))
        self.assertEqual(engine.state.values["diagnostics/house-energy-status"][0], "synchronizing")
