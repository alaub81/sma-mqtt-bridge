"""Exercise the compiled CLI and Compose templates without SMA or MQTT access."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory(prefix='sma-bootstrap-test-')
        cls.binary = Path(cls.directory.name) / 'sma_mqtt_bridge'
        subprocess.run(['c++', '-std=c++17', '-Wall', '-Wextra', '-Wpedantic',
                        str(ROOT / 'resources/src/sma_mqtt_bridge.cpp'),
                        '-o', str(cls.binary)], check=True, capture_output=True)

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def test_version_is_available_without_credentials(self):
        result = subprocess.run([str(self.binary), '--version'],
                                capture_output=True, text=True, check=True)
        self.assertRegex(result.stdout, r'^sma-mqtt-bridge \d+\.\d+\.\d+[-\w]*\n$')

    def test_status_does_not_claim_a_functioning_runtime(self):
        result = subprocess.run([str(self.binary), '--project-status'],
                                capture_output=True, text=True, check=True)
        status = json.loads(result.stdout)
        self.assertFalse(status['runtimeImplemented'])
        self.assertFalse(status['paidSmaApisRequired'])

    def test_start_fails_clearly_without_exposing_credentials(self):
        env = dict(os.environ, SMA_PORTAL_PASSWORD='test-do-not-log-this')
        result = subprocess.run([str(self.binary)], env=env, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('not implemented yet', result.stderr)
        self.assertNotIn('test-do-not-log-this', result.stdout + result.stderr)

    def test_unsupported_commands_are_rejected(self):
        result = subprocess.run([str(self.binary), '--set-pv-share', '50'],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)

    def test_both_compose_templates_render_without_personal_configuration(self):
        env = dict(os.environ, SMA_BRIDGE_VERSION='test')
        for filename in ('docker-compose.example.yml', 'docker-compose.dev.yml'):
            with self.subTest(filename=filename):
                result = subprocess.run(['docker', 'compose', '--env-file', '.env.sample',
                                         '-f', filename, 'config', '--format', 'json'],
                                        cwd=ROOT, env=env, capture_output=True, text=True, check=True)
                configuration = json.loads(result.stdout)
                self.assertIn('sma-mqtt-bridge', configuration['services'])
                self.assertIn('sma_bridge_state', configuration['volumes'])
                self.assertFalse(any('BMB_' in key for key in
                                     configuration['services']['sma-mqtt-bridge'].get('environment', {})))


if __name__ == '__main__':
    unittest.main()
