# Implementation and acceptance plan

Updated: **2026-10-13**. This plan covers remaining work. Current acceptance and
its evidence limits belong in [VALIDATION.md](VALIDATION.md); architecture decisions
in [CONTEXT.md](CONTEXT.md); active tasks and question references in
[the German diary](../todo.md). The
[pre-cleanup snapshot](archive/2026-10-13/IMPLEMENTATION_PLAN.md) preserves older plans.

## 1. Publish and accept the locally tagged v0.3.8 changes

The target host runs published v0.3.7. Local tag v0.3.8 adds the battery energy
return ratio, Basic derating reason and Basic ISO Home Manager plant time, with
Advanced raw Unix seconds. The local suite has 253 passing tests, lint and
Compose parity; hosted publication and live acceptance still require a release
request. See [release notes](RELEASES.md).

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
