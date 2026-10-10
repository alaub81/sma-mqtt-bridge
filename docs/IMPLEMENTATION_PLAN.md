# Implementation plan

## Current milestone: repository foundation

Prepared: Git-ready source layout, inherited Docker/CI/lint foundations, diagnostic C++ executable, offline tests, protocol handoff and private reference directory. No SMA or MQTT runtime is implemented yet. No GitHub repository or image has been published.

## 1. Inventory the existing installation

Read incoming openHAB Things, Items, transformations, rules, persistence and UI exports. Fill `docs/migration-coverage.csv`. Record all units, decimal scaling, register addresses, byte/word order, Modbus function and unit IDs, update intervals, invalid sentinels, counters and calculated properties. Obtain inverter models/firmware, Home Manager details and deployment network requirements.

Every existing capability needs a bridge property or an explicit preserved openHAB calculation. Do not guess inverter register mappings from a different SMA model.

## 2. Implement the common runtime

Configuration loading, independently managed source sessions, scheduling, timeouts, bounded reconnection and redacted diagnostics. Adopt the useful BMW MQTT/TLS/watchdog patterns, but separate device adapters from MQTT publishing. MQTT metadata and retained state must reflect actual source availability and sample timestamps.

## 3. Implement read adapters

- Inverters: configured local Modbus profiles reproducing the supplied mappings.
- Home Manager: local meter protocol and serial/interface selection; check UDP multicast delivery on the deployment host.
- eCharger: confirmed local parameters/live data and SEMP as appropriate.
- Portal: optional normal-account session and explicit retrieval of minimum PV percentage; no paid developer API.

Create sanitized fixtures from actual responses. Use deterministic tests for byte order, units, counters, unknown/invalid values, auth expiry and partial responses. Do not replace unavailable values with zero.

## 4. Homie discovery and migration

Stable configurable device IDs, nodes, property metadata, units and correct Homie types. Describe only confirmed writable properties with `$settable=true`; subscribe to non-retained `/set` commands. Retained state reports confirmed values. Handle retained incoming commands and command replay explicitly. Define source freshness independently from MQTT connection health.

Existing BMW Homie code is useful for retained discovery, reconnect and Last Will handling, but VIN-specific names and telemetry-only assumptions need redesign. Check Homie ID rules and openHAB compatibility directly rather than copying historical quirks.

Supply migration examples linking existing Item names to new channels so rules, widgets and persistence continue to work. Discovery does not automatically migrate old Item links.

## 5. Command adapters

Port only the confirmed wallbox option allowlist, then optional portal minimum PV share. Validate rights/limits and preserve unrelated settings. Publish readback results and explicit pending/failed/uncertain outcomes. Preserve Home Manager as the sole charging regulator; do not send competing SEMP power recommendations.

Initially verify commands only through mocked protocol tests. A live command must follow a user-requested test and use a known reversible setting.

## 6. Acceptance and publication

Reconcile every migration row against the old openHAB integration. Compare representative live values at aligned sample times. Verify MQTT reconnect, stale source behavior, command readback, token expiry and container shutdown. Run offline tests, all linters and Docker builds.

After the user chooses GitHub repository visibility and authorizes publication, create the remote repository and configure GHCR. Do not assume that a workflow file or local Git commit means GitHub CI has run successfully.
