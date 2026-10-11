# Implementation and acceptance plan

This plan contains future work. Implemented capabilities and live acceptance are
recorded in [VALIDATION.md](VALIDATION.md); architecture decisions live in
[CONTEXT.md](CONTEXT.md). The [German diary](../todo.md) tracks active tasks and
questions. Earlier plans remain in the [archive](archive/README.md).

## 1. Resolve the code-review findings

Use deterministic regression cases before changing behavior. Preserve existing
Channel IDs, retained last-known measurements and all uncertainty guards.

The API confirmation/unit and integer-payload findings are resolved offline; see
the acceptance matrix.
The remaining review findings are:

1. Add mandatory, stable Homie node `$type` metadata and verify discovery against
   the [Homie 4 specification](https://homieiot.github.io/specification/spec-core-v4_0_0/).
2. Preserve remaining sample freshness from the device timestamp instead of
   restarting a full lifetime on receipt. Test near-expiry and partial samples.
3. Resolve unhandled MQTT future exceptions during disconnect tests and fail tests
   on unexpected event-loop exceptions. Do not merely suppress diagnostics.
4. Correct CLI project-status capability reporting and module descriptions for
   optional writes and configuration file I/O. The documentation portion is resolved.

Run complete lint, offline tests and Compose parity. Record evidence and unresolved
limits in the acceptance matrix. Green tests alone do not close a proven review gap.

## 2. Complete operational acceptance

Compare the latest image on the target host with the local evidence. Check source
status with optional diagnostics disabled, startup summary, Home Manager init/ready
and energy units. Preserve the existing state volume and command journals.

- Verify inverter morning wake-up after the reported successful evening behavior;
  distinguish sleep from a connection or data-quality failure.
- Add deterministic, multi-hour fault simulation for slow/partial responses,
  device outages and MQTT disconnect/restart. Check recovery, memory and connections.
- Test abrupt process/host failures, Last Will, broker restart, TLS trust and topic
  retirement. Controlled stop/start acceptance does not cover these failures.
- Configure external alarms for unhealthy/stalled processes, broker loss and stale
  critical measurements; verify host reboot and state restoration.
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
and restart behavior. Complete eCharger total-energy kWh deployment and persistence
acceptance without rewriting existing history silently.

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
small named steps where this removes duplicated responsibilities. Consider a small
immutable setting definition instead of positional tuples. Simplify repeated widget
expressions only with preserved gating and visible behavior.

Enable formatter/import-order and selected additional lint rules in focused changes.
Do not convert style hints into a broad rewrite or introduce a generic adapter platform.
Keep current status in one acceptance matrix and archive completed diary periods.

## 6. Prepare publication and release

Publication remains separately authorized work. Before a GitHub upload or GHCR
release, verify private-data exclusions, namespace/tags, hosted CI/security scans and
amd64/arm64 images. Recheck stable official Python tags before updating the image.
Local workflow files and tests do not prove that hosted CI or release jobs have run.
