# Implementation and acceptance plan

## Current baseline

The Python read runtime, configuration/profile loaders, local adapters, optional portal reader, Homie lifecycle, heartbeat and deterministic offline tests are implemented. Actual SMA/MQTT deployment and full openHAB continuity remain unverified. The three bundled inverter profiles are identity-only; normal polling is blocked before network access. Confirmed local eCharger commands are the next functional milestone alongside telemetry acceptance; publication remains a later milestone.

The obsolete C++ diagnostic runtime and compiler/container scripts have been removed. Keep the original [baseline provenance](BASELINE.md), import manifest and [MIT attribution](THIRD_PARTY.md). Private original references remain read-only. Historical scaffold checks are archived under `docs/archive/`.

## Implemented foundation

- Typed configuration with precedence built-in/profile defaults < optional JSON < explicit `SMAB_` ENV. Every source has its own activation flag; disabled sources perform no device I/O. Root `smab.env` is private; `smab.example.env` documents all variables. Configuration files live under `data/sma-mqtt-bridge/` and `/data/sma-mqtt-bridge` in the container; persistent runtime state uses the named Compose volume `data_smab_state` at its `state/` child path.
- File-based reusable inverter profiles, strict schema/path/identity checks, host overrides and `file:<name>.json`. No invented registers or model-specific adapter branches.
- Generic read-only Modbus, Home Manager meter telegrams, separate eCharger HTTPS API and SEMP, and optional ennexOS minimum PV share through a normal portal account. No paid Developer API or evcc substitution.
- Bounded timeouts, supervised reconnection with jitter, separate local/portal sessions, verified TLS, redacted diagnostics and controlled shutdown. Authentication challenges block repeated login attempts.
- Homie 4 discovery, one client/Last Will per device, independent source freshness, retained retirement and unavailable values instead of zero. No `/set` subscriptions or device-write paths.
- Atomic main-loop heartbeat and local healthcheck separate from device/MQTT availability.
- One `Dockerfile-SMAB` using the stable official Python 3.14.8 slim-trixie index verified on 2026-10-10. The 3.15.0 stable slim tag was absent when selected; recheck stable official tags before future image updates.
- Standalone Compose files with identical runtime options: development builds locally; example pulls GHCR. `ressources/` holds image inputs only (Python package, bundled profiles and requirements), copied into `/app`. Examples and tooling remain outside it. Root Compose/ENV/build-context files remain directly usable by editors and Compose.
- Offline tests, complete repository lint, Compose parity/override checks and prepared amd64/arm64 CI. Release is prepared for stable tags but has not run.

