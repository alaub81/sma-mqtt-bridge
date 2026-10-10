# Collected SMA integration findings

Evidence date: 2026-10-10. This document distinguishes observed behavior from planned or unverified capabilities. See `private/CONTEXT.local.md` for installation-specific addresses and identifiers.

## Scope chosen by the user

Create a self-hosted Docker SMA-to-Homie-MQTT bridge based on the existing BMW-MQTT-Bridge development foundation. Cover three SMA inverters already read via Modbus, Sunny Home Manager 2.0 and SMA eCharger. Match the full existing openHAB integration after its configurations are provided. Keep Home Manager as charging controller.

Use local sources for inverter/meter measurements and wallbox settings. Use the existing ennexOS portal web API for the minimum PV percentage. The user explicitly rejected paying for SMA Developer APIs. A completely local setter for the SMA PV-percentage slider has not been confirmed.

Each source must be independently configurable and enabled/disabled. The chosen environment prefix is `SMAB_`; all operational options need defaults and ENV overrides so only installation basics are necessary. The private `smab.env` lives in the repository root; `smab.example.env` documents every variable. Optional JSON configuration, profiles, certificates, password files and persistent state belong under `./data/sma-mqtt-bridge/`. See [the binding configuration contract](CONFIGURATION.md). Compose prepares this layout; the Python configuration loader and first read runtime are offline tested; hardware acceptance remains pending.

## Known devices and software

- openHAB 5.2.1.
- SMA eCharger EVC22-3AC-20, firmware 2.6.37.R; distinct from the older EV Charger models.
- Sunny Home Manager 2.0, portal-reported firmware 2.19.1.R.
- Read-only ennexOS inventory confirmed STP8.0-3AV-40 (4.10.10.R), SBS3.7-10 (4.07.31.R) and SB4.0-1AV-41 (4.10.10.R). The original third-device comment says Sunny Boy 3.0; preserve that historical label until local Modbus identity/host mapping is reconciled. The exports contain 41 active data Things across 19 pollers.
- Sunny Portal powered by ennexOS, normal App/Portal account.
- Local wallbox administrator/installer access exists separately from portal credentials.

## Confirmed local wallbox protocol

The working reference is local openHAB package v2.1. The user confirmed successful local authentication, writable option discovery, and a status-light write/readback. Later the user reported that all values needed from the current packages were available. Do not interpret that as every individual command having been independently hardware-tested.

- Authentication: `POST /api/v1/token`, separate local credentials and short-lived Bearer token.
- Parameter catalog/current values: `POST /api/v1/parameters/search` with a query for component `IGULD:SELF`.
- Live values: `POST /api/v1/measurements/live` for component `IGULD:SELF`.
- Parameter write: `PUT /api/v1/parameters/IGULD:SELF`; reproduce the exact reference payload and metadata checks.
- Public SEMP: `/SEMP/` and `/SEMP/Parameters`, XML namespace `http://www.sma.de/communication/schema/SEMP/v1`.

The uploaded local parameter catalog contains 85 metadata entries. SEMP parameter output contained 25 channels. Neither provided a confirmed minimum-PV-percentage parameter. `Setpoint.PlantControl.Inverter.WModCfg.WCtlComCfg.WSptMinNom` is a power setpoint; do not interpret it as PV/grid mix.

## Local writable option inventory

The user's device reported these options writable:

| Option | Channel |
| --- | --- |
| Charging mode | `Parameter.Chrg.ActChaMod` |
| Charging release | `Parameter.Chrg.ChrgApv` |
| Approval required | `Parameter.Chrg.ChrgLok` |
| Stop when vehicle is full | `Parameter.Chrg.StpWhenFl` |
| Delay before ending | `Parameter.Chrg.StpWhenFlTm` |
| Permanent cable locking | `Parameter.Chrg.CblLok` |
| Status-light brightness | `Parameter.Sys.DevSigBri` |
| Ambient brightness | `Parameter.Sys.AmbLghtBri` |
| Ambient enabled | `Parameter.Sys.UseAmbLght` |
| Planned target energy | `Parameter.Chrg.Plan.En` |
| Planned end time | `Parameter.Chrg.Plan.StopTm` |

Reference mode mapping: 4718 fast, 4719 optimized PV, 4720 target charging, 4721 stop. Validate supported choices from device metadata rather than applying this model's enums universally. Target energy is an amount to charge for a plan, not vehicle battery state of charge. Preserve source units and explicit time zones; verify API energy scaling before porting conversions.

Additional catalog entries include current limits, phase configuration, communication configuration and installer settings. Do not automatically offer all editable catalog entries as user-facing MQTT writes.

## Confirmed ennexOS portal protocol

Working reference: portal extension v1.0.2. User initially entered the wrong password; corrected credentials work. This is the web application's API, not the paid SMA SmartHome/Monitoring developer service.

