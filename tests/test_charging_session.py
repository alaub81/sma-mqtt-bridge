"""Session pause/resumption, disconnect archival, freshness and durable recovery."""

import asyncio
import json
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from sma_mqtt_bridge.adapters.echarger import NS, semp_values
from sma_mqtt_bridge.charging_session import ENERGY, POWER, VEHICLE, ChargingSession, observation
from sma_mqtt_bridge.config import load_config
from sma_mqtt_bridge.errors import StateError
from sma_mqtt_bridge.model import SampleValues, SourceState
from sma_mqtt_bridge.runtime import run_locked, supervise

NOW = datetime(2026, 10, 16, 5, tzinfo=timezone.utc)


class ChargingSessionTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.config = load_config({"SMAB_STATE_DIR": tmp.name})
        self.session = ChargingSession(self.config)

    def sample(self, seconds, energy=1000, vehicle=200113, power=3000, energy_seconds=None):
        now = NOW + timedelta(seconds=seconds)
        stamps = {c: now.isoformat() for c in (ENERGY, POWER, VEHICLE)}
        if energy_seconds is not None:
            stamps[ENERGY] = (NOW + timedelta(seconds=energy_seconds)).isoformat()
        return observation(
            {ENERGY: energy, VEHICLE: vehicle, POWER: power}, stamps, 180, now, 1000 + seconds
        )

    def update(self, seconds, **kw):
        self.session.update(self.sample(seconds, **kw), now=1000 + seconds)
        return self.session.state.fresh_values(1000 + seconds)

    def test_pause_expiry_resumption_and_disconnect_preserve_energy(self):
        values = self.update(0)
        self.assertEqual(values["session/status"], "charging")
        self.assertEqual(values["session/energy"], "1")
        values = self.update(60, energy=2000, vehicle=200112, power=0)
        self.assertEqual(values["session/status"], "paused")
        values = self.update(250, energy=2000, energy_seconds=60, vehicle=200112, power=0)
        self.assertEqual(values["session/status"], "paused")
        self.assertEqual(values["session/energy"], "2")
        self.assertEqual(values["session/energy-time"], (NOW + timedelta(seconds=60)).isoformat())
        self.assertEqual(self.session.data["last"], None)
        values = self.update(270, energy=2100)
        self.assertEqual(values["session/status"], "charging")
        values = self.update(300, energy=0, vehicle=200111, power=0)
        self.assertEqual(values["session/status"], "completed")
        self.assertEqual(values["session/energy"], "2.1")
        self.assertEqual(values["session/ended-at"], (NOW + timedelta(seconds=300)).isoformat())
        values = self.update(330, energy=0, energy_seconds=300, vehicle=5169, power=0)
        self.assertEqual(values["session/status"], "completed")
        self.assertEqual(values["session/energy"], "2.1")
        values = self.update(400, energy=100)
        self.assertEqual(values["session/status"], "charging")
        self.assertEqual(values["session/energy"], "0.1")
        self.assertEqual(values["session/ended-at"], "")
        self.assertEqual(self.session.data["last"]["energy"], "2.1")

    def test_recovery_preserves_history_without_live_charging_claim(self):
        self.update(0)
        self.update(10, energy=1200)
        recovered = ChargingSession(self.config)
        self.assertEqual(recovered.data["current"]["energy"], "1.2")
        self.assertEqual(recovered.state.fresh_values()["session/status"], "unknown")
        recovered.update(self.sample(20, vehicle=200111, power=0, energy=0), now=1020)
        recovered = ChargingSession(self.config)
        self.assertEqual(recovered.data["last"]["energy"], "1.2")
        self.assertFalse(recovered.state.contributes_availability)
        values = recovered.state.fresh_values(10**12)
        self.assertEqual(values["session/energy"], "1.2")
        self.assertNotIn("session/status", values)
        self.assertEqual(self.session.path.stat().st_mode & 0o777, 0o600)

    def test_zero_first_start_stale_energy_and_unknown_states_do_not_fabricate_history(self):
        for vehicle in (200111, 200112, 5169):
            values = self.update(0, vehicle=vehicle, power=0, energy=0)
            self.assertEqual(values["session/status"], "waiting")
            self.assertNotIn("session/energy", values)
        self.session.update(None, now=1000)
        self.assertEqual(self.session.state.fresh_values(1000)["session/status"], "unknown")
        values = self.update(200, energy_seconds=0)
        self.assertEqual(values["session/status"], "unknown")
        self.assertNotIn("session/energy", values)
        values = self.update(210, vehicle=200115, power=0)
        self.assertEqual(values["session/status"], "unknown")
        self.assertIsNone(self.session.data["last"])

    def test_fresh_reset_is_not_completion_and_old_samples_cannot_reopen_session(self):
        self.update(0)
        self.update(10, energy=2000)
        values = self.update(11, energy=0, vehicle=200112, power=0)
        self.assertIsNone(self.session.data["last"])
        self.assertEqual(values["session/status"], "unknown")
        self.assertEqual(self.session.data["current"]["energy"], "2")
        self.update(20, energy=300)
        self.update(30, energy=0, vehicle=200111, power=0)
        self.update(40, energy_seconds=20, energy=300, vehicle=200112, power=0)
        self.assertIsNone(self.session.data["current"])
        self.assertEqual(self.session.data["last"]["energy"], "0.3")
        self.session.update(self.sample(20, energy=300), now=1040)
        self.assertIsNone(self.session.data["current"])

    def test_zero_reset_before_disconnect_and_restart_does_not_lose_last_amount(self):
        self.update(0, energy=2000)
        self.update(20, energy=0, vehicle=200112, power=0)
        self.session = ChargingSession(self.config)
        values = self.update(30, energy=0, energy_seconds=20, vehicle=200112, power=0)
        self.assertEqual(values["session/status"], "unknown")
        self.assertEqual(values["session/energy"], "2")
        values = self.update(40, energy=0, vehicle=200111, power=0)
        self.assertEqual(values["session/status"], "completed")
        self.assertEqual(values["session/energy"], "2")
        self.assertIsNone(self.session.data["resetTime"])

    def test_invalid_timestamp_numeric_and_missing_inputs_are_rejected(self):
        for invalid in ("bad", "NaN", "-1", True, None):
            sample = self.sample(0, energy=invalid)
            self.assertIsNone(sample.energy)
        for stamp in (
            "bad",
            NOW.replace(tzinfo=None).isoformat(),
            (NOW + timedelta(seconds=1)).isoformat(),
        ):
            sample = observation(
                {ENERGY: 1, VEHICLE: 200113, POWER: 3000},
                {ENERGY: stamp, VEHICLE: stamp, POWER: stamp},
                180,
                NOW,
                1000,
            )
            self.session.update(sample, now=1000)
            self.assertEqual(self.session.state.fresh_values(1000)["session/status"], "unknown")
            self.assertIsNone(self.session.data["current"])

    def test_write_failure_never_advances_visible_or_saved_history(self):
        self.update(0)
        before = self.session.path.read_bytes()
        with patch(
            "sma_mqtt_bridge.charging_session.write_state", side_effect=OSError("fixture secret")
        ):
            with self.assertLogs("sma_mqtt_bridge.charging_session", level="WARNING") as logs:
                values = self.update(10, energy=2000)
        self.assertEqual(values["session/energy"], "1")
        self.assertEqual(values["session/status"], "unknown")
        self.assertEqual(self.session.path.read_bytes(), before)
        self.assertNotIn("fixture secret", str(logs.output))
        self.assertEqual(self.update(20, energy=2000)["session/energy"], "2")

    def test_corruption_and_identity_changes_fail_closed(self):
        self.update(0)
        data = json.loads(self.session.path.read_text())
        for changed in (
            dict(data, identity="changed"),
            dict(data, schemaVersion=True),
            dict(data, current={"energy": "NaN", "time": NOW.isoformat()}),
        ):
            self.session.path.write_text(json.dumps(changed))
            with self.assertRaises(StateError):
                ChargingSession(self.config)
        self.session.path.unlink()
        protected = self.session.path.with_name("protected")
        protected.write_text("unchanged")
        self.session.path.symlink_to(protected)
        with self.assertRaises(StateError):
            ChargingSession(self.config)
        self.assertEqual(protected.read_text(), "unchanged")

    def test_semp_metadata_keeps_raw_filter_separate_from_historical_display(self):
        self.update(0)
        rows = "".join(
            f"<Parameter><channelId>{c}</channelId><value>{v}</value><timestamp>{t.isoformat()}</timestamp></Parameter>"
            for c, v, t in (
                (ENERGY, 1000, NOW),
                (POWER, 0, NOW + timedelta(seconds=200)),
                (VEHICLE, 200112, NOW + timedelta(seconds=200)),
            )
        )
        with patch("sma_mqtt_bridge.adapters.echarger.time.monotonic", return_value=1200):
            values = semp_values(
                f'<Device2EM xmlns="{NS}"><Parameters>{rows}</Parameters></Device2EM>',
                180,
                NOW + timedelta(seconds=200),
            )
        self.assertIsNone(values["measurements/session-energy"])
        self.session.update(values.session_observation, now=1200)
        self.assertEqual(self.session.state.fresh_values(1200)["session/status"], "paused")
        self.assertEqual(self.session.state.fresh_values(1200)["session/energy"], "1")


