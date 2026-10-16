# eCharger charging data check, 2026-10-15

## Scope and method

Andreas requested a read-only check while the vehicle was charging. MQTT Explorer
was already connected. Its current values, Homie metadata and local received-message
histories were inspected around 15:43–15:47 Europe/Berlin. Two additional reads of
each already enabled local API and SEMP adapter, approximately 60 seconds apart,
checked source freshness. The existing configured TLS trust file was resolved from
its container bind-mount path to its local host path; verification settings were
not weakened. Existing API catalog/SEMP identity validation remained in use.

Only selected numeric channels, timestamps and availability were examined; no
credentials, headers, endpoints, serials or raw authenticated responses are saved
here. No device-setting request, MQTT publication, service restart, configuration,
openHAB or persistence change was performed. The temporary reader did not activate
the persistent timestamp recorder. MQTT Explorer receive timestamps are not device
acquisition timestamps, and its history is not a complete source recording.

## Findings

- The eCharger Homie state, API status and SEMP status were ready. Vehicle status
  was charging (200113). This is current sampled evidence, not continuous uptime.
- Charging was single-phase on L3, approximately 3.0–3.3 kW. L1/L2 active power was
  near zero. API phase readings and total active power agreed: in two directly read
  sets, phase-sum minus API total was approximately +0.005 W and -0.002 W. Phase
  units were accepted by the existing metadata/firmware validation. This confirms
  the sampled phase/total mapping; it does not accept every phase under load or
  identify which limit/controller selected single-phase charging.
- Negative signed phase currents were preserved, including approximately -13.86 A
  on L3. No sign conversion or assumed fault was introduced. Source voltage was
  approximately 236 V on the loaded phase.
- MQTT session energy increased monotonically in the observed window, with recent
  changed values about 30 seconds apart. At 15:40:43–15:43:43 its increment was
  0.1584 kWh; total-energy receipt endpoints approximately two seconds later gave
  0.158375 kWh. The difference is 0.025 Wh, with approximate average power 3.2 kW.
  These nearly aligned receive windows are a consistency check, not calibrated
  metering acceptance or an exact source-time integral.
- API total energy also increased by 0.0545 kWh across the two direct reads,
  consistent with approximately 3.27 kW over a minute. Power, phase currents,
  phase voltages and total-energy source timestamps advanced; observed ages were
  below 0.2 seconds. API/SEMP vehicle status ages were below 0.7 seconds. Unchanged
  control-setpoint values had advancing timestamps, aged approximately 6–21 seconds.
- Session energy was accepted as fresh by the existing SEMP reader on both reads.
  Its exact raw timestamp was not retained in the scoped numeric observer. The
  MQTT evidence establishes active-session progression, not idle authority.
- Device/vehicle health and event values kept their September 11 timestamps in
  both reads and transports, approximately 34 days old. Mode/authorization kept
  July 21 timestamps, approximately 86 days old. No natural changes occurred in
  these channels. Their values must not become fresh merely because the reader
  is reachable. The existing filters remain appropriate pending semantic evidence.
- Frequency and health had metadata but no measurement payload in MQTT Explorer.
  The API measurement snapshots contained no frequency channel. Health remained
  filtered by the stale source timestamp. Neither absence establishes a device
  fault or permanent lack of firmware support.
- The MQTT history contains earlier multi-minute gaps, including roughly 16 minutes.
  Their cause is not established; observation/reconnect/deployment gaps must not be
  attributed to the charger without independent evidence.

## Remaining acceptance

No reset, unplug/replug, charging-to-idle transition or physical target completion
occurred during this check. Session reset scope and authoritative idle energy
remain open. Health/event/mode/authorization need natural transitions or verified
protocol semantics before changing freshness policy. There is no basis here for
removing filters, disabling the timestamp recorder, claiming full charging-target
acceptance or changing maximum-power/phase controls. Existing Home Manager control
ownership remains unchanged. The investigation is narrowed, not globally closed.