- Portal: `https://ennexos.sunnyportal.com`.
- Login realm: `https://login.sma.energy/auth/realms/SMA`.
- Public portal client ID: `SPpbeOS`, not a secret or separately issued developer credential.
- OAuth authorization-code flow with PKCE and refresh tokens. The current reference automates the login form; MFA/extra login challenges are not supported and must be reported clearly.
- Redirect: `https://ennexos.sunnyportal.com/dashboard/initialize`.
- API base: `https://uiapi.sunnyportal.com/api/v1`.
- Read: `GET /plants/{plantId}/devices/{deviceId}?menuItemType=ViewDeviceProperties`.
- Write: `PUT /plants/{plantId}/devices/{deviceId}/optionalenergydemand`.

Observed `optionalEnergyDemand` fields: `isOptionalConsumer`, `pvSurplusOnly`, `minPvPercentage`, `feedInLimitation`, `priceLimit`, `usePriceLimit`. The observed normal PV configuration had `isOptionalConsumer=true`, integer PV percentage, `pvSurplusOnly=null`, `priceLimit=null`, `usePriceLimit=false`.

The write payload contains only `minPvPercentage`, `pvSurplusOnly`, `usePriceLimit`, and `priceLimit`; preserve the latter three. Do not overwrite unrelated feed-in limits. User-visible allowed grid share is `100 - minPvPercentage`, a charging preference rather than measured grid share.

Identity guard in the reference checks plant/device IDs, `productTagId=19143` and consumer type `EVehicle`. Writable permission is presence of `_links.ui_Edit_OptionalEnergyDemand`; the value can legitimately be an empty array. Do not require a nonempty link collection.

The reference checks whole-number percentages 0-100, refuses writes while cost-limit or the special `pvSurplusOnly=true` option is active, and reads the setting back. It sends no commands on startup, no writes merely from moving the staging slider, and performs no background polling. After an ambiguous write response it reports uncertainty rather than retrying the write automatically.

## Inverters and Home Manager

The supplied Modbus Things are the first part of the acceptance baseline. The five referenced transforms and additional SMA maps/energy transforms have now been supplied under `private/transform/` and inspected. Their legacy scaling and negative-value filters are recorded in `docs/MIGRATION.md`. The later MainUI inventory confirms 34 inverter Item links, four Home Manager Items and ten derived capabilities; raw units/sentinels and the complete rule/persistence/UI audit remain pending. Some additional transforms use private historical counter offsets, while the active Home Manager energy links use offset profiles; do not apply both. All three TCP bridges use port 502, unit ID 3 and input-register pollers. The exports use both signed and unsigned 32-bit decoding, so type and sentinel behavior must be preserved and checked against the actual models. SMA devices do not share one universal documented configuration API. Home Manager meter data is available in local energy-meter telegrams; that does not expose every planning preference. Home Manager acting as a Modbus client for external devices does not imply that it serves all its own settings as Modbus registers.

The deployment target is a Raspberry Pi 5 with a 64-bit system (`linux/arm64` container target); OS/network details are still pending. Exact hardware designations were confirmed in ennexOS; matching complete register coverage remains pending. The separate read-only MainUI inventory received during catalogue work confirms the active house-day calculations through InfluxDB Flux, the Shelly wallbox day counter and selected consumption/aggregate rules. See `docs/MIGRATION.md` for their actual semantics and remaining continuity checks; they initially stay in openHAB.

Local meter telegrams use UDP port 9522 and the SMA Energy Meter/Speedwire protocol. Network interface, multicast reachability, serial-number selection, phase channels and encrypted Speedwire applicability must be checked against the actual installation. Docker multicast reception needs deliberate Linux networking configuration; do not assume Docker Desktop behaves like a Linux host.

## Value catalogue and portal inventory

The user requested a maintained German Markdown catalogue with units, brief descriptions and eventual MQTT topics. [WERTEKATALOG.md](WERTEKATALOG.md) now covers all 198 rows of the supplied Sunny Boy -40 register list, its 63 SunSpec-mapped rows, all 85 local eCharger parameter metadata entries, all 25 supplied SEMP parameters, all 458 parameter rows from the five current portal exports, existing migration channels and additional Home Manager/portal candidates. Export values and identity headers were excluded. The -40 list targets firmware 01.03.24.R and is not a validated profile for the installed SB4.0-1AV-41, Tripower or Storage. Complete matching profiles remain an input dependency.

The supplied HM-20 NSD document describes a real Home Manager Modbus server, separate from its client for external Modbus devices. Unit 1 exposes identification/assignment information; Unit 2 plant reads and delegated inverter parameters require Grid Guard according to that document. Pure write control registers are inventoried without Homie commands. The observed portal shows Modbus NSD input and the external-device Modbus client both disabled. Do not enable either or enter Grid Guard credentials for this inventory. Direct meter communication can replace multicast and needs an installation-specific check.

