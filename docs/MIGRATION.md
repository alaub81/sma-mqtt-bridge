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
