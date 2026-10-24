# Plant measurements and energy accounting

Optional plant calculations reuse existing source observations without extra
polling. Select enabled contributors by configured role and profile contribution
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

## Durable accounting

Counter vectors, local calendar boundaries, compatible AC storage counters and
bounded skew determine daily balances. Preserve original observation age rather
than renewing it during calculations. Invalid inputs, resets, backward time,
negative balances and unsupported battery boundaries block affected accounting.
Partial/gap/complete statuses describe coverage, independently of MQTT connectivity.

A rising outflow counter can temporarily precede older inflow measurements.
Household energy then reports `synchronizing` for one bounded wait, while the
rejected energy remains unavailable. After the older inflows are sampled again,
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