Sources: [official Python images](https://hub.docker.com/_/python), [configuration contract](CONFIGURATION.md), [profile schema](PROFILES.md), [validation evidence](VALIDATION.md).

## Next: accept the read adapters on the target installation

1. Start on the Mac, as requested. Reconcile local host/model/firmware/serial identities and build validated register profiles from the existing Things and matching official SMA evidence. The user has no additional validated profiles; do not wait for another chat to provide them. The sanitized [Things inventory](../reference/inverter-things-inventory.json) preserves all 41 channels and 19 FC04 pollers without authorizing polling. Preserve raw types, units, sentinel handling and per-poller sampling. The unrelated Sunny Boy -40 register list is not evidence for the installed -41.
2. Verify MQTT hostname, TLS trust and topic permissions on the Mac. Check host directory permissions for the configured UID/GID. Keep all untested sources disabled until their required configuration is supplied. Follow the [Mac acceptance steps](MAC_TEST.md).
3. Enable one read source at a time. Verify Home Manager UDP multicast/interface/serial filtering separately; Docker Desktop host networking is optional from 4.34 and does not expose native host interfaces like Linux. If LAN multicast is unavailable in the container, test the existing Python receiver natively on the Mac before Linux/Pi acceptance. Compare the four existing total power/energy values. Verify eCharger SEMP identity, local HTTPS certificate hostname/CA, API identity, timestamps and raw units. Portal and local sessions remain independent.
4. Capture sanitized real protocol fixtures without credentials, tokens or installation identifiers. Compare representative live values against openHAB at aligned times, including stale/partial responses, reconnect and container stop behavior.

Missing input for one device must not block independent foundation or adapter work. Use the existing [value catalogue](WERTEKATALOG.md) and [migration ledger](migration-coverage.csv); do not repeat completed inventories or alter private originals.

## Then: finish openHAB continuity

Reconcile all 100 migration rows and preserve exact Item names, quantity units, maps, counter offsets, polling intervals, calculations, rules, UI links and persistence dependencies. Keep Shelly-derived charging state, Smart-Grid consumers and InfluxDB history in openHAB until equivalent behavior is accepted. Seven inverter3 Item links and complete rule/UI audits remain open. Homie discovery alone does not migrate existing Item links.

Provide example Items, sitemap and MainUI widget only for implemented properties and confirmed commands. Consult official [MQTT/Homie](https://www.openhab.org/addons/bindings/homie/), [Modbus](https://www.openhab.org/addons/bindings/modbus/), [Items](https://www.openhab.org/docs/configuration/items.html) and [persistence](https://www.openhab.org/docs/configuration/persistence.html) documentation. Keep every ledger row pending until its actual acceptance is recorded.

## Next functional milestone: confirmed local commands

Home Manager remains the charging regulator. Introduce only confirmed command allowlists with identity, metadata, rights, unit/bounds checks and readback; expose measurements as non-settable. Reject retained-command replay, writes on startup/reconnection and duplicate write retries after uncertain outcomes. Live writes require a concrete user-requested action.

Implement the confirmed local enum/boolean controls first: charging mode, release, approval, stop-when-full, cable locking, status/ambient brightness and ambient enablement. Planned charging requires a separate confirmed energy/end-time transaction before mode activation. Keep energy and stop-delay setters blocked until local units/scaling are verified. Maximum charging power remains a separate unresolved mapping/bounds task; the existing metadata minimum does not authorize a 4 kW limit or silent rounding. Portal preference writes follow separately.

## Later: publication

GitHub upload and GHCR publication remain later tasks. The authorized cleanup checkpoint is a local Git commit only. Before publication, execute hosted CI/security scans, verify the image source namespace and choose release tags; do not infer successful CI from local workflow files. Maintain the German project diary after each milestone.

## Current installation step, 2026-10-10

The inverter profile blocker is resolved for the original 41-channel read baseline: official model-specific lists, local identity checks and live MQTT publication are recorded in REGISTER_VALIDATION.md. Complete openHAB value/dependency comparison remains pending. SEMP is active; API/portal await private credentials. Home Manager is prepared but intentionally disabled on the Mac and awaits Pi-network acceptance. Explicit MQTT/local-wallbox TLS_VERIFY=false overrides are supported at Andreas' request; safe defaults and portal verification remain intact.

## Initial local command implementation, 2026-10-10

The first enum/boolean allowlist is now implemented behind global and local API gates, both false by default. It covers fast/PV/stop mode, release, approval requirement, stop-when-full, cable locking and status/ambient lighting. Target mode 4720, stop-delay writes, plan transactions and portal writes remain blocked. Fresh identity/rights/choice checks, serialized read/write access, exact reference PUT payload, confirmed readback, retained replay rejection and a durable uncertain-write journal are included. See CONFIGURATION.md. Offline tests do not certify a live action; the private installation remains read-only.

## Home Manager Modbus read transport, 2026-10-10

The requested alternative transport is implemented with all officially documented readable Unit 1/2 entries, the complete assignment table and delegated read parameter templates. Unit 1 identity, request pacing, persistent sessions, independent rejected-block handling and changing Homie inventory are offline tested. Select `SMAB_HOME_MANAGER_TRANSPORT=modbus-tcp` only with the independently enabled source, real host and serial. Default UDP selection is unchanged. [Home Manager Modbus](HOME_MANAGER_MODBUS.md) records access restrictions and the still-required Pi/firmware/openHAB acceptance; no NSD activation or Grid Guard write is performed automatically.
