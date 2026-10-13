# Target-host resource recording analysis, 2026-10-13

## Result and coverage

The supplied recording supports stable operation over **22 h 06 min 07.7 s**,
accepted by Andreas on 2026-10-13 as sufficient to close resource acceptance.
This is a 22-hour measurement, not a completed 24-hour recording. It contains 1,324 valid JSON samples from
2026-10-12 21:00:11.671 to 2026-10-13 19:06:19.348 Europe/Berlin.
Approximately 1 h 53 min 52 s of the configured 24-hour duration remains outside
this file. No recorder log was supplied, so the reason the file ends here is
unknown; it may be an interim copy. Do not infer a stopped recorder.

All samples report running/healthy, restart count 0 and generation 1. These
minute-scale observations cannot exclude shorter unobserved faults and certify
process health rather than every source or broker connection.

## CPU and process memory

| Metric | Observation |
| --- | --- |
| CPU, time-weighted average | 4.355% of one core |
| CPU, median | 4.312% of one core |
| CPU, p95 / p99 | 4.830% / 5.217% of one core |
| CPU, maximum sampled interval | 5.708% of one core |
| CPU accounting delta | 57.76 CPU minutes |
| RSS with two observed processes | 52.953–53.469 MiB; median 53.250 MiB |
| Complete two-process samples, first/last hour median RSS | 53.094 / 53.188 MiB |
| RSS with three observed processes | 59.484–81.141 MiB; median 73.750 MiB |
| Threads | 3 in 1,275 samples; 4 in 49 samples |

The first CPU rate is intentionally null; the other 1,323 are valid. Percentiles
use the lower observed order statistic at floor((n-1)*p). The short check file
has three samples over 120 seconds, constant RSS 53.094 MiB and two CPU intervals
of 4.328% and 3.686%; it is a functional check rather than a separate long-term
baseline.

49 samples observe a third process, coinciding with the fourth thread and larger
RSS sum. The recorder contains no process identities. The Dockerfile launches a
separate Python healthcheck every 10 seconds, making that a plausible explanation,
not confirmed identification of the additional process. Neither the summed RSS
nor the summed per-process high-water marks is a continuous container memory
peak; shared pages may be counted repeatedly and process membership changes.

51 samples expect three processes, but two of these read only two. These are
partial process snapshots; process exit between Docker enumeration and procfs
reading is possible, but the file does not prove the cause. Base-memory comparison
excludes those two samples. The first/last hour difference is only 0.094 MiB and
there is no sustained growth evident in the supplied process-memory observations.
This is no general proof against all leaks or future memory growth.

## Continuity and accounting limits

- Sample spacing: minimum 60.116 s, median 60.135 s, maximum 61.159 s; no gaps
  above 90 seconds, no CPU or network counter resets.
- Container cgroup memory is null throughout: unavailable, not zero consumption.
- Two physical host interfaces are reported throughout. Host counter increments
  are 5.824 GiB received and 36.790 GiB sent. Host networking means these are
  host-wide counters, not bridge traffic; no bridge bandwidth optimization can
  be justified from them alone.
- The uploaded JSONL files were read without modifying them. Raw observations
  remain outside the public repository. No target-host settings or services changed.

## Decision and remaining acceptance

No CPU, persistent process-memory growth, restart or sampled-health finding in
this window calls for a polling/runtime optimization. Keep the current baseline
configuration. Andreas explicitly accepted the observed 22-hour duration as
sufficient on 2026-10-13; no additional recording is required. Resource acceptance
is closed with the accounting limits above. Andreas reports removing the external
recorder and copied recording files from the target host; repository tooling and
tests remain available. No direct cleanup inspection was performed.

Device freshness, charging behavior, source/broker availability and command
recovery remain separate acceptance criteria. This analysis does not certify them.
