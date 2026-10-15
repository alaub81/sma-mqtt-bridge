# PV inventory and plant aggregation design

Inventory reviewed: **2026-10-14**; Wallbox topic ownership updated **2026-10-15**. Plant calculations are implemented and offline
tested alongside the read-only inventory; deployment and migration remain pending. Existing Items, rules, links,
persistence and the running resource recorder were not changed.

## Inventory and evidence

The current installation was inspected through MainUI and read-only REST Item
metadata. The previous [migration baseline](MIGRATION.md) and 100-row capability
ledger remain intact. These supplementary files establish the current comparison
inputs rather than rewriting that historical baseline:

- [Item inventory](pv-item-inventory-2026-10-14.csv): 129 entries, comprising the
  51-entry legacy `PV_Plant` tree including groups, four new device groups with
  70 non-group Homie Items, and four external dependency Items. Names, types,
  units, display patterns, groups and semantic tags only; no live states saved.
- [Homie links](pv-homie-links-2026-10-14.csv): 70 current Item/topic associations,
  verified through live channel-link views. These are configured links, not an
  independent measurement comparison or certification that every channel is fresh.
  The 38 corresponding old links were also checked: 34 still use Modbus and four
  use the SMA Energy Meter binding, providing independent legacy sources.
- [Rule inventory](pv-rule-inventory-2026-10-14.csv): all 109 listed rule code views
  were read; 29 measurement, forecast, Smart-Grid and related consumer rules were
  selected by their names and observed literal Item/condition/trigger references.
  The inventory keeps current enabled states, cron expressions, persistence
  method names, timer/HTTP markers and proposed ownership. Private thresholds,
  tariff, endpoints, Blockly identifiers and raw scripts are omitted.
- [Query inventory](pv-query-inventory-2026-10-14.csv): four current InfluxDB query
  definitions with source series, time boundaries, calculations and intervals.
  Database credentials, hostnames and bucket/organization identities are omitted.
- [Comparison manifest](pv-comparison-2026-10-14.csv): 38 existing legacy/bridge
  Item pairs, ten implemented aggregate destinations without new live Items, four legacy-only entries
  and 32 new-only Items. These topics require a build containing this feature and are not in published v0.3.11.

The rule scan records observed references, not a static-program-analysis proof:
dynamic Item names, imported code and Thing actions need separate auditing if
their ownership changes. Empty reference fields do not imply no dependencies.
An unused function can contain a persistence call; in the household-power rule,
`present()` is active and `average()` remains unused. Full controller thresholds,
timer races, scripts outside the rule list, Pages and map/link profiles are not
accepted by this inventory. Original private exports remain read-only.

## Existing calculations and migration boundaries

`inverterActivePower` already sums the two PV inverters in openHAB every five
seconds. The deployed inventory has individual bridge observations; the new optional
plant source adds aggregates without changing those per-device observations. `inverterDailyYield` and `inverterTotalYield`
sum PV1/PV3 counters every five minutes. Storage is not a third PV generator.
The production rule also forwards the result to a display. A separate enabled
`PV Produktion` action performs forwarding without an observed automatic trigger;
retain that action when replacing the measurement sum.

`TotalPowerConsumption` is instantaneous W, not a lifetime kWh counter. Its
15-second active formula adds PV1, PV3, battery discharge and inverter1 grid import,
then subtracts inverter1 grid export and battery charge. `PowerConsumptionBatIncl` adds battery
charge back. Both skip negative results and leave the previous Item value in place.
The requested new household lifetime energy is a distinct kWh property; preserve
the existing power Items and their consumers. The battery AC/DC boundary remains
unverified for independent physical household accounting.

Current daily import/export/household queries integrate old power series in
10-second mean windows, use local midnight in Europe/Berlin and refresh every
300 seconds. Counter deltas intentionally change the method and need a parallel
comparison, not an assumption of exact numerical equivalence. The seven-day
consumption average excludes Wallbox ON days and feeds Smart-Grid; its timezone
option remains commented out. Forecasts, tariffs, Shelly day counters, household
controllers, presence actions and seasonal alarms stay in openHAB.

The live `smahomemanager_Anlagenzeit_DateTime` link still points to numeric
`measurements/planttime`, not `planttimeiso`. This is a link-review finding only;
no value failure, deployed version, link correction or history repair is inferred.

## Calendar and measurement time

Reuse existing validated `SMAB_TIMEZONE` / `runtime.timezone`, default
`Europe/Berlin`; no duplicate timezone flag is needed. Derive local calendar date
and midnight with that IANA zone. Compute the next local midnight from the next
calendar date, not by adding 86400 elapsed seconds. Berlin DST days can span 23
or 25 hours. Save UTC observation times and the baseline's local date/timezone;
use monotonic time for source freshness and supervisor scheduling.

