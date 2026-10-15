# Topic classification

Basic describes normal plant operation: measurements, energy counters, device
state, everyday charging settings, command feedback and concise data-quality
status. Basic is always published for its enabled source; it is not a minimal
dashboard selection. Phase/DC measurements, temperature and derating remain Basic.

Advanced adds technical identity/firmware, power limits, operating/feed-in time,
delegated Home Manager properties and supplementary SEMP parameters/setpoints.
Diagnostics adds failure investigation: counters, receipt times, raw event codes,
calculation inputs, accounting timestamps and scope details.

Each inverter, Home Manager and eCharger retains its independent Advanced and
Diagnostics switches. Portal and plant have their documented Diagnostics switches.
All default to enabled. Classification does not grant write access, select
readiness requirements, activate adapters or change freshness/retention policies.

## Basic quality status

These existing topic suffixes remain visible with Diagnostics disabled:

| Owner | Topic suffix | Meaning |
| --- | --- | --- |
| Plant | `diagnostics/importdaystatus` | Daily grid import coverage |
| Plant | `diagnostics/exportdaystatus` | Daily grid export coverage |
| Plant | `diagnostics/houseenergystatus` | Daily household energy coverage |
| Plant | `diagnostics/housewithoutwallboxdaystatus` | Household coverage excluding Wallbox |
| Plant | `diagnostics/averagedaystatus` | Seven-day household average coverage |
| Plant | `diagnostics/averagewithoutwallboxdaystatus` | Average coverage excluding Wallbox |
| eCharger | `diagnostics/wallboxdaystatus` | Daily Wallbox energy coverage |

Wallbox-related properties still require their configured calculation inputs.
The existing values and semantics remain unchanged, including partial coverage,
missing input/history and reset guards. Coverage is distinct from source
availability: an old retained number and an old retained status cannot establish
a current connection. Observe operational source status/Homie state as well.
Detailed timestamps, local accounting date, battery boundary, `powerinputstatus`
and `validproperties` remain optional Diagnostics under their owning device flag.

Home Manager `parameters/datachangecounter` and
`parameters/gridguardunlockeddevices` are Diagnostics rather than Advanced.
With Advanced disabled and Diagnostics enabled, their core Unit 1 blocks can
still be polled. Identity verification remains mandatory for every combination.
Delegated assignment discovery/reads still require Advanced.

## Authoritative declarations and catalog

Every bundled mapping declares `channelGroup`; every runtime `Property` call
declares `channel_group`. Tests reject missing declarations in maintained source
and bundled profiles. Legacy custom host profiles may still omit the field and
retain their documented node-based defaults. Reconcile host overrides explicitly
to adopt the two Home Manager changes; the image does not replace host files.

The generated [CSV catalog](topic-catalog.csv) lists device/profile, source,
published topic suffix, meaning, unit and group. It uses runtime constructors and
bundled mappings, not installation configuration or captured device responses.
It includes alternate API/SEMP ownership, conditional command channels and plant
outputs with multiple PV/storage contributors. It describes supported properties,
not live availability or write permission. Command subscriptions, Homie `$...`
metadata and device `$state` are not separate property rows.

Prepend the configured Homie prefix/device ID to each suffix. `<N>` stands for a
configured inverter or discovered Home Manager slot; source IDs expand likewise.
Repeated suffixes across sources are alternatives, not duplicate active owners.
Units are source metadata; blank does not imply a verified physical unit.

Regenerate with `.venv/bin/python tools/export_topic_catalog.py`; use `--check`
to detect drift. The offline suite checks reproducibility and all four reader
flag combinations. CI mounts the catalog/tool read-only for container tests;
neither is added to the runtime image.