## Plugged-in idle follow-up, evening

Andreas reports charging approximately 13:00–16:00 and confirms the vehicle remains
plugged in. Two read-only API/SEMP samples at approximately 21:28 and 21:29 local
time, about 60 seconds apart, used the existing readers and configured TLS policy.
Only allowlisted numeric channel observations were retained privately; no settings,
commands or recorder activation were performed. MQTT Explorer was inspected too.

Both transports reported 0 W and vehicle status 200112 (connected/waiting). API
total energy remained 1499.938875 kWh; its source timestamp advanced with ages
about 0.11–0.22 seconds. Power and vehicle status also remained fresh. Small signed
phase readings around zero were preserved; no clamping was applied.

Both transports returned session energy 13.515 kWh with the same fixed device
timestamp, 16:28:02.494 local time. Its age increased from approximately 17,997 to
18,058 seconds, beyond the configured 180-second freshness limit. Both readers
therefore omitted the current session-energy output. MQTT still displayed the
previous retained 13.515 kWh observation. This confirms idle timestamp freezing,
not current-session authority or a successful reset. The user's charging window
is approximate and is not an exact source-time boundary.

Device/vehicle health and event timestamps remained on September 11; mode and
authorization remained on July 21. No value transitions were observed, so their
classification and existing filters remain unchanged. Missing frequency was already
removed and is not an open acceptance item.

Idle behavior is sampled and consistent. A natural unplug/replug or new session
is still required to settle the reset boundary. Do not clear retained session
energy, force zero or weaken freshness checks from these two stationary samples.

## User-operated unplug transition, evening

Andreas unplugged the vehicle and explicitly confirmed this. MQTT changed from
200112 (connected/waiting) to 200111 (not connected), and session energy changed
from the old retained 13.515 kWh to zero. A direct API/SEMP sample at about 21:31:57
confirmed both session values as zero with the same new device timestamp,
21:31:28.467 local time, approximately 29 seconds old and fresh. A second sample about 60 seconds later retained the same zero and session
timestamp in both transports, still within the freshness window. API total energy
remained 1499.938875 kWh and power stayed zero. The Bridge sent no charging command.

This establishes the session-energy reset on this unplug event, independently
of the cumulative counter and the Bridge energy-ledger reset earlier that evening.
It does not establish all reset triggers, a complete subsequent charging session
or old health/event timestamp semantics. Keep the existing session freshness
filter and last-known retained behavior; never use session energy as cumulative
energy for daily house/Wallbox accounting.

## User-operated replug transition, evening

Andreas confirmed reconnecting the vehicle. At approximately 21:34:51 local time,
API and SEMP both reported vehicle status 5169 (locked), zero power and raw session
energy zero. The API cumulative counter remained 1499.938875 kWh with a fresh
source timestamp. Vehicle status was also fresh in both transports. A second sample about one
minute later confirmed the same locked/zero-power state, unchanged cumulative
energy and the same stale zero-session timestamp.

The session timestamp remained 21:31:28.467, from the preceding unplug event;
it was now approximately 203 seconds old, beyond the 180-second freshness limit.
Both readers therefore omitted session-energy publication despite a successful
read and raw zero. This establishes that replug alone did not refresh/reset this
channel in the observed locked state. The new plugged-in state did not restore
the prior 13.515 kWh session amount.

Do not interpret locked as a new Bridge command or a demonstrated fault. Charging
permission was not changed and the cause of the lock was not investigated. A new
charging interval is still needed for charging-start/reset behavior. The observed
idle/unplug/replug cycle is sufficient to reject a universal acquisition-time
interpretation for session energy; retain the existing filter until an explicit
last-session-versus-current-session publication policy is chosen.

## Next charging interval, 2026-10-16

Andreas reported that the vehicle had just begun charging. Two read-only samples
at 07:02:00 and 07:02:55 Europe/Berlin used the enabled local API and SEMP readers
with existing identity and TLS checks. No device setting, MQTT publication,
service restart or persistent timestamp-recorder activation was performed.
Allowlisted numeric observations are retained privately.

