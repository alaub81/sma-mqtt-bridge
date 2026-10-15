# Register validation

Evidence date: 2026-10-10. The three bundled profiles now contain the existing 41 read channels plus three identity properties per device. Validation means that mappings were checked against official model-specific SMA lists, deterministic decoding tests and a bounded local FC04 read. It does not mean that openHAB migration or every operating state has been accepted.

## Source evidence

| Profile | Official register evidence | Installed firmware verified locally |
| --- | --- | --- |
| `sma-stp8-0-3av-40` | [Parameter-STP8-10-3AV-40 V13](https://files.sma.de/downloads/Parameter-STP8-10-3AV-40_V13.zip), [GG10 variant](https://files.sma.de/downloads/Parameter-STP8-10-3AV-40__GG10_V13.zip), valid from 4.00.61.R | 4.10.10.R |
| `sma-sbs3-7-10` | [MODBUS-HTML SBS3.7-6.0-10 V13](https://files.sma.de/downloads/MODBUS-HTML_SBS3.7-6.0-10-V13.zip), valid from 3.12.33.R | 4.07.31.R |
| `sma-sb4-0-1av-41` | [PARAMETER-HTML SBxx-1AV-41 V16](https://files.sma.de/downloads/PARAMETER-HTML_SBxx-1AV-41-V16.zip), [GG10 variant](https://files.sma.de/downloads/PARAMETER-HTML_SBxx-1AV-41-GG10_V16.zip), valid from 4.01.15.R | 4.10.10.R |

Public source archives were downloaded for verification; their original copyrighted documents and installation responses are not redistributed. The non-GG10/GG10 lists agree on the selected read mappings. No country dataset or Grid Guard setting was changed. Runtime compatibility is intentionally limited to the locally checked firmware versions. Additional firmware needs explicit profile evidence.

| Download | SHA-256 |
| --- | --- |
| `Parameter-STP8-10-3AV-40_V13.zip` | `bc5511e76a5a61315ecf5d5a5ccb07abaeaa6294a26f0efd3ddc0e6b1a059ec5` |
| `Parameter-STP8-10-3AV-40__GG10_V13.zip` | `55adb7dc2c662ff403d225fa24eec05c8534f6640af11e76d0f903b4ffa95218` |
| `MODBUS-HTML_SBS3.7-6.0-10-V13.zip` | `091458b2a64bf73f40fc60f689677ffe9d78e943dd9f77ce936d9f6094d42a18` |
| `PARAMETER-HTML_SBxx-1AV-41-V16.zip` | `55d68deb25789c4ba6480d2cf15e59ee8223d9b71019d264b2ba3f048c070c7a` |
| `PARAMETER-HTML_SBxx-1AV-41-GG10_V16.zip` | `677c247992d5ca8ed0c862160bebd230c883a9d7f66b4e585fa54cbf8646399a` |

## Encoding and migration corrections

The [official SMA Modbus interface description](https://files.sma.de/downloads/SMA-Modbus-TI-en-10.pdf), sections 3.5.4–3.5.8, defines big-endian words/bytes, numeric NaN sentinels, fixed-point scaling and firmware encoding. Firmware major/minor bytes use BCD; the build byte is binary and release code 4 is R. Identity uses model 30053, serial 30057 and firmware 30059; the model codes 9347/9356/9403 were confirmed both in the corresponding lists and at the configured local endpoints. The serial guards are stored only in the private `smab.env`.

Unsigned values formerly decoded as signed in some Things now use the documented U32 type. A counter above 2³¹ must remain valid. U32 invalid is 0xFFFFFFFF; S32 invalid is 0x80000000; unavailable status is 0xFFFFFD. Invalid or unsupported values remain unavailable rather than becoming zero. Existing German condition/contactor/battery strings are preserved. Genuine negative signed measurements remain signed, so their old negative-to-zero/UNDEF transforms must be reviewed during parallel acceptance.

**Energy units (corrected 2026-10-11):** All three bundled inverter profiles publish addresses 30531/30537 as whole kWh, with U32/FIX0, scale 1 and Homie integer. The Storage V13 list labels both registers Wh. This is an intentional deviation based on Andreas' installation observation: daily raw value 2 corresponds to 2 kWh discharged from the battery, and total-energy values also match kWh. The previous Wh metadata was incorrect for this installation; do not divide the raw values by 1000. This user-reported evidence does not establish behavior for other firmware or the adjacent 30535/30539 registers. Complete independent parallel acceptance remains pending. The Tripower parameter UI leaves some measurement-unit cells blank: current/voltage/power/temperature dimensions are reconciled with the identified source channel, format and existing quantity Items.

Each original FC04 block and 3–180-second poller interval is preserved. Each property expires after the larger of its configured stale threshold and twice its effective poller interval; slower energy polls do not extend the freshness of fast power channels.

## Implemented read mappings

| Device | Homie property under measurements | Address | Raw type | Scale | MQTT unit | Poll seconds |
| --- | --- | --- | --- | --- | --- | --- |
| inverter1 | status | 30201 | uint32 | 1 | — | 60.0 |
| inverter1 | grid-contactor | 30217 | uint32 | 1 | — | 60.0 |
| inverter1 | power-drawn | 30865 | int32 | 1 | W | 5.0 |
| inverter1 | power-grid-feed-in | 30867 | int32 | 1 | W | 5.0 |
| inverter1 | day-yield | 30537 | uint32 | 1 | kWh | 180.0 |
| inverter1 | total-yield | 30531 | uint32 | 1 | kWh | 180.0 |
| inverter1 | current-a-input | 30769 | int32 | 0.001 | A | 3.0 |
| inverter1 | voltage-a-input | 30771 | int32 | 0.01 | V | 3.0 |
| inverter1 | power-a-input | 30773 | int32 | 1 | W | 3.0 |
| inverter1 | active-power | 30775 | int32 | 1 | W | 3.0 |
| inverter1 | current-b-input | 30957 | int32 | 0.001 | A | 5.0 |
| inverter1 | voltage-b-input | 30959 | int32 | 0.01 | V | 5.0 |
| inverter1 | power-b-input | 30961 | int32 | 1 | W | 5.0 |
| inverter1 | internal-temperature | 34113 | int32 | 0.1 | °C | 120.0 |
| inverter2 | status | 30201 | uint32 | 1 | — | 60.0 |
| inverter2 | grid-contactor | 30217 | uint32 | 1 | — | 60.0 |
| inverter2 | day-yield | 30537 | uint32 | 1 | kWh | 180.0 |
| inverter2 | total-yield | 30531 | uint32 | 1 | kWh | 180.0 |
| inverter2 | current-bat-stat-charge | 30845 | uint32 | 1 | % | 30.0 |
| inverter2 | current-batcapacity | 30847 | uint32 | 1 | % | 30.0 |
| inverter2 | current-bat-temp | 30849 | int32 | 0.1 | °C | 120.0 |
| inverter2 | battery-status | 30955 | uint32 | 1 | — | 60.0 |
| inverter2 | pres-bat-charge | 31393 | uint32 | 1 | W | 5.0 |
| inverter2 | pres-batt-discharge | 31395 | uint32 | 1 | W | 5.0 |
| inverter2 | internal-temperature | 34113 | int32 | 0.1 | °C | 120.0 |
| inverter3 | type | 30053 | uint32 | 1 | — | 60.0 |
| inverter3 | status | 30201 | uint32 | 1 | — | 20.0 |
| inverter3 | grid-contactor | 30217 | uint32 | 1 | — | 20.0 |
| inverter3 | max-power | 30231 | uint32 | 1 | W | 20.0 |
| inverter3 | set-max-power | 30233 | uint32 | 1 | W | 20.0 |
| inverter3 | power-drawn | 30865 | int32 | 1 | W | 5.0 |
| inverter3 | power-grid-feed-in | 30867 | int32 | 1 | W | 5.0 |
| inverter3 | day-yield | 30537 | uint32 | 1 | kWh | 60.0 |
| inverter3 | total-yield | 30531 | uint32 | 1 | kWh | 60.0 |
| inverter3 | current-a-input | 30769 | int32 | 0.001 | A | 3.0 |
| inverter3 | voltage-a-input | 30771 | int32 | 0.01 | V | 3.0 |
| inverter3 | power-a-input | 30773 | int32 | 1 | W | 3.0 |
| inverter3 | active-power | 30775 | int32 | 1 | W | 3.0 |
| inverter3 | power-l1 | 30777 | int32 | 1 | W | 3.0 |
| inverter3 | volt-g1 | 30783 | uint32 | 0.01 | V | 3.0 |
| inverter3 | internal-temperature | 34113 | int32 | 0.1 | °C | 120.0 |

## Installation observations

The first bounded read returned 39 of the 41 measurement channels, plus all nine identity properties. Sunny Boy registers 30777 (`power-l1`) and 30783 (`volt-g1`) returned SMA NaN; their mappings remain declared but no value is published. Check again during daytime operation and compare with openHAB before classifying this as unsupported. SEMP identity matched the configured eCharger. Seven baseline SEMP values were usable; the device-health measurement had an old source timestamp and was withheld. Neither local API nor portal authentication was attempted without credentials. No device write was performed.

Home Manager remains disabled for the Mac: the Mac is on a different network and does not receive meter multicast. Complete sender/serial/interface configuration and acceptance on the Raspberry Pi in the device network. Existing openHAB rules, offsets, historical counter corrections and persistence remain untouched.

## Full inventory audit, 2026-10-12

The original mapping validation does not imply complete register coverage. See the
[model-specific topic audit](MODBUS_TOPIC_AUDIT.md) and its complete register ledger
for all documented RO/RW/WO entries, current mappings and outstanding candidates.

## Sunny Boy L2/L3 profile extension, 2026-10-12

The user requested explicit L2 and L3 properties after the production scan confirmed
L3 assignment. The existing L1 properties and every original poller remain unchanged.
The matching Sunny Boy V16 list supplies the following RO mappings:

| Compact property under measurements | Register | Raw type / format | Scale | Unit | Poll interval |
| --- | --: | --- | --: | --- | --- |
| powerl2 | 30779 | S32 / FIX0 | 1 | W | 3 s |
| powerl3 | 30781 | S32 / FIX0 | 1 | W | 3 s |
| voltg2 | 30785 | U32 / FIX2 | 0.01 | V | 3 s |
| voltg3 | 30787 | U32 / FIX2 | 0.01 | V | 3 s |
| currentl2 | 30979 | S32 / FIX3 | 0.001 | A | 5 s |
| currentl3 | 30981 | S32 / FIX3 | 0.001 | A | 5 s |

Power/voltage fit the existing 30769–30788 block without increasing its size or
request frequency. Currents use one new four-register FC04 block at 30979.
S32 invalid is -2147483648 and U32 invalid is 4294967295. Values use big-endian
word/byte order; zero is valid and signed power/current remain signed.

These properties follow the existing phase-measurement basic default and are not
required for readiness. They remain exposed when optional advanced/diagnostics
filters are disabled. All six are non-settable. No model-specific adapter code or
fixed L3 phase selection is added: explicit phase topics remain explicit, and an
inactive phase may return NaN. Existing measurements/powerl1 and measurements/voltg1
keep their original register definitions and retained-history meaning.

The earlier scan returned L3 values and L2 NaN; L2 is deliberately included at the
user's request as a documented, potentially unavailable phase. This is offline-tested
profile implementation, not a new bridge/MQTT/openHAB deployment acceptance.
The three profiles now contain 47 measurement properties plus nine identity
properties. Historical audit coverage counts describe the pre-extension snapshot.

## Small inverter measurement extension, 2026-10-12

The user requested type/limits for Tripower and Storage, grid frequency and available
phase currents, and Storage AC power/battery current/voltage. Sixteen additive
properties implement this selection. Existing properties and pollers, including
the earlier Sunny Boy L2/L3 extension, remain unchanged.

| Device | Compact measurement ID | Register | Raw type / format | Scale | Unit | Default interval |
| --- | --- | --: | --- | --: | --- | --- |
| Tripower, Storage | type | 30053 | U32 / TAGLIST | 1 | — | Identity reads / 60 s |
| Tripower, Storage | maxpower | 30231 | U32 / FIX0 | 1 | W | Existing status block / 60 s |
| Tripower, Storage | setmaxpower | 30233 | U32 / FIX0 | 1 | W | Existing status block / 60 s |
| All three | frequency | 30803 | U32 / FIX2 | 0.01 | Hz | 5 s |
| Tripower | currentl1 / currentl2 / currentl3 | 30977 / 30979 / 30981 | S32 / FIX3 | 0.001 | A | 5 s |
| Storage | currentl1 | 30977 | S32 / FIX3 | 0.001 | A | 5 s |
| Storage | activepower | 30775 | S32 / FIX0 | 1 | W | 5 s |
| Storage | batterycurrent | 30843 | S32 / FIX3 | 0.001 | A | 5 s |
| Storage | batteryvoltage | 30851 | U32 / FIX2 | 0.01 | V | 5 s |

Type/limits reuse existing identity/status reads without additional requests and
use the same IDs, labels and advanced group as Sunny Boy. `type` reports the raw
model code rather than replacing identity/model. All limits remain RO; `setmaxpower`
is an observed limit and never a `/set` command. The measurement additions follow
existing basic defaults and are not additional readiness requirements.

Frequency uses one two-register FC04 block per device. Tripower currents use one
six-register block and Storage current one two-register block. Storage AC power,
battery current and battery voltage each use a two-register block, avoiding gaps
and preserving the existing slow SOC/temperature pollers. All new blocks default
to 5 seconds; explicit device poll-interval overrides still apply. SMA S32/U32
invalid values remain -2147483648/4294967295. Signed power/current are not clipped
or converted into inferred charging state.

All added addresses returned non-NaN values in the earlier production scan. The
matching model lists confirm addresses/types/formats; Storage explicitly provides
Hz/A/V/W units. The Tripower parameter UI leaves frequency/current unit fields
blank: Hz and A are reconciled with GridMs.Hz / GridMs.A.phsA–C, their FIX formats
and the physical quantities, consistent with the earlier documented unit method.
This does not extend firmware support or validate new MQTT/openHAB deployment.

Tripower exposes L1/L2/L3 currents, Storage only the available L1 current. Sunny Boy
retains its explicitly requested L2/L3 currents; the prior scan returned NaN for
L1/L2 and a value for L3. No additional inactive-phase channels are added to Storage.
The complete profiles now contain 63 measurement properties plus nine identities.

## Sunny Boy DC input B extension, 2026-10-12

The SB4.0-1AV-41 V16 list maps input B current/voltage/power to 30957/30959/30961 (S32, FIX3/FIX2/FIX0, A/V/W). The availability scan returned valid zero for all three. The profile now adds basic read-only `current-b-input`, `voltage-b-input`, `power-b-input` with scales 0.001/0.01/1 and SMA S32 sentinel -2147483648. A new six-register FC04 block polls every five seconds; existing blocks and input A properties are unchanged. These optional values do not gate readiness. Two independent MPP inputs are confirmed by the [official specification](https://manuals.sma.de/SBxx-1AV-41/de-DE/4177679243.html); installed string wiring remains unknown. Live publication remains pending.

## Selected counters and derating extension, 2026-10-12

The previously verified model-specific lists and production scan support eleven
additional read-only properties. Existing mappings, counters, labels and poller
intervals are preserved.

| Models | Published property | Register | Source / published unit | Group |
| --- | --- | --: | --- | --- |
| All three | measurements/operatingtime | 30521 | U64 seconds, scale 1, integer s | Advanced |
| All three | measurements/feedintime | 30525 | U64 seconds, scale 1, integer s | Advanced |
| All three | diagnostics/deratingreason | 30219 | U32 TAGLIST, model-specific enum | Basic (since 2026-10-13) |
| Storage only | measurements/batterychargeenergy | 31397 | U64 FIX0 Wh / float kWh, scale 0.001 | Basic |
| Storage only | measurements/batterydischargeenergy | 31401 | U64 FIX0 Wh / float kWh, scale 0.001 | Basic |

Storage V13 and Sunny Boy V16 explicitly specify seconds for both duration
registers. Tripower V13 omits the unit; the corresponding U64 duration addresses
in the official SMA_Modbus-de-en_V25 ZIP, SMA_Modbus-TI-en-31.xlsx, explicitly
specify s. Duration format alone would not prove seconds. Storage V13 explicitly
specifies Wh for both battery energy registers; the installation kWh override for
30531/30537 is not applied to these distinct addresses. Existing scan evidence
proves readability, not an aligned counter comparison with the device GUI.

The duration properties share the existing yield block, at its unchanged 180 s
Tripower/Storage and 60 s Sunny Boy intervals. Derating shares the existing status
block, at its unchanged 60/60/20 s intervals. Only Storage gains one FC04 block,
31397 with eight registers every 60 seconds.

All U64 properties reject 0xffffffffffffffff and preserve valid zero. Derating
rejects both 0xffffffff and status-NaN 0x00fffffd; unknown codes remain unavailable.
All three models map 557/884/1705/3520. Only Tripower additionally maps
3554/3556/4560/4561 from its own V13 list. No cross-model enum inheritance or
unavailable event-register fallback is used. The published enum strings preserve
SMA mnemonics and do not change with UI language, matching existing status values.

These properties are optional for readiness and expose no setter. Do not infer
daily/session/lifetime reset behavior, battery efficiency or a physical charging
scenario from the new counters without aligned observations. Live publication
and counter-growth comparisons remain pending.

## Derived battery energy return ratio, 2026-10-13

When a profile exposes battery-charge-energy and battery-discharge-energy in
kWh in the same poller, the reader adds basic read-only float
`measurements/batteryefficiency` with unit `%`. It computes discharge / charge
× 100 from that response, rounded to two decimal places; no extra register read.
Its lifetime is the shorter lifetime of the two counters and it never affects
readiness. Missing/invalid/negative counters or zero charged energy yield no
valid ratio; zero discharged energy yields 0%. Intermediate polls do not renew
the ratio. Values above 100% are not clamped, since differing initial stored energy
or counter/reset scope can make a raw ratio exceed 100%.

Andreas confirms a common counter start for his installation. His observed
8507 kWh charged and 6699 kWh discharged produce 78.75%. The complementary
21.25% is the unreturned share, not the efficiency. The AC/DC measurement boundary
and reset scope remain unverified; this cumulative energy return ratio is not
an independently measured cell or full-system round-trip efficiency. Comparable
state of charge at the interval boundaries improves period comparisons; monthly
ratios require counter deltas and are not provided by this cumulative property.

Host profile overrides missing the counter pair receive no derived topic.
Existing counter IDs/units/history, polling and invalid-value behavior remain.

## Installation AC-boundary evidence, 2026-10-15

The [aligned history comparison](BATTERY_ENERGY_BOUNDARY_2026-10-15.md) strongly
supports AC-side semantics for both 31397 and 31401 on the observed installation.
A nearly seven-hour discharge gives 1.711 kWh at the counter versus 1.711919 kWh
integrated AC and approximately 1.929356 kWh DC. An approximately 18-minute charge
gives 0.106 kWh versus 0.106640 kWh AC and approximately 0.092495 kWh DC.
These are aggregate empirical observations with documented sampling limits,
not a model-wide calibration or round-trip-efficiency acceptance. The runtime
profile/evidence promotion is separate and must preserve existing ledger binding.
