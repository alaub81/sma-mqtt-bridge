# Implementation and acceptance plan

Updated: **2026-10-15, evening**. This document contains future work only.
Current evidence is in [VALIDATION.md](VALIDATION.md), the German task list in
[todo.md](../todo.md). The previous detailed plan is preserved in the
[2026-10-15 snapshot](archive/2026-10-15/IMPLEMENTATION_PLAN.md).

## 1. Preserve accepted deployment and upgrade continuity

Andreas accepts the release/CI step. The supplied production logs confirm the
nighttime PV sentinel normalization, and live MQTT now shows plant ready with
fresh house power. The user requested a backed-up energy-ledger reset; day and
average statuses subsequently changed to partial, with average values present.
Do not repeat the accepted earlier AC deployment, full-day/midnight/restart/gap
acceptance or resource baseline as blanket pending work.

Verify the next midnight and following day specifically after this new reset.
Check house/day values with and without Wallbox, average-window rotation and the
previous saved-versus-recomputed house-without-Wallbox discrepancy. No additional
ledger reset, signature rewrite or history repair is automatic.

Verify daytime recovery of the nine DC channels after the completed 15-channel
assessment; decide how consumers show individual unavailable retained measurements.
Battery/counter invalid values are not zero; signed temperatures remain valid.
See [the audit](INVALID_VALUE_AUDIT.md). No config.json or host profile overrides
are present according to Andreas. The private minimal ENV candidate preserves the
resolved configuration offline; apply it on the host separately and verify startup.

## 2. Resolve remaining eCharger freshness semantics (Review 4)

Charging checks and the subsequent plugged-in idle samples are documented in
[the live report](ECHARGER_LIVE_CHECK_2026-10-15.md). Total energy, power and vehicle
status refresh during idle; session energy retains its activity timestamp and
is correctly filtered as stale. Keep this distinction in UI and persistence.

The user-operated unplug reset is now confirmed in API/SEMP with a fresh zero
session value and unchanged cumulative energy. Replug in a locked state is also sampled: raw session zero remains, while its
unplug-time timestamp expires. Charging-start behavior and other possible reset
triggers remain separate acceptance. Health/event/mode/authorization still require an
actual state transition or verified protocol contract. Do not refresh old samples
on receipt. Decide separately whether to retain/archive timestamp recording.
No device setting or charging-controller change is part of these read checks.

## 3. Finish openHAB and history continuity

The 2026-10-15 inventory and 48-pair Grafana dashboard are prepared and saved.
Five replacement Items have persistence; PV daily/lifetime links are corrected.
Remuneration has a linked persisted Item; both house averages have live values.
Do not repeat these as missing setup. Full numerical acceptance remains distinct.

Independently verify the 205,552 copied history points before removing obsolete
Items; original measurements remain. Carport L1/L2 had no source history. Earlier
verification was blocked by query-queue saturation. Review any prior mixed
PV daily/lifetime history separately. See [the transfer record](INFLUX2_ITEM_MIGRATION.md).

Complete the 100-row migration ledger for rules, UI, persistence, units, offsets,
DST/day boundaries and dependency ownership. Preserve Shelly/Smart-Grid logic until
equivalent behavior is accepted. Apply grid-energy offsets exactly once. Use the
current mapping instead of historical unmatched-link counts. Verify the Home
Manager ISO DateTime link, canonical batteryenergyreturnratio naming, coverage
status grouping and remaining Storage current/frequency comparisons. Other
Derating states need natural events. Finer PV counter precision remains a separate
possible improvement, not a reason to revoke accepted existing measurements.

## 4. Resume charging checks when the vehicle can charge

The single-phase L3/total-power comparison is already sampled and consistent.
Other natural load points and Item-level acceptance remain. Validate the garage
widget, physical target completion and return from target mode. Maximum-power and
winter single-phase behavior have separate [bounds](ECHARGER_POWER_LIMIT.md).
Preserve existing write gates and readback/uncertainty protection. Home Manager
remains the charging controller; live writes need explicit target instructions.

## 5. Infrastructure changes and maintenance

Check actual service integration of existing Watchtower/Autoheal containers and
coordinate automatic updates with version pinning. Consider bridge networking for
Home Manager Modbus only as a separately accepted change; multicast tests apply
only to UDP. Existing operational/recovery and resource acceptance stays closed.
Document manufacturer polling limits or alarm thresholds if needed. Further
simplification requires concrete benefit and preserved behavior. Maintain the
MainUI guide and later prepare its wiki version; no example Items/sitemaps are planned.

## 6. Deferred extensions

Additional Modbus/wallbox/SEMP/portal mappings remain deferred until prioritized:
reactive/apparent power, power factor, alternate counters, I/O/event diagnostics,
BMS strings, planning/capability fields, charging parameters and current charging
mix. Three existing SEMP control values still lack complete physical semantics.
No new setters follow merely from metadata. API-only fallback expansion with SEMP
disabled remains out of scope. See the [German candidate list](../todo.md#zurückgestellte-erweiterungen).

## Release validation for every future version

Run the full linter, regression suite, Compose parity and hosted multi-architecture
CI/security gates for relevant changes. Tags or local passing tests alone do not
establish published-image or live installation acceptance. Preserve private files,
state volume, topic manifest and command journals on every deployment.
