"""Timestamp observation, bounded storage and unchanged read behavior."""

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

from sma_mqtt_bridge.adapters.echarger import NS, EChargerReader, SempReader
from sma_mqtt_bridge.config import ECharger, load_config
from sma_mqtt_bridge.errors import ConfigError
from sma_mqtt_bridge.runtime import sources
from sma_mqtt_bridge.timestamp_diagnostics import TimestampDiagnostics
from tests.helpers import write_json

POWER = "Measurement.Metering.GridMs.TotWIn.ChaSta"
NOW = datetime(2026, 10, 11, 12, tzinfo=timezone.utc)


class TimestampDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.observer = TimestampDiagnostics(self.directory.name, 4096, 300)

    def rows(self):
        return [json.loads(line) for line in self.observer.path.read_text().splitlines()]

    def observe(self, value, stamp=None, now=NOW, source="api", channel=POWER):
        self.observer.observe(source, channel, value, stamp or NOW.isoformat(), 180, now)

    def test_constant_values_new_timestamps_and_natural_changes(self):
        with patch("sma_mqtt_bridge.timestamp_diagnostics.time.monotonic", return_value=10):
            self.observe(0)
            self.observe("0.0")
            self.observe(
                0, now=NOW + timedelta(seconds=30), stamp=(NOW + timedelta(seconds=30)).isoformat()
            )
            self.observe(
                4500,
                now=NOW + timedelta(seconds=60),
                stamp=(NOW + timedelta(seconds=60)).isoformat(),
            )
        rows = self.rows()
        self.assertEqual(len(rows), 3)
        self.assertIsNone(rows[0]["valueChanged"])
        self.assertEqual(rows[0]["value"], "0")
        self.assertFalse(rows[1]["valueChanged"])
        self.assertTrue(rows[1]["timestampChanged"])
        self.assertEqual(rows[1]["suppressedSamples"], 1)
        self.assertTrue(rows[2]["valueChanged"])
        self.assertEqual(rows[2]["deviceAgeSeconds"], 0)

    def test_unchanged_summary_and_age_boundary_are_recorded(self):
        with patch(
            "sma_mqtt_bridge.timestamp_diagnostics.time.monotonic", side_effect=[0, 30, 300, 301]
        ):
            self.observe(4500)
            self.observe(4500, now=NOW + timedelta(seconds=30))
            self.observe(4500, now=NOW + timedelta(seconds=180))
            self.observe(4500, now=NOW + timedelta(seconds=181))
        rows = self.rows()
        self.assertEqual(rows[1]["repeatedSamples"], 3)
        self.assertEqual(rows[1]["timestampQuality"], "fresh")
        self.assertEqual(rows[2]["timestampQuality"], "stale")
        self.assertFalse(rows[2]["valueChanged"])
        self.assertFalse(rows[2]["timestampChanged"])

    def test_allowlist_redacts_invalid_values_and_timestamps(self):
        self.observe("fixture-secret", stamp="fixture-secret")
        self.observe(123, channel="Parameter.Nameplate.SerNum")
        self.observe(123, source="fixture-secret")
        row = self.rows()[0]
        self.assertIsNone(row["value"])
        self.assertIsNone(row["deviceTimestamp"])
        self.assertEqual(row["timestampQuality"], "invalid")
        self.assertNotIn("fixture-secret", self.observer.path.read_text())
        self.assertEqual(len(self.rows()), 1)
        self.observe("NaN", stamp="2026-10-11T12:00:01Z", source="semp")
        self.assertEqual(self.rows()[-1]["timestampQuality"], "future")

    def test_rotation_permissions_and_restart(self):
        for i in range(40):
            self.observe(i)
        backup = self.observer.path.with_suffix(".jsonl.1")
        self.assertTrue(backup.is_file())
        for path in (self.observer.path, backup):
            self.assertLessEqual(path.stat().st_size, 4096)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            for line in path.read_text().splitlines():
                self.assertEqual(json.loads(line)["schemaVersion"], 1)
        before = self.observer.path.read_text()
        restarted = TimestampDiagnostics(self.directory.name, 4096, 300)
        self.assertEqual(self.observer.path.read_text(), before)
        restarted.observe("api", POWER, 41, NOW.isoformat(), 180, NOW)
        self.assertEqual(self.rows()[-1]["value"], "41")

    def test_storage_failure_is_bounded_and_does_not_escape(self):
        with patch.object(self.observer, "append", side_effect=OSError("fixture-secret")) as append:
            with patch(
                "sma_mqtt_bridge.timestamp_diagnostics.time.monotonic", side_effect=[0, 10, 300]
            ):
                with self.assertLogs(
                    "sma_mqtt_bridge.timestamp_diagnostics", level="WARNING"
                ) as logs:
                    self.observe(4500)
                    self.observe(4500)
                    self.observe(4500)
        self.assertEqual(append.call_count, 2)
        self.assertEqual(len(logs.output), 2)
        self.assertNotIn("fixture-secret", "\n".join(logs.output))

    def test_symlinks_and_fifos_cannot_stall_or_overwrite_other_files(self):
        target = Path(self.directory.name) / "protected.txt"
        target.write_text("unchanged")
        self.observer.path.symlink_to(target)
        with self.assertLogs("sma_mqtt_bridge.timestamp_diagnostics", level="WARNING"):
            self.observe(1)
        self.assertEqual(target.read_text(), "unchanged")
        self.observer.path.unlink()
        os.mkfifo(self.observer.path)
        self.observer.retry_after = 0
        with self.assertLogs("sma_mqtt_bridge.timestamp_diagnostics", level="WARNING"):
            self.observe(2)

    def test_configuration_defaults_overrides_and_disabled_sources(self):
        config = load_config({})
        self.assertFalse(config.echarger.timestamp_diagnostics_enabled)
        configured = load_config(
            {
                "SMAB_STATE_DIR": self.directory.name,
                "SMAB_ECHARGER_TIMESTAMP_DIAGNOSTICS_ENABLED": "true",
                "SMAB_ECHARGER_TIMESTAMP_DIAGNOSTICS_MAX_BYTES": "4096",
                "SMAB_ECHARGER_TIMESTAMP_DIAGNOSTICS_SUMMARY_INTERVAL_SECONDS": "60",
            }
        )
        self.assertEqual(configured.echarger.timestamp_diagnostics_summary_interval_seconds, 60)
        config_file = write_json(
            self.directory.name,
            "config.json",
            {
                "echarger": {
                    "timestampDiagnosticsEnabled": True,
                    "timestampDiagnosticsMaxBytes": 8192,
                    "timestampDiagnosticsSummaryIntervalSeconds": 120,
                }
            },
        )
        json_config = load_config({"SMAB_CONFIG_FILE": config_file})
        self.assertTrue(json_config.echarger.timestamp_diagnostics_enabled)
        self.assertEqual(json_config.echarger.timestamp_diagnostics_max_bytes, 8192)
        override = load_config(
            {
                "SMAB_CONFIG_FILE": config_file,
                "SMAB_ECHARGER_TIMESTAMP_DIAGNOSTICS_ENABLED": "false",
            }
        )
        self.assertFalse(override.echarger.timestamp_diagnostics_enabled)
        with patch("sma_mqtt_bridge.runtime.TimestampDiagnostics", side_effect=AssertionError):
            self.assertEqual(sources(configured), [])
        self.assertFalse(self.observer.path.exists())
        for key, value in (
            ("MAX_BYTES", "4095"),
            ("MAX_BYTES", "16777217"),
            ("SUMMARY_INTERVAL_SECONDS", "0"),
            ("ENABLED", "invalid"),
        ):
            with self.subTest(key=key, value=value), self.assertRaises(ConfigError):
                load_config({"SMAB_ECHARGER_TIMESTAMP_DIAGNOSTICS_" + key: value})


