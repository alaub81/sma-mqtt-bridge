"""Explicit baseline reset archives only the energy ledger with exclusive ownership."""

import io
import json
import os
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import test_wallbox_daily

from sma_mqtt_bridge.__main__ import main
from sma_mqtt_bridge.config import load_config
from sma_mqtt_bridge.energy_balances import reset_energy_baselines
from sma_mqtt_bridge.errors import StateError
from sma_mqtt_bridge.plant import PlantEngine
from sma_mqtt_bridge.storage import state_lock


class EnergyResetTests(unittest.TestCase):
    def setUp(self):
        self.fixture = test_wallbox_daily.WallboxDailyTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.env = self.fixture.env | {
            "SMAB_PLANT_ASSUME_AC_BATTERY_ENERGY": "true",
            "SMAB_PLANT_PUBLISH_PARTIAL_DAY": "true",
        }
        self.old = self.fixture.engine(env=self.env)
        self.old.refresh(100, self.fixture.wall)
        self.path = self.old.ledger.path

    def test_bundled_ac_upgrade_archives_old_five_accounts_and_restarts_without_assumption(self):
        env = dict(self.env)
        env.pop("SMAB_PLANT_ASSUME_AC_BATTERY_ENERGY")
        config = load_config(env)
        self.assertFalse(config.plant.assume_ac_battery_energy)
        mapping = config.profiles["inverter2"]["plant"]["battery"]
        self.assertEqual(mapping["energyBoundary"], "ac")
        self.assertIn("2026-10-15", mapping["energyEvidence"])
        blocked = PlantEngine(config, list(self.old.sources.values()))
        blocked.refresh(100, self.fixture.wall)
        self.assertEqual(
            blocked.state.fresh_values(100)["diagnostics/house-energy-status"],
            "configuration-changed",
        )
        others = {
            name: self.path.parent / name
            for name in (
                "mqtt-topics.json",
                "local-command-uncertainty.json",
                "portal-command-uncertainty.json",
            )
        }
        for path in others.values():
            path.write_bytes(b"unrelated-state-fixture")
        before = self.path.read_bytes()
        backup = reset_energy_baselines(config)
        self.assertFalse(self.path.exists())
        self.assertEqual((self.path.parent / backup).read_bytes(), before)
        self.assertEqual(len(json.loads(before)["accounts"]), 5)
        fresh = PlantEngine(config, list(self.old.sources.values()))
        fresh.refresh(100, self.fixture.wall)
        values = self.fixture.output_values(fresh, 100)
        self.assertEqual(values["diagnostics/battery-energy-boundary"], "ac")
        for key in (
            "grid/daily-energy-import",
            "grid/daily-energy-export",
            "house/daily-consumption",
            "house/daily-consumption-without-wallbox",
            "measurements/daily-consumption",
        ):
            self.assertEqual(float(values[key]), 0)
        for path in others.values():
            self.assertEqual(path.read_bytes(), b"unrelated-state-fixture")
        self.assertEqual((self.path.parent / backup).read_bytes(), before)

    def test_running_bridge_lock_prevents_reset(self):
        before = self.path.read_bytes()
        with state_lock(self.old.config.runtime.state_dir):
            with self.assertRaises(StateError):
                reset_energy_baselines(self.old.config)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.glob("energy-balances.backup-*.json")), [])

    def test_cli_resets_offline_and_repeated_missing_ledger_is_noop(self):
        before = self.path.read_bytes()
        with patch.dict(os.environ, self.env, clear=True), patch("asyncio.run") as run:
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["--reset-energy-baselines"]), 0)
            result = json.loads(output.getvalue())
            self.assertTrue(result["reset"])
            self.assertEqual(Path(result["backup"]).name, result["backup"])
            self.assertEqual((self.path.parent / result["backup"]).read_bytes(), before)
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["--reset-energy-baselines"]), 0)
            self.assertEqual(json.loads(output.getvalue()), {"reset": False, "backup": None})
            run.assert_not_called()

    def test_corrupt_and_symlink_ledgers_are_not_retired(self):
        before = self.path.read_bytes()
        self.path.write_text('{"schemaVersion":999}')
        with self.assertRaises(StateError):
            reset_energy_baselines(self.old.config)
        self.assertEqual(self.path.read_text(), '{"schemaVersion":999}')
        self.path.unlink()
        target = self.path.parent / "untouched.json"
        target.write_bytes(before)
        self.path.symlink_to(target)
        with self.assertRaises(StateError):
            reset_energy_baselines(self.old.config)
        self.assertEqual(target.read_bytes(), before)
        self.assertTrue(self.path.is_symlink())

    def test_archive_failure_keeps_active_ledger(self):
        before = self.path.read_bytes()
        with patch.object(Path, "rename", side_effect=OSError("fixture")):
            with self.assertRaises(OSError):
                reset_energy_baselines(self.old.config)
        self.assertEqual(self.path.read_bytes(), before)
