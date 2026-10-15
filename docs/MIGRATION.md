# Existing openHAB capability migration

> Current MQTT node/property IDs remove hyphens at the publication boundary. Internal profile and
> readiness keys keep their spelling; historical examples below may use the former IDs. See
> [compact IDs and display translations](CONFIGURATION.md#display-language-and-compact-channel-ids).

The goal is to preserve the user's complete existing integration, including calculations and automation, not only a selection of dashboard values.

## Files to provide

Place relevant exports under `private/incoming/openhab/`, keeping useful names/subdirectories:

The first inverter exports were provided under `private/things/`. Read that location too; leave those originals in place.

- `.things` definitions for all inverter Modbus bridges, pollers/data Things and the Home Manager.
- `.items` including units, profiles, transformations, channel links and Item metadata.
- Referenced `.map`, `.js`, `.scale`, JSONPath/XPath and other transformations.
- Rules/scripts that calculate totals, consumption, day counters or use/command SMA Items.
- Persistence configuration and restore-on-startup requirements.
- Relevant sitemaps/MainUI YAML; Item names matter for preserving widgets.
- MainUI-managed Things/Items/links as exports if they are not represented by text files.
- Inverter model/firmware information and Home Manager identity/firmware.

## Inventory received on 2026-10-10

| Source export | Device label in original comments | Active data Things | Pollers |
| --- | --- | --- | --- |
| `private/things/sma.things` | Tripower 8 (`inverter1`) | 14 | 6 |
| `private/things/sma.things` | Sunny Boy Storage 3.7 (`inverter2`) | 11 | 7 |
| `private/things/sma-sunnyboy.things` | Sunny Boy 3.0 (`inverter3`) | 16 | 6 |

Total: 41 active data Things, not 41 confirmed Item links. Commented-out duplicate definitions are excluded. Every configured data Thing is read-only in these exports; a label such as `Set_Max_Power` does not authorize writing it.

The TCP bridges specify port 502, unit ID 3 and three connection attempts. All pollers use `type="input"` (FC04), with refresh intervals between 3 and 180 seconds. Preserve poller start/length and zero-based addressing from the export; do not translate an SMA register address a second time. The first two profiles use `int32`; the third mixes `int32` and `uint32`. Validate those choices and invalid sentinels without silently correcting the original configuration.

The five referenced transforms were subsequently supplied under `private/transform/` and inspected without modifying them:

| Transform | Nonnegative numeric input | Negative input |
| --- | --- | --- |
| `smalimit.js` | `parseFloat(input)` | `0` |
| `smalimit_undef.js` | `parseFloat(input)` | `UNDEF` |
| `smalimit1000.js` | `parseFloat(input) / 1000` | `0` |
| `smalimit100.js` | `parseFloat(input) / 100` | `0` |
| `smalimit10_undef.js` | `parseFloat(input) / 10` | `UNDEF` |

These are legacy filtering rules, not validated device-sentinel definitions. They do not explicitly guard nonnumeric input. Device-specific invalid values must be rejected before applying any legacy numeric transformation; genuine signed measurements must not silently be treated as unavailable or changed to zero. Record any compatibility filtering separately and reconcile it with the existing Item links.

Additional supplied files include `sma_undef.js` (numeric zero becomes `UNDEF`), unfiltered division transforms, status/type maps and `smagrid_consumption.js` / `smagrid_feedin.js`. The latter divide by 1000 and add installation-specific cumulative-energy offsets; negative input becomes zero. Keep those offset values private. Their actual dependencies and necessity are pending the Item/rule inventory; do not assume that a new bridge counter starts at the historical offset or that these are daily calculations.

Read-only MainUI access became available on 2026-10-10. The inventory below confirms existing Item types, links, selected metadata and several calculation sources. A complete audit of all rules, link profiles, metadata, persistence definitions and UI dependencies is still pending. File-managed sources may need private exports if their complete definitions are not exposed by the UI.

The coverage ledger includes one row per active data Thing. MainUI confirmed 34 inverter Item links; seven register rows still have no identified Item. Actual links use both `:number` and `:string`, so the originally derived UIDs have been reconciled where confirmed. Homie topics remain proposals. Neither an ONLINE indication in openHAB nor a populated Item validates the future Python adapter or every source register.

The user clarified that only the existing Things information is available; no additional validated profiles are expected from another chat. Build and verify profiles from these exports and matching official SMA documentation. The sanitized [machine-readable inventory](../reference/inverter-things-inventory.json) preserves all 41 active channels and 19 pollers, including raw types, offsets, transformations and intervals. It omits private addresses/labels and is deliberately rejected as a runtime polling profile. Preserve all existing configured channels and add confirmed supported measurements after the profiles are reconciled. Missing registers and private configuration parameters must not be guessed or published indiscriminately.

References: [official openHAB Modbus documentation](https://www.openhab.org/addons/bindings/modbus/), [Item configuration](https://www.openhab.org/docs/configuration/items.html), [persistence configuration and rule extensions](https://www.openhab.org/docs/configuration/persistence.html).

### Documentation and authenticated portal inventory

The German [value catalogue](WERTEKATALOG.md) records the complete supplied register/parameter inventories, unit gaps, access restrictions and proposed MQTT topics. The 45 wallbox/portal ledger rows now have explicit source/topic mappings, including staged input Items that remain in openHAB. Their status remains pending; no runtime migration is claimed. Existing inverter transform notes and proposed topics are preserved.

The authorized read-only ennexOS inspection confirmed STP8.0-3AV-40 / 4.10.10.R, SBS3.7-10 / 4.07.31.R and SB4.0-1AV-41 / 4.10.10.R, plus Home Manager 2.19.1.R and eCharger 2.06.37.R. The third inverter's old comment differs from the portal model. Local host/identity mapping is still required. The supplied 198-row Sunny Boy list is for -40 firmware 01.03.24.R, so its types/units are comparative evidence rather than an approved profile for any of the installed devices. Obtain matching profiles before extending polling or changing signed decoding.

This ennexOS inspection is separate from the MainUI inventory received later below. Portal access alone does not validate openHAB links, calculations or persistence. The shared value catalogue now incorporates the 34 inverter Item links, four Home Manager Items and ten derived capabilities from that inventory; all 100 ledger rows are retained. No capability is marked runtime-migrated based on either browser inventory.

The current portal CSV exports additionally supplied 458 parameter rows for the five installed devices (55 Home Manager, 109 Tripower, 164 Storage, 108 Sunny Boy, 22 eCharger). The catalogue contains only channel/name/unit/access metadata, without current values or export identity headers. Export access is RO throughout; this does not override separate local API rights or establish a portal setter. These parameter channels still need verified API endpoints and do not provide missing Modbus addresses/types.

Credentials and tokens must not be copied into public fixtures. The incoming folder is excluded from Git and Docker. Preserve original exports there as read-only references; create sanitized derived examples separately.

## Read-only MainUI inventory on 2026-10-10

The inverter search returned 42 Items: 34 linked measurements/status Items (14 + 11 + 9), three aggregate Items and five equipment/location groups. The seven configured inverter3 data Things without an identified Item are device type, maximum power, set maximum power, grid import, grid export, phase L1 power and phase L1 voltage. Preserve these configured registers while their device support and any links outside the search are checked.

The inverter3 equipment label is **Sunny Boy 4.0**, whereas its supplied Thing comment says **Sunny Boy 3.0**. Neither label establishes hardware identity. Reconcile this discrepancy with the hardware inventory being prepared in the other chat.

During this inventory, the shared [values catalogue](WERTEKATALOG.md) became available with a reported portal identity check: STP8.0-3AV-40 / 4.10.10.R, SBS3.7-10 / 4.07.31.R and SB4.0-1AV-41 / 4.10.10.R; Home Manager firmware 2.19.1.R. This supports the UI's 4.0 label. Local Modbus endpoint identity and suitable full register profiles remain to be reconciled; this browser pass did not independently inspect the portal.

MainUI confirmed quantity types for power, energy, DC voltage/current, temperature and battery percentages. Explicit unit metadata exists for the inspected inverter1/inverter2 quantity Items; inverter3 often relies on defaults/display formatting. Status Items are Strings, including inverter3 Items linked to numeric channels. `sma.map` was confirmed in the link profiles for inverter1 status, inverter3 status/contactor and inverter2 battery status. Selected inverter1/inverter3 yield links use the Standard profile. Register scale, Item unit and formatting must therefore be reconciled separately; displayed rounded energy is not proof of raw precision.

The Home Manager has four linked Items: `SMAEnergyMeter_BezogeneEnergie` (`energyIn`), `SMAEnergyMeter_EingespeisteEnergie` (`energyOut`), `SMAEnergyMeter_BezogeneLeistung` (`powerIn`) and `SMAEnergyMeter_EingespeisteLeistung` (`powerOut`). Both energy links use a configured **offset profile**. Preserve those private offsets and historical continuity; the supplied older JavaScript offset transforms alone do not describe the currently active configuration. Phase measurements are additional coverage, not existing linked Items established by this inventory.

### Calculations and automation to preserve

| Existing capability | Inspected behavior | Dependencies |
| --- | --- | --- |
| `inverterActivePower` | PV1 + PV3, updated every 5 seconds | Existing rule also forwards the value to a Shelly display; Smart-Grid consumes this Item |
| `inverterDailyYield`, `inverterTotalYield` | PV1 + PV3 day/total counters, every 5 minutes | Existing Item names, units and persistence groups |
| `TotalPowerConsumption` | PV1 + PV3 + battery discharge + grid import − grid export − battery charge, every 15 seconds | Negative results are skipped, retaining the previous value; source freshness requires separate handling |
| `PowerConsumptionBatIncl` | Same calculation plus battery charge | Updated only for a nonnegative result |
| `Wallbox_Tagesverbrauch` | Shelly cumulative counter `deltaSince` local midnight, on counter change | Default persistence service, Shelly counter and quantity/unit semantics |
| `Strom_Tagesverbrauch_Number_Result` | InfluxDB Flux integration of `TotalPowerConsumption` since today; 10-second mean windows, integral per hour / 1000 | Europe/Berlin; query every 300 seconds; historical measurement name |
| `Strom_Tagesbezug` | Same Flux integration using `inverter1PowerDrawn` | Europe/Berlin; query every 300 seconds |
| `Strom_Durchschnitt_Tagesverbrauch_Number_Result` | Daily maxima of day consumption over seven completed days; exclude days with persisted `Wallbox_Switch = 1`; average the remaining days | Query every 14400 seconds; Berlin timezone option is commented out; day-boundary alignment remains open |
| `TotalPowerEarnings` | Cumulative feed-in energy multiplied by a private installation tariff, every 30 minutes | Home Manager export counter/offset and Item metadata |

The active consumption rule calls `present()`. Its separate `average()` function is not called by the inspected script. Do not mistake that unused function for the active calculation. Likewise, `Tagesstromverbrauch` is disabled and references `DailyEnergyConsumption`, for which the Item search returned no result; it is not the active house-day calculation.

### Requested bridge calculations: feasibility review, 2026-10-14

Andreas requested daily grid import, daily grid export, daily household energy
and household total consumption in the bridge where practical. This review uses
the existing MainUI inventory above and bundled profiles; it adds no runtime
calculation or migration acceptance.

| Requested value | Available bridge inputs | Remaining equivalence decision |
| --- | --- | --- |
| Daily grid import | Inverter1 grid-import power in W; Home Manager import counter in kWh | Existing calculation integrates persisted inverter1 power. A Home Manager midnight counter difference is an alternative method, not an equivalent implementation established by this review. |
| Daily grid export | Inverter1 grid-export power in W; Home Manager export counter in kWh | Current openHAB formula, Item and persistence source are not recorded in the inspected baseline; obtain them before selecting integration or counter differences. |
| Daily household energy | Inputs for the existing household-power balance | Current result integrates persisted `TotalPowerConsumption` with 10-second mean windows in InfluxDB. An online integrator has different sampling and outage behavior and cannot recover historical gaps without additional evidence/data. |
| Household total consumption | PV1/PV3 active power, Storage charge/discharge power, inverter1 grid-import/export power, all in W | Confirm that the requested label means instantaneous `TotalPowerConsumption`, rather than cumulative energy or `PowerConsumptionBatIncl`. Preserve the existing choice of grid source and negative-result policy. |

The smallest prospective runtime step is the stateless household-power balance,
once its Item/meaning is confirmed. Require enabled source roles, matching units
and fresh valid inputs; do not use last-known retained MQTT values as current
inputs, substitute missing inputs with zero, or clamp a negative balance to zero.
The existing openHAB rule skips negative results and keeps its prior value;
publication and internal freshness must be considered separately. Measurement
skew and the existing signed-value versus legacy-transform differences need a
focused comparison before switching ownership.

Daily calculations require an explicit `Europe/Berlin` calendar boundary,
including 23/25-hour DST days, and a documented method per value. A counter-based
method needs persisted date/baselines and identity/reset guards; absent midnight
baselines, first starts partway through a day and outages across midnight must
not invent a complete-day result. A power integrator must define sample gaps,
midnight splitting and restart continuity. Existing per-inverter daily yields
alone do not establish household daily energy because battery and grid flows
also contribute. Fixed historical counter offsets cancel only for unchanged
counter baselines; existing openHAB offsets and histories stay in place.

Before implementation, obtain the four current rules/queries and exact Item
names/units, then choose the compatible method and test midnight, DST, resets,
missing/stale samples and restart behavior. Publish any new measurements in
parallel first and preserve existing Item identities, rules and persistence until
comparison is accepted. Official background: [openHAB persistence](https://www.openhab.org/docs/configuration/persistence)
and [units of measurement](https://www.openhab.org/docs/concepts/units-of-measurement.html).

### Counter-based energy design clarified, 2026-10-14

Andreas clarified that all four requested outputs are energy counters in kWh,
including household total consumption. Exact reproduction of the old InfluxDB
queries is not requested: design a new calculation from available cumulative
device counters first. The preceding feasibility table preserves the historical
comparison; its instantaneous-household-power assumption and request for all old
queries no longer define this new feature. Implementation remains deferred while
the calculation is discussed.

For an aligned interval, define each delta as `counter(end) - counter(start)`:

- Daily grid import: Home Manager import counter now minus its midnight baseline.
- Daily grid export: Home Manager export counter now minus its midnight baseline.
- Household energy candidate: PV1 delta + PV3 delta + grid import delta
  - grid export delta + battery discharge delta - battery charge delta.
- Daily household energy uses the same balance from local midnight; cumulative
  household energy uses a shared commissioning baseline and an optional verified
  opening reading, with persisted continuity across restarts.

For example, 20 kWh PV, 6 kWh imported, 8 kWh exported, 5 kWh battery discharge
and 7 kWh battery charge give `20 + 6 - 8 + 5 - 7 = 16 kWh`, conditional on matching
AC measurement boundaries. Do not sum unrelated lifetime counters directly:
their initial dates, offsets and stored battery energy need not align. The
Storage yield counter is not a third PV generator and must not be counted twice.
Wallbox and other consumers downstream of the household meter already contribute
to household energy; adding their counters again would double-count them.

Two evidence gaps limit the household formula. Published PV yields currently
have whole-kWh resolution; float output would not create finer source precision.
Previously audited Wh-resolution alternatives require independent unit/live
verification before adding mappings. Battery counters 31397/31401 have verified
Wh encoding but their AC/DC boundary remains unverified; the official Storage
V13 rows only label them Battery charge/discharge. Do not certify the candidate
as AC household consumption or infer a loss correction from the cumulative return
ratio. Confirm compatible Storage AC energy flows, or assess a separately labelled
power-integrated alternative, before choosing the final household method.

Grid-counter differences are the first independently supported part. Calendar
baseline, reset, freshness and missing-data rules from the preceding review still
apply. A first partial day must be labelled partial/unavailable, and an outage
across midnight cannot be assigned exactly to separate days without boundary data.
The later optional implementation below uses existing observations without new polling.

### Current PV inventory and aggregation implementation, 2026-10-14

The requested current read-only installation inventory is now available in
[PV_AGGREGATION_DESIGN.md](PV_AGGREGATION_DESIGN.md), with Item, Homie-link, rule,
query and comparison CSVs. It includes the previously missing
`Strom_Tageseinspeisung` Item/query and confirms that existing
`TotalPowerConsumption` is W. The newly requested household lifetime counter
remains kWh; Andreas additionally requests current household power and generic
PV/storage sums. Explicit contributor roles and a separate logical Homie plant
device are implemented locally, disabled by default, and await deployment.
See [configuration](CONFIGURATION.md#plant-aggregates-and-energy-state) for settings,
coverage diagnostics and energy-balances.json recovery. Profile host overrides
need explicit contribution mappings. Existing Items, links, rules and persistence
remain active until each comparison passes. Household kWh is deliberately blocked
with the bundled unverified battery measurement boundary; synthetic AC tests
establish software behavior only.

All 109 listed rules were read and 29 relevant rules recorded. This updates
observed dependencies without accepting dynamic-name/imported-code coverage,
controller equivalence, migration or measurement agreement. Existing maps,
private offsets, UI and persistence must still be preserved. The original
100-row ledger stays intact; the supplementary comparison manifest prepares
future Grafana validation rather than claiming a completed dashboard.

The Wallbox charging-state rule infers `Wallbox_Switch` from a Shelly power threshold. That switch also determines which days enter the household consumption average. Preserve this dependency; do not automatically substitute the eCharger's charging enum without checking equivalence.

Smart-Grid rules consume exact mapped contactor strings (`Geschlossen (Cls)` / `Offen (Opn)`), battery SOC, PV/feed-in/consumption history and forecasts. They control the heat pump and other consumers. Their complete timer, seasonal threshold and trigger audit remains pending. These rules should initially stay in openHAB with their existing source Item names; supplying measurements through Homie does not require moving household control into the bridge.

### Persistence continuity

InfluxDB is the configured default service. Relevant inspected policies include:

- `pEveryUpdate30s*`: `everyUpdate`, `restoreOnStartup`, `every5min`; filters `30seconds`, `NULL_UNDEF`.
- `pEveryChangeCron*`: `everyChange`, `restoreOnStartup`, `every5min`.
- `pEveryChangeCron15min*`: `everyChange`, `restoreOnStartup`, `every15min`.
- `pEveryChange*`: `everyChange`, `restoreOnStartup` (multiple policy entries exist).

Preserve Item names, persistence groups and database measurement continuity when replacing channel links. Complete filter/cron definitions, all aliases, startup ordering, missing-history behavior and timezone alignment still require review. The official [persistence documentation](https://www.openhab.org/docs/configuration/persistence.html) distinguishes storing group values from storing group members and explains default-service selection and restore behavior. The [SMA Energy Meter binding documentation](https://www.openhab.org/addons/bindings/smaenergymeter/) remains the reference for comparison with the future local meter adapter.

No settings were saved, no rules were executed manually and no device commands were sent during this inventory. Private addresses, account identifiers, offsets and tariffs are omitted here.

## Coverage ledger

`migration-coverage.csv` starts with every non-group Item from our current wallbox and portal packages. Python read support is recorded separately from live acceptance. Extend it with every incoming inverter/Home Manager Item and derived capability.

Required mapping fields: original Item/channel, data source, source register/channel, type/unit, scaling/invalid handling, read/write capability, proposed Homie topic, dependent rules/widgets/persistence, verification evidence and migration status.

The bridge may publish all required raw values while an existing openHAB rule continues to calculate a derived value. Record that explicitly. A capability counts as migrated only after units, timestamps, behavior and dependencies are checked.

## First Python read implementation, 2026-10-10

All 100 ledger rows are preserved. `offline-read-implemented-pending-live` records a read path with synthetic coverage, not completed migration. `offline-read-tested-pending-live` covers the four meter values. `pending-validated-profile` keeps all 41 inverter channels blocked until complete model/firmware/identity mappings are available. `pending-local-unit-verification` keeps local plan energy/stop delay unavailable without explicit matching units. Commands, staging, convenience outcomes and additional diagnostics retain their outstanding status.

SEMP reproduces baseline topics, vehicle/health/approval maps and session Wh-to-kWh conversion. Local API provides settings and additional measurements; when both are enabled, property ownership is separated. With SEMP disabled, baseline reads use the API. Portal preferences retain `portal/` topic IDs and are observations rather than measured grid share. Every Homie property is read-only.

Runtime diagnostics are `diagnostics/<source>-status` and `diagnostics/<source>-last-success`, except portal uses `portal/status` and `portal/last-success`. Status is `init`, `ready`, `stale`, `error`. Convenience diagnostics such as option summaries, command outcomes and aggregate adapter status are not yet reproduced; their ledger rows remain pending. Existing openHAB calculations, offsets, persistence, String maps, staging rules and control remain in place. Do not remove old links or rename Items before parallel-value and dependency acceptance.

No direct installation reads or writes were executed during implementation. Private original exports and host MQTT configuration remain unchanged.

## First installation publication, 2026-10-10

All 100 ledger rows remain. The three model profiles now reproduce all 41 existing inverter channels, with official type/unit/sentinel corrections and original per-poller intervals. Local identity checks matched the configured hosts and private serial guards. The actual broker retained 39 measurements plus nine inverter identity values. Sunny Boy 30777/30783 returned SMA NaN and remain unavailable pending daytime comparison. See REGISTER_VALIDATION.md.

SEMP publishes the existing baseline, confirmed enum/boolean settings and additional raw diagnostic/setpoint channels. Settings ownership belongs to API when enabled, otherwise SEMP. Energy/delay properties with engineering units remain unavailable without confirmed local metadata; clearly named raw properties allow inspection without guessed units. Measurement and setpoint source timestamps are checked. The private location label is not telemetry.

The Mac read service has published 69 values across the three inverters and eCharger after expanding SEMP. MQTT certificate verification was explicitly disabled at Andreas' request after an untrusted self-signed chain blocked the real handshake; TLS encryption and account authentication remain active. Local wallbox certificate/name verification passed. Local API/portal credentials are still missing, and Home Manager is intentionally disabled until Pi-network testing. Every Homie property remains read-only. No old openHAB links/rules/offsets/persistence were changed, no device write was sent and no capability is marked fully migrated.

## Authenticated read acceptance, 2026-10-10

Local API and portal credentials are now configured privately and both sources are explicitly enabled. Fresh local API current, voltage and total-energy readings passed; the observed live timestamp field is `time`. API owns settings while SEMP retains baseline measurements. Local plan energy and stop delay remain blocked because their parameter metadata has no unit. The isolated API read did not provide frequency, session energy or health.

Portal authentication and device checks passed. Minimum PV preference, allowed grid preference and edit permission were verified on the actual broker together with selected local API values. All 100 ledger rows remain, with read-publication evidence added only for verified properties. This does not accept staged commands, writable functions or openHAB dependencies. Portal polling remains zero; an explicitly requested one-shot refresh was used and values expire under the configured freshness limit.

## Optional Home Manager Modbus source, 2026-10-10

The four existing Home Manager meter properties retain `measurements/power-import`, `power-export`, `energy-import`, and `energy-export` under the same Homie identity when selecting `modbus-tcp`. Modbus U32 Wh counters are converted to kWh; the existing active openHAB offset profiles remain external and must not be duplicated by historical JS offsets. The new source adds documented status/time/identity, assignment and delegated parameter observations. It does not accept the existing four ledger rows as live-migrated or change their previously pending installation acceptance.

All additional properties remain read-only; model-specific rejection and Grid Guard restrictions are explicit availability gaps. Complete topic/register/unit mappings and acceptance steps are in [HOME_MANAGER_MODBUS.md](HOME_MANAGER_MODBUS.md). No existing Item link, calculation, charging controller, persistence group or private export was changed for this implementation.

## Plan and PV command milestone, 2026-10-10

Local staging can submit a combined JSON plan to commands/plan/set only on explicit apply. Do not bind individual plan inputs to device setters. Target mode 4720 is activated only after both plan values are confirmed. Portal minimum PV uses portal/pv-minimum/set behind the independent portal write gate; allowed grid share remains read-only. These paths are offline-tested, not migrated/accepted live. Existing openHAB staging, control rules, offsets and persistence remain in place until explicitly switching command ownership; do not run duplicate command rules. Full protocol and uncertainty recovery are documented in CONFIGURATION.md.

## Last-known observations and inverter night availability

On the user's request, invalid or expired individual measurements now leave the last retained value
unchanged, including MQTT reconnect and container restart. openHAB can therefore continue displaying
the last observation. No missing value is converted to zero. Internal freshness checks and command
readback still require current valid samples; retained values do not prove current device state.
Explicit source/property retirement continues to remove owned retained topics.

All three bundled inverter profiles use their fresh measurements/status for readiness rather than
production or battery power. Missing nighttime power alone no longer publishes Homie alert.
Communication errors or an expired required status still affect availability. The status channel
continues to report device warnings/errors independently. Existing custom profiles and explicit
READY_PROPERTIES overrides must be reconciled separately. Production night/day/outage acceptance
remains pending; these changes are verified through offline regressions.

## Storage energy unit correction, 2026-10-11

Storage (`sma-sbs3-7-10`, inverter2) day/total yield now publishes kWh instead of Wh. This deliberately overrides the official V13 labels based on the user's installation comparison; see REGISTER_VALIDATION.md. Raw numbers, scale 1, U32/FIX0 and Homie integer remain unchanged. No division or multiplication is applied.

Rebuild/recreate the bridge to publish corrected retained `$unit` metadata for `measurements/dayyield` and `measurements/totalyield`. Apply the same correction to any host profile override. In openHAB, keep the existing Item names, groups, persistence and links; use `Number:Energy` with Unit metadata `kWh` and State Description pattern `%.0f %unit%` (or more display decimals if desired). Unit metadata controls quantity conversion; a display pattern alone does not correct a wrong source unit. Remove any workaround that compensates for the old Wh label by scaling the value. Check the next fresh update against the broker (raw 2 must become 2 kWh). If channel metadata remains stale, disable/re-enable the affected Homie Thing and verify again before considering rediscovery; preserve Item links.

Historical samples stored under the wrong Wh interpretation are not repaired by this change. Determine the affected time window and actual persisted units before any database correction. Existing correctly recorded Modbus history must remain unchanged. Sources: [Homie binding](https://www.openhab.org/addons/bindings/homie/), [units of measurement](https://www.openhab.org/docs/concepts/units-of-measurement.html).

## Maximum charging power command, 2026-10-11

The local API now reads `Parameter.Inverter.WMaxIn` as integer W and exposes
`settings/maxchargepower` under the existing charger identity. German discovery label:
**Maximale Ladeleistung**; openHAB suffix `settings#maxchargepower`, Number:Power with
Unit W and `autoupdate=false`. [Setup instructions](../openHAB/openHAB.md#maximum-charging-power)
cover input bounds and explicit submission. This adds a setting without replacing
existing Items, rules, SEMP control or persistence; all 100 migration ledger rows remain.

WebUI mapping/unit and current 4500–22000 W rights/bounds have read-only installation
evidence. The setter is offline tested behind existing gates with confirmed readback
and durable uncertainty protection. Physical limiting and phase-switch behavior remain
unaccepted; no device setting or openHAB instance was changed. See
[the investigation](ECHARGER_POWER_LIMIT.md) for why a 4.5 kW cap alone does not promise
single-phase operation and why 4000 W is currently rejected.

## Wallbox total-energy unit update, 2026-10-11

The Python local API counter `measurements/totalenergy` now matches the original migration
mapping: source Wh divided by 1000, published float kWh. Both primary and fallback channels
use the same conversion; zero stays valid and stale/invalid samples remain unavailable.
Channel/Item identity is unchanged. Session energy was already kWh. Follow the
[deployment and history procedure](../openHAB/openHAB.md#wallbox-total-energy-migration-to-kwh)
before changing persisted unit assumptions. Correct kWh history must not be rescaled;
mixed Wh/kWh series require a verified timestamp boundary and service-specific treatment.
No persistence data, legacy offsets, original exports or device counters were changed.
Live readback and installation history inspection remain pending.

## Sunny Boy explicit L2/L3 extension, 2026-10-12

The bundled Sunny Boy profile now adds read-only measurements/powerl2, powerl3,
voltg2, voltg3, currentl2 and currentl3. Existing L1 IDs and their register meanings
are preserved; do not transfer their history or reinterpret their values as L3.
After deploying the extension, create/link new phase-specific Items as needed.
Power uses W, voltage V and current A. L2 may have discovery metadata without a
measurement payload because the installation scan returned SMA NaN. The L3 scan
values do not by themselves certify publication or new openHAB links.

The original 100-row capability ledger remains the original integration baseline;
new phase properties are an extension, not silently substituted migration rows.
The [official Homie binding documentation](https://www.openhab.org/addons/bindings/homie/)
was consulted; no live Item links, transformations or persistence were changed.

## Selected inverter additions, 2026-10-12

Read-only type/limits now share measurements/type, maxpower and setmaxpower on all
three profiles. New measurements/frequency uses Hz on all devices. Tripower adds
currentl1/currentl2/currentl3 (A); Storage adds currentl1 (A), activepower (W),
batterycurrent (A) and batteryvoltage (V). These are additive properties outside
the original capability ledger. Old Items, quantities, maps, counter offsets,
links and persistence remain unchanged. Preserve signed AC/battery observations;
no battery charging-state convention is inferred from sign alone.

## eCharger phase active power addition, 2026-10-12

Local API now provides measurements/powerl1, powerl2 and powerl3, each float W and
read-only, from GridMs.W.phsA/B/C. Existing measurements/power remains the total
charging-power observation with its original source ownership. Keep existing Items,
links and persistence; new phase Items may use Number:Power with Unit metadata W.
No existing aggregate is replaced with a phase sum. The new properties follow the
existing API measurement basic default and do not require an advanced flag.
Rebuild/recreate the service to load the change, then verify broker metadata/values
and new Item links separately. No running bridge or openHAB instance was changed.

## Sunny Boy DC input B addition, 2026-10-12

Three additional basic read-only properties publish as `measurements/currentbinput` (A), `voltagebinput` (V), `powerbinput` (W). Input A IDs and history remain unchanged. Valid zero is published; missing or SMA-NaN observations preserve last valid retained values. These properties are added after v0.3.3 and need a subsequent deployment for live acceptance.

## Selected counters and derating channels, 2026-10-12

New additive topics are `measurements/operatingtime` and `feedintime` (integer s,
Advanced) plus `diagnostics/deratingreason` (enum, Basic since 2026-10-13) on all three
inverters, and `measurements/batterychargeenergy`/`batterydischargeenergy` (float
kWh, Basic) on Storage. Published IDs are compact; internal profile IDs retain
hyphens. Existing Items, yield counters, offsets and history are unchanged.
For new Item links use the published units and preserve signed/invalid semantics
of other properties. Device-GUI counter-growth/reset and live MQTT/openHAB
acceptance remain separate steps; no deployed configuration was modified.

## Wallbox daily energy extension, 2026-10-14

The optional plant source now adds wallbox/dailyconsumption and
house/dailyconsumptionwithoutwallbox in kWh when the local eCharger API is enabled.
It uses the existing total-energy counter, not the session counter, and subtracts
Wallbox energy in the household counter vector over a common covered day.
The house result retains the battery AC-boundary gate; Wallbox daily energy is
independent. Initial partial days and missing/reset/stale inputs remain explicit.
No new live Item, persistence policy, Shelly history, seven-day exclusion rule or
control ownership was changed. Existing power-integral day values need a measured
comparison against this counter method. See the [configuration contract](CONFIGURATION.md#wallbox-daily-consumption).

## Wallbox day-topic ownership correction, 2026-10-15

At Andreas' request, Wallbox daily consumption now belongs to the configured
eCharger Homie identity: measurements/dailyconsumption, float kWh, read-only.
The Wallbox day-status/snapshot-time diagnostics move with it. Household energy
without Wallbox remains on the plant. Existing activation requirements are unchanged.
The persistent wallbox account is reused without a new baseline. Owned old plant
wallbox topics/diagnostics retire through the existing manifest. Preserve the
openHAB Item/history when relinking an already created day Item; the new channel
suffix is measurements#dailyconsumption under the existing eCharger Thing.
Homie discovery/channel structure was checked against the official
[openHAB Homie binding documentation](https://www.openhab.org/addons/bindings/homie/).
No live Item/link/persistence change or deployment is included in this correction.

## Household lifetime topic removed, 2026-10-15

Andreas no longer requires house/totalconsumption. The inventory identifies it as
a new bridge-baseline counter with no concrete existing openHAB Item counterpart;
the old TotalPowerConsumption Item is a power value in W. The lifetime topic and
its discovery are removed; household daily energy and daily energy without
Wallbox remain. Existing state fields and legacy opening-value configuration are
retained for compatibility, so daily baselines do not reset. The existing ownership
manifest retires the old retained topic/metadata when the new build runs. No live
openHAB Item, link or history is deleted. Official Homie binding documentation was
consulted; no target deployment is implied by the offline retirement test.