class SessionSupervisorTests(unittest.IsolatedAsyncioTestCase):
    async def test_successful_selected_reader_feeds_session_without_extra_io(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = load_config({"SMAB_STATE_DIR": tmp})
            session = ChargingSession(config)
            text = (
                f'<Device2EM xmlns="{NS}"><Parameters>'
                + "".join(
                    f"<Parameter><channelId>{c}</channelId><value>{v}</value><timestamp>{datetime.now(timezone.utc).isoformat()}</timestamp></Parameter>"
                    for c, v in ((ENERGY, 1000), (VEHICLE, 200113), (POWER, 3000))
                )
                + "</Parameters></Device2EM>"
            )
            values = semp_values(
                text,
                180,
                advanced=config.echarger.advanced_channels_enabled,
                diagnostics=config.echarger.diagnostics_enabled,
            )
            state = SourceState("semp", "fixture", (), 180)
            # Use actual reader metadata; the supervisor must still validate every key.
            from sma_mqtt_bridge.adapters.echarger import SempReader

            state.properties = SempReader(config.echarger, 4096).properties
            reader = AsyncMock()
            reader.read.return_value = values
            stop = asyncio.Event()

            async def delay(*_):
                stop.set()

            with patch("sma_mqtt_bridge.runtime.wait_stop", side_effect=delay):
                await supervise(state, reader, 1, config, stop, session=session)
            self.assertEqual(session.state.fresh_values()["session/status"], "charging")
            reader.read.assert_awaited_once()
            reader.close.assert_awaited_once()

    async def test_runtime_selects_semp_else_api_and_disabled_creates_no_history(self):
        for api, semp, expected in (
            (True, True, "2"),
            (True, False, "1"),
            (False, True, "2"),
            (False, False, None),
        ):
            with self.subTest(api=api, semp=semp), tempfile.TemporaryDirectory() as tmp:
                base = load_config({"SMAB_STATE_DIR": tmp})
                config = replace(
                    base, echarger=replace(base.echarger, enabled=api, semp_enabled=semp)
                )
                readers = []
                for enabled, source, amount in ((api, "api", 1000), (semp, "semp", 2000)):
                    if not enabled:
                        continue
                    values = SampleValues({}, {})
                    now = datetime.now(timezone.utc)
                    values.session_observation = observation(
                        {ENERGY: amount, VEHICLE: 200113, POWER: 3000},
                        {c: now.isoformat() for c in (ENERGY, VEHICLE, POWER)},
                        180,
                        now,
                        1000,
                    )
                    reader = AsyncMock()
                    reader.identity_fingerprint = ""
                    reader.read.return_value = values
                    readers.append(
                        (SourceState(source, config.echarger.homie_id, (), 180), reader, 1)
                    )
                captured = []

                class Publisher:
                    status = {}

                    def __init__(self, _config, states, captured=captured):
                        captured.extend(states)

                    async def run(self, stop):
                        await asyncio.sleep(0)
                        stop.set()

                with patch("sma_mqtt_bridge.runtime.sources", return_value=readers):
                    await run_locked(config, publisher_factory=Publisher)
                derived = [s for s in captured if s.id == "charging-session"]
                if expected is None:
                    self.assertEqual(derived, [])
                    from pathlib import Path

                    self.assertFalse(Path(tmp, "echarger-session.json").exists())
                else:
                    self.assertEqual(len(derived), 1)
                    self.assertEqual(derived[0].fresh_values()["session/energy"], expected)
                    self.assertFalse(derived[0].contributes_availability)
                for _, reader, _ in readers:
                    reader.read.assert_awaited_once()
