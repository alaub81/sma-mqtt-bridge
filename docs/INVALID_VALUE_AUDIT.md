# Invalid-value compatibility audit, 2026-10-15

Scope: static comparison of the supplied openHAB Things and private transforms,
bundled inverter profiles, plant dependency/freshness guards, energy ledger,
averages, Home Manager and eCharger measurement handling. This is not live device
acceptance. Private originals were read only; no device configuration was changed.

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

- Reconcile host profile overrides and deploy the nighttime fix separately.
- Verify fresh PV zero, house power and plant readiness at night.
- Decide whether other legacy zeroing channels need explicit compatibility; no
  blanket conversion is applied to unverified channels.
- Investigate the observed configuration-changed day coverage using the actual
  installed configuration and ledger without deleting or resetting state.
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
status register 30203 is declared; the shared MAP catalogue alone cannot provide
a fresh standby predicate.

## Item-link clarification

Andreas confirmed that the Item links have no additional transformations. The
Item-link inspection question is resolved by user confirmation. Neither the
current Things export nor these links attaches sma_undef.js or the legacy grid
offset scripts. Their presence in the transform directory alone does not prove
active use. No rule usage has been established; no runtime change is required
solely because these files exist.