Both sources reported charging (200113), with power approximately 10.10 and
10.16 kW. API session energy increased from 0.952625 to 1.108250 kWh; SEMP gave
0.9526 and 1.1083 kWh. Both carried the same advancing session timestamps, with
observed ages below 0.2 seconds. The API cumulative counter increased from
1500.892000 to 1501.047750 kWh. Over approximately 55 seconds, session and total
increments were 0.155625 and 0.155750 kWh, differing by 0.125 Wh. Their growth is
consistent with the sampled power; this is not a calibrated meter comparison.

Compared with the previous unplug/replug observations, session energy has resumed
fresh progression during charging. The exact charging-start instant was not
captured, so an additional reset at that instant is neither established nor ruled
out. No MQTT/openHAB delivery or three-phase mapping acceptance is inferred.
Health/event timestamps remain on September 11 and mode/authorization on July 21
in both samples. Charging alone did not refresh these channels. Preserve the
existing filters; other reset triggers and last/current-session publication policy
remain separate decisions.

## Reported charging completion and observed resumption, 2026-10-16

Andreas reported that charging had completed. Read-only API/SEMP samples at
07:09:47 and 07:10:42 Europe/Berlin both reported zero power and connected/waiting
vehicle status (200112). API session energy remained 1.871625 kWh, SEMP
1.8716 kWh; both retained the same device timestamp, 07:09:02.072. Its age grew
from approximately 46 to 101 seconds, still within the 180-second limit.
The API cumulative counter remained 1501.811000 kWh with advancing timestamps.
These samples confirm the observed transition to idle and frozen session
value during the pause, not a battery-SOC target or a specific cause of the stop. No device command,
MQTT publication or configuration change was made. The session value must
not be used as the cumulative input to daily energy accounting.

A follow-up at 07:12:24, intended to inspect the expired session timestamp,
instead found charging active again in both transports (200113), at approximately
1.658 kW. API session energy had increased to 1.905250 kWh and SEMP to 1.9053 kWh,
with the same new device timestamp and age below 0.1 seconds. API cumulative
energy had increased to 1501.844125 kWh. The observed idle interval was therefore
a pause followed by charging resumption. No reset to zero is visible across the
sampled pause/resumption; the exact transition instants were not captured.
This follow-up cannot establish post-180-second idle filtering because the
session timestamp had resumed advancing. Yesterday's separate idle evidence
remains valid. The reason for resumption, target completion and controller intent
are not inferable from these measurements. No charging control was changed.

## Second reported completion, 2026-10-16

Andreas reported completion again. Read-only API/SEMP sampling began at 07:17:05
Europe/Berlin. The first three samples through 07:18:46 all reported zero power,
connected/waiting vehicle status (200112), unchanged API total energy
1501.941750 kWh and session energy 2.002625 kWh (API), 2.0026 kWh (SEMP).
The shared session timestamp stayed at 07:15:54.260 while its age increased from
approximately 72 to 172 seconds. Total-energy timestamps continued advancing.
No session reset was observed after the preceding charging resumption. No device
setting, MQTT publication, runtime configuration or persistence change was made.

Two further samples at 07:19:36 and 07:20:26 confirmed the same idle state,
zero power, constant cumulative energy and unchanged raw session value/timestamp.
Session ages were approximately 222 and 272 seconds. Both readers classified
session energy as stale and omitted it from their current output; power,
vehicle status and cumulative energy remained fresh. This confirms the configured
180-second session filter across this observed charging-to-idle interval.
Five samples over approximately 201 seconds showed no further charging resumption.
This does not certify permanent completion, vehicle SOC/target achievement or
actual MQTT/openHAB delivery. Existing retained-session behavior and any future
last/current-session publication policy remain separate; no new zero or reset
was synthesized. Health/event/mode/authorization timestamps stayed old throughout.