Changing timezone, source membership or device identity must invalidate affected
daily baselines explicitly. A first sample after midnight is not an exact
midnight reading: define its bounded sampling uncertainty. Initial partial days,
outages spanning midnight and missing/stale counters cannot yield an invented
complete-day result. Same-day restart can reuse persisted valid baselines;
resets/replacements require reconciliation. Cumulative household energy needs
aligned starting baselines and optionally a verified opening value. Persist state
under the existing state volume without changing topic manifests or journals.

## Explicit roles and generic profiles

The per-inverter setting is `SMAB_INVERTER<n>_ROLE` with values `none`, `pv`,
`battery`, `hybrid`, and a safe default `none`. The existing enabled flag continues
to control device I/O independently. Plant activation and Homie identity
are separate typed settings: `SMAB_PLANT_ENABLED=false` and
`SMAB_PLANT_HOMIE_ID=sma-plant`. Settings, defaults and JSON/ENV precedence are documented in
[configuration](CONFIGURATION.md#plant-aggregates-and-energy-state).

For this installation, inverter1/inverter3 are configured as PV contributors and inverter2 as
a battery contributor. Validate explicit roles against file-based profile
contribution mappings, including property keys, units, sign convention and
measurement boundary. No model-name branching or inference from addresses,
credentials, labels or a generic active-power property. Additional inverters
should enter the same configured contributor sets without adapter-specific code.

A hybrid role requires distinct verified PV and storage contributions. Its AC
output may already combine PV and battery; never add that combined output and
battery discharge again. Profiles lacking separable contributions remain excluded
from that particular balance until a supported mapping is established. Explicitly
select one plant grid-meter source; do not sum repeated inverter observations of
the same grid connection. Initially compare the legacy inverter1 grid observations
with Home Manager before choosing/replacing the accounting source.

## Sums and formulas

Sum additive observations only, with common units and compatible boundaries:

- PV AC power, PV daily yield, and the sum of component PV lifetime yield counters.
- Battery charge/discharge power and compatible charge/discharge energy counters.
- Distinct DC input powers as a separate DC aggregate, never added to AC production.
- Household power candidate: PV AC power plus grid import and compatible battery
  discharge power, minus grid export and compatible battery charge power.
- Household energy candidate: the same balance using counter deltas over one
  shared interval. Daily uses local-day baselines; lifetime uses a common start.

Do not sum temperature, voltage, frequency, percentages, device states or
overlapping total/phase/input measurements. A fleet SOC needs verified energy
capacity weighting; current capacity/health percentages are not kWh weights.
Battery return ratio must use compatible summed energy deltas/counters, not the
sum or unweighted average of percentage ratios. Grid flow already includes
downstream Wallbox/heat-pump consumption; do not add those again.

Required contributors are fixed by configuration. Missing/stale/invalid data must
make the aggregate unavailable instead of publishing a silently partial sum.
An explicitly empty PV/storage set differs from a configured but failed device.
Valid zero remains valid, including at night. Do not turn nighttime NaN into zero
based on the clock. Propagate the oldest contributing observation time and enforce
configured sample skew; unrelated fresh values may not renew old aggregate inputs.
Preserve last-known MQTT observations independently of current aggregate validity.

Current PV yields are whole-kWh observations; float output cannot improve their
precision. Verify the audited finer Wh counters separately before new mappings.
Battery counters 31397/31401 still need AC/DC-boundary confirmation. The balance
is a candidate, not accepted physical household energy.

## Implemented Homie layout

The optional source uses one additional logical plant device to group results by their meaning, while
keeping all existing per-device topics. The configured Homie prefix and plant ID replace the example path.
PV and battery sum properties are declared only for at least two configured
enabled contributors in that group; unavailability never reduces membership:

| Topic | Unit | Existing counterpart / meaning |
| --- | --- | --- |
| `homie/sma-plant/pv/totalactivepower` | W | `inverterActivePower`; sum of verified PV AC contributions |
| `homie/sma-plant/pv/totaldayyield` | kWh | `inverterDailyYield`; sum of compatible PV daily yields |
| `homie/sma-plant/pv/totalyield` | kWh | `inverterTotalYield`; sum of component lifetime counters |
| `homie/sma-plant/battery/totalpresbatcharge` | W | Sum of compatible storage charging power |
| `homie/sma-plant/battery/totalpresbattdischarge` | W | Sum of compatible storage discharging power |
| `homie/sma-plant/battery/totalbatterychargeenergy` | kWh | Compatible storage charge counters with documented scope |
| `homie/sma-plant/battery/totalbatterydischargeenergy` | kWh | Compatible storage discharge counters with documented scope |
| `homie/sma-plant/grid/dailyenergyimport` | kWh | `Strom_Tagesbezug`; designated grid counter delta |
| `homie/sma-plant/grid/dailyenergyexport` | kWh | `Strom_Tageseinspeisung`; designated grid counter delta |
| `homie/sma-plant/house/consumption` | W | `TotalPowerConsumption`; current household power |
| `homie/sma-plant/house/consumptionwithcharging` | W | `PowerConsumptionBatIncl`; preserve distinct legacy meaning |
| `homie/sma-plant/house/dailyconsumption` | kWh | `Strom_Tagesverbrauch_Number_Result`; household day balance |
| `homie/sma-plant/house/totalconsumption` | kWh | New household energy counter from a common starting baseline |
| `homie/sma-echarger/measurements/dailyconsumption` | kWh | Local API total-energy counter delta; independent of battery boundary |
| `homie/sma-plant/house/dailyconsumptionwithoutwallbox` | kWh | Household counter balance minus Wallbox delta over one shared baseline |

The Wallbox day counter belongs to the configured eCharger Homie device; household
energy without Wallbox belongs to the plant. Both require the independently enabled
local eCharger API and the plant calculation flag.
They use the existing total-energy counter, never the session counter; household
kWh without Wallbox retains the battery-boundary gate. No additional device I/O.

All aggregates are read-only. Coverage/date/battery-boundary diagnostics remain
available independently of optional source diagnostics. Retained values alone
do not establish a current/full-day result. Current power and direct counter sums
use existing receipts; grid/house energy publishes durable snapshots at the
configured checkpoint cadence (default 300 seconds), plus critical transitions.
The state file is energy-balances.json under the existing state volume.
No extra device polling is added. Unverified battery energy boundaries block
house daily/lifetime kWh with unsupported-battery-boundary; current power ports
the existing openHAB device-power balance and still needs physical acceptance.
For provisional comparison, SMAB_PLANT_ASSUME_AC_BATTERY_ENERGY=true explicitly
allows the unverified boundary as assumed-ac. This also permits household daily
energy without Wallbox, while preserving all counter/freshness/coverage guards.
Documented DC boundaries remain blocked. Physical confirmation stays pending;
the assumption does not change the bundled profile's evidence or existing baselines.

## Grafana comparison preparation

Use the comparison manifest to build a later dashboard with one graph per
measurement showing old/new series, plus an aligned absolute difference where
meaningful. First priorities: both PV inverter powers, PV power sum, grid
import/export power, storage charge/discharge power and SOC, current household
power, PV day yield and daily import/export/consumption.

Many old Items use periodic persistence groups while new Items use every-change
groups. Resolve effective service policies and actual persisted measurement
names before querying. Item names are comparison identities, not proof of exact
InfluxDB measurement aliases. Confirm database version/schema, datasource UID,
field names, units, sampling windows and timezone before generating importable
Grafana JSON. The inventory does not create/install a dashboard or new Items.

Compare power at aligned intervals; do not carry missing samples forward as
evidence of agreement. Compare offset counters by verified aligned starting
readings or interval deltas. Daily energy from old integration versus new counter
balance needs a method/coverage annotation; exclude first partial days and do not
interpret every difference as a defect. Add source/aggregate freshness alongside
retained measurements. Preserve all existing histories during parallel operation.

## Next acceptance steps

1. Build/deploy the optional feature with explicit roles and reconciled host profiles;
   observe power/yield sums, single-battery suppression and per-value diagnostics.
2. Verify battery AC energy boundaries and finer PV counter precision. The complete
   household counter engine is offline tested with synthetic verified AC mappings;
   the bundled unverified Storage boundary has no household kWh result by default.
   Andreas requested the explicit provisional AC override for comparison on 2026-10-15.
3. Compare covered full days after midnight; verify the first partial day, restart,
   controller/history continuity and the saved snapshot times before accepting data.
4. Add separate comparison Items/persistence and a Grafana dashboard after datasource
   inventory. Accept parallel results before changing existing Item ownership.

Official integration references: [openHAB Homie binding](https://www.openhab.org/addons/bindings/homie/),
[persistence](https://www.openhab.org/docs/configuration/persistence.html), and
[units of measurement](https://www.openhab.org/docs/concepts/units-of-measurement.html).
