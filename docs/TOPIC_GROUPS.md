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
Advanced and optional Diagnostics default to disabled; Basic remains enabled. Classification does not grant write access, select
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

Homie nodes map to Channel Groups as described in the official
[openHAB Homie binding](https://www.openhab.org/addons/bindings/homie/).
Basic/Advanced/Diagnostics are independent bridge publication settings.
