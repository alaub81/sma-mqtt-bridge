# Modbus availability during PV production

One user-authorized FC04 scan completed on 2026-10-12, approximately
08:25–08:31 Europe/Berlin. Both PV inverters had positive active power before and
after the scan. All three devices passed the configured model, firmware and serial
gates. No device writes, Grid Guard login, MQTT connection, profile changes or
openHAB changes were performed. The daily automation is now paused.

The [complete public result matrix](modbus-availability-2026-10-12.csv) records
only device/model-profile, register, channel, source metadata and availability.
Raw values, serials and network identities remain in ignored private verification
files. The [documentary inventory](MODBUS_TOPIC_AUDIT.md) defines the source scope.
This is an SMA register scan of the three inverters, not a SunSpec, Home Manager,
eCharger API/SEMP or MQTT acceptance test.

## Complete result

| Device | Read attempts | Non-NaN samples | Of these valid numeric zero | SMA NaN | Undecodable strings | WO skipped | Access control skipped |
| --- | --: | --: | --: | --: | --: | --: | --: |
| STP8.0-3AV-40 / inverter1 | 507 | 457 | 50 | 50 | 0 | 19 | 1 |
| SBS3.7-10 / inverter2 | 423 | 218 | 26 | 203 | 2 | 26 | 1 |
| SB4.0-1AV-41 / inverter3 | 377 | 197 | 29 | 180 | 0 | 12 | 1 |
| Total | 1307 | 872 | 105 | 433 | 2 | 57 | 3 |

Every distinct ledger address was accounted for: 1,307 readable addresses queried,
57 write-only addresses skipped, and access-control register 43090 skipped once
per device. No Modbus rejection, transport error, incomplete scan or untested
ledger entry occurred. The two Storage strings returned data that the UTF-8
classifier could not decode; they are not claimed as usable text channels.

A non-NaN sample means that the documented read returned a number or decodable
nonempty string without a recognized SMA invalid sentinel. It does not establish
correct engineering units, complete enum semantics, current sensor presence,
command permission, or meaningful Smart Home use. Many samples are configuration
parameters, identity fields or alternative representations of the same quantity.
The 872 successful samples are therefore not a proposal for 872 MQTT topics.

## Sunny Boy phase assignment and DC input B

The missing L1 topics have a concrete installation explanation:

| AC quantity | L1 register/status | L2 register/status | L3 register/status |
| --- | --- | --- | --- |
| Active power | 30777 / NaN | 30779 / NaN | 30781 / value |
| Phase voltage | 30783 / NaN | 30785 / NaN | 30787 / value |
| Phase current | 30977 / NaN | 30979 / NaN | 30981 / value |

The observed read of `Inverter.OutPhs` at 40183 returned code 329. The matching
[official Sunny Boy V16 parameter list](https://files.sma.de/downloads/PARAMETER-HTML_SBxx-1AV-41-V16.zip)
defines 325/327/329 as L1/L2/L3. This confirms the configured **L3 assignment** and
agrees with the three valid L3 measurements. It does not make the single-phase
inverter a three-phase inverter or prove wiring by physical inspection.

The existing L1 properties remain unchanged. Do not silently relabel an L1 topic
as L3 or change existing history. Agree an explicit model/installation mapping or
new phase-correct topic IDs before implementation.

DC input A current/voltage/power returned nonzero readings. Input B registers
30957/30959/30961 each returned a valid numeric zero. They are readable, and remain
candidates rather than being excluded as unsupported. This observation is
consistent with an unused second input but does not independently prove its wiring.
The [official model specification](https://manuals.sma.de/SBxx-1AV-41/de-DE/4177679243.html)
lists two independent MPP inputs.

## Useful additions for a joint selection

These are availability-backed candidates. No new property, channel group or
setter has been implemented. Existing measurements and history remain intact.

| Candidate | Availability observed | Remaining review |
| --- | --- | --- |
| Grid frequency, 30803 | All three devices | Source U32/FIX2; define final topic/unit and interval. |
| Actual-phase AC currents | Tripower L1/L2/L3; Storage L1; Sunny Boy L3 | Use 30977/30979/30981 according to actual phase support; S32/FIX3. |
| Phase voltage and active power | Tripower all phases; Storage L1; Sunny Boy L3 | Preserve existing L1 property identity; agree new phase-correct mappings. |
| Storage AC total power, 30775 | Value | Separate signed AC power from battery charge/discharge power. |
| Storage battery current and voltage, 30843/30851 | Values | Source S32/FIX3 A and U32/FIX2 V; retain sign semantics. |
| Storage battery charged/discharged energy, 31397/31401 | Values | U64/FIX0, source Wh; verify live scaling independently of the old kWh override. |
| Apparent power, 30813 | All three devices | Source S32/FIX0; source-unit evidence differs between lists. |
| Power-factor variants, 30949/31221 | All three devices | Select one evidenced representation; do not merge different conventions. |
| Total reactive power | Tripower 31497 returned a value; Storage/Sunny Boy 30805 returned NaN | Use phase-specific alternatives only after their semantics are checked; no guessed substitution. |
| Device active-power limits, 30231/30233 | All three devices | Observations are RO in the source lists; keep separate from writable control parameters. |
| Higher-resolution yield alternatives, 30513/30517 | All three devices | Preserve old whole-kWh topics; validate units and prefer one counter representation. |
| Operating/feed-in durations, 30521/30525 | All three devices | 64-bit duration alternatives; select once rather than duplicating 32-/64-bit topics. |
| Derating state, 30219 | All three devices | Decode documented codes before choosing labels/groups. |
| Current event number, 30247 | NaN on all three | Excluded from initial candidates for this observed state; could require an active event. |

Storage L2/L3 AC current returned NaN; they are excluded from initial candidates.
PV-device battery energy counters 31397/31401 also returned NaN, while the matching
Storage counters returned values. Do not generalize battery-related coverage in a
shared manufacturer list to the PV-device hardware.

## Exclusion and next decisions

The 433 NaN readings and two undecodable strings are marked
`excluded-from-initial-candidates` in the matrix. Their source entries and test
context are retained. This follows Andreas' request to start with actually readable
values rather than publishing the whole manufacturer inventory.

Valid zero remains available. The 872 non-NaN samples remain eligible for semantic
and usefulness review; identity/network-related samples carry a separate privacy
review marker. That marker is a review priority, not a newly assigned MQTT channel
group. All basic/advanced/diagnostics choices remain pending a joint decision.

This is a sequential snapshot during morning PV production. It is not a simultaneous
sample of all registers or a test of every battery, charging, fault and event state.
An absent event or optional sensor can return NaN despite documentary support.
Do not permanently erase that evidence or change existing retained topics on the
basis of this one scan. No further automatic scan is scheduled.

Next, agree a small useful first set from the availability-backed candidates,
resolve units/enums/counter alternatives and model-specific phase mappings, then
add file-based properties with conservative polling. RW observations do not create
write permission or `/set`; those remain a separate confirmed-command review.

Validation: the complete lint check passed for 118 project files; all 208 offline
tests passed. The public matrix has 1,367 unique device/register keys and matches
private result counts and exclusion/valid-zero decisions. `git diff --check` passed.
