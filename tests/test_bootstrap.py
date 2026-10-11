"""Exercise Python CLI offline, without private ENV files or network sessions."""

import json
import logging
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from sma_mqtt_bridge.__main__ import TimestampFormatter

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ressources" if (ROOT / "ressources/sma_mqtt_bridge").is_dir() else ROOT


class BootstrapTests(unittest.TestCase):
    def test_log_timestamps_follow_timezone_and_daylight_saving(self):
        formatter = TimestampFormatter('Europe/Berlin')
        for month, offset, hour in ((1, '+01:00', '13'), (7, '+02:00', '14')):
            with self.subTest(month=month):
                record = logging.LogRecord('fixture', logging.WARNING, '', 0,
                                           'Source portal unavailable (stale)', (), None)
                record.created = datetime(2026, month, 11, 12, 0, 0, 123000,
                                          tzinfo=timezone.utc).timestamp()
                self.assertEqual(formatter.format(record),
                                 f'2026-{month:02d}-11T{hour}:00:00.123{offset} '
                                 'WARNING Source portal unavailable (stale)')

    def cli(self, *args, env=None):
        clean = {key: value for key, value in os.environ.items() if not key.startswith('SMAB_')}
        clean.update(env or {})
        return subprocess.run([sys.executable, '-m', 'sma_mqtt_bridge', *args], cwd=SOURCE,
                              env=clean, capture_output=True, text=True, timeout=5)

    def test_version_without_credentials(self):
        result = self.cli('--version')
        self.assertEqual(result.returncode, 0)
        self.assertRegex(result.stdout, r'^sma-mqtt-bridge \d+\.\d+\.\d+\n$')

    def test_status_distinguishes_runtime_from_live_acceptance(self):
        status = json.loads(self.cli('--project-status').stdout)
        self.assertTrue(status['runtimeImplemented'])
        self.assertFalse(status['liveVerified'])
        self.assertEqual(status['bundledPollingProfiles'], 3)
        self.assertTrue(status['readOnly'])

    def test_no_sources_fail_without_secret_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.cli(env={'SMAB_PORTAL_PASSWORD': 'fixture-do-not-log', 'SMAB_STATE_DIR': tmp})
        self.assertEqual(result.returncode, 2)
        self.assertIn('No sources enabled', result.stderr)
        self.assertNotIn('fixture-do-not-log', result.stderr + result.stdout)

    def test_check_config_without_network(self):
        result = self.cli('--check-config')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)['enabledSources'], 0)

    def test_check_profile_reports_validated_profile(self):
        result = self.cli('--check-profile', 'sma-stp8-0-3av-40')
        self.assertEqual(result.returncode, 0)
        self.assertTrue(json.loads(result.stdout)['pollingValidated'])

    def test_command_option_is_not_available(self):
        self.assertEqual(self.cli('--set-pv-share', '50').returncode, 2)