Topic-group classification alone preserves IDs and links. The separate Home Manager
power rename on 2026-10-15 requires relinking existing Items from powerimport/powerexport
to powerdrawn/powergridfeedin; keep Item identities and histories. As documented by the official
[openHAB Homie binding](https://www.openhab.org/addons/bindings/homie/), Homie nodes
map to Channel Groups; these publication classes are a separate bridge policy.
Deployment and live MQTT/openHAB acceptance remain separate steps.

## Naming review, 2026-10-15 — implementation selected

The generated catalog currently contains 298 rows and 199 distinct published
suffixes. Repeated rows include alternative transports, source ownership and model
profiles; they do not imply duplicate live measurements. Catalog reproducibility
was checked against runtime metadata. The following findings were cross-checked
against bundled profile mappings and units. Andreas subsequently requested the concrete renames below, including the battery
energy-return-ratio name. They are now applied at the MQTT publication boundary;
see the complete [old/new map](topic-renames-2026-10-15.csv). Internal profile IDs remain stable.

| Current suffix or property | Candidate | Reason and boundary |
| --- | --- | --- |
| Sunny Boy `measurements/voltg1`, `voltg2`, `voltg3` | `measurements/voltagel1`, `voltagel2`, `voltagel3` | Match Wallbox phase-voltage terminology. Keep registers 30783/30785/30787, V units and phase identity; a rename does not make invalid/missing samples valid. |
| Storage `measurements/presbatcharge`, `presbattdischarge` | `measurements/batterychargepower`, `batterydischargepower` | Explicit W quantities; align wording with existing batterychargeenergy/batterydischargeenergy in kWh. Plant aggregate names should follow the same charge/discharge convention. |
| Storage `measurements/currentbatstatcharge` | `measurements/batterystateofcharge` | Full name of the existing percentage, register 30845; no change of physical meaning. |
| Storage `measurements/currentbattemp` | `measurements/batterytemperature` | Match batterycurrent/batteryvoltage; retain register 30849 and degrees Celsius. |
| Inverter `measurements/dayyield` | `measurements/dailyyield` | Use daily consistently with dailyconsumption/dailyenergyimport. The corresponding plant day-yield name must be reviewed in the same migration. |
| Wallbox `parameters/nameplatepkgrev` | `identity/firmware` | Match inverter firmware naming. Preserve API/SEMP ownership and Advanced grouping; no metadata/write-policy change. |
| Storage `measurements/batteryefficiency` | `measurements/batteryenergyreturnratio` | Accurately name the cumulative energy-counter ratio. It is not independently verified physical round-trip efficiency. |
| Plant `pv/totalearnings` | `grid/totalearnings` | Actual export-based remuneration belongs to the grid node after the approved calculation correction. This does not change the formula. |
| Plant `house/consumption`, `consumptionwithcharging` | `house/consumptionpower`, `consumptionpowerwithbatterycharging` | Make W and battery charging explicit; avoid confusion with kWh or Wallbox charging. Longer names are a readability tradeoff. |
| Inverter `measurements/maxpower`, `setmaxpower` | `measurements/ratedactivepower`, `configuredactivepowerlimit` | Distinguish rating from a read-only observed limit; the existing set prefix does not authorize a command. Wallbox maxchargepower is a different setting. |

Lower-priority inconsistencies include duplicate battery wording under the plant
battery node, mixed daystatus/energystatus coverage names, and different English
metadata labels for identical IDs (firmware, model, serial, phase current, grid
contactor, internal temperature and status). Many already share German labels
through translations. Standardizing labels alone may avoid disruptive relinking.

Storage currentbatcapacity (register 30847, percent) needs a precise semantic
review before choosing a more specific name. It must not be renamed to an energy
capacity in kWh or declared battery state of health solely from the existing label.
Read-only settings must never gain /set merely because a name includes set.

Do not unify PV totalyield, Wallbox totalenergy and Home Manager energyexport as
though they were the same counter: production, charging consumption and grid
export have different boundaries. Likewise inverter operating status, vehicle
status, source availability and day-accounting coverage remain distinct states.
Group classification, physical sign conventions, raw/converted codes, UTC versus
numeric times and controller ownership are not naming shortcuts.

For an agreed implementation, maintain a complete old/new map and preserve
profile semantics, units, filters and energy baselines. Verify manifest retirement
of previous retained values/metadata. Relink existing openHAB Items in place while
preserving Item identity, rules, persistence and history. Do not edit the dated
source inventories to pretend a live relink has already happened. Prioritize the
clear phase-voltage and battery names plus the grid location of remuneration;
the concrete rows above have now been selected by Andreas. Lower-priority
coverage/duplicate-wording suggestions and unverified capacity semantics remain
unimplemented. Existing Home Manager energy IDs remain stable with configurable
corrected totals and separate optional raw-energy diagnostics.
