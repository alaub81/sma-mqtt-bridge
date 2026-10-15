# Releases and upgrade notes

Images are published at `ghcr.io/alaub81/sma-mqtt-bridge` for Linux amd64/arm64.
Git release tag `v0.3.6` corresponds to image tag `0.3.6`. Stable tag pushes
run reusable CI before the release build/scan/publish steps. `latest`, major and
minor aliases are updated only for the newest stable tag according to the
release workflow. Use an exact version for a reproducible installation.

[Git tags](https://github.com/alaub81/sma-mqtt-bridge/tags) identify the source;
[GitHub Actions](https://github.com/alaub81/sma-mqtt-bridge/actions) contains the
hosted validation and release results. A tag existing alone does not establish
successful image publication. Current installation acceptance belongs in
[VALIDATION.md](VALIDATION.md).

## v0.6.0 — 2026-10-15

- Calculate feed-in remuneration from Home Manager grid export and one explicitly
  configured plant tariff. Legacy inverter production tariffs no longer contribute.
- Add signed Home Manager cumulative import/export offsets in kWh, default zero.
  Publish corrected totals and optional raw diagnostic totals; daily baselines and
  seven-day histories remain unchanged. Apply export correction to earnings once.
- Unify channel names, including batteryenergyreturnratio and grid/totalearnings.
  See the [complete rename map](topic-renames-2026-10-15.csv). Relink existing
  openHAB Items in place and remove previous openHAB energy offsets to avoid
  double correction. Preserve Item names and persisted histories.
- Remove the unsupported Wallbox frequency property.

Local validation: 389 offline tests, complete lint, generated catalog and Compose
parity passed. Publication and target-host deployment are not confirmed by these
local checks. Configure private tariffs/offsets separately and preserve the state
volume; no energy-baseline reset is required.

## v0.3.11 — 2026-10-13

- Heartbeats retain atomic replacement and existing liveness checks without forcing
  disk sync. Command uncertainty journals and topic ownership remain durable.
- Reuse immutable source metadata and MQTT descriptions with inventory/flag/monitor
  invalidation; measurements, freshness, identity and command rights stay current.
- Bound observation payload expansion before allocating fixed-point strings.
  `SMAB_MAX_PAYLOAD_BYTES` / JSON `runtime.maxPayloadBytes` defaults to 4096 UTF-8
  bytes. Normal telemetry is unchanged; invalid/oversized values preserve the
  last-known retained observation and never fabricate zero.
- Extend the separately copied Linux resource recorder with cgroup block I/O,
  process logical/storage counters and continuity-safe rates. Missing metrics
  remain null; device/process changes and resets invalidate rates. No process or
  container identities are saved. Host Python 3.9+ remains supported.

Local validation: 275 offline tests, complete lint and Compose parity, plus all
275 tests in each local ARM64/AMD64 release image with exact version 0.3.11.
Hosted [CI](https://github.com/alaub81/sma-mqtt-bridge/actions/runs/38454497216)
and [release](https://github.com/alaub81/sma-mqtt-bridge/actions/runs/38454496808)
completed successfully, including both container suites and security gates.
GHCR publishes `0.3.11` for Linux amd64/arm64, index digest
`sha256:39512557b7da42d7f3bb0a6da251d746ec1620b42d3f521399637667d057aedc`.
Andreas performs deployment. Preserve the state volume and existing installation
settings. The host recorder must be copied again independently of the image;
see [the overnight comparison instructions](OPERATIONAL_ACCEPTANCE.md#bounded-linux-host-resource-recording).
The old resource recording provides a CPU baseline, but no storage baseline.

## v0.3.10 — 2026-10-13

Includes the shared strict JSON decoder, equivalent Modbus property metadata
construction, simplified widget expressions and focused correctness lint rules.
The existing topics, polling, device settings and uncertainty protection remain.
Hosted [CI](https://github.com/alaub81/sma-mqtt-bridge/actions/runs/38449973600)
and [release](https://github.com/alaub81/sma-mqtt-bridge/actions/runs/38450118099)
completed successfully. No new target-host version is inferred from publication.

## v0.3.9 — 2026-10-13 (historical baseline tag)

At Andreas' request, this annotated local tag points to `e1c9a2d`, the last
commit before the shared JSON decoder and widget-expression refactoring in
`73a60bd`. It includes the v0.3.8 features and focused lint rules, but neither
refactoring. The existing branch history was not rewritten.

An isolated source snapshot of the tagged commit passed all **253 offline tests**,
complete lint over 140 public files and Compose parity/overrides. The tag is a
source rollback point. At that checkpoint publication was pending; the later
[hosted release](https://github.com/alaub81/sma-mqtt-bridge/actions/runs/38450117939)
completed successfully. No deployment is inferred. Refactorings follow this tag.

## v0.3.8 — 2026-10-13

Prepared locally with 253 passing offline tests, complete lint and Compose parity.
The later [hosted release](https://github.com/alaub81/sma-mqtt-bridge/actions/runs/38448474116)
completed successfully. Deployment/channel checks below describe the acceptance
limits at preparation; publication alone does not confirm them.

- Home Manager Modbus adds Basic `measurements/planttimeiso`, an ISO 8601 UTC
  string from the existing clock read. Raw `measurements/planttime` becomes
  Advanced. Keep Advanced enabled for existing numeric Items and update host
  overrides before switching links. New openHAB DateTime setup is documented;
  live acceptance and deployment are pending.

- Derating reason is now Basic in all three bundled inverter profiles. Existing
  `diagnostics/deratingreason` IDs and enum values remain; Advanced/Diagnostics
  may be disabled without hiding this property. Host overrides need the matching
  `channelGroup: basic` update; deployment is pending.

- Basic read-only `measurements/batteryefficiency` (%) derives the cumulative
  discharged/charged energy ratio from a profile's same-poll kWh battery counters.
  No extra Modbus request, counter/history change or readiness dependency.
  See [the calculation and interpretation](REGISTER_VALIDATION.md#derived-battery-energy-return-ratio-2026-10-13).
  Physical interpretation and deployment acceptance remain separate from publication.

## v0.3.7 — 2026-10-13

- `measurements/vehiclestatuscode` is now a basic eCharger channel. Its ID,
  integer values, read-only metadata and timestamp policy are preserved.
- An enabled portal adapter accepts `refresh` on `portal/refresh/set` without
  preference-write gates. It wakes the existing read supervisor, coalesces
  requests and reports progress on `portal/refresh`. Read deadlines,
  authentication blocking and retry backoff remain in force. Interval zero is
  supported without a startup read unless explicitly requested.
- MainUI setup documents the portal refresh button, Home Manager plant-time
  display/DateTime link and minimum-PV sliders. Existing Items/history remain.
- Extended deterministic outage tests and a reusable external resource recorder
  accompany the release. Andreas accepted the stable 22-hour resource baseline;
  see [the analysis](RESOURCE_SOAK_ANALYSIS_2026-10-13.md).
- Further optional extensions are deferred; additional API-only fallback mappings
  for operation without SEMP are removed from scope. Existing mappings remain.

Validation: 247 local offline tests, complete lint and Compose parity; hosted
CI and release checks passed for amd64/arm64. GHCR 0.3.7 was published and deployed
on the target host, with version 0.3.7, healthy and all data sources/MQTT recovered.
Detailed workflow links, digest and acceptance limits are in
[VALIDATION.md](VALIDATION.md#v037-release-and-target-host-deployment-2026-10-13).

The new refresh channel needs discovery after upgrade. Follow the
[MainUI instructions](../openHAB/openHAB.md#manual-portal-refresh); do not send
retained refresh requests or add automatic replay rules.

## v0.3.6 — 2026-10-12

Preserve remaining measurement lifetime for the eCharger channels classified as
periodically refreshed: charging power, API phase current, primary total charging
energy, vehicle-status aliases and three SEMP plant-control setpoints. Device age
survives parsing, and subsequent processing consumes the remaining lifetime.
Repeated receipt of an unchanged device timestamp no longer extends that deadline.
An unchanged numeric value with a new timestamp still refreshes it.

There are no new ENV settings, MQTT IDs, writable properties or polling requests.
Selected source properties may expire earlier during delayed/stale responses;
readiness follows the existing required-property rules. MQTT retains last-known
observations. Session energy and unresolved timestamp families keep their existing
policy; see [the timestamp evidence](ECHARGER_TIMESTAMP_ANALYSIS_2026-10-12.md).
Full freshness/openHAB acceptance remains separate from healthy startup.

Release validation: 232 offline tests, complete local lint and Compose parity.
Andreas reported v0.3.6 pulled from GHCR and healthy on the target host. This is
installation evidence, not a direct inspection of every hosted workflow job.

## Upgrade procedure

1. Read the target version's changes and check configuration/profile overrides.
   Back up private configuration and persistent state using the installation's
   existing procedure. Preserve the same Compose project and state volume;
   the topic manifest and command uncertainty journals must survive replacement.
2. Set `SMAB_BRIDGE_VERSION` in root `smab.env` to the exact image version.
   With the standalone example file:

   ```sh
   docker compose --env-file smab.env -f docker-compose.example.yml pull
   docker compose --env-file smab.env -f docker-compose.example.yml run --rm --no-deps sma-mqtt-bridge --check-config
   docker compose --env-file smab.env -f docker-compose.example.yml up -d
   docker compose --env-file smab.env -f docker-compose.example.yml exec -T sma-mqtt-bridge python -m sma_mqtt_bridge --version
   docker compose --env-file smab.env -f docker-compose.example.yml ps sma-mqtt-bridge
   ```

3. Verify expected image version, healthy container, configured sources and MQTT
   recovery. Compare selected openHAB values/history and read-back settings;
   preserve existing Items, units, offsets and rules. A successful startup does
   not complete every migration or physical charging check.
4. If an upgrade fails, restore the previous pinned image version with the same
   Compose project, mounts and state. Investigate uncertainty journals before
   requesting any command retry. Do not remove the state volume with `down -v`.

A restart alone does not apply a changed image/environment. No command or charge
plan needs to be resent as part of an upgrade. Host profile/translation overrides
can mask bundled additions and need an explicit independent review.
