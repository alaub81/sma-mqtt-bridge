# eCharger timestamp observations, 2026-10-12

## Evidence and method

Andreas supplied the rotated timestamp diagnostic file followed by the current
file. Together they contain 4,597 valid schema-1 numeric records: 2,689 API and
1,908 SEMP records, covering 29 source/channel pairs. Receipt times are ordered
across the rotation boundary. The retained window is 15:35:02–18:55:30
Europe/Berlin on 2026-10-12, about 3 h 20 min. Every recorded age limit is 180 s;
there are no invalid or future timestamps. Both idle and charging-power periods
occur. This is the retained window, not the complete history since activation.

The [per-channel matrix](echarger-timestamp-classification-2026-10-12.csv)
contains counts, age ranges and classifications without raw telemetry. Adjacent
records are compared per source/channel using numeric value equality. Repeated
identical observations are suppressed by the recorder and periodically summarized;
record counts are not request counts. First-record change flags can refer to a
previous observation outside the retained files. Classification therefore uses
observed pairs, not those flags. No device, portal, MQTT or openHAB request was made.
The supplied files were read in place and were not modified or copied into Git.

Input SHA-256, in chronological order:

- Rotated file: `22326f1d6d2b930a8de5d86175d77ad418e50a8c7e1ac1c5bd201c74f20b1c86`
- Current file: `4cd3a08a3b5fa2f2786960fe646aea7ba0745d94f92901b6622c2d9a5367b6e4`

## Findings

| Channel family | Transport | Observation | Interpretation |
| --- | --- | --- | --- |
| Charging power | API and SEMP | Fresh timestamps advance during sustained zero and during changing power; age below 0.25 s | Periodically refreshed observation, not solely last value change |
| Phase current | API | All three timestamps advance while numeric values repeat; age below 0.25 s | Periodically refreshed observation |
| Phase voltage | API | Fresh varying values, age below 0.25 s; no adjacent identical values | Acquisition candidate; constant-value behavior not established |
| Total charging energy | API | Timestamp advances while counter remains constant; age below 0.25 s | Periodically refreshed observation; counters cannot be classified as one family |
| Vehicle status | API and SEMP | Timestamp advances while status repeats and across natural transitions; age below 1.05 s | Periodically refreshed observation despite being an enum |
| Three plant-control setpoints | API and SEMP | Timestamp advances with constant values; age below 45 s | Periodically refreshed control observation; physical meaning is a separate question |
| Session energy | API and SEMP | Fresh during activity, fixed timestamp while idle, then stale | Activity-dependent observation; a universal acquisition-age rule is unsuitable |
| Health, vehicle health, event, mode switch, authorization | API and SEMP | One fixed old timestamp and one value per source/channel; stale throughout | Change-time or cached-state candidate; unresolved without a natural transition |

No observed value change shares an unchanged timestamp with the preceding retained
record in any source/channel pair. This does not prove a firmware-wide contract.
Refresh on receipt also does not prove that the hardware acquired a new physical
sample; the local endpoint may stamp a cached observation.

## Natural transitions and session energy

Charging power is positive in two observed periods, approximately 16:18–16:35
and 16:38–16:46 Europe/Berlin. These are sampled observations, not exact physical
start/stop times. API polls are approximately one minute apart and SEMP power/status
polls approximately thirty seconds apart. A roughly three-minute observation gap
around 16:35–16:38 is present in both transports; its cause is not established.
Do not infer uninterrupted availability from the file.

Session energy is initially returned with a timestamp already older than two
hours. It becomes fresh near the first charging period, changes during activity,
and ends with a timestamp at about 16:46:02. Unchanged repeated observations become
stale around 16:49 as that timestamp exceeds 180 s. Around the later vehicle-status
transition at 17:30 it receives another fresh timestamp, then becomes stale again
around 17:33 while other measurement channels remain fresh. API and SEMP show the
same frozen session timestamps. This is direct evidence that session timestamp
progression depends on activity, rather than always tracking reader reachability.
It does not settle session reset scope, cumulative/additional plan semantics or
whether an idle value is still authoritative for a current session.

Health/event timestamps remain approximately 31 days old; mode/authorization
approximately 83 days old, including throughout charging transitions. No change in
these channels is captured. It would be premature to declare those values current
or to remove their age checks wholesale.

## Recommended next change and remaining gates

The evidence supports a narrowly scoped remaining-lifetime fix for periodically
refreshed power, phase-current, total-energy, vehicle-status and plant-control
observations. Phase voltage has strong near-receipt evidence but lacks a constant
value pair; document that narrower confidence separately. Carry device age through
parsing and subtract processing time using monotonic elapsed time, rather than
starting a new complete lifetime on receipt. Keep API/SEMP ownership independent.

Session energy needs a separate explicit policy for activity-dependent timestamps;
retain the current filter until idle authority and session boundaries are agreed.
Health/event/mode/authorization remain unresolved. Do not treat a successful poll
as proof that every cached property is current. Preserve last-known retained
observations and distinguish source reachability from property freshness.

Before implementation, add failing deterministic cases for near-limit samples,
processing delay, equal values with new timestamps, fixed session timestamps,
partial responses, aliases/fallbacks, API/SEMP independence and restart/retained
behavior. Shared-model changes need regressions for Modbus, UDP and portal sources.
Preserve readiness, command confirmation and uncertainty journals. Then run full
lint/tests/Compose checks and accept openHAB source gating on the installation.
Review 4 remains open: this analysis is evidence, not a runtime correction or rollout.