The authorized authenticated portal inspection confirmed five devices in the active plant view. A second view contains the same Storage device, with matching private identity and no live data; it does not add another physical device. Read-only UI inventory includes energy flows/history, charging priority/PV preference, forecast and scheduled battery charging, peak shaving, optimization goal, tariffs and communications. These UI capabilities are candidates until their API fields, units, rights and timestamps are verified. Only the existing minimum-PV setter is in the initial portal command scope. No credentials, private IDs or raw authenticated responses were copied; no device command was executed.

## Earlier fixes worth preserving

- An openHAB script initially failed because `Proxy` was unavailable in its JavaScript engine. Preserve the working modern JavaScript Scripting setup; this is not an SMA authentication error.
- Missing XPATH transformation caused XML channel warnings; a missing transformation is not an empty SMA value.
- An early sitemap had invalid `releaseOnly=true` syntax; classic sitemap syntax uses bare `releaseOnly`. MainUI widget metadata is a different format.
- Portal extension v1.0.2 improved login errors, including HTTP 200 HTML login failures. Do not infer successful login merely from HTTP 200.
- Portal regression harness includes 42 simulated protocol tests; these do not certify real device behavior or every firmware version.

## Other routes researched

Official SMA Monitoring, SmartHome, Live and GridControl are separately provisioned developer services with access registration, owner consent, fees and usage limits. The user rejected this paid route. SmartHome has PV-percentage/charging settings in its schema, but its published docs contain conflicting compatibility statements and restrict idle polling. No developer credentials have been obtained.

evcc has an eCharger SEMP integration and its own solar-share control. That would change ownership of charging regulation and require removing the direct simultaneous Home Manager consumer control. The user chose the existing local-plus-portal access instead; do not substitute evcc.

Existing reference projects studied include SMA-ennexOS-cloud (normal portal login plus selected cloud reads), sma2mqtt/SMA-EM (local meter/inverter data) and pysmaev (local charger protocol). They are references, not evidence of a complete drop-in bridge for this installation.

## Primary references

- [openHAB Homie binding](https://www.openhab.org/addons/bindings/homie/)
- [openHAB SMA Energy Meter binding](https://www.openhab.org/addons/bindings/smaenergymeter/)
- [openHAB Modbus binding](https://www.openhab.org/addons/bindings/modbus/)
- [openHAB JavaScript Scripting](https://www.openhab.org/addons/automation/jsscripting/)
- [Homie 4 specification](https://homieiot.github.io/specification/spec-core-v4_0_0/)
- [SMA on-site integration and protocol downloads](https://developer.sma.de/on-site-integration)
- [SMA Home Manager minimum PV share configuration](https://manuals.sma.de/HM-20-ennexOS/de-DE/13674317323.html)
- [SMA Home Manager Modbus configuration](https://manuals.sma.de/HM-20-ennexOS/de-DE/12570246795.html)
- [SMA Developer API overview](https://developer.sma.de/sma-apis)
- [SMA API access](https://developer.sma.de/api-access-control)
- [SMA API pricing](https://developer.sma.de/api-plans)
- [SMA SmartHome OpenAPI](https://sandbox.smaapis.de/smarthome/index.html)
- [evcc SMA eCharger SEMP integration](https://docs.evcc.io/en/chargers/sma-echarger-semp/)

Protocol implementation references:

- [pysmaev](https://github.com/alengwenus/pysmaev)
- [SMA ennexOS Cloud](https://github.com/MauroDruwel/SMA-ennexOS-cloud)
- [sma2mqtt](https://github.com/jollyjinx/sma2mqtt)
- [SMA-EM](https://github.com/datenschuft/SMA-EM)

## Python implementation milestone

On 2026-10-10 the Python configuration/profile loaders, generic read adapters, Homie lifecycle and heartbeat replaced the C++ runtime in Docker/tests/CI. Bundled models remain identity-only and cannot poll. API/SEMP and portal sources are separately gated; no command code exists. Migration acceptance, local certificate hostname matching, local units and Pi multicast reachability remain outstanding. See VALIDATION.md and todo.md.

## First installation read and explicit TLS overrides, 2026-10-10

The bundled model files now cover all 41 existing inverter channels using matching official lists and locally checked identity/firmware, with private serial guards. See REGISTER_VALIDATION.md. Three inverters and SEMP run on the Mac and have published values to the installation broker. Complete openHAB parallel acceptance remains pending. Home Manager stays disabled because the Mac runs in another network; prepare and verify its receiver on the Pi. Local API and portal still await the four private account fields.

At Andreas' explicit request, MQTT and local-wallbox TLS verification can each be disabled independently through their TLS_VERIFY flag. Defaults remain true; portal verification remains mandatory. The private Mac test uses unverified MQTT TLS after the real broker presented an untrusted self-signed chain. Wallbox certificate/name verification has passed and remains enabled. This overrides the earlier mandatory-verification requirement only for explicitly configured MQTT/local-API sessions. No trust is automatically adopted from a network download.
