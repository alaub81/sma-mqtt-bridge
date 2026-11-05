# Plant measurements and energy accounting

Optional plant calculations reuse source observations. With coordinated reads
enabled, contributing W pollers use a shared cadence and immutable complete-cycle
snapshots; counter pollers keep their intervals on a shared time origin.
See [coordinated reads](CONFIGURATION.md#coordinated-calculation-reads). Select enabled contributors by configured role and profile contribution
mapping; use one grid source. Validate units and independently measured hybrid
contributions before enabling accounting. See [configuration](CONFIGURATION.md#plant-aggregates-and-energy-state).

## MQTT properties

The [generated catalog](topic-catalog.csv) is the complete property inventory.
Per-device topics remain independent. PV/storage sum topics require at least two
configured contributors; failure does not shrink membership or fabricate zero.
Household W balances require fresh, aligned PV, grid and battery observations.
Use the opt-in [joint recorder](CONFIGURATION.md#joint-power-and-status-recorder)
to inspect actual calculation frames and source/plant status transitions.
`SMAB_PLANT_POWER_MAX_SKEW_SECONDS` selects a separate W-only timing limit;
its default 0 retains the general limit until a capture has been reviewed.
Wallbox daily kWh belongs to the eCharger; household energy excluding Wallbox
belongs to the plant. Derived day coverage does not determine charger availability.

## Battery daily energy

With at least one configured battery contributor, the plant publishes two read-only
Basic properties, including for a single battery:

| Topic suffix | English label | German label | Unit |
| --- | --- | --- | --- |
| `battery/dailychargeenergy` | Daily battery charge energy | Batterie-Tagesladung | kWh |
| `battery/dailydischargeenergy` | Daily battery discharge energy | Batterie-Tagesentladung | kWh |

Each direction uses the sum of the configured contributors' cumulative charge or
discharge counter deltas against its own saved daily baseline. Membership never
shrinks on failure. These are directional energy flows, not state of charge or
battery losses. They retain the configured counters' physical measurement boundary;
they do not establish an AC boundary for household accounting. The inverter's
existing device daily-discharge property remains independent.

The same calendar, first-day partial coverage, checkpoint, freshness, identity,
reset and midnight-gap rules as grid daily energy apply. With coordinated reads,
each battery direction waits for all its contributors in a complete counter round.
PV or grid failure does not block valid battery day values. Check the Basic
`diagnostics/batterychargedaystatus` and `diagnostics/batterydischargedaystatus`
properties alongside the numbers; optional Diagnostics timestamps are
`diagnostics/batterychargeenergytime` and `diagnostics/batterydischargeenergytime`.

Existing energy accounts keep their baselines when upgrading. The two new accounts
start at their first valid observation, not retrospectively at midnight; initial
partial publication follows `SMAB_PLANT_PUBLISH_PARTIAL_DAY`. Preserve the state
volume. openHAB can display these kWh values directly without calculating daily
differences itself.

## Durable accounting

Counter vectors, local calendar boundaries, compatible AC storage counters and
bounded skew determine daily balances. Preserve original observation age rather
than renewing it during calculations. Invalid inputs, resets, backward time,
negative balances and unsupported battery boundaries block affected accounting.
Partial/gap/complete statuses describe coverage, independently of MQTT connectivity.

A rising outflow counter can temporarily precede older inflow measurements.
Household energy then reports `synchronizing` for one bounded wait, while the
rejected energy remains unavailable. Later outflow advances update the required inflow cutoff without renewing the
original timeout. After the older inflows are sampled again,
or the configured skew timeout expires, an unresolved decrease reports
`inconsistent`. Retained values keep their last-known meaning. Actual counter
resets and source changes remain blocked immediately. See the
[accounting contract](CONFIGURATION.md#plant-aggregates-and-energy-state).

Persist energy baselines, hardware/configuration fingerprints and bounded daily
history atomically in the state volume before publishing committed balances.
Preserve topic manifests, command journals and saved price preferences separately.
Never reset baselines automatically after incompatible configuration/profile changes.
Price preferences revalue the documented current counters; they do not rewrite
historical samples or establish historical tariff accounting.

Check coverage status alongside numeric values. A retained MQTT value can remain
visible while its input is unavailable; it does not establish current freshness.
