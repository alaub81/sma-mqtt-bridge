# Sunny Home Manager 2.0 Modbus reads

> Current MQTT node/property IDs remove hyphens at the publication boundary. Internal profile and
> readiness keys keep their spelling; historical examples below may use the former IDs. See
> [compact IDs and display translations](CONFIGURATION.md#display-language-and-compact-channel-ids).

Implemented and offline tested on 2026-10-10. Hardware/MQTT acceptance on the Home Manager and complete openHAB migration remain pending. The source is independently enabled and defaults to UDP; select Modbus TCP explicitly. The supported read inventory comes from [SMA HM-20-Modbus-NSD-TI-de-12, version 1.2](https://files.sma.de/downloads/HM-20-Modbus-NSD-TI-de-12.pdf), chapters 4–6. No newer revision was found during this work.

## Configuration and access

Add these overrides to private root `smab.env`, alongside the existing broker settings:

```dotenv
SMAB_HOME_MANAGER_ENABLED=true
SMAB_HOME_MANAGER_TRANSPORT=modbus-tcp
SMAB_HOME_MANAGER_HOST=home-manager.example.invalid
SMAB_HOME_MANAGER_SERIAL=1234567890
```

Replace the example address and serial with the actual installation values. Additional JSON configuration is optional. `SMAB_HOME_MANAGER_MODBUS_PORT=502` is separate from the existing UDP port. The selected profile defaults to `sma-home-manager-2-modbus`, supports host overrides, and contains no installation identifiers. All timing options are documented in [CONFIGURATION.md](CONFIGURATION.md) and [smab.example.env](../smab.example.env). The sample JSON preserves profile polling intervals unless an explicit `homeManager.pollIntervalSeconds` override is added.

The Home Manager's NSD Modbus server must already be reachable. The external-device Modbus client setting is a different interface. SMA documents Grid Guard login for Unit 2 plant access and delegated inverter parameters. The implementation sends **only FC04 reads**, including a read of unlocked-device count at 43090. It never writes that register, logs in, logs out, enables NSD, or changes charging/grid regulation. A rejected block becomes unavailable and increments `diagnostics/modbus-rejected-blocks`; other read blocks continue. Whether installed firmware allows measurement reads without login requires installation testing. Inaccessible documented registers are not claimed as available live values.

## Complete documented read coverage

Base topics are `homie/<HOME_MANAGER_HOMIE_ID>/`. All Home Manager properties have `$settable=false`.

| Unit | Register | Topic suffix | Type / source unit | Default interval |
| --- | --- | --- | --- | --- |
| 1 | 30001 | `parameters/profile-version` | U32, raw profile revision | 60 s |
| 1 | 30003 | `identity/susy-id` | U32 | 60 s |
| 1 | 30005 | `identity/serial` | U32 | 60 s |
| 1 | 30007 | `parameters/data-change-counter` | U32, wrapping counter | 60 s |
| 1 | 30051 | `identity/device-class` | U32, 8128 communication product | 60 s |
| 1 | 30053 | `identity/model` | U32, 9343 Home Manager | 60 s |
| 1 | 30055 | `identity/manufacturer` | U32, 461 SMA | 60 s |
| 1 | 30057 | `identity/serial-copy` | U32 | 60 s |
| 1 | 30193 | `parameters/system-time` | U32, Unix UTC seconds | 60 s |
| 1 | 43090 | `parameters/grid-guard-unlocked-devices` | U32, device count on read; never a code | 60 s |
| 2 | 30193 | `measurements/plant-time` | U32, Unix UTC seconds; Advanced | 30 s |
| 2 | 30193 | `measurements/plant-time-iso` | ISO 8601 UTC string; Basic, same read | 30 s |
| 2 | 30201 | `measurements/plant-status` | U32 enum: ok/warning/error | 30 s |
| 2 | 30581 | `measurements/energy-import` | U32 Wh → kWh | 60 s |
| 2 | 30583 | `measurements/energy-export` | U32 Wh → kWh | 60 s |
| 2 | 30865 | `measurements/power-import` | S32 W | 3 s |
| 2 | 30867 | `measurements/power-export` | S32 W | 3 s |

Unit 1 assignment records span 42109–43088: all 245 slots are read in nine blocks of at most 120 registers, every 180 seconds. Occupied slots expose `device-<slot>/susy-id`, `/serial`, and `/unit-id`. Empty/invalid slots are omitted. Unit 255 remains visible as an unassigned record but is never queried. Duplicate units use only the first slot, as documented by SMA. This assignment table is identity evidence for delegated reads, not a discovery of undocumented measurement registers.

Each valid assigned unit 3–247 gets the following read-only properties under its `device-<slot>/` node, at 180-second intervals. Source RW metadata never creates `/set` subscriptions.

| Register | Property | Source type / unit / scaling |
| --- | --- | --- |
| 30233 | `permanent-power-limit` | U32 W; PV inverters only |
| 30825 | `reactive-control-mode` | U32 enum |
| 30831 | `cos-phi-setpoint` | S32 FIX2, × 0.01 |
| 30833 | `excitation-setpoint` | U32 enum |
| 40200 | `configured-reactive-control-mode` | U32 enum, source RW |
| 40206 | `configured-cos-phi-setpoint` | S32 FIX2, × 0.01, source RW |
| 40208 | `configured-excitation-setpoint` | U32 enum, source RW |
| 40216 | `overfrequency-power-mode` | U32 enum, source RW |
| 40218 | `gradient-start-frequency-offset` | U32 FIX2 Hz, × 0.01, source RW |
| 40220 | `gradient-reset-frequency-offset` | U32 FIX2 Hz, × 0.01, source RW |
| 40222 | `cos-phi-curve-start` | U32 FIX2, × 0.01, source RW |
| 40224 | `cos-phi-curve-start-excitation` | U32 enum, source RW |
| 40226 | `cos-phi-curve-end` | U32 FIX2, × 0.01, source RW |
| 40228 | `cos-phi-curve-end-excitation` | U32 enum, source RW |
| 40230 | `cos-phi-curve-start-power` | U32 %, source RW |
| 40232 | `cos-phi-curve-end-power` | U32 %, source RW |

Unknown enum codes and SMA NaN sentinels are unavailable. Signed power is preserved. Status enums use their explicit profile mapping; reactive-mode payloads preserve documented numeric codes. Pure Unit 2 write-only registers 40015, 40016, 40024, 40025, 40149, 40151 and 40153 are excluded from read polling. Phase currents/voltages and per-phase energy are defined in the UDP meter protocol, but not in this Home Manager NSD register table; no speculative Modbus addresses are added. This profile covers all readable entries of this document, not all firmware-internal settings or portal preferences.

## Connection supervision and retained state

TCP sessions persist between read cycles. Every new session waits the configured startup delay and verifies both Home Manager serial registers, device type, class and manufacturer before reading plant data or assignments. Individual requests have bounded timeouts; transaction and reconnect pauses apply separately. No unsuccessful read is retried immediately in a loop. Protocol framing/connection errors close the session and trigger supervised reconnect, with a fresh identity check.

The scheduler performs one due block at a time and prioritizes the earliest expiry deadline, so slow delegated reads cannot starve fast grid-power reads. Delegated reads begin at their first 180-second deadline after assignment discovery. Assignment changes retire old topics and invalidate associated samples; stale assignments cannot authorize further delegated polling. Homie discovery is refreshed as occupied slots change. Topic ownership is saved before retained publication, and removed properties/metadata are retired using the existing persistent manifest. Runtime state remains in `data_smab_state`.

Freshness is per property, using the larger of configured stale seconds and twice the effective interval. Device time is published as an observed register value; it is not substituted for the receipt timestamp or used to renew stale measurements. Rejected blocks clear their own values instead of publishing zero. Basic identity/diagnostics may remain ready while access to plant data is rejected; use property availability and rejected-block count for acceptance.

## Installation acceptance still required

1. Validate the bundled/host mapping with `--check-home-manager-profile sma-home-manager-2-modbus` and configuration with `--check-config`; confirm NSD server state/port without changing grid settings automatically.
2. Start on the Pi in the device network and verify configured serial, identity and Unit 1 assignment records.
3. Compare the four meter values and status against openHAB at aligned times; preserve existing Item names, active offset profiles, quantity units and persistence. The bridge publishes device counters without legacy private offsets.
4. Record which Unit 2 and delegated registers are actually readable on installed firmware. Compare scaling, enums and NaN behavior; unavailable model-specific entries stay unavailable.
5. Check reconnect, rejected registers, stale values, changing assignments and retained retirement. Only then accept the installation; no source links/rules are removed by implementation.

Deterministic tests cover register inventory, U32 high counters, signed values, sentinel/enum handling, identity-before-plant reads, session reuse, request correlation, timeouts/reconnect, pacing, assignment boundaries/duplicates/expiry and dynamic Homie discovery/manifest retirement. No live Home Manager read or write was performed for this implementation.

## Reduced production polling

Set `SMAB_HOME_MANAGER_ADVANCED_CHANNELS_ENABLED=false` to retain the six Unit 2 plant/grid
readings while skipping Unit 1 metadata polling, the assignment table and all delegated inverter
parameters. Mandatory Unit 1 identity verification still runs when a connection is established.
`SMAB_HOME_MANAGER_DIAGNOSTICS_ENABLED=false` separately removes MQTT source diagnostics and the
rejected-block counter. Both defaults are `true`; see [configuration](CONFIGURATION.md#optional-channel-groups).

## Subsequent complete live read check, 2026-10-12

The [one-shot availability check](HOME_MANAGER_AVAILABILITY_2026-10-12.md) now supplies
live identity, all fixed property, complete assignment-table and delegated-read
evidence. All fixed properties were valid; only delegated 30233 returned values in
the three occupied slots, while fifteen other parameters per slot returned NaN.
This updates read availability evidence, not full MQTT/openHAB/operational acceptance.

## ISO plant time, 2026-10-13

The bundled profile maps register 30193 twice within the existing single poll:
Advanced raw seconds (`measurements/planttime`) and Basic ISO UTC text
(`measurements/planttimeiso`), for example `2026-10-13T17:00:00Z`.
The generic profile format `unix-time-iso` requires unscaled U32, string datatype,
empty unit and no value map or numeric bounds. Raw invalid sentinels are checked
before conversion; no current bridge timestamp is substituted. Both channels
retain the same read interval/lifetime and remain read-only.

This changes discovery with Advanced disabled: the raw channel is no longer
published. Keep Advanced enabled if existing numeric Items/history or epoch-link
profiles still depend on it. Host overrides need the new mapping and raw group
change explicitly; UDP meter transport does not provide this device clock.
See the [openHAB migration instructions](../openHAB/openHAB.md#home-manager-plant-time-display-and-rules).
