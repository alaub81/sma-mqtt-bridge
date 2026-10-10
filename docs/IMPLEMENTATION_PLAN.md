# Implementation plan

## Current milestone: repository foundation

Prepared: Git-ready source layout, inherited Docker/CI/lint foundations, diagnostic C++ executable, offline tests, protocol handoff and private reference directory. No SMA or MQTT runtime is implemented yet. No GitHub repository or image has been published.

## Decisions recorded on 2026-10-10

The target runtime is Python, as explicitly chosen by the user. The existing C++ executable and Dockerfiles remain the historical diagnostic scaffold until the first Python implementation. Preserve `docs/BASELINE.md` as provenance rather than rewriting the original validation history.

Use the newest published stable official Python image, with an explicit version and Debian slim variant. As checked on 2026-10-10, `python:3.14.8-slim-trixie` is published (registry index digest `sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170`). Python 3.15.0 was released on 2026-10-09, but `python:3.15.0-slim-trixie` returned not found. Recheck before the Python Dockerfile is implemented; use the newest stable published tag then. Do not choose an RC to match the newest language version.

Sources: [Python releases](https://www.python.org/downloads/), [official Python images](https://hub.docker.com/_/python).

Local MQTT connection settings were copied from BMW-MQTT-Bridge into the ignored `.env`, with file mode 0600. BMW client IDs, topic prefixes and unrelated credentials were excluded. The new base client ID is `sma-mqtt-bridge`; certificate verification stays enabled. The scaffold does not load this configuration and no connection was attempted.

The subsequent configuration decision uses `SMAB_` exclusively. The private MQTT configuration has been migrated to `data/sma-mqtt-bridge/.env` with its values and file mode preserved. Follow [the configuration contract](CONFIGURATION.md): each inverter, Home Manager, eCharger and portal source has its own enabled flag and connection settings; built-in defaults and optional JSON are overridden by explicit ENV values. The host directory `./data/sma-mqtt-bridge/` contains configuration, profiles, certificates and state, bind-mounted to `/data/sma-mqtt-bridge`. No second configuration file is mandatory. Disabled sources perform no device I/O; validate enabled sources before connecting.

Maintain [the project diary](../todo.md) after each work session, including outstanding inputs and questions. Read exports from both `private/incoming/openhab/` and `private/things/`; original exports remain unchanged.

The deployment target is a Raspberry Pi 5 running a 64-bit system, so the primary Linux image platform is `linux/arm64`. Exact OS, Docker/Compose versions and LAN/VLAN/multicast setup remain pending; the persistent host bind directory is now specified above. Exact hardware designations have now been confirmed in ennexOS. Additional matching device register profiles are still expected from another chat; consume its delivered findings rather than duplicating that research.

## Reliability requirements inherited from BMW

- Run independent source adapters under supervision; one unavailable source must not stop the others.
- Bound connection and read timeouts, reconnect with capped backoff and jitter, and rebuild a stalled MQTT client after a supervised timeout. Port behavior into Python rather than copying C++ thread mechanics.
- Preserve verified TLS, independent token lifetimes, redacted diagnostics and separate local/portal sessions.
- Publish retained Homie discovery and confirmed state; reannounce on reconnect. Assign unique client IDs and a Last Will per advertised Homie device.
- Distinguish process liveness, MQTT availability and freshness of each source. A cached value is not a fresh sample; never substitute zero for missing data.
- Write an atomic heartbeat from the main loop and provide a local Docker health check. Adapter callbacks alone must not keep a blocked main loop apparently healthy. Define outage thresholds separately from restart policy.
- On SIGTERM, stop polling, persist necessary non-secret state, publish disconnected state and wait a bounded time for acknowledgement. If acknowledgement fails, allow the broker's Last Will to report the loss.
- Never replay retained commands or retry an uncertain write. Begin the first runtime milestone with reads and deterministic fixtures.

## 1. Inventory the existing installation

Read incoming openHAB Things, Items, transformations, rules, persistence and UI exports. Fill `docs/migration-coverage.csv`. Record all units, decimal scaling, register addresses, byte/word order, Modbus function and unit IDs, update intervals, invalid sentinels, counters and calculated properties. Obtain inverter models/firmware, Home Manager details and deployment network requirements.

The first two inverter exports define 41 active data Things and 19 pollers across three devices. All five referenced JS transforms and further maps/energy-offset transforms were inspected. The later MainUI inventory confirms 34 inverter Item links, four Home Manager Items and ten derived capabilities; the ledger now preserves 100 rows. Remaining links, raw scaling and complete automation/persistence/UI dependencies still need review. Exact model/firmware identification is confirmed through ennexOS; matching complete register profiles remain pending. See `docs/MIGRATION.md` and `todo.md` for the current inventory.

Every existing capability needs a bridge property or an explicit preserved openHAB calculation. Do not guess inverter register mappings from a different SMA model.

The German [value catalogue](WERTEKATALOG.md) supplies the current register/parameter/SEMP inventory and topic proposals, including 458 parameter metadata rows exported through the authenticated portal. Read-only ennexOS access confirmed exact installed models/firmware; local host identities and matching complete register profiles remain pending. The supplied Sunny Boy -40 list does not validate the installed -41 profile. Review catalogue evidence and unresolved units before adapter work. Keep all existing ledger rows pending until protocol behavior and openHAB dependencies are checked.

Home Manager NSD Modbus is a separate, currently portal-disabled server feature with Grid Guard requirements; local meter telegrams remain the preferred measurement path. Portal UI settings beyond minimum PV share are inventory candidates, not newly authorized command adapters. The authenticated ennexOS session does not resolve the outstanding openHAB inventory.

## 2. Implement the common runtime

Configuration loading, independently managed source sessions, scheduling, timeouts, bounded reconnection and redacted diagnostics. Adopt the useful BMW MQTT/TLS/watchdog patterns, but separate device adapters from MQTT publishing. MQTT metadata and retained state must reflect actual source availability and sample timestamps.

Replace the C++ diagnostic executable, compiler-dependent tests and Docker/CI build steps with a buildable Python scaffold before implementing live adapters. Select and pin runtime libraries only after checking current Python compatibility. Support environment-based credentials and a directory of per-inverter profiles.

Implement the configuration contract first, with typed defaults, conditional requirements for enabled sources, deterministic precedence, separate credentials and redacted validation errors. Cover minimal ENV-only configuration, numbered inverter slots, disabled-device behavior, invalid values and secret handling in offline tests. Preserve the imported per-poller intervals unless explicitly overridden; changing the generic default must not silently change existing openHAB sampling behavior.

Implement reusable model profile selection and resolution as described in `profiles/README.md`. Three bundled identity descriptors establish default model IDs; their empty register definitions are deliberately not approved for polling. Package profile resources, validate their schema and support host overrides/new model files without model-specific adapter branches. Test selection independent of slot number, invalid overrides, path containment, identity mismatches and rejection of unvalidated profiles.

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
