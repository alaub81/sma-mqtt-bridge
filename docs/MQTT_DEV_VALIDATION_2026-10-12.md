# Full DEV MQTT observation, 2026-10-12

Andreas started a DEV instance and authorized read-only inspection through the
already connected MQTT Explorer. The observation around 18:33–18:47 Europe/Berlin
covered all properties advertised by the five requested DEV device IDs, including
Advanced and Diagnostics. It did not publish commands, delete topics, change
device settings or modify bridge configuration. Model/firmware metadata matched
the three validated inverter profiles. The DEV display language was English.

## Complete advertised-property check

Counts describe Homie properties, not individual metadata topics. Device-level
`$state` was ready for all five devices, including a recheck after reconnecting
the Explorer with the unchanged saved connection.

| DEV adapter | Advertised properties checked | With payload | Without payload |
| --- | --: | --: | --: |
| Tripower | 35 | 35 | 0 |
| Storage | 35 | 35 | 0 |
| Sunny Boy | 40 | 35 | 5 |
| Home Manager | 82 | 37 | 45 |
| eCharger including portal and command nodes | 76 | 63 | 13 |
| Total | 268 | 205 | 63 |

For each declared property, the exact device/node/property path was searched in
the UI and its payload presence and metadata inspected. All declared properties
had `$datatype`, `$settable` and `$retained`; retained metadata was true throughout.
Physical units matched the documented mappings. Present integer, float, boolean
and enum payloads matched their advertised type/format. No literal NaN/Infinity
payload or unexpected measurement/control setter was found. Existing allowlisted
setting/plan setters were observed without exercising them.

## Newly added properties and diagnoses

All 39 additions from the recent inverter/eCharger expansion were present,
including the previously disabled inverter type/power limits and the eleven new
counter/derating properties. Thirty-six had payloads; only the three Sunny Boy
L2 additions lacked values, as expected from the register scan.

- All inverter type codes and read-only power limits had correct integer metadata;
  power limits were in W and model codes matched the documented device identities.
- All six operating/feed-in time properties were integer seconds. Rechecking
  operating times several minutes later showed increasing counters on all three
  devices. This does not establish reset behavior or the full counter semantics.
- Storage battery charge/discharge energy had float kWh metadata and values.
  The source Wh-to-kWh mapping is unchanged; a parallel comparison with the SMA
  display and charge/discharge counter growth is still required.
- All three derating properties reported no derating with the documented enum.
  Fault, timeout, consecutive failure, missing-critical and outage counters were
  zero for the inverter, Home Manager, API, SEMP and portal read sources.
  Home Manager rejected-block count was also zero.
- Sunny Boy and Tripower DC current/voltage/power names correctly distinguished
  input A from input B. Valid zero payloads remained numeric.
- eCharger phase powers had float/W metadata and numeric idle readings. The
  vehicle was disconnected and total charging power zero, so actual charging
  scaling/phase-power acceptance remains outstanding.

## Properties without payload

These properties have discovery metadata; absence of a payload is not a zero
measurement and does not imply permanent lack of device support.

- Sunny Boy: `currentl2`, `powerl1`, `powerl2`, `voltg1`, `voltg2`. This matches the
  known L3 installation mapping and SMA NaN on the unused phase observations.
- Home Manager: three assigned devices each advertised sixteen delegated
  parameters plus three identity/assignment properties. `permanentpowerlimit`
  had a value for each; the other fifteen delegated parameters per device did
  not, matching the earlier forty-five SMA-NaN responses. All sixteen core
  properties and nine diagnostics had payloads.
- eCharger measurements: `authregistrationcode`, `eventcode`, `frequency`,
  `health`, `healthcode`, `modeswitchcode`, `sessionenergy`, `vehiclehealth`.
  Frequency was absent in the earlier API audit; other channels were subject to
  the existing transport/timestamp availability rules. The MQTT UI alone does
  not establish a new underlying cause for each missing value.
- eCharger commands: `localresult`, `plan`, `portalresult`, plus the two command
  last-success diagnostics. Both command-source statuses were init; no successful
  DEV command was established. This is distinct from the ready read sources and
  does not constitute a failed device action.

## Explorer cache and remaining acceptance

Initial broad tree views showed some old hyphenated entries outside the current
`$properties` lists. Targeted searches did not yield content. After reconnecting
the Explorer, nine checked legacy paths across the three inverters were absent;
these observations support an Explorer cache artifact, not a demonstrated broker
retirement defect. No retained topic was deleted by this check.

This accepts DEV discovery/publication for the observed configuration and values.
It does not accept production configuration changes, openHAB Item links/history,
counter resets, charging under load, setter execution or fault/reboot behavior.
Public evidence omits private identities, network addresses, raw telemetry and
command history. The Explorer was left connected with its search filter cleared.
