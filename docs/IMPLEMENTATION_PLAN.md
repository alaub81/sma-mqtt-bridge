# Implementation and acceptance plan

Updated: **2026-10-15**. This plan covers remaining work. Current acceptance and
its evidence limits belong in [VALIDATION.md](VALIDATION.md); architecture decisions
in [CONTEXT.md](CONTEXT.md); active tasks and question references in
[the German diary](../todo.md). The
[pre-cleanup snapshot](archive/2026-10-13/IMPLEMENTATION_PLAN.md) preserves older plans.

## 1. Preserve accepted deployment and upgrade continuity

Andreas confirms the newer AC-profile build deployment, host-profile reconciliation,
backed-up ledger reset and installed-version verification complete on 2026-10-15.
The full-day grid/house/Wallbox comparison including midnight/restart/gaps is also
accepted. The older deployment wording below is historical; do not schedule it again.
New remuneration/average features need their own subsequent deployment and live check.
The [topic-group refinement](TOPIC_GROUPS.md) is offline verified separately:
after a requested deployment, confirm the seven Basic coverage statuses with
Diagnostics disabled and the two Home Manager protocol diagnostics independently
of Advanced. Reconcile used Home Manager host profiles; preserve topics, links,
state and the existing accepted energy balances.

Andreas requested the v0.3.11 release after the performance/hardening review and
resource-recorder extension. Publication is complete: hosted CI/security and
both architectures passed. Andreas supplied the completed voluntary 24-hour post-update comparison on
2026-10-14; see [the analysis](RESOURCE_SOAK_ANALYSIS_2026-10-14.md). The recording
shows stable sampled health and resources but does not record the installed
version. For deployment and recorder procedure, see [release notes](RELEASES.md) and
[the recorder procedure](OPERATIONAL_ACCEPTANCE.md#bounded-linux-host-resource-recording).
Public v0.3.8–v0.3.10 workflows have completed successfully. The last documented
target-host version here is v0.3.7; do not infer later deployment from publication.
Preserve acceptance limits for battery ratio, Basic derating and ISO plant time.

Before deployment, reconcile actually used host-profile overrides, preserve
state-volume/manifest/journals and existing numeric Items/history. Verify hosted
CI/security results and both image architectures, then installed version/health
and the new channel behavior. Switch the existing DateTime link to ISO only with
preserved Item identity/dependencies and live verification.

## 2. Resolve remaining eCharger freshness semantics (Review 4)

The scoped remaining-lifetime fix for evidenced periodically refreshed channels
is implemented and deployed. Remaining semantic questions concern session energy
at idle/reset, fixed old state/event channels, phase measurements and alternative
counters. Analyze API and SEMP independently using natural operating transitions.
See [the timestamp analysis](ECHARGER_TIMESTAMP_ANALYSIS_2026-10-12.md).

Decide retain/change/remove behavior per channel, then implement any needed
regression cases and UI acceptance. Do not refresh old device samples merely on
receipt, replace missing values with zero or loosen uncertainty guards. Decide
separately whether to stop/archive timestamp diagnostics after the investigation.

## 3. Finish openHAB and history continuity

The optional [plant aggregation implementation](PV_AGGREGATION_DESIGN.md) now has
explicit per-inverter PV/storage/hybrid roles, profile contribution mappings,
SMAB_TIMEZONE and a separate Homie plant identity. The 2026-10-14 live inventory
and comparison manifest provide current Item names and rule/query dependencies.
PV/storage sums, current household power and durable counter balances are
implemented locally and disabled by default. Deploy a separately tested build
when requested, activate configured roles, and compare values in parallel.
Wallbox daily energy and household day energy without Wallbox are also implemented
from the existing local API total-energy counter, with Wallbox daily consumption
on the eCharger identity and household exclusion on the plant; validate a covered midnight,
restart and parallel Shelly comparison before replacing existing calculations.
Finer PV counter units and whole-day comparisons remain prerequisites for accepting
household counter accuracy. The [2026-10-15 history comparison](BATTERY_ENERGY_BOUNDARY_2026-10-15.md)
strongly supports AC boundaries for both installed battery counters; the bundled
profile now declares ac. Andreas approves fresh energy baselines for this upgrade.
Deploy the new build, reconcile host overrides and archive only the energy ledger
with the offline reset command before restarting. Preserve the state volume,
topic manifest and journals; verify all five new day accounts and ac diagnostics.
For provisional comparison, Andreas requested an explicit AC assumption for
unverified battery counters on 2026-10-15. The optional override reports assumed-ac;
it permits house kWh without completing physical acceptance or changing profile evidence.
An optional initial-partial-day publication flag also permits immediate counter
comparison from the first saved snapshot while retaining partial status; covered
midnight/restart acceptance remains required for normal calendar-day accounting.
The Grafana comparison dashboard is updated with 47 pairs and an additional
Bridge average panel; full history
coverage and numerical equivalence remain pending. Preserve histories and ownership.

Complete the 100-row [migration ledger](migration-coverage.csv), remaining legacy
Item associations, maps, offsets, rules, UI, persistence and midnight/DST behavior.
Existing user-accepted value comparisons and selected restart/history checks
remain accepted; do not repeat them as blanket pending work.

Build aligned Grafana comparisons only for unresolved series. Remaining selected
measurement checks include Storage frequency/current L1; other Derating states
need natural occurrences. Battery-counter measurement boundary/reset semantics
remain distinct from plausible readouts and user-confirmed common counter start.
Sunny Boy L2 had no valid scan payload; never reinterpret existing L1 history.

Keep Shelly-derived charging state, Smart-Grid consumers and InfluxDB calculations
in openHAB until equivalent behavior is accepted. Preserve Item identities, units,
private offsets and persistence. No example Item files or sitemaps are planned.

## 4. Resume charging checks when the vehicle can charge

The wallbox phase-power comparison is deferred until Andreas can charge again.
Compare phase and total active power with matching units and aligned updates.
Then assess physical target attainment, session-energy semantics and return from
target mode. Maximum-power limiting/winter single-phase behavior has separate
[evidence and bounds](ECHARGER_POWER_LIMIT.md).

Live writes require explicitly requested target values. Home Manager remains the
charging controller; metadata editability alone never authorizes another setter.

## 5. Infrastructure changes and maintenance

The complete quality/resource review and three focused optimizations on
2026-10-13 are documented in [the performance review](PERFORMANCE_REVIEW_2026-10-13.md).
Heartbeats avoid forced disk sync, immutable metadata is reused and observation
payload expansion is bounded. Further optimization needs isolated probe/logging/
broker I/O evidence; do not add measurement or command-rights caches.

Operational/recovery acceptance and the stable 22-hour resource baseline were
closed by Andreas on 2026-10-13. See
[the user acceptance](VALIDATION.md#remaining-operational-acceptance-closed-by-user-2026-10-13)
and [resource analysis](RESOURCE_SOAK_ANALYSIS_2026-10-13.md). Additional scenario
details were not supplied; preserve that evidence limit without scheduling reruns.

Watchtower/Autoheal setup and a possible switch to Docker bridge networking are
future changes requiring their own focused verification. Align automatic updates
with version pinning; preserve recovery state. UDP multicast checks apply only
when that transport is selected. Document vendor polling/connection limits and
specific alarm thresholds if needed; current operational acceptance stays closed.

Simplify large functions or repeated widget expressions only for concrete
maintenance benefits and preserved behavior. Formatting, import ordering and
named immutable setting definitions and ten focused correctness lint rules are
already implemented. Further rules require a concrete benefit; do not build a
generic adapter platform or broad rewrite.
Duplicate JSON decoding checks were consolidated on 2026-10-13 with unchanged
caller-specific errors and offline acceptance. Further consolidation requires
proven equivalent behavior; authentication, freshness and command flows need
separate focused changes.
The local historical tag `v0.3.9` preserves the source before that refactoring;
it is not a published image. Shared Modbus property metadata construction is also
implemented and equivalent across 240 offline comparison cases. This limited
round passed local ARM64/AMD64 image builds and all 259 tests in each container.
The metadata refactoring is recorded separately in `bf21423`; validate and commit
any future implementation step separately. Publication remains a separate request.
Maintain the [MainUI guide](../openHAB/openHAB.md) and later prepare the wiki article.

## 6. Deferred extensions

Additional Modbus/wallbox/SEMP mappings, power-factor/reactive/apparent values,
I/O/event diagnostics, further charging parameters and detailed interpretation of
three existing SEMP control properties remain deferred until reprioritized.
Additional portal values/current charging mix need verified units, time scope and
identity. Period shares and minimum-PV preference are not live charging mix.
The [active diary](../todo.md#zurückgestellte-erweiterungen) retains candidates,
unresolved questions and audit references; no automatic expansion is planned.

API-only fallback expansion for operation without SEMP was removed from scope.
Preserve existing ownership, topics and documented availability exclusions.

## Release validation for every future version

Publication requires an explicit request. Verify private-data exclusions,
namespace/tags, hosted CI/security gates, amd64/arm64 images and target upgrade
continuity. Recheck stable official Python tags when changing the base image.
Local tests alone do not establish hosted success or deployment.

## New plant statistics, 2026-10-15

Local implementation now values actual cumulative grid export with one common
plant tariff and independent Home Manager cumulative import/export corrections, replacing the earlier
PV-yield valuation. Home Manager is the default selected source; duplicate inverter
grid views are never summed. Configurable currency and seven-completed-day house averages including and
subtracting Wallbox consumption. Charging days remain included. Validate new
channels after a separately requested deployment and seven days of collection;
existing accepted daily balances do not need blanket reacceptance.

## Offset and naming migration acceptance

After separately deploying the new build, verify corrected Home Manager cumulative
import/export against raw diagnostics and private historical offsets, with correction
applied once to feed-in remuneration. Preserve all energy baselines/history. Relink
existing Items using topic-renames-2026-10-15.csv, check old retained retirement and
current values, and retain existing units/rules/persistence. No reset is planned.

## Immediate average-window acceptance, 2026-10-15

After the next installation, compare both house averages using today plus up to
six available preceding dates. Confirm startup-day publication, midnight window
rotation and measured Wallbox subtraction. The earlier wait for seven completed
days is superseded; preserve state and existing Item links.

## InfluxDB 2 history transfer before Item removal

Complete the [Item mapping](influx2-item-migration-2026-10-15.csv) with actual new
names and persistence metadata. Review backup/cutover, run preview and per-pair
copy, validate history and dependent rules/charts before removing old Items.
Keep unsupported frequency and semantically different old earnings separately.
See the [prepared workflow](INFLUX2_ITEM_MIGRATION.md); three populated histories have been copied; independent post-copy acceptance remains pending.

## Current inventory and Grafana gaps, 2026-10-15

The refreshed inventory and comparison worksheet are dated 2026-10-15; retain the
original 2026-10-14 snapshots. Ten renamed-channel Items retain their identity and
need no InfluxDB copy; five actual replacement Items have confirmed new names.
The two new Home Manager power Items and three Carport voltages are not persisted.
PV total daily yield and old production remuneration have no channel link. Resolve
these separately before accepting full comparisons. New averages are linked and
configured for persistence, but their panels had no data in the inspected last-hour
window. The old average and Bridge average have different algorithms. No Item,
persistence or database changes were made while refreshing the dashboard.

## Follow-up status of inventory gaps, 2026-10-15

The five missing persistence policies reported above are now enabled and live
verified. Feed-in earnings now have a linked, persisted Item and a Grafana pair.
Do not repeat these as missing configuration. Stored-history completeness and any
copy into the five replacement series remain separate. Resolve the PV daily/lifetime
link conflict: daily channel currently also writes to the lifetime Item; the daily
Item remains unlinked. Andreas will correct this manually; re-read both links
before closing it. Do not repair or delete the affected history automatically.

### PV link correction verified, 2026-10-15

Andreas corrected the links manually. Live Item details confirm that
`smaplant_PVGesamtertrag` has only `pv#totalyield` and
`smaplant_PVGesamttagesertrag` has only `pv#totaldailyyield`. Both retain
everyChange/restoreOnStartup persistence. The link conflict is resolved; review
any earlier mixed lifetime-history interval separately, without automatic repair.
The 48-pair Grafana follow-up was saved in the existing TESTS folder after
Grafana restarted. Opening import from that folder bypassed the unresponsive
folder picker. Updated introduction and earnings panel were verified in the UI.

## Nighttime PV compatibility follow-up

Deploy the explicit PV power sentinel normalization with matching host profiles.
Verify fresh nighttime house power and plant availability; retain failure/expiry
behavior. Investigate the independently observed configuration-changed day coverage
without resetting energy state automatically.
