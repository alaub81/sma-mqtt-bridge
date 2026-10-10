"""Atomic main-loop heartbeat; source/MQTT availability is separate from liveness."""

import json
import math
import os
from pathlib import Path
import time


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        os.chmod(temporary, 0o600)
        json.dump(data, stream, allow_nan=False, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
    # Persist the renamed journal/manifest entry as well as its file contents.
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def heartbeat(config, states, mqtt, mqtt_diagnostics=None):
    atomic_json(Path(config.runtime.state_dir) / "heartbeat.json", {
        "schemaVersion": 2, "status": "running", "pid": os.getpid(), "timestamp": time.time(),
        "monotonic": time.monotonic(),
        "sources": {s.id: s.status() for s in states}, "mqtt": dict(mqtt),
        "sourceDiagnostics": {s.id: {**s.monitor.snapshot(), "missingCritical": s.missing_critical()}
                              for s in states if s.monitor is not None},
        "mqttDiagnostics": mqtt_diagnostics or {},
    })


def healthy(state_dir, stale_seconds, now=None):
    try:
        data = json.loads((Path(state_dir) / "heartbeat.json").read_text())
        if data["schemaVersion"] != 2 or data["status"] != "running":
            return False
        pid, received = data["pid"], data["monotonic"]
        if type(pid) is not int or pid <= 0 or type(received) not in (int, float) or not math.isfinite(received):
            return False
        elapsed = (time.monotonic() if now is None else now) - received
        if not 0 <= elapsed <= stale_seconds:
            return False
        # The probe runs in the bridge's PID namespace and as the same user.
        os.kill(pid, 0)
        return True
    except (OSError, ValueError, TypeError, KeyError, OverflowError):
        return False
