"""Atomic main-loop heartbeat; source/MQTT availability is separate from liveness."""

import json
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


def heartbeat(config, states, mqtt):
    atomic_json(Path(config.runtime.state_dir) / "heartbeat.json", {
        "schemaVersion": 1, "status": "running", "pid": os.getpid(), "timestamp": time.time(),
        "sources": {s.id: s.status() for s in states}, "mqtt": dict(mqtt),
    })


def healthy(state_dir, stale_seconds, now=None):
    try:
        data = json.loads((Path(state_dir) / "heartbeat.json").read_text())
        elapsed = (time.time() if now is None else now) - data["timestamp"]
        return data["status"] == "running" and 0 <= elapsed <= stale_seconds
    except (OSError, ValueError, TypeError, KeyError):
        return False
