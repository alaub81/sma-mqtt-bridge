# Implementation and acceptance plan

This plan contains future work. Implemented capabilities and live acceptance are
recorded in [VALIDATION.md](VALIDATION.md); architecture decisions live in
[CONTEXT.md](CONTEXT.md). The [German diary](../todo.md) tracks active tasks and
questions. Earlier plans remain in the [archive](archive/README.md).

## 1. Resolve the code-review findings

Use deterministic regression cases before changing behavior. Preserve existing
Channel IDs, retained last-known measurements and all uncertainty guards.

The API confirmation/unit, integer-payload, node-metadata, MQTT future and CLI findings are resolved
offline; see the acceptance matrix.
The remaining review findings are:

1. Accept the scoped eCharger remaining-lifetime correction on the installation.
   Periodically refreshed channels now retain device age through processing;
   see [the implementation evidence](VALIDATION.md#scoped-echarger-remaining-lifetime-correction-2026-10-12).
   Classify the remaining phase-voltage/power, alternate-counter and fixed old
   state channels independently. Agree session-energy idle authority and reset
   semantics before changing that filter. Review 4 remains partially open.
   Follow the targeted observation/UI criteria in
   [the freshness investigation](VALIDATION.md#measurement-freshness-investigation-2026-10-11).

Run complete lint, offline tests and Compose parity. Record evidence and unresolved
limits in the acceptance matrix. Green tests alone do not close a proven review gap.

## 2. Complete operational acceptance

Continue target-host operational acceptance beyond the completed checks. Source
availability with optional diagnostics disabled, startup summary, Home Manager
init/ready and eCharger total-energy kWh checks were accepted by the user on
2026-10-11; see the acceptance matrix. Preserve the existing state volume and
command journals.

- Verify inverter morning wake-up after the reported successful evening behavior;
  distinguish sleep from a connection or data-quality failure.
- Accept remaining target-host fault scenarios and measure real resource behavior.
  Extended virtual twelve-hour supervisor/MQTT sequences and repeated actual
  watchdog cancellations are implemented; see
  [operational evidence](OPERATIONAL_ACCEPTANCE.md#extended-deterministic-fault-sequences-2026-10-12).
  They verify recovery/session cleanup, not a real memory/network soak.
- Test abrupt process/host failures, Last Will, broker restart, TLS trust and topic
  retirement. Controlled stop/start acceptance does not cover these failures.
- External monitoring and alarm setup was reported complete by the user on
  2026-10-11. Verify host reboot and state restoration; record specific monitored
  signals and alarm scenarios when evidence is available.
- For Home Manager Modbus deployment, evaluate the planned switch from host to
  Docker bridge networking in both Compose files. Verify device, broker, DNS and
  TLS reachability; retain UDP multicast as an independently documented alternative.
- Accept Pi multicast only when UDP is actually selected. Direct Modbus evidence
  does not certify UDP/interface/VLAN behavior.

Follow the [installation test procedure](MAC_TEST.md). A live write still requires
an explicitly requested action with concrete target values.

## 3. Finish openHAB and history continuity

Accept all 100 [migration rows](migration-coverage.csv) through aligned parallel
measurements, not discovery alone. Resolve the seven inverter channels without an
identified Item and the remaining rule/UI/persistence inventory. Preserve Item names,
maps, private counter offsets, quantity units, polling and history semantics.

Build Grafana comparisons of existing openHAB and bridge time series with matching
units and measurement times. Verify energy scaling, midnight/DST boundaries, gaps
and restart behavior for remaining migration capabilities. The eCharger total-energy
kWh unit, scaling and existing history were accepted by the user on 2026-10-11;
see the acceptance matrix.

Keep Shelly-derived charging state, Smart-Grid consumers and InfluxDB calculations
in openHAB until equivalent behavior is accepted. Maintain
[the MainUI guide](../openHAB/openHAB.md); prepare the requested lhlab.wiki article
only after the installation procedure is accepted. No example Item or sitemap files
are planned.

## 4. Verify charging semantics and assess small features

- Observe physical target charging, session-energy semantics and the return from
  target mode. Reported 10-kWh plan transmission and mode activation do not settle
  cumulative-versus-additional energy or completed charging.
- Accept maximum-power limiting with explicitly requested values and measured phase
  currents/power. Investigate winter single-phase behavior and minimum current using
  [the power-limit evidence](ECHARGER_POWER_LIMIT.md). Add a setter only after its
  metadata, bounds, units and controller interaction are confirmed.
- Verify any additional portal values and a current charging mix from actual
  timestamped API evidence; period shares and minimum PV preference are insufficient.
- Consider a read-only runtime diagnostic command, per-property age/quality and an
  explicit portal read refresh without restarting a zero-interval service.

Choose one evidenced improvement at a time. Keep Home Manager as charging controller;
no paid Developer API or replacement regulation is planned.

## 5. Simplify maintenance incrementally

After correctness fixes, split large configuration/session/command functions into
small named steps where this removes duplicated responsibilities. Named immutable
setting definitions are implemented and checked against the previous mappings.
Simplify repeated widget
expressions only with preserved gating and visible behavior.

Consider selected additional lint rules in focused changes; formatting and import
ordering are already enforced by the repository check.
Do not convert style hints into a broad rewrite or introduce a generic adapter platform.
Keep current status in one acceptance matrix and archive completed diary periods.

## 6. Prepare publication and release

Publication remains separately authorized work. Before a GitHub upload or GHCR
release, verify private-data exclusions, namespace/tags, hosted CI/security scans and
amd64/arm64 images. Recheck stable official Python tags before updating the image.
The release workflow now requires the reusable full CI for the tagged commit before
publication, including lint, tests, Compose checks and amd64/arm64 image builds,
container tests and scans. Repeated successful hosted runs of the existing CI were
reported by the user on 2026-10-11. Verify the newly added release-to-CI dependency
in a hosted run; release publication remains separately authorized.

## Complete model-specific Modbus coverage

Use the [full topic audit](MODBUS_TOPIC_AUDIT.md) as the expansion ledger. Validate
all readable measurements and RW observations in coherent groups, preserving
existing IDs and separating alternative counters and conditional equipment. Agree
basic/advanced/diagnostics with Andreas before assigning new groups. File-based
profile extensions need verified units, enums/sentinels and suitable poll intervals.
Review WO/RW commands separately; documentation access flags alone never enable setters.
