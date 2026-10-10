# Implementation and acceptance plan

## Current baseline

The Python read runtime, configuration/profile loaders, local adapters, optional portal reader, Homie lifecycle, heartbeat and deterministic offline tests are implemented. Actual SMA/MQTT deployment and full openHAB continuity remain unverified. The three bundled inverter profiles are identity-only; normal polling is blocked before network access. Device commands and publication are later milestones.

The obsolete C++ diagnostic runtime and compiler/container scripts have been removed. Keep the original [baseline provenance](BASELINE.md), import manifest and [MIT attribution](THIRD_PARTY.md). Private original references remain read-only. Historical scaffold checks are archived under `docs/archive/`.

## Implemented foundation

- Typed configuration with precedence built-in/profile defaults < optional JSON < explicit `SMAB_` ENV. Every source has its own activation flag; disabled sources perform no device I/O. Root `.env` is private; `.env.example` documents all variables. Other installation files live under `data/sma-mqtt-bridge/` and `/data/sma-mqtt-bridge` in the container.
- File-based reusable inverter profiles, strict schema/path/identity checks, host overrides and `file:<name>.json`. No invented registers or model-specific adapter branches.
- Generic read-only Modbus, Home Manager meter telegrams, separate eCharger HTTPS API and SEMP, and optional ennexOS minimum PV share through a normal portal account. No paid Developer API or evcc substitution.
- Bounded timeouts, supervised reconnection with jitter, separate local/portal sessions, verified TLS, redacted diagnostics and controlled shutdown. Authentication challenges block repeated login attempts.
- Homie 4 discovery, one client/Last Will per device, independent source freshness, retained retirement and unavailable values instead of zero. No `/set` subscriptions or device-write paths.
- Atomic main-loop heartbeat and local healthcheck separate from device/MQTT availability.
- One `Dockerfile-SMAB` using the stable official Python 3.14.8 slim-trixie index verified on 2026-10-10. The 3.15.0 stable slim tag was absent when selected; recheck stable official tags before future image updates.
- Standalone Compose files with identical runtime options: development builds locally; example pulls GHCR. Supplemental deployment files live under `ressources/`. Root Compose/ENV/build-context files remain directly usable by editors and Compose.
- Offline tests, complete repository lint, Compose parity/override checks and prepared amd64/arm64 CI. Release is prepared for stable tags but has not run.

Sources: [official Python images](https://hub.docker.com/_/python), [configuration contract](CONFIGURATION.md), [profile schema](../profiles/README.md), [validation evidence](VALIDATION.md).

## Next: accept the read adapters on the target installation

1. Reconcile local host/model/firmware/serial identities and obtain validated register profiles for all three inverters. Preserve the supplied FC04 blocks, raw types, units, sentinel handling and per-poller sampling. The unrelated Sunny Boy -40 register list is not evidence for the installed -41.
2. Verify MQTT hostname, TLS trust and topic permissions on the Raspberry Pi. Check host directory permissions for the configured UID/GID. Keep all untested sources disabled until their required configuration is supplied.
3. Enable one read source at a time. Verify Home Manager UDP multicast/interface/serial filtering on the Pi; compare the four existing total power/energy values. Verify eCharger SEMP identity, local HTTPS certificate hostname/CA, API identity, timestamps and raw units. Portal and local sessions remain independent.
4. Capture sanitized real protocol fixtures without credentials, tokens or installation identifiers. Compare representative live values against openHAB at aligned times, including stale/partial responses, reconnect and container stop behavior.

Missing input for one device must not block independent foundation or adapter work. Use the existing [value catalogue](WERTEKATALOG.md) and [migration ledger](migration-coverage.csv); do not repeat completed inventories or alter private originals.

## Then: finish openHAB continuity

Reconcile all 100 migration rows and preserve exact Item names, quantity units, maps, counter offsets, polling intervals, calculations, rules, UI links and persistence dependencies. Keep Shelly-derived charging state, Smart-Grid consumers and InfluxDB history in openHAB until equivalent behavior is accepted. Seven inverter3 Item links and complete rule/UI audits remain open. Homie discovery alone does not migrate existing Item links.

Provide example Items, sitemap and MainUI widget only for implemented properties and confirmed commands. Consult official [MQTT/Homie](https://www.openhab.org/addons/bindings/mqtt.homie/), [Modbus](https://www.openhab.org/addons/bindings/modbus/), [Items](https://www.openhab.org/docs/configuration/items.html) and [persistence](https://www.openhab.org/docs/configuration/persistence.html) documentation. Keep every ledger row pending until its actual acceptance is recorded.

## Later: commands and publication

Home Manager remains the charging regulator. Introduce only confirmed command allowlists with identity, metadata, rights, unit/bounds checks and readback; expose measurements as non-settable. Reject retained-command replay, writes on startup/reconnection and duplicate write retries after uncertain outcomes. Live writes require a concrete user-requested action.

GitHub upload and GHCR publication remain later tasks. The authorized cleanup checkpoint is a local Git commit only. Before publication, execute hosted CI/security scans, verify the image source namespace and choose release tags; do not infer successful CI from local workflow files. Maintain the German project diary after each milestone.
