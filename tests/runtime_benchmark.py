"""Offline CPU and heartbeat-write benchmark; never load installation configuration."""

import hashlib
import json
import os
import statistics
import sys
import tempfile
import time
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if (ROOT / "ressources/sma_mqtt_bridge").is_dir():
    sys.path.insert(0, str(ROOT / "ressources"))

from sma_mqtt_bridge.availability import Availability  # noqa: E402
from sma_mqtt_bridge.config import DEFAULT_PROFILES, load_config  # noqa: E402
from sma_mqtt_bridge.health import heartbeat  # noqa: E402
from sma_mqtt_bridge.home_manager_profile import load_home_manager_profile  # noqa: E402
from sma_mqtt_bridge.homie import HomiePublisher  # noqa: E402
from sma_mqtt_bridge.profiles import load_profile  # noqa: E402
from sma_mqtt_bridge.runtime import sources  # noqa: E402


def fixture(state_dir):
    """Use bundled mappings and synthetic values, without opening network sessions."""
    config = load_config({"SMAB_STATE_DIR": state_dir})
    profiles = {
        device.id: load_profile(profile, "/nonexistent-smab-benchmark")
        for device, profile in zip(config.inverters, DEFAULT_PROFILES, strict=True)
    }
    profiles["home-manager"] = load_home_manager_profile(
        config.home_manager.profile, "/nonexistent-smab-benchmark"
    )
    config = replace(
        config,
        profiles=profiles,
        inverters=tuple(replace(d, enabled=True) for d in config.inverters),
        home_manager=replace(config.home_manager, enabled=True, transport="modbus-tcp", serial="1"),
        echarger=replace(config.echarger, enabled=True, semp_enabled=True, tls_verify=False),
        portal=replace(config.portal, enabled=True),
    )
    states = [state for state, _, _ in sources(config)]
    for state in states:
        values = {
            p.key: True
            if p.datatype == "boolean"
            else p.format.split(",")[0]
            if p.datatype == "enum"
            else "fixture"
            if p.datatype == "string"
            else 1
            for p in state.properties
        }
        state.initialization_deadline = None
        state.update(values, now=1000, timestamp="2026-10-13T00:00:00Z")
        state.monitor = Availability("Fixture " + state.id, 300)
        state.monitor.last_progress = 1000
    return config, states


def main():
    with tempfile.TemporaryDirectory() as directory:
        config, states = fixture(directory)
        publisher = HomiePublisher(config, states)
        devices = [
            [s for s in states if s.device == device]
            for device in sorted({s.device for s in states})
        ]

        def cycle():
            for group in devices:
                publisher.snapshot(group, now=1000)
            for state in states:
                state.status(1000)
                state.missing_critical(1000)

        cycle()
        timings = []
        for _ in range(5):
            started = time.process_time()
            for _ in range(2000):
                cycle()
            timings.append(time.process_time() - started)
        snapshots = [publisher.snapshot(states, now=now) for now in (999, 1000, 1031, 1061, 1361)]
        encoded = json.dumps(snapshots, sort_keys=True).encode()
        with patch("sma_mqtt_bridge.health.os.fsync", wraps=os.fsync) as sync:
            for _ in range(20):
                heartbeat(config, states, {})
        print(
            json.dumps(
                {
                    "sources": len(states),
                    "properties": sum(len(s.properties) for s in states),
                    "cyclesPerRepeat": 2000,
                    "repeats": 5,
                    "medianCpuSeconds": statistics.median(timings),
                    "snapshotSha256": hashlib.sha256(encoded).hexdigest(),
                    "heartbeatWrites": 20,
                    "heartbeatFsyncCalls": sync.call_count,
                    "python": sys.version.split()[0],
                },
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
