# Polling, timeouts and alarm acceptance

Current status, 2026-10-13: Andreas reports further own tests and closes remaining
operational acceptance, including recovery/state restoration tasks. Existing
procedures below remain reusable references, not outstanding requests to rerun
accepted tests. Additional per-scenario evidence/version details were not supplied;
see [the acceptance note](VALIDATION.md#remaining-operational-acceptance-closed-by-user-2026-10-13).
Future releases and infrastructure changes retain separate validation.

## Effective installation limits

Run against the updated image in the existing service, without stopping it:

```sh
docker compose exec -T sma-mqtt-bridge python -m sma_mqtt_bridge.operational_limits
```

This validates and reads the container configuration/profile files with normal
precedence, but performs no device or broker requests. Output is allowlisted:
source slots, enabled-source scheduling, timeouts, property expiry and readiness
keys. Addresses, credentials, serial numbers and configured MQTT identities are
excluded. Configuration errors disclose only the exception class.
The command requires an image containing this module; it is not in older images.

Repository defaults (not evidence of the installation's effective configuration):

| Source | Poll interval | Request timeout | Source expiry |
| --- | --- | --- | --- |
| Inverters | Profile pollers unless explicitly overridden; fallback 10 s | 5 s | 60 s; individual properties can have longer profile-derived expiry |
| Home Manager Modbus | 3 s; transactions are paced | 5 s; connect 5 s | 30 s |
| Local eCharger API | 60 s | 10 s | 180 s |
| SEMP | 30 s | 10 s | 180 s |
| Portal | 0 s: periodic polling disabled | 15 s | 180 s |

Whole-read watchdog defaults to 120 s, retry backoff to 1–60 s, outage log
summaries to 300 s, heartbeat to 10 s and heartbeat expiry to 60 s.
MQTT connect timeout defaults to 10 s and keepalive to 60 s.
The log summary interval is not an alarm delay. A polling wait can follow the
request duration; the configured interval alone is not a precise detection bound.
Authentication failures deliberately stop automatic retries until resolved/restarted.
Per-property expiry and paced Home Manager reads must be considered separately.

## Target-host procedure

1. Save the limit report and the external monitoring conditions, delay, repeat
   interval and recovery condition. Do not change thresholds until compared.
2. Observe a full day including inverter wake-up and natural charging changes.
   Keep timestamp recording enabled. Capture logs with:

   ```sh
   docker compose logs --since 24h --timestamps sma-mqtt-bridge > smab-operation.log
   ```

3. Agree on a single read source and maintenance window before a controlled
   interruption. Do not interrupt Home Manager charging regulation or power off
   equipment during charging. Use a reversible network restriction limited to the
   bridge-to-device read connection, with broker/other sources left reachable.
   The exact restriction depends on the host/network and is not prescribed here.
4. Record interruption time, first source error/stale state, external alarm time,
   connection restoration, source ready and alarm clearance. Restore the restriction
   even if the test fails. Verify independent sources keep updating, the bridge
   stays alive, last-known values are preserved and no write is replayed.
5. Compare observed times against effective polling, request/whole-cycle limits,
   backoff, property expiry and external alarm delay. Avoid promises that a device
   outage always waits for expiry: a failed read can report error immediately.

Docker health is process liveness, not proof that all devices or MQTT are available.
External alarms must distinguish those signals. Sleeping inverters need their
accepted readiness policy; missing night production alone is not an outage.
UDP/interface/multicast tests are required only when the UDP transport is selected.
Selected periodically refreshed eCharger channels now retain their device age;
unresolved channel semantics and installation freshness acceptance remain separate. No threshold changes or live interruptions are performed
by this procedure's implementation.

## Automated evidence and limits

Existing fixtures cover hung reads, swallowed cancellation, session reset,
partial/invalid samples, source isolation, authentication, MQTT reconnection and
health semantics. New cases simulate twelve hours of partial samples using explicit
monotonic times and sixty repeated timeout/retry cycles without real waiting.
They check bounded outage summaries, retained last-known values, independent fresh
zero readings, bounded retry delays and recovery. This is not a twelve-hour live
load test, memory/connection soak, or external alarm delivery test.

## Extended deterministic fault sequences, 2026-10-12

`tests/test_long_outages.py` exercises production supervisors and the Homie
connection loop with synthetic readers/clients and virtual monotonic time:

- Twelve virtual hours: one source passes through normal reads, partial responses,
  repeated read timeouts, slow responses carrying expired observation times,
  connection failures and recovery. A second actual supervisor receives scheduled
  ticks and stays ready with valid zero samples. Critical expiry, bounded stored
  property counts, serialized reads, timeout session cleanup, outage counters,
  bounded logging and autonomous recovery are asserted.
- Twenty-four actual asyncio watchdog cancellations followed by recovery; each
  cancelled read finishes before retry and sessions close. Virtual time advances
  thirty minutes per cancellation, while the watchdog is one millisecond in the
  fixture. This verifies repeated cancellation handling, not a real twelve-hour
  hanging connection.
- Twelve virtual hours: ten hours of refused broker connections, then repeated
  lost/delayed publish acknowledgements until the final recovery. Only one
  connected fixture client exists at a time, each connected session closes,
  reads continue updating, retry delays stay bounded and source readiness remains
  independent. Retained payloads, obsolete-topic retirement, the persisted topic
  manifest and an untouched synthetic journal are checked. No controller handle
  is invoked and no background task remains after completion.

The module bindings for time are patched independently of asyncio's real timer.
There are no multi-hour sleeps or installation requests. The synthetic MQTT client
does not prove network-level ACK behavior, TLS or broker Last Will delivery;
existing loopback-stack tests and user-reported installation checks cover separate
parts of those contracts. This is not a memory/network/resource soak: session,
task and property-count assertions do not establish target-host resource usage.
The synthetic journal byte check verifies non-interference only, not all command
uncertainty scenarios, which have their own regression tests.

## Bounded Linux host resource recording

`tests/resource_soak.py` runs outside the bridge image with Python 3.9+ and the
Docker CLI, from the installation's Compose directory. It performs read-only
Docker/procfs/sysfs sampling; it never loads ENV secrets or queries devices/MQTT.
Defaults are 24 hours and a 60-second sampling interval. CLI flags
`--duration-seconds` (1..86400), `--interval-seconds` (1..3600), `--output` and
optional `--compose-file` configure this host tool, not the service runtime.
No additional service environment variables or image dependencies are introduced.
Use the actual installed Compose filename if it differs from the example below.

Copy the current script onto the host. Updating the bridge image does not update
this separately copied host tool. For v0.3.11, download the tagged source:

```sh
curl -fL https://raw.githubusercontent.com/alaub81/sma-mqtt-bridge/v0.3.11/tests/resource_soak.py \
  -o resource_soak.py
```

Run a short two-minute check first. Reading another UID's `/proc/PID/io` may need
root permissions; run only this read-only host recorder with `sudo` when needed,
without changing the service user, capabilities or kernel controllers:

```sh
sudo python3 resource_soak.py --compose-file docker-compose.example.yml \
  --duration-seconds 120 --output smab-resource-soak-v0311-check.jsonl
```

After checking the output, start the bounded recording:

```sh
sudo -v
nohup sudo -n python3 resource_soak.py --compose-file docker-compose.example.yml \
  --output smab-resource-soak-v0311-24h.jsonl \
  > smab-resource-soak-v0311-24h.log 2>&1 < /dev/null &
```

The output file is created exclusively: existing observations are never
overwritten. The default produces approximately 1,441 JSON lines with a final
sample at the duration boundary; slow Docker calls can extend wall duration.
Each Docker command has a ten-second deadline. Host shutdown stops the recorder;
container restart/replacement and unavailable samples reset CPU comparisons.
`generation` identifies continuity segments, including unavailable intervals,
not an exact restart count. Docker's `restartCount` is reported separately.

Recorded fields include UTC time/elapsed time, container health/status, cgroup-v2
CPU usage and delta percent (100% means one CPU core), optional cgroup memory,
summed resident/peak process memory, process/thread counts and aggregate physical
host-interface byte counters. The memory sums may double-count shared pages and
are not interchangeable with Docker's cache-adjusted memory accounting. If
processes disappear during a sample, expected/read counts expose partial results.
Missing memory controllers/cgroup metrics produce null, never a fabricated zero.
The first CPU sample and discontinuities produce null rather than invalid rates.
No container IDs, addresses, command lines or ENV values are saved.

Schema 2 additionally records:

| Field | Meaning |
| --- | --- |
| `cgroupIo` | Kernel `io.stat` counters per block-device major:minor: `rbytes`, `wbytes`, `rios`, `wios`. Device numbers are kernel accounting keys, not serial numbers. |
| `cgroupIoPerSecond` | Per-device byte/s and I/O/s deltas with the same keys, only within the same container generation and unchanged device set; resets produce null. |
| `processIo` | Summed `/proc/PID/io` counters: `rchar`, `wchar`, `syscr`, `syscw`, `read_bytes`, `write_bytes`, `cancelled_write_bytes`. |
| `processIoExpected`, `processIoRead` | Expected versus readable process accounting snapshots. Partial raw totals are marked by these counts. |
| `processIoPerSecond` | Counter deltas per second, only for complete snapshots with identical PID/start-time membership and no counter reset. Process identities are used internally and never serialized. |

Logical `rchar`/`wchar` and syscall counts include non-disk I/O and page-cache hits;
they are not HDD operations. Process `write_bytes` is accounted when pages become
dirty; subsequent deletion/truncation can cancel writes, tracked separately rather
than silently subtracted. cgroup I/O is block-layer accounting per device, not
direct physical drive wear or seek measurements. Keep devices separate to avoid
blindly adding stacked-device accounting. Read cgroup CPU, memory and I/O
independently: a missing controller must not hide another available metric.
Missing/denied I/O metrics are null. An available empty `io.stat` is `{}` and means
no device counters reported, not a general proof of zero storage activity.
See the official kernel [proc I/O definitions](https://docs.kernel.org/filesystems/proc.html#proc-pid-io-display-the-io-accounting-fields)
and [cgroup-v2 I/O controller](https://docs.kernel.org/admin-guide/cgroup-v2.html#io).

Minute-scale process snapshots can miss short-lived health probes; cgroup totals
include their accounted activity. Docker daemon log persistence and the external
recorder's own output are outside the bridge cgroup. `fsync` calls are not counted
by these interfaces. Test permissions in the short run before collecting overnight;
inspect `processIoRead` and `cgroupIo` rather than interpreting null as zero.

For the optimization comparison, deploy the new image first and verify its version
and health. Keep polling intervals, adapter flags and timestamp diagnostics aligned
with the previous run. CPU can be compared with the accepted 4.355% one-core mean;
the old recording has no I/O baseline, so storage figures initially establish a
new baseline. This voluntary comparison does not reopen the previous operational
acceptance. Andreas performs deployment and starts the recording; the release itself
does not launch it. Use a fresh output filename for any repeated run.

Host physical-interface traffic includes other services and excludes loopback;
it is context only, not Bridge-specific throughput. Interface resets or membership
changes require separate interpretation of counter deltas. A network-mode change
or dedicated traffic attribution would need independent acceptance; do not alter
networking just to collect this baseline. Docker/procfs sampling itself has some
overhead; this is a coarse one-minute resource trend, not microbenchmarking.

After recording, compare CPU/RSS trends with natural night/morning and charging
phases, available source diagnostics and same-period bridge logs. Preserve units,
polling and measurement coverage until a measured change has an explicit
before/after acceptance plan. Generated observations/logs stay outside Git.
