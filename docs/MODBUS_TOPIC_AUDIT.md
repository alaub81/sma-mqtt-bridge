# Model-specific Modbus topic audit

Audit date: 2026-10-12. **The inverter profiles are not complete inventories of
readable SMA registers.** They reproduce the original openHAB integration and
identity checks. This audit compares the three model-specific SMA lists with the
bundled profiles, independently of the currently configured channel filters.
No device or MQTT connection was made, and no profile or command path was changed.

The [complete register ledger](modbus-topic-audit.csv) contains one row per device
and distinct numeric SMA register address, including RO, RW and write-only entries.
The [Storage SunSpec-only ledger](modbus-sunspec-only-audit.csv) retains source rows
without a numeric SMA address. These are alternative-interface evidence, not
invented addresses for the existing SMA adapter.

## Sources and method

Use the exact archives and SHA-256 values recorded in
[REGISTER_VALIDATION.md](REGISTER_VALIDATION.md):

- Tripower: [Parameter-STP8-10-3AV-40 V13](https://files.sma.de/downloads/Parameter-STP8-10-3AV-40_V13.zip), valid from 4.00.61.R; installed 4.10.10.R.
- Storage: [MODBUS-HTML SBS3.7-6.0-10 V13](https://files.sma.de/downloads/MODBUS-HTML_SBS3.7-6.0-10-V13.zip), valid from 3.12.33.R; installed 4.07.31.R.
- Sunny Boy: [PARAMETER-HTML SBxx-1AV-41 V16](https://files.sma.de/downloads/PARAMETER-HTML_SBxx-1AV-41-V16.zip), valid from 4.01.15.R; installed 4.10.10.R.

The locally retained archives match all three recorded hashes. Parse the English
HTML table directly inside each ZIP. Tripower and Sunny Boy use the parameter-list
layout (SMA address/type/format/access in columns 11–15); Storage uses the combined
SMA/SunSpec layout (SMA address/type/format/access in columns 2–6).
Count only numeric SMA addresses in the primary ledger. Collapse repeated rows at
an identical address after checking channel, type, length, format, unit and access
agreement; combine differing read/write-level annotations. Do not collapse
*different* addresses merely because their channel names match.

Resolve each bundled property to `poller.start + property.offset`. Match by device
and register address, not by label or an assumed contiguous polling range. A block
that reads an address does not publish it unless a property mapping exists.
Record compact publication IDs, removing hyphens as the Homie publisher does.
Check that every existing property has source evidence, and that its raw type,
length and FIX/TEMP scaling agree. These checks passed for all 50 properties
(41 original measurement properties and nine identity properties). Sunny Boy type
and identity/model share address 30053, hence 49 distinct mapped addresses.
This does not independently validate every enum choice, unit, physical meaning,
firmware behavior or live value. The known Storage kWh override remains explicit.

## Coverage

| Device | Source rows | Repeated address rows | No numeric SMA address | Distinct SMA addresses | RO | RW | WO | Mapped addresses | Missing readable addresses |
| --- | --: | --: | --: | --: | --: | --: | --: | --: | --: |
| inverter1 / STP8.0-3AV-40 | 533 | 6 | 0 | 527 | 186 | 322 | 19 | 17 | 491 |
| inverter2 / SBS3.7-10 | 588 | 12 | 126 | 450 | 230 | 194 | 26 | 14 | 410 |
| inverter3 / SB4.0-1AV-41 | 396 | 6 | 0 | 390 | 178 | 200 | 12 | 18 | 360 |

Missing RO/RW splits are 169/322, 216/194 and 160/200 respectively. The total is
1,261 unmapped readable **device/register pairs**, not 1,261 new independent
measurements or guaranteed working topics. The lists include alternative counter
representations, repeated channels, optional/external equipment and access-control
registers. In particular, battery and meteorological channels listed for the PV
models do not establish that those devices have the corresponding sensors.

## Concrete gaps to review together

These examples are documentary candidates, not newly enabled polling mappings.
Their register metadata and current topic coverage are in the CSV.

| Capability | Registers | Current gap |
| --- | --- | --- |
| Legacy device type | 30053 | Already identity/model on all devices; measurements/type exists only on inverter3. Add aliases for inverter1/2 while preserving the requested legacy type channel. |
| Rated and set active-power limits | 30231 / 30233 | Missing on inverter1/2; U32 FIX0 W, RO in all three lists. The set limit is an observed limit, not a Modbus write register. |
| AC active power | 30775 | Present on inverter1/3; missing on Storage. |
| Phase active power and voltage | 30777–30793 | Tripower/Storage lack these topics; Sunny Boy has L1 power/voltage but returned NaN previously. Listed L2/L3 entries do not prove physical phases on a single-phase device. |
| Phase AC currents | 30977 / 30979 / 30981 | Missing on all three; S32 FIX3. Distinguish from older total-current register 30795. |
| Grid frequency | 30803 | Missing on all three; U32 FIX2. |
| Reactive/apparent power and power factor | 30813, 30807–30819, 30949, 31221; total reactive power 31497 for Tripower and 30805 for Storage/Sunny Boy | Additional AC information is missing. Preserve the model-specific address difference. |
| Second DC input on Sunny Boy | 30957 / 30959 / 30961 | Current, voltage and power are missing on inverter3; analogous topics already exist on Tripower. |
| Battery current and voltage | 30843 / 30851 | Missing on Storage; S32 FIX3 A and U32 FIX2 V. |
| Battery energy counters | 31397 / 31401 | Missing on Storage; U64 FIX0, source Wh. Do not transfer the 30531/30537 kWh override to these registers. |
| Battery limits, cell voltages, BMS identity and states | 31377–31391, 31461–31495, 32221–32279 | Storage has substantial additional documentary coverage; repeated addresses/channels need battery-port association and live evidence. |
| Fine-resolution yield counters | 30513 / 30517 / 30529 / 30535 | Missing alternatives to the existing whole-kWh topics; preserve existing IDs/history and confirm independent counter units before adding. |
| Operating/feed-in duration | 30521 / 30525 and 30541 / 30543 | Missing 64-/32-bit alternatives; these are durations, unlike system time. |
| System time, event and derating information | 30193, 30211 / 30213 / 30215 / 30219 / 30247, 30559–30563 and 35377–35385 | Additional time, event codes/counters and operating-state observations are missing. |
| Readable configuration | All unmapped RW entries in the CSV | Includes power/reactive control, protection curves, communication and battery settings. Read coverage and writable command approval are separate work. |

## Ledger interpretation and remaining implementation

`mapped` means a bundled property exists. `missing` means the source documents RO
or RW but the inverter profile has no property. `write-only` has no normal read
mapping. `same_channel_registers` identifies potentially related representations;
it does not establish that they can be merged. `format_scale` records FIXn/TEMP
scaling only; RAW, DT, duration, FW, UTF8, TAGLIST and HIDDEN need their own semantic
review. `explicit_unit` intentionally stays blank when the source field is not an
unambiguous unit; a FIX format or parameter step size alone cannot supply one.
Source warnings against cyclical writes are retained in `source_access_note`.

`candidate_topic=registers/r<address>` is an address-stable **review placeholder**,
not an implemented topic or a final naming decision. Existing topics remain the
canonical mappings. All new classifications are pending: Andreas and the bridge
maintainer will decide basic/advanced/diagnostics together after reviewing the
capabilities. Existing channel groups have not changed.

The expanded goal is complete coverage of verified readable values and configurable
parameters, including readable observations of RW parameters. No subset is discarded
because it is expected to become advanced or diagnostics. Register 43090 is explicitly
inventoried but has no candidate value topic: inspect access-control read semantics
without publishing a Grid Guard code. Secrets have no ordinary telemetry mapping.
Write-only operations remain inventoried for separate command review. A documented
RW flag does not create `/set`; bounds, units, identity, authorization, readback,
uncertainty handling and interaction with Home Manager must be established first.
The inverter profile loader currently requires an empty command list.

Next, validate semantically coherent groups and then add file-based mappings with
model-specific units, enum/sentinel definitions and conservative polling intervals.
Record live supported/NaN/rejected results separately. Avoid giant reads spanning
undocumented gaps and avoid increasing every configuration poll to a fast measurement
interval. Mandatory identity checks and existing readiness behavior must survive
optional-channel filtering. Complete offline tests before a separately authorized
installation acceptance. No live write is authorized by this audit.

## Other installed devices

The [Home Manager NSD profile](HOME_MANAGER_MODBUS.md) already maps the documented
readable Unit 1/2 inventory, assignment table and delegated parameter templates.
Its write-only plant commands are intentionally absent from read polling. This does
not cover every portal preference or UDP meter quantity, and delegated mappings do
not replace complete direct inverter profiles. The present full row-by-row audit
covers the three inverters; Home Manager completeness remains based on the existing
NSD evidence and tests.

The supplied EVC22-3AC-20 operating manual and datasheet do not provide a matching
complete eCharger Modbus register table. Do not borrow inverter/Data Manager
addresses. eCharger local API/SEMP and portal completeness require a separate audit
against their metadata and responses, as recorded in the existing value catalogue.

The [official SMA interface guidance](https://www.sma.de/produkte/produktfeatures-schnittstellen/modbus-protokoll-schnittstelle)
and [official openHAB Modbus binding documentation](https://www.openhab.org/addons/bindings/modbus/)
were consulted. No existing openHAB Items, maps, rules, offsets, persistence or
private original files were modified.

Validation: full project lint passed (116 files), all 208 offline tests passed,
and `git diff --check` passed. These checks do not establish new live register support.

## Availability-first selection, 2026-10-12

Andreas subsequently clarified the priority: test documented readable addresses
once during PV production, then select useful Smart Home topics together rather
than publishing every address. The initial probe passed both PV identities but
returned valid 0 W on both devices; the full scan remains pending. Treat missing
values as unavailable in the tested state and exclude them from the first candidate
set; preserve the evidence for later battery/event-state review. Valid zero is
available; failed connections and partial scans are not unsupported-register proof.

The Sunny Boy [official input specification](https://manuals.sma.de/SBxx-1AV-41/de-DE/4177679243.html)
lists two independent MPP inputs. A second input may be unwired in this installation;
the documentary candidate does not establish actual wiring.

## Production scan results

The [completed 2026-10-12 production scan](MODBUS_AVAILABILITY_2026-10-12.md) and
[full availability matrix](modbus-availability-2026-10-12.csv) now provide direct
read evidence for all in-scope inverter addresses. This supersedes the earlier
pending-scan status without changing documentary counts or installed profiles.

## Subsequent profile extension

The coverage CSV is the documentary audit snapshot before profile expansion.
The [Sunny Boy L2/L3 implementation](REGISTER_VALIDATION.md#sunny-boy-l2l3-profile-extension-2026-10-12)
subsequently adds six mappings. The dated availability matrix remains the original
scan evidence; its existing-topic column is not rewritten as later implementation.
