# Invalid-value compatibility audit, 2026-10-15

Scope: comparison of the supplied openHAB Things and private transforms,
bundled inverter profiles, plant dependency/freshness guards, energy ledger,
averages, Home Manager and eCharger measurement handling. The final section adds
a bounded live nighttime sample; it is not full day/night acceptance. Private originals were read only; no device configuration was changed.

| Area | Finding | Consequence / decision |
| --- | --- | --- |
| PV active power, register 30775 | Legacy `smalimit.js` converts negative input to zero; explicit SMA sentinel normalization now enabled in both PV profiles | Fixes the identified nighttime plant-power dependency on fresh successful reads; other negative values remain signed |
| PV DC powers, registers 30773 / 30961; Carport phase power 30777 | Legacy `smalimit.js` zeroes negatives; current profiles omit invalid sentinels | Possible old retained displays at night or on unsupported channels; these are not inputs to current house power; leave unchanged pending per-channel decision |
| PV DC currents / voltages, 30769 / 30771 / 30957 / 30959 | Legacy scaling transforms zero negative input; current profiles preserve valid signed values and omit sentinels | Similar display difference; scaling-transform names alone do not establish that every invalid voltage/current means zero |
| Inverter grid powers, 30865 / 30867 | Legacy `smalimit.js` zeroes negatives; current profiles omit sentinels | If an inverter is explicitly selected as plant grid source, a missing value can block house power; the installation uses Home Manager, so no current dependency on these inverter channels |
| Battery charge/discharge power | Required for house power; missing/invalid input blocks the complete balance | No legacy zeroing transform on these channels; no evidence supports turning unavailable battery power into zero |
| Yield / energy counters | Invalid counters remain unavailable; counter decreases trigger reset protection | Never normalize to zero: this can simulate a reset or corrupt daily deltas |
| Temperature | Legacy `_undef` transform rejects all negatives; bridge preserves valid negative temperature | Intentional physically valid difference; do not clamp or discard real subzero readings |
| Status / grid contactor | Optional contactor can be unavailable while source status is OK | Source ready is not proof that every measurement is fresh; code 307 is OK, not standby |
| Home Manager / Wallbox | Missing data, stale timestamps, invalid types and source errors remain unavailable | No generic missing-to-zero fallback was found; a real zero and an unavailable sample remain distinct |
| Retained MQTT values | Missing/expired measurements leave the previous retained observation | Consumers must use availability/coverage; a displayed number alone does not prove a current measurement |
| House averages | Derived from counter ledger, not instantaneous PV power | Power correction does not repair configuration-changed, reset or insufficient-history states |

## Energy-ledger identity correction

Previously the energy binding hashed complete device profiles. Merely adding the
power-only `invalidAsZero` option would change this hash and block all daily
accounts as configuration-changed. The hash now excludes only this validated
power option, preserving the previous signature when the option was absent.
Counter mappings, scale, units, identities, roles, time zone and all other existing
signature inputs remain protected. Existing ledgers are not rewritten or reset.
A persisted-ledger regression test confirms preserved accounts and binding across
this power-option change. An already existing configuration-changed state can
have other causes and is not automatically cleared by this correction.

## Remaining acceptance

- Nighttime PV zero, house power and plant readiness have subsequently been
  observed; Andreas reports no host profile overrides.
- The 15 additional channel decisions are recorded below; verify DC daytime recovery
  and consumer handling of individual unavailable observations.
- Andreas explicitly chose a backed-up ledger reset to resolve the existing binding
  mismatch. Verify the next midnight, daily balances and averages after that reset.
- Check dependent openHAB rules for availability handling before retiring old Items.

