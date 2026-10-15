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
