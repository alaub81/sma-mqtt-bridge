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

Local validation: 247 offline tests, complete lint and Compose parity. Hosted
release validation and deployment are tracked separately in VALIDATION.md.
The image is published by the stable-tag workflow after CI and security checks;
writing these notes alone does not establish publication or installation.

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