The official [Modbus binding documentation](https://www.openhab.org/addons/bindings/modbus/)
explains the read-transformation stage used by the original Things. Existing
[retained observation behavior](MIGRATION.md) remains unchanged.

## Additional supplied transformation catalogue

Andreas supplied a concatenated `sma*` catalogue after the audit. The private
transform directory contains the corresponding maps and scripts; originals remain
unchanged. `smalimit1000.js` and `smalimit100.js` combine scaling with negative-to-zero
filtering, whereas `_undef` variants reject negatives. `sma_undef.js` rejects exactly
zero; its active Item/channel attachment is not established by the supplied Things
or current mapping worksheet. Do not apply this filter to real zero power, energy
or state of charge. MAP catalogues are shared across channels: a listed operating
status does not establish that its register is actually polled. Status 307 remains
OK; battery code 2291 is a battery-specific standby state.

The two cumulative grid transforms combine unit conversion and installation-specific
offsets. Their private constants must not be copied into public documentation.
When migrating, reconcile units and apply each offset exactly once; do not retain
legacy offset transformations on already corrected Bridge energy Items.

## Current Things export reconciled

The current concatenated SMA Things export supplied by Andreas contains 41 active
data Things. After whitespace normalization, their declarations match the earlier
private exports exactly. Attached transforms: smalimit.js on 10 channels,
smalimit1000.js on 3, smalimit100.js on 4, smalimit_undef.js on 6 and
smalimit10_undef.js on 4. The zero-to-UNDEF sma_undef.js transformation is not
attached in this Things export; Item-link profiles and rules remain a separate
possible attachment point. Grid-offset transformations are absent here as well.

Of the 17 negative-to-zero channel transformations, two are PV active power covered
by the new sentinel option. The remaining 15 cover four inverter grid powers,
three DC powers, one Carport phase power, three DC currents and four voltages.
This count describes legacy transformations, not 15 proven faults. In particular,
Carport voltage register 30783 is decoded unsigned in the original Things: its
unsigned invalid sentinel is positive and is not caught by the negative test.
The battery charge/discharge powers have no readTransform. No explicit PV operating
status register 40029 is declared; the shared MAP catalogue alone cannot provide
a fresh standby predicate.

## Item-link clarification

Andreas confirmed that the Item links have no additional transformations. The
Item-link inspection question is resolved by user confirmation. Neither the
current Things export nor these links attaches sma_undef.js or the legacy grid
offset scripts. Their presence in the transform directory alone does not prove
active use. No rule usage has been established; no runtime change is required
solely because these files exist.

## Per-channel assessment and nighttime sample, 2026-10-15

A bounded read-only Modbus sample at 21:39 CEST verified device identity before
reading these 15 channels. No device settings, profiles or MQTT values were
written. The ignored private record contains only the selected registers and
numeric results. This sample establishes nighttime behavior, not every possible
failure state or an independent physical zero measurement.

| Inverter | Register / channel | Night sample | Decision |
| --- | --- | --- | --- |
| Roof | 30865 / power-drawn | 0 W, valid | Preserve measured zero; no sentinel-to-zero fallback |
| Roof | 30867 / power-grid-feed-in | 1 W, valid | Preserve measured value; no fallback |
| Roof | 30769 / current-a-input | S32 NaN | Keep unavailable; no independently confirmed current measurement |
| Roof | 30771 / voltage-a-input | S32 NaN | Keep unavailable; darkness does not establish zero DC voltage |
| Roof | 30773 / power-a-input | S32 NaN | Keep unavailable; not required by plant house-power calculation |
| Roof | 30957 / current-b-input | S32 NaN | Keep unavailable; no independently confirmed current measurement |
| Roof | 30959 / voltage-b-input | S32 NaN | Keep unavailable; darkness does not establish zero DC voltage |
| Roof | 30961 / power-b-input | S32 NaN | Keep unavailable; not required by plant house-power calculation |
| Carport | 30865 / power-drawn | 0 W, valid | Preserve measured zero; no fallback |
| Carport | 30867 / power-grid-feed-in | 1 W, valid | Preserve measured value; no fallback |
| Carport | 30769 / current-a-input | S32 NaN | Keep unavailable; no independently confirmed current measurement |
| Carport | 30771 / voltage-a-input | S32 NaN | Keep unavailable; darkness does not establish zero DC voltage |
| Carport | 30773 / power-a-input | S32 NaN | Keep unavailable; not required by plant house-power calculation |
| Carport | 30777 / power-l1 | S32 NaN | Keep unavailable: inactive phase; earlier daytime evidence also showed NaN |
| Carport | 30783 / volt-g1 | U32 NaN | Keep unavailable: inactive phase; legacy negative filter did not catch this unsigned sentinel |

The [official SMA Modbus specification](https://files.sma.de/downloads/SMA-Modbus-TI-en-10.pdf)
identifies S32 NaN as 0x80000000 and U32 NaN as 0xFFFFFFFF. It also documents NaN
for undefined registers within a readable block. These sentinels alone do not
establish a measured zero or a unique standby condition. Status 307 is not such a
condition either.

Assessment complete: retain the current unavailable handling for all 15 channels.
No additional profile compatibility option is justified by this evidence. The
existing active-AC-power exception remains limited to register 30775. The four
inverter grid channels do not affect the installation's Home Manager based house
balance; DC and inactive-phase channels are not its inputs. An installation that
selects an inverter grid source must still treat unavailable grid power as an
incomplete balance.

For the nine DC channels, legacy transforms previously displayed synthetic zero
at night. The current bridge instead withholds unavailable samples; an older
retained number can therefore remain visible. It must not be presented as a fresh
nighttime observation. Per-property unavailable publication/expiry in MQTT and
openHAB remains a separate consumer-availability task; this assessment does not
change retained messages or historical data. Carport L1 must not be renamed to L3
or copied into L3 history. Daytime recovery of the nine DC channels remains to be
checked across a complete night/day transition.

## Approved DC compatibility revision

After the assessment, Andreas requested legacy-compatible zeroes for the three DC
currents and three DC powers, retaining unavailable voltage handling. The bundled
profiles now apply this only to successfully read S32 sentinels when fresh decoded
AC power is zero and fresh device condition is OK. This includes existing AC
sentinel normalization; it is an inferred no-production rule, not a measured DC
zero or confirmed standby status. The earlier recommendation to leave all 15
unchanged is superseded for these six channels only.

The official model catalogues identify operating status at **40029**, not 30203
(which is nominal power in OK mode). A read-only probe of 40029 returned enum NaN
on both devices, so no operating-status gate or new public channel was added.
Status 307 alone remains insufficient; it is combined with fresh AC power.

A second read-only sample at 21:58 CEST with the local updated reader produced
0 A / 0 W for all six selected DC sentinels, while the three DC voltages and two
Carport L1 channels remained unavailable. Guard reads use the same verified
connection as the DC observation, including an additional fresh input-A read when
input B is due separately. Production MQTT was not changed. Daytime transition and
host deployment remain pending. Valid negative measurements are preserved.
