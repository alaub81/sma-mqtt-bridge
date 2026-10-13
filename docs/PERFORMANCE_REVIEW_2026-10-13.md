# Runtime quality and resource review, 2026-10-13

## Result and scope

The implemented bridge passes the complete local suite and both container
architectures after three focused changes. No remaining functional failure was
found in the exercised offline scenarios. This does not prove every possible
runtime path or physical charging result. The selected feature scope is
implemented; deferred extensions, unresolved timestamp semantics and complete
openHAB migration remain explicitly separate in the
[implementation plan](IMPLEMENTATION_PLAN.md) and [diary](../todo.md).

Review covered configuration/profile validation, read adapters, freshness and
readiness, HTTP sessions, MQTT discovery/publication/recovery, command gates and
uncertainty journals, health/storage, diagnostics, Docker/CI and documentation.
Source comments reviewed are English. German device state labels and private
legacy references are intentional data, not untranslated source comments.
Existing formatting, import rules and focused correctness rules pass. Longer
orchestration functions remain a maintenance consideration; splitting them without
a concrete behavior or reuse benefit is not part of this optimization.

## Evidence baseline

The accepted [target-host recording](RESOURCE_SOAK_ANALYSIS_2026-10-13.md) spans
22 h 06 min, with mean CPU 4.355% of one core, stable sampled base RSS and no
observed restart. It contains no HDD/I/O counters or process identities; the
host-wide network counters cannot establish bridge bandwidth. Raw recording
files were removed by Andreas; this review uses their documented analysis.
That operational acceptance remains closed.

The initial source baseline passed 259 offline tests, full repository lint and
Compose parity. Offline synthetic benchmarks isolate avoidable work; their
percentages are not predicted savings for the entire target container.

## Changes and independent checks

| Change | Purpose and preserved behavior | Evidence |
| --- | --- | --- |
| Atomic heartbeat without forced disk sync | Keep whole-file visibility and PID/monotonic liveness checks. Recovery journals and topic manifest remain durable. | 20 heartbeats: 40 explicit `fsync` calls before, zero after; failed rename preserves the preceding complete heartbeat. |
| Immutable property metadata reuse | Avoid rebuilding source indexes/readiness defaults and MQTT descriptions every cycle. Inventory replacement, flags and late monitor creation invalidate the description. | 168 independent before/after state cases match; regressions cover changing TTL/readiness, invalid samples, dataclass copies and retained discovery retirement. |
| Bounded observation serialization | Prevent extreme numeric exponents from allocating enormous fixed-point strings; reject invalid Unicode. | Nine input bytes previously expanded to 1,000,001 bytes. Extreme exponents now fail before formatting; UTF-8 and exact numeric boundaries are tested. |

Heartbeats still replace a file every configured interval. At the default 10 s,
8,640 replacements per day remain, while 17,280 explicit sync calls disappear.
The OS decides when buffered writes reach storage; this is not a measured physical
write reduction. A power failure may lose the latest heartbeat. An obsolete or
missing heartbeat cannot prove a new process healthy: PID and monotonic age must
still match the liveness contract. Device writes retain their existing durable
uncertainty protection.

Only descriptions are cached. Measurements, freshness calculations, parameter
rights, write bounds, device identity checks and command readback are current.
No polling interval, topic, unit, retained-value policy or write retry changed.
The payload limit is `SMAB_MAX_PAYLOAD_BYTES` / JSON `runtime.maxPayloadBytes`,
default 4096 UTF-8 bytes; see [configuration](CONFIGURATION.md).

Run the repeatable offline benchmark with:

```sh
.venv/bin/python tests/runtime_benchmark.py
```

It uses seven synthetic sources, 150 properties, five repeats of 2,000 cycles,
bundled mappings and an isolated temporary configuration. It performs no device,
broker or portal requests. Median process CPU for snapshot/status/missing-critical
work was 0.436556 s before and 0.255259 s on the hardened source, approximately
42% less for those paths. Absolute timings vary by machine and load. The snapshots
at five freshness boundaries have the same SHA-256 digest before and after:
`32d9f1c27f8a54fbc7a2523e88edf5f5142a0655ac87d5670cc91ce9b3d5be50`.

## Complete checks and limits

- All 269 offline tests pass locally and inside Linux ARM64 and AMD64 images.
  ARM64 runs natively; AMD64 is emulated. Container suites took approximately
  7.8 s and 11.2 s respectively; these are test durations, not runtime benchmarks.
- Images built from runtime commit `e378535e`, version
  `0.3.10-dev.3+e378535e`, with the unchanged pinned Dockerfile/dependencies.
  Tests ran with `--network none` and public read-only fixtures.
- ARM64 version, disabled-source configuration and exclusions for private ENV,
  Git metadata, pip and ensurepip passed. No external device was contacted.
- Complete lint, Compose parity/overrides, compilation, local documentation
  targets, complete ENV option/default documentation and diff hygiene pass.
- No new hosted CI/Trivy result or target-host deployment is inferred. Hardware
  charging, remaining semantic questions and openHAB acceptance keep their
  existing evidence limits. Public configuration examples cover the new limit.

The local images are `sma-mqtt-bridge:performance-check-arm64` and
`sma-mqtt-bridge:performance-check-amd64`. No test containers are left running.
Unrelated concurrent Compose comments and `.env.example` were preserved outside
the optimization commits.

## Further CPU and storage opportunities

1. **Timestamp diagnostics:** bounded rotation limits retained space, not total
   write traffic. Changing timestamps/values still append records. Finish the
   outstanding channel analysis, then explicitly disable/archive diagnostics if
   they no longer provide evidence. Do not silently remove the ongoing observation.
2. **Docker logs:** the templates do not configure log rotation. Inspect the target
   daemon/logging policy before proposing limits in both standalone templates.
   Host-wide logging may already rotate. Rotation limits space; avoiding repeated
   messages saves writes. Outage summaries are already bounded and transition logs
   remain necessary. Do not disable useful fault information.
3. **Health probe CPU:** the Docker probe starts Python and fully validates local
   configuration every 10 s, including profile/translation/password files and
   applicable TLS contexts. The resource recording does not isolate this cost.
   Measure the probe separately before changing its implementation or cadence;
   keep JSON/ENV precedence and invalid-configuration failure behavior.
4. **Unchanged MQTT state:** the existing one-second loop periodically republishes
   `$state` to verify acknowledged delivery. Five active devices can therefore
   produce roughly five state publications per second, even for unchanged values.
   Any slower cadence needs explicit connection-loss detection and recovery tests;
   suppressing it blindly would change availability monitoring. Broker persistence
   costs require broker-specific evidence.
5. **Reconnect manifest writes:** ownership is persisted repeatedly before/after
   discovery and on retries. Skipping identical snapshots could reduce outage I/O,
   but must preserve pre-publication ownership, retirement and size-limit failures.
   It is lower priority than the eliminated periodic heartbeat sync.

HTTP connection pools and token reuse already exist; Home Manager Modbus keeps a
paced connection. A global value/permission cache or persistent HTTP-response cache
would add stale-state and command risks with no measured benefit. Persistent
inverter sessions would need new identity/reconnection evidence. The current
small metadata caches provide bounded memory cost without a generic cache system.

For this implementation round, stop at the verified changes. A future target
comparison should keep device flags, intervals, diagnostic settings and operating
conditions aligned. Optional short CPU/probe/I/O measurements can distinguish
costs; repeating the previously accepted 22-hour resource check is not required.
