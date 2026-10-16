# Inverter topic parity review, 2026-10-16

The Tripower phase voltage/power registers exist and were already inside its
FC04 block at 30769–30788. The profile lacked six property definitions. All six
returned valid values in the [2026-10-12 production scan](MODBUS_AVAILABILITY_2026-10-12.md).
The new mappings complete the shared PV measurement inventory without another
Tripower request or a different interval.

The [complete comparison CSV](inverter-topic-parity-2026-10-16.csv) covers all
44 distinct runtime inverter properties, including identities and the derived
Storage battery energy-return ratio. It uses current publication aliases and
the historical scan evidence. `unmapped` is a profile distinction; `sma-nan`
describes only the observed operating state. The matrix does not claim current
live MQTT discovery or current values. Per-source operational status/last-success
properties have intentionally source-specific IDs and are outside this register
comparison; optional group settings can also change the deployed inventory.

## Completed gaps

All topics below are under `measurements/`, Basic, optional for readiness and
read-only. Existing total active power remains its own measurement.

| Device | Current published topics | Register(s) | Raw format | Unit | Interval |
| --- | --- | --- | --- | --- | --- |
| Tripower / inverter1 | powerl1, powerl2, powerl3 | 30777, 30779, 30781 | S32/FIX0 | W | Existing 3 s block |
| Tripower / inverter1 | voltagel1, voltagel2, voltagel3 | 30783, 30785, 30787 | U32/FIX2 | V | Existing 3 s block |
| Storage / inverter2 | powerl1 | 30777 | S32/FIX0 | W | Expanded existing 5 s block |
| Storage / inverter2 | voltagel1 | 30783 | U32/FIX2 | V | New 5 s block |
| Storage / inverter2 | powerdrawn, powergridfeedin | 30865, 30867 | S32/FIX0 | W | One new 5 s block |

Voltage scale is 0.01; power scale is 1. Signed power, valid zero and existing
S32/U32 sentinel semantics are preserved. No missing phase becomes zero. The
Storage scan returned valid L1 voltage/power and zero for both grid-power fields.
Those zeroes establish readable samples, not independent measurement of all
household flows. The new grid-power properties are telemetry only: no new plant
grid-source mapping, automatic failover or household calculation input is added.

The official Tripower V13 and Storage V13 archives were downloaded again and
matched their [recorded SHA-256 values](REGISTER_VALIDATION.md#source-evidence).
Their English rows confirm addresses, channel names, lengths, RO access and types.
Storage explicitly provides W/V. The Tripower unit fields are blank; V/W follow
the phase-voltage/active-power channels and the existing quantity contract, as
with its other documented mappings.

## Remaining differences and further candidates

The two PV profiles now expose the same 33 direct properties: three identity
properties and 30 mapped measurements/diagnostics. Storage exposes 31 direct
properties plus its derived battery energy-return ratio. Common quantities use
the same topic IDs, units and datatypes. Model codes, enum choices, intervals,
actual phase availability and enabled group filters remain device-specific.

| Difference | Evidence and disposition |
| --- | --- |
| Storage L2/L3 current, voltage and power | Documented, but all six returned SMA NaN in the production scan. Keep outside the initial supported-value selection. Existing Sunny Boy inactive-phase declarations remain intact. |
| PV input A/B current, voltage and power | Both PV devices expose the same six DC topics. Storage has no corresponding numeric SMA registers in the audited model list; do not substitute battery values. |
| Battery state, current, voltage, temperature, capacity, charge/discharge power and energy | Storage-specific telemetry. Matching PV-list entries, where present, returned NaN; no PV placeholders or battery contribution are added. |
| Battery energy-return ratio | Derived from Storage charged/discharged counters; no corresponding independent PV quantity. |
| Identity, type, active-power limits, total/daily yield, active power, frequency, internal temperature, operating/feed-in duration and derating | Already implemented across all three; retain model-specific identity/enum and energy-unit evidence. |
| Apparent/reactive power, power factor, finer counters and event/configuration data | Additional candidates in the existing full register audit, rather than differences between current topic sets. Keep deferred pending semantic selection; reactive-power addresses and live support differ by model. No new setters. |

## Upgrade and verification

Internal `volt-g1`–`volt-g3` keys publish through the existing aliases as
`voltagel1`–`voltagel3`; no second spelling or topic rename is introduced.
The six new Tripower mappings do not change its existing poller range. Storage
extends its AC-power read from two to four registers and adds two short read
blocks. Explicit interval overrides and host-profile precedence remain intact.

The energy binding retains the released profile layout only for the exact
recognized bundled telemetry additions, including the preceding Sunny Boy L1
current correction. Full normalized-profile hashes gate this compatibility;
unrecognized changes retain the existing strict signature mismatch behavior.
Only fingerprint construction uses the old layout. Polling/discovery uses the
complete new profile. Counters, contribution references, baselines, accounting
boundaries and durable state are neither rewritten nor reset. Modified host
profiles require separate compatibility review.

Offline tests check register addresses, scaling, signs, zero/NaN, shared offsets,
read-only discovery, PV metadata parity, optional freshness and released energy
identity preservation. The official [openHAB Homie binding documentation](https://www.openhab.org/addons/bindings/homie/)
was consulted. No live device scan, build deployment, Item/link or history change
was performed. Rebuild/recreate and broker/value checks remain installation steps.
