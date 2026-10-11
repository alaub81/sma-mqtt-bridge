"""Bounded, best-effort observations of allowlisted eCharger sample timestamps."""

import json
import logging
import os
import stat
import time
from datetime import datetime, timezone
from pathlib import Path

from .model import number

LOG = logging.getLogger(__name__)
CHANNELS = frozenset(
    {
        "Measurement.Metering.GridMs.TotWIn.ChaSta",
        "Measurement.ChaSess.WhIn",
        "Measurement.Metering.GridMs.TotWhIn.ChaSta",
        "Measurement.Metering.GridMs.TotWhIn",
        "Measurement.Operation.EVeh.ChaStt",
        "Measurement.Operation.Health",
        "Measurement.Operation.EVeh.Health",
        "Measurement.Operation.Evt.Msg",
        "Measurement.Chrg.ModSw",
        "Measurement.Acs.AuthRegistStt",
        "Measurement.GridMs.Hz",
        "Setpoint.PlantControl.PCC.ChrgActCnt",
        "Setpoint.PlantControl.Inverter.WModCfg.WCtlComCfg.WSptMaxNom",
        "Setpoint.PlantControl.Inverter.WModCfg.WCtlComCfg.WSptMinNom",
    }
    | {f"Measurement.GridMs.{kind}.phs{phase}" for kind in ("A", "PhV") for phase in "ABC"}
)


def sample_timestamp(timestamp, now, stale_seconds):
    """Normalize timestamps without copying untrusted strings into diagnostics."""
    try:
        measured = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        age = (now - measured).total_seconds()
    except AttributeError, TypeError, ValueError, OverflowError:
        return None, None, "invalid"
    quality = "future" if age < 0 else "fresh" if age <= stale_seconds else "stale"
    return measured.astimezone(timezone.utc).isoformat(), age, quality


class TimestampDiagnostics:
    def __init__(self, state_dir, max_bytes, summary_interval_seconds):
        self.path = Path(state_dir) / "echarger-timestamps.jsonl"
        self.max_bytes = max_bytes
        self.summary_interval = summary_interval_seconds
        self.previous = {}
        self.retry_after = 0

    def observe(self, source, channel, value, timestamp, stale_seconds, now):
        if source not in ("api", "semp") or channel not in CHANNELS:
            return
        monotonic = time.monotonic()
        if monotonic < self.retry_after:
            return
        try:
            self.record(source, channel, value, timestamp, stale_seconds, now, monotonic)
        except Exception as error:
            # Diagnostic storage must never fail a successful read or disclose response data.
            self.retry_after = monotonic + self.summary_interval
            LOG.warning(
                "eCharger timestamp diagnostics unavailable; error=%s", type(error).__name__
            )

    def record(self, source, channel, value, timestamp, stale_seconds, now, monotonic):
        stamp, age, quality = sample_timestamp(timestamp, now, stale_seconds)
        numeric = number(value)
        encoded = str(numeric) if numeric is not None else None
        if encoded is not None and len(encoded) > 128:
            encoded = None
            numeric = None
        signature = (numeric, stamp, quality)
        key = source, channel
        previous = self.previous.get(key)
        repeated = previous is not None and signature == previous[0]
        count = previous[2] + 1 if previous else 1
        if repeated and monotonic - previous[1] < self.summary_interval:
            self.previous[key] = previous[0], previous[1], count
            return
        row = {
            "schemaVersion": 1,
            "source": source,
            "channel": channel,
            "receivedAt": now.astimezone(timezone.utc).isoformat(),
            "deviceTimestamp": stamp,
            "deviceAgeSeconds": age,
            "staleSeconds": stale_seconds,
            "timestampQuality": quality,
            "value": encoded,
            "valueValid": encoded is not None,
            "valueChanged": None if previous is None else numeric != previous[0][0],
            "timestampChanged": None if previous is None else stamp != previous[0][1],
            "repeatedSamples": count if repeated else 1,
            "suppressedSamples": previous[2] - 1 if previous else 0,
        }
        self.append(json.dumps(row, allow_nan=False, sort_keys=True).encode("utf-8") + b"\n")
        self.previous[key] = signature, monotonic, 1

    def append(self, data):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Refuse symlinks and special files, including FIFOs that could stall polling.
        if self.path.exists() or self.path.is_symlink():
            mode = self.path.lstat().st_mode
            if not stat.S_ISREG(mode):
                raise OSError("Diagnostic destination is not a regular file")
            if self.path.stat().st_size + len(data) > self.max_bytes:
                self.path.replace(self.path.with_suffix(".jsonl.1"))
        if len(data) > self.max_bytes:
            raise ValueError("Diagnostic record exceeds file limit")
        descriptor = os.open(
            self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600
        )
        with os.fdopen(descriptor, "ab") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise OSError("Diagnostic destination is not a regular file")
            os.fchmod(stream.fileno(), 0o600)
            stream.write(data)
