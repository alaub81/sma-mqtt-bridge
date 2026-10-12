#!/usr/bin/env python3
"""Bounded read-only Linux host sampling; requires Docker CLI and Python 3.9+."""

import argparse
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def command(args):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=10, check=True)
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def integer_file(path):
    try:
        return int(path.read_text().strip())
    except (OSError, ValueError):
        return None


def process_memory(pids):
    rss, peak, threads, available = 0, 0, 0, 0
    for pid in pids:
        try:
            fields = {}
            for line in Path(f"/proc/{pid}/status").read_text().splitlines():
                key, _, value = line.partition(":")
                if key in ("VmRSS", "VmHWM", "Threads"):
                    fields[key] = int(value.split()[0])
            if "VmRSS" not in fields:
                continue
            rss += fields["VmRSS"] * 1024
            peak += fields.get("VmHWM", 0) * 1024
            threads += fields.get("Threads", 0)
            available += 1
        except (OSError, ValueError, IndexError):
            continue
    return {
        "processesExpected": len(pids),
        "processesRead": available,
        "processRssSumBytes": rss if available else None,
        "processPeakRssSumBytes": peak if available else None,
        "processThreads": threads if available else None,
    }


def cgroup_metrics(pid):
    result = {"cgroupCpuUsec": None, "cgroupMemoryBytes": None}
    try:
        group = next(
            line[3:]
            for line in Path(f"/proc/{pid}/cgroup").read_text().splitlines()
            if line.startswith("0::")
        )
        path = Path("/sys/fs/cgroup") / group.lstrip("/")
        # Never fall back to root-cgroup totals if the container group is unknown.
        if group == "/" or ".." in Path(group).parts:
            return result
        result["cgroupMemoryBytes"] = integer_file(path / "memory.current")
        for line in (path / "cpu.stat").read_text().splitlines():
            key, value = line.split()
            if key == "usage_usec":
                result["cgroupCpuUsec"] = int(value)
    except (OSError, ValueError, StopIteration):
        pass
    return result


def host_network():
    rx, tx, count = 0, 0, 0
    try:
        for line in Path("/proc/net/dev").read_text().splitlines()[2:]:
            name, _, values = line.partition(":")
            # Physical host interfaces only; this is not container-attributed traffic.
            if not (Path("/sys/class/net") / name.strip() / "device").exists():
                continue
            values = values.split()
            rx += int(values[0])
            tx += int(values[8])
            count += 1
    except (OSError, ValueError, IndexError):
        return {"hostPhysicalInterfaceCount": 0, "hostRxBytes": None, "hostTxBytes": None}
    return {
        "hostPhysicalInterfaceCount": count,
        "hostRxBytes": rx if count else None,
        "hostTxBytes": tx if count else None,
    }


def sample(compose):
    row = {"timestampUtc": datetime.now(timezone.utc).isoformat(), "status": "unavailable"}
    container = command(compose + ["ps", "--all", "-q", "sma-mqtt-bridge"])
    if not container or len(container.splitlines()) != 1:
        return row, None
    template = (
        "{{.State.Pid}} {{.RestartCount}} {{.State.Status}} "
        "{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} {{.State.StartedAt}}"
    )
    state = command(["docker", "inspect", "--format", template, container])
    if not state or len(state.split()) != 5:
        return row, None
    pid, restarts, status, health, started = state.split()
    row.update(status=status, health=health, restartCount=int(restarts))
    identity = container, started  # Used internally only; do not save installation IDs.
    if status != "running" or not pid.isdigit() or pid == "0":
        return row, identity
    process_list = command(["docker", "top", container, "-eo", "pid"])
    pids = [p.strip() for p in (process_list or "").splitlines()[1:] if p.strip().isdigit()]
    row.update(process_memory(pids))
    row.update(cgroup_metrics(pid))
    row.update(host_network())
    return row, identity


def cpu_percent(previous, current, elapsed):
    if previous is None or current is None or elapsed <= 0 or current < previous:
        return None
    return (current - previous) / (elapsed * 10000)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration-seconds", type=int, default=86400)
    parser.add_argument("--interval-seconds", type=int, default=60)
    parser.add_argument("--output", type=Path, default=Path("smab-resource-soak.jsonl"))
    parser.add_argument("--compose-file", type=str)
    args = parser.parse_args()
    if not 1 <= args.duration_seconds <= 86400 or not 1 <= args.interval_seconds <= 3600:
        parser.error("duration must be 1..86400 seconds; interval must be 1..3600 seconds")
    compose = ["docker", "compose"]
    if args.compose_file:
        compose += ["-f", args.compose_file]
    previous_identity, previous_cpu, previous_time, generation = None, None, None, 0
    started = time.monotonic()
    deadline = started + args.duration_seconds
    # Exclusive creation prevents overwriting previous measurements.
    with args.output.open("x", encoding="utf-8") as output:
        while True:
            row, identity = sample(compose)
            measured = time.monotonic()
            row["elapsedSeconds"] = round(measured - started, 3)
            if identity != previous_identity:
                generation += 1
            row["generation"] = generation
            row["cpuPercentOneCore"] = (
                cpu_percent(previous_cpu, row.get("cgroupCpuUsec"), measured - previous_time)
                if identity is not None
                and identity == previous_identity
                and previous_time is not None
                else None
            )
            output.write(json.dumps(row, allow_nan=False, sort_keys=True) + "\n")
            output.flush()
            previous_identity, previous_cpu, previous_time = (
                identity,
                row.get("cgroupCpuUsec"),
                measured,
            )
            if measured >= deadline:
                break
            time.sleep(min(args.interval_seconds, deadline - measured))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
