# Architecture and project decisions

This document records the architecture and scope decisions. The
[current acceptance matrix](VALIDATION.md) owns status and evidence; the
[implementation plan](IMPLEMENTATION_PLAN.md) contains future milestones.
Earlier protocol investigations and decisions remain in the
[working-document archive](archive/README.md).

## Scope and ownership

One Python Docker service integrates three SMA inverters, Sunny Home Manager 2.0
and SMA eCharger with Homie 4 MQTT. Raspberry Pi 5 with a 64-bit system is the
primary target. Home Manager remains the charging controller. The bridge supplies
measurements and explicitly requested, allowlisted preferences and controls.

Prefer local measurements and local eCharger settings. Use the existing ennexOS
web-portal API only where needed, initially for minimum PV percentage. A paid SMA
Developer API and replacing the charging controller with evcc are outside scope.
Local wallbox and portal authentication are separate sessions.

The installed eCharger model/firmware evidence is EVC22-3AC-20 / 2.6.37.R.
Model-dependent units or writable choices require matching metadata or a narrowly
verified fallback. Do not extend one device's protocol assumptions to other SMA
models. Private installation identities and original exports stay in ignored,
read-only reference files.

## Configuration and deployment

The binding contract is [CONFIGURATION.md](CONFIGURATION.md). Every operational
setting has a typed default and an explicit `SMAB_` environment override. Precedence
is built-in/profile defaults < optional JSON configuration < explicit environment.
Validate configuration before network connections. Credentials and addresses have
empty defaults and are required only for enabled sources that need them.

Each inverter, Home Manager transport, local API, SEMP reader and portal adapter
has its own configuration and activation flag. Credentials or an address never
implicitly enable a source. Disabled adapters perform no device I/O.

Root `smab.env` is private; `smab.example.env` documents all supported variables.
Optional JSON, reusable profiles, certificates and password files live under
`data/sma-mqtt-bridge/`, mounted at `/data/sma-mqtt-bridge`. Persistent state uses
`data_smab_state` at `/data/sma-mqtt-bridge/state`. Preserve the topic manifest,
command uncertainty journals and process-lock protection during storage changes.
Resolved environment secrets must never be written into generated configuration.

Both standalone Compose files share runtime settings. Development builds
`Dockerfile-SMAB`; the example selects a GHCR image after publication.
`ressources/` contains image inputs only: the Python package, bundled profiles and
runtime dependencies, copied into `/app`. Documentation and tooling stay outside it.
Use a verified stable official Python image; recheck published tags before updates.

TLS verification defaults to enabled. Only explicit local-wallbox or MQTT
`TLS_VERIFY=false` overrides are supported. Portal verification is mandatory;
certificate download alone does not establish trust.

## Read adapters and units

Inverter models use [file-based profiles](PROFILES.md), with bundled defaults and
host overrides. New models must be addable without model-specific adapter code.
Identity-only descriptors remain blocked for polling. Register types, sentinels,
units, signed values and independent poller intervals require model-specific evidence.
The original 41-channel baseline is documented in
[register validation](REGISTER_VALIDATION.md).

Home Manager offers separate UDP meter and Modbus TCP read transports; selecting
one does not imply that every setting is available through it. Unit tables, access
restrictions and delegated reads are documented in
[HOME_MANAGER_MODBUS.md](HOME_MANAGER_MODBUS.md). Linux multicast/interface/VLAN
acceptance is distinct from Modbus acceptance.

The eCharger local API uses `/api/v1/token`, `/parameters/search`,
`/measurements/live` and the allowlisted parameter-write endpoint. SEMP is a
separate public XML reader. Preserve source units and timestamps; static metadata
alone does not prove a live channel exists. Unit evidence and its acceptance limits
are linked from [VALIDATION.md](VALIDATION.md#unit-and-protocol-evidence).

Portal minimum PV is a preference. Its complementary allowed grid share is
`100 - minPvPercentage`; neither is a measurement of current charging mix. Observed
consumer-balance PV/battery/grid percentages describe period energy shares. A live
charging-mix feature needs a verified endpoint, timestamp and consumer association.

## Commands and uncertainty

Only confirmed writable parameters belong on Homie `/set`; measurements remain
non-settable. Independent global, local and portal gates default to disabled.
Validate identity, permissions, metadata choices, units and bounds before a write.
Read back the device setting before publishing confirmation. HTTP success alone
cannot establish completion.

Local enum/boolean controls, combined energy/end-time plans and portal PV updates
have distinct contracts in [CONFIGURATION.md](CONFIGURATION.md). Confirm both plan
targets before activating target mode. Preserve unrelated portal options. Maximum
power and possible future phase controls have additional
[mapping and acceptance requirements](ECHARGER_POWER_LIMIT.md).

Reject retained-command replay and writes on startup or reconnection. An ambiguous
response records uncertainty and blocks duplicate retries; recovery must preserve
that journal. openHAB command Items use device readback rather than optimistic
state updates. Device setting confirmation does not prove completed physical charging.

## Availability and MQTT

Supervise sources and MQTT independently with bounded backoff and read watchdogs.
Docker health checks main-loop progress; source and broker availability have their
own diagnostics. A single device outage must not force a restart loop.

Retained measurements represent the last valid observation. Invalid, stale or missing
samples must not become fabricated zeros; readiness describes freshness separately.
Keep receipt timestamps distinct from device measurement timestamps. The remaining
freshness gap and offline MQTT cleanup evidence are tracked in the acceptance matrix.

Owned topic names are persisted for retirement after source/ID/prefix changes.
Preserve the state volume to clean up old discovery. Moving brokers also requires
retirement on the old broker. One client and Last Will per Homie device maintain
independent availability. Commands are never replayed during recovery.

## openHAB continuity and repository maintenance

Keep existing Items, maps, offsets, rules, units, UI dependencies and persistence
until each [migration-ledger](migration-coverage.csv) row is accepted.
[MIGRATION.md](MIGRATION.md) records the existing calculations, InfluxDB day boundaries,
Shelly dependencies and remaining inventory gaps. They initially stay in openHAB.

The maintained [MainUI guide](../openHAB/openHAB.md) and
[garage widget guide](../openHAB/echarger-comfort.md) use existing Items. Example Item
files and sitemaps were removed from scope at the user's request.
The garage widget has one canonical YAML source and a generated manual-import file;
its exporter and lint check prevent divergent copies. Consult
[official openHAB documentation](https://www.openhab.org/docs/) for integration work.

Keep active German tasks and decisions in [todo.md](../todo.md). Archive earlier
working documents without deleting entries or unresolved questions. Configuration,
profile, migration and technical evidence documents remain maintained contracts.
GitHub publication and releases require a separate later milestone.

## Complete register coverage decision, 2026-10-12

The goal includes all verified readable device values and readable configurable
parameters, beyond the original openHAB baseline. The
[Modbus completeness audit](MODBUS_TOPIC_AUDIT.md) inventories candidates without
preselecting basic/advanced/diagnostics; agree those groups with Andreas. Keep
documentary evidence, implemented mappings and observed live support distinct.
RW/WO inventory does not alter command allowlists or authorize device writes.

## Availability-first scope refinement, 2026-10-12

Andreas clarified that the full register inventory is evidence for selection, not
a target to publish every address. First run one read-only availability scan while
both PV inverters produce. Then choose useful Smart Home properties together.
Exclude missing values from the initial candidate set while preserving the tested
operating-state evidence; valid zero is available, and transport failure is not
proof of unsupported registers. Agree channel groups after this selection.
