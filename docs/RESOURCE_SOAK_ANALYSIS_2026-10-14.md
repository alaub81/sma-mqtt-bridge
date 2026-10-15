# Post-update target-host resource analysis, 2026-10-14

## Result

The user-supplied `smab-resource-soak-v0311-24h.jsonl` contains 1,438 valid
schema-2 samples, spanning 2026-10-13 21:45:59.906 to 2026-10-14 21:45:59.906
Europe/Berlin: 24 hours by wall clock, 86,399.983 seconds between monotonic
observations. This completes the voluntary post-update recording. Andreas
identifies it as the post-update run; the recorder does not include an installed
version or image digest, so the filename alone cannot independently verify v0.3.11.

All observations report running/healthy, restart count zero and generation one.
Sample spacing is median 60.134 s, maximum 60.801 s; the final shortened interval
is 38.416 s. There are no gaps above 90 seconds. This supports sampled process
health, not uninterrupted health of every adapter or MQTT connection.

## Comparison with the accepted baseline

| Metric | Previous 22 h 06 min | New 24 h |
| --- | --- | --- |
| CPU, time-weighted average, one core | 4.355% | 4.300% |
| CPU median | 4.312% | 4.274% |
| CPU p95 / p99 | 4.830% / 5.217% | 4.751% / 4.886% |
| Maximum sampled CPU interval | 5.708% | 5.802% |
| Complete two-process RSS median | 53.250 MiB | 50.344 MiB |
| Complete two-process RSS range | 52.953–53.469 MiB | 49.453–52.688 MiB |
| First / last hour two-process RSS median | 53.094 / 53.188 MiB | 52.656 / 50.234 MiB |

Average CPU is about 0.055 percentage points (1.27% relative) lower; this is a
small observational difference, not an isolated causal benchmark. The workload,
configuration and external device activity are not controlled by this file.
The base RSS median is about 2.906 MiB lower. No sustained memory growth is
evident; this does not rule out all leaks. CPU is derived from the cgroup counter
delta divided by monotonic duration. Percentiles use floor((n-1)*p).
See [the original baseline](RESOURCE_SOAK_ANALYSIS_2026-10-13.md).

There are 1,391 complete two-process RSS samples and 46 complete three-process
samples (RSS 56.422–79.047 MiB, median 72.000 MiB). One RSS snapshot expects three
processes but reads two and is excluded from base-memory comparisons. A transient
healthcheck process is plausible, but the recording does not identify it.
Summed RSS can double-count shared pages. Cgroup memory remains unavailable
(null throughout), so no continuous container memory peak is established.

## New I/O baseline and limits

Process I/O rates are valid in 1,343 intervals covering approximately 22 h 25 min
46 s (93.46% of the observation window). The remaining 95 rows include the first
sample and intervals rejected by the recorder's identity/completeness guards;
these are missing rates, not zero activity. Integration of valid rates gives
approximately 159.25 MiB of process storage-write accounting and 82.37 MiB of
logical writes, with median accounted writes about 2.13 KiB/s. These are partial
observations, not extrapolated full-day physical storage totals. The cumulative
process set includes transient processes and must not be treated as one stable
process counter across membership changes.

Cgroup device 179:0 accumulates 4,780,032 read bytes and 388 read operations.
Device 254:0 appears during the recording and ends at 2,572,288 read bytes and
157 operations; its appearance invalidates one cgroup rate interval. Both devices
report zero write bytes/operations throughout their observations. Device counters
may describe layers of one storage stack and must not be added as independent
physical disks. Zero cgroup write accounting does not establish zero disk writes,
especially alongside nonzero process write accounting. Filesystem, mount and
writeback attribution would require separate evidence.

The old recorder did not collect I/O, so there is no before/after HDD saving
measurement. Process counters do not measure physical HDD seeks or wear. Docker
log writes and recorder output are outside the bridge cgroup. Host network
counters are host-wide: about 6.461 GiB received and 1.048 GiB sent, not bridge
bandwidth. No logging, polling or durability change is justified by these data.

## Disposition

The voluntary recording is complete with stable sampled CPU, process memory and
health. The resource acceptance already closed by Andreas remains closed.
No runtime optimization is indicated by this recording. Installed version,
new-topic acceptance, device freshness, charging and complete openHAB migration
remain separate evidence. The original file was read without modification and
was not copied into the public repository. No target-host action was performed.
