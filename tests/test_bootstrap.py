"""Exercise Python CLI offline, without private ENV files or network sessions."""

import json
import logging
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from sma_mqtt_bridge.__main__ import TimestampFormatter

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ressources" if (ROOT / "ressources/sma_mqtt_bridge").is_dir() else ROOT


class BootstrapTests(unittest.TestCase):
    def test_log_timestamps_follow_timezone_and_daylight_saving(self):
        formatter = TimestampFormatter("Europe/Berlin")
        for month, offset, hour in ((1, "+01:00", "13"), (7, "+02:00", "14")):
            with self.subTest(month=month):
                record = logging.LogRecord(
                    "fixture", logging.WARNING, "", 0, "Source portal unavailable (stale)", (), None
                )
                record.created = datetime(
                    2026, month, 11, 12, 0, 0, 123000, tzinfo=timezone.utc
                ).timestamp()
                self.assertEqual(
                    formatter.format(record),
                    f"2026-{month:02d}-11T{hour}:00:00.123{offset} "
                    "WARNING Source portal unavailable (stale)",
                )

    def cli(self, *args, env=None):
        clean = {key: value for key, value in os.environ.items() if not key.startswith("SMAB_")}
        clean.update(env or {})
        return subprocess.run(
            [sys.executable, "-m", "sma_mqtt_bridge", *args],
            cwd=SOURCE,
            env=clean,
            capture_output=True,
            text=True,
            timeout=5,
        )

    def test_version_without_credentials(self):
        result = self.cli("--version")
        self.assertEqual(result.returncode, 0)
        self.assertRegex(
            result.stdout, r"^sma-mqtt-bridge \d+\.\d+\.\d+(?:-dev\.\d+)?(?:\+[a-z0-9.]+)?\n$"
        )

    def test_status_distinguishes_runtime_from_live_acceptance(self):
        status = json.loads(self.cli("--project-status").stdout)
        self.assertTrue(status["runtimeImplemented"])
        self.assertFalse(status["liveVerified"])
        self.assertEqual(status["bundledPollingProfiles"], 3)
        self.assertFalse(status["readOnly"])
        self.assertFalse(status["commandsEnabledByDefault"])

    def test_project_status_is_static_and_does_not_resolve_private_configuration(self):
        result = self.cli(
            "--project-status",
            env={
                "SMAB_CONFIG_FILE": "/missing-fixture-config.json",
                "SMAB_COMMANDS_ENABLED": "invalid",
                "SMAB_ECHARGER_PASSWORD": "fixture-do-not-log",
            },
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), json.loads(self.cli("--project-status").stdout))
        self.assertNotIn("fixture-do-not-log", result.stdout + result.stderr)

    def test_check_config_read_only_follows_global_and_adapter_command_gates(self):
        for adapter in ("ECHARGER", "PORTAL"):
            for global_gate, adapter_gate in (
                (False, False),
                (False, True),
                (True, True),
                (True, False),
            ):
                with self.subTest(
                    adapter=adapter, global_gate=global_gate, adapter_gate=adapter_gate
                ):
                    env = {
                        "SMAB_MQTT_HOST": "fixture.invalid",
                        "SMAB_COMMANDS_ENABLED": str(global_gate).lower(),
                        f"SMAB_{adapter}_COMMANDS_ENABLED": str(adapter_gate).lower(),
                        f"SMAB_{adapter}_ENABLED": "true",
                        f"SMAB_{adapter}_USERNAME": "fixture-account",
                        f"SMAB_{adapter}_PASSWORD": "fixture-do-not-log",
                    }
                    if adapter == "ECHARGER":
                        env.update(
                            SMAB_ECHARGER_HOST="fixture.invalid",
                            SMAB_ECHARGER_EXPECTED_SERIAL="123",
                        )
                    else:
                        env.update(SMAB_PORTAL_PLANT_ID="123", SMAB_PORTAL_DEVICE_ID="456")
                    result = self.cli("--check-config", env=env)
                    self.assertNotIn("fixture-do-not-log", result.stdout + result.stderr)
                    if global_gate and not adapter_gate:
                        self.assertEqual(result.returncode, 2)
                    else:
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertEqual(
                            json.loads(result.stdout)["readOnly"],
                            not (global_gate and adapter_gate),
                        )

    def test_no_sources_fail_without_secret_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.cli(
                env={"SMAB_PORTAL_PASSWORD": "fixture-do-not-log", "SMAB_STATE_DIR": tmp}
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("No sources enabled", result.stderr)
        self.assertNotIn("fixture-do-not-log", result.stderr + result.stdout)

    def test_check_config_without_network(self):
        result = self.cli("--check-config")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["enabledSources"], 0)
        self.assertTrue(json.loads(result.stdout)["readOnly"])

    def test_check_profile_reports_validated_profile(self):
        result = self.cli("--check-profile", "sma-stp8-0-3av-40")
        self.assertEqual(result.returncode, 0)
        self.assertTrue(json.loads(result.stdout)["pollingValidated"])

    def test_command_option_is_not_available(self):
        self.assertEqual(self.cli("--set-pv-share", "50").returncode, 2)