class TimestampReaderTests(unittest.IsolatedAsyncioTestCase):
    async def test_api_observation_preserves_outputs_and_request_count(self):
        with tempfile.TemporaryDirectory() as directory:
            observer = TimestampDiagnostics(directory, 4096, 300)
            catalog = [
                {
                    "componentId": "IGULD:SELF",
                    "values": [
                        {"channelId": "Parameter.Nameplate.SerNum", "value": "123"},
                        {"channelId": "Parameter.Nameplate.ModelStr", "value": "EVC22-3AC-20"},
                    ],
                }
            ]
            live = [
                {"channelId": POWER, "values": [{"value": 4500, "time": NOW.isoformat()}]},
                {
                    "channelId": "Measurement.ChaSess.WhIn",
                    "values": [{"value": 1500, "time": (NOW - timedelta(days=3)).isoformat()}],
                },
            ]
            results = []
            for sink in (None, observer):
                reader = EChargerReader(
                    ECharger(expected_serial="123"), 10000, timestamp_observer=sink
                )
                reader.access_token = AsyncMock(return_value="fixture-token")
                reader.http.get_json = AsyncMock(side_effect=[catalog, live])
                with patch("sma_mqtt_bridge.adapters.echarger.datetime") as clock:
                    clock.now.return_value = NOW
                    clock.fromisoformat.side_effect = datetime.fromisoformat
                    results.append(await reader.read())
                self.assertEqual(reader.http.get_json.await_count, 2)
                self.assertEqual(reader.access_token.await_count, 1)
                await reader.close()
            self.assertEqual(results[0], results[1])
            rows = [json.loads(line) for line in observer.path.read_text().splitlines()]
            self.assertEqual(rows[1]["timestampQuality"], "stale")
            self.assertEqual(rows[1]["value"], "1500")
            self.assertIsNone(results[1]["measurements/session-energy"])

    async def test_semp_observation_preserves_outputs_even_with_storage_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            observer = TimestampDiagnostics(directory, 4096, 300)
            body = (
                f'<Device2EM xmlns="{NS}"><Parameters><Parameter><channelId>{POWER}</channelId>'
                f"<timestamp>{NOW.isoformat()}</timestamp><value>0</value></Parameter>"
                "</Parameters></Device2EM>"
            )
            results = []
            for sink in (None, observer):
                reader = SempReader(ECharger(), 10000, timestamp_observer=sink)
                reader.http.request = AsyncMock(side_effect=[(200, {}, body), (200, {}, body)])
                with (
                    patch("sma_mqtt_bridge.adapters.echarger.validate_semp_identity"),
                    patch("sma_mqtt_bridge.adapters.echarger.datetime") as clock,
                ):
                    clock.now.return_value = NOW
                    clock.fromisoformat.side_effect = datetime.fromisoformat
                    if sink is None:
                        results.append(await reader.read())
                    else:
                        with patch.object(observer, "append", side_effect=OSError("full")):
                            with self.assertLogs(
                                "sma_mqtt_bridge.timestamp_diagnostics", level="WARNING"
                            ):
                                results.append(await reader.read())
                self.assertEqual(reader.http.request.await_count, 2)
                await reader.close()
            self.assertEqual(results[0], results[1])
