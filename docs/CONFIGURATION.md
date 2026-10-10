# Configuration contract

Andreas requested this contract on 2026-10-10. It is binding for the Python implementation. **Implemented by the Python loader.** Inverter and SEMP reads have been checked against the installation; complete hardware/openHAB acceptance remains pending. See [register validation](REGISTER_VALIDATION.md).

## Host files and precedence

The private `smab.env` belongs in the repository root next to the Compose files. `smab.example.env` documents every available variable, including its purpose, type and default. Store other installation files under `./data/sma-mqtt-bridge/` relative to the Compose project directory; bind-mount that directory to `/data/sma-mqtt-bridge` in the container:

```text
smab.env               # Explicit overrides and installation credentials, host only
smab.example.env       # Public, fully commented variable reference
data/sma-mqtt-bridge/
  config.json          # Optional non-secret configuration
  profiles/            # Verified register profiles, one or more per inverter
  certificates/        # CA certificates and optional client certificate/key
  secrets/             # Optional password files

Docker volume data_smab_state -> /data/sma-mqtt-bridge/state
                       # Heartbeat and owned MQTT-topic manifest
```

Both Compose files mount the project-scoped named volume `data_smab_state` at the state path, over the configuration bind mount. Docker initializes a fresh volume from the image-owned directory for UID/GID 10001. Keep this volume when replacing containers; `docker compose down -v` deletes it. Changing the Compose project name creates a different volume. Only one bridge instance may write this state. If overriding UID/GID, prepare matching ownership on the state volume; host-file access alone is insufficient. If changing `SMAB_STATE_DIR` or JSON `runtime.stateDir`, also adjust the volume target.

The private `smab.env` and data directory are excluded from Git and Docker build contexts. Compose reads `smab.env` on the host and passes its values into the container; the file itself is not mounted. Keep `smab.env` readable only by its host owner, and secret files/private keys readable only by the owner/container user. Never generate a configuration file containing resolved passwords or session tokens. Do not rewrite user configuration automatically.

The loader uses built-in defaults and selected profile connection defaults, then optional `config.json`, then explicit `SMAB_` environment values. Resolve the profile selector from configuration/ENV first; its defaults never override explicit installation settings. Missing default `config.json` is valid; an explicitly selected missing file or invalid JSON is an error. Profiles supply protocol metadata and per-poller intervals, not credentials or device activation. A device-level interval explicitly set in JSON or ENV overrides all its pollers; otherwise preserve profile intervals and use the default only for pollers without an interval.

Every operational option must be overridable through ENV and documented with type, default and validation. Unknown runtime `SMAB_` keys, malformed values, duplicate device/Homie IDs and conflicting password/password-file settings must fail validation before any connection. Recognize Compose-only variables without treating them as runtime options. An absent variable uses the previous layer; an empty value clears only optional strings. Empty booleans or numbers are errors. Accept boolean `true`/`false` case-insensitively, validate finite positive durations, ports 1–65535 and Modbus unit IDs 1–247. Portal polling accepts zero to mean no periodic polling. Home Manager Modbus pacing/reconnect delays also accept zero; connection/request timeouts and polling intervals remain positive.

JSON is optional, not a second mandatory setup step. JSON names use camelCase as illustrated in [config.example.json](../config.example.json); runtime fields live under `runtime`, MQTT fields under `mqtt`, device fields under their respective sections, and global command settings under `commands`. Compose-only settings are not JSON fields. Credentials use ENV or optional password files.

## Minimal deployment overrides

A broker address and each enabled device's required installation values suffice. All sources and write paths are disabled by default; setting a host or credentials does not enable a source. Enabling an adapter enables bridge access, not the physical inverter/charger itself. A disabled source creates no device sessions, polling, subscriptions to its commands or writes, and must not advertise its unavailable properties as fresh. A Homie device with no enabled sources must not be advertised as ready. Sources sharing one Homie device retain independent availability; disabling one does not implicitly enable or disable the other. Previously retained discovery/state must have an explicit retirement policy when a source is disabled.

For one supported inverter, the runtime configuration needs only:

```dotenv
SMAB_MQTT_HOST=mqtt.example.invalid
SMAB_INVERTER1_ENABLED=true
SMAB_INVERTER1_HOST=inverter.example.invalid
SMAB_INVERTER1_PROFILE=sma-stp8-0-3av-40
```

Add broker authentication/CA overrides if required by that installation. Select a reusable model profile by ID; the repository packages three validated profiles under [ressources/profiles/](../ressources/profiles/), covering the existing 41 channels. Their schema and host overrides are documented in [PROFILES.md](PROFILES.md). Never invent an IP address, password, serial number or register mapping as a working default.

Each inverter is independent. The first three slots default respectively to `sma-stp8-0-3av-40`, `sma-sbs3-7-10` and `sma-sb4-0-1av-41`, and each selection can be overridden. A profile is reusable across slots; slot number does not determine the connected model. Further slots use the same `SMAB_INVERTER<N>_` family, with an empty profile default requiring explicit selection, without another hard-coded adapter. A disabled slot does not require a host or profile. An enabled slot requires a host and validated matching profile; validate discovered device identity against the profile and an optional expected serial number before accepting data.

For an ID, the resolver checks `<id>.json` under `SMAB_PROFILE_DIR` before the bundled resource. An invalid override must fail instead of silently falling back. `file:custom-name.json` selects only a host file, with no bundled fallback; reject directory traversal and absolute paths. Model profiles contain model/firmware compatibility evidence, protocol defaults, register definitions and Homie metadata, not installation credentials or addresses. Add future supported inverters as profile files rather than code branches. See the profile README for the version-1 schema and validation gate.

Home Manager requires a serial selector for both transports. `TRANSPORT=udp` (default) receives meter telegrams; HOST is an optional IPv4 sender filter. `TRANSPORT=modbus-tcp` requires HOST and uses the separate MODBUS_PORT (502 by default), with persistent sessions and a documented read profile. Exactly one transport owns its Homie values. Modbus server enablement and Grid Guard access are installation prerequisites; the bridge never changes them or sends a Grid Guard login. See [Home Manager Modbus](HOME_MANAGER_MODBUS.md) for complete coverage and acceptance. Encrypted Speedwire support remains a separate UDP verification task.

eCharger requires a host and local account credentials. With the default TLS verification, supply a trusted certificate/CA unless system trust already covers it. `TLS_SERVER_NAME` optionally verifies the certificate's DNS name while connecting to the configured IP. An explicit `SMAB_ECHARGER_TLS_VERIFY=false` skips certificate/name verification and ignores the CA path. Its API and SEMP activation flags and schedules are separate. SEMP defaults to disabled. The portal remains separately enabled and uses separate credentials, plant/device IDs and session handling. It initially supplies minimum PV percentage for the configured eCharger Homie device, independently of local API availability. Home Manager remains the charging controller.

## ENV options and defaults

All names below include the `SMAB_` prefix. Empty strings are the default for optional strings and installation-specific values. Paths refer to the container except the Compose-only host paths. Boolean flags, integer ports/IDs/counts and numeric durations follow the validation above; other entries are strings.

| Variable | Default | Meaning / validation |
| --- | --- | --- |
| `SMAB_BRIDGE_VERSION` | `latest` | Compose image tag; select a published version for deployment. No release exists yet. |
| `SMAB_DATA_DIR` | `./data/sma-mqtt-bridge` | Compose host bind directory. |
| `SMAB_ENV_FILE` | `./smab.env` | Compose service ENV file; optional for diagnostics. |
| `SMAB_UID`, `SMAB_GID` | `10001` | Compose-only integer user/group IDs; align file access with the host account. |
| `SMAB_CONFIG_FILE` | `/data/sma-mqtt-bridge/config.json` | Optional JSON configuration. |
| `SMAB_PROFILE_DIR` | `/data/sma-mqtt-bridge/profiles` | Verified device profile directory. |
| `SMAB_STATE_DIR` | `/data/sma-mqtt-bridge/state` | Non-secret persistent state and heartbeat; Compose mounts `data_smab_state` here. |
| `SMAB_TIMEZONE` | `Europe/Berlin` | IANA timezone for timestamps and day boundaries. |
| `SMAB_LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`; redact secrets at every level. |
| `SMAB_HEALTH_INTERVAL_SECONDS` | `10` | Main-loop heartbeat interval. |
| `SMAB_HEALTH_STALE_SECONDS` | `60` | Heartbeat failure threshold; greater than heartbeat interval. |
| `SMAB_SHUTDOWN_TIMEOUT_SECONDS` | `10` | Bounded graceful shutdown. |
| `SMAB_RECONNECT_MIN_SECONDS` | `1` | Initial supervised reconnection delay, with jitter. |
| `SMAB_MAX_RESPONSE_BYTES` | `1048576` | Positive integer HTTP response limit, including decompressed data. |
| `SMAB_RECONNECT_MAX_SECONDS` | `60` | Maximum delay; at least the minimum. No uncertain write retries. |
| `SMAB_COMMANDS_ENABLED` | `false` | Global gate for confirmed command allowlists. |
| `SMAB_COMMAND_READBACK_TIMEOUT_SECONDS` | `30` | Time limit to confirm a command through readback. |
| `SMAB_COMMAND_READBACK_INTERVAL_SECONDS` | `1` | Positive delay between command readback requests. |

| MQTT suffix after `SMAB_MQTT_` | Default | Meaning / validation |
| --- | --- | --- |
| `HOST` | empty | Required broker IP/hostname. |
| `PORT` | `8883` | TCP port, independently configurable. |
| `USERNAME`, `PASSWORD`, `PASSWORD_FILE` | empty | Optional broker authentication; choose direct password or a file. |
| `CLIENT_ID` | `sma-mqtt-bridge` | Base ID; derive unique clients for advertised Homie devices. |
| `HOMIE_PREFIX` | `homie` | One valid Homie topic level, without wildcards. |
| `TLS` | `true` | Use TLS; explicit `false` selects a plaintext broker connection. |
| `TLS_VERIFY` | `true` | Explicit `false` skips broker certificate/name verification and ignores the CA path; TLS encryption remains active. Portal verification is unaffected. |
| `TLS_CA_FILE` | empty | System trust by default; optional private broker CA. |
| `TLS_CERT_FILE`, `TLS_KEY_FILE` | empty | Optional mutual TLS; require both together. |
| `KEEPALIVE_SECONDS` | `60` | MQTT keepalive interval. |
| `CONNECT_TIMEOUT_SECONDS` | `10` | Bounded connection timeout. |
| `QOS` | `1` | Homie publish QoS, allowed values 1 or 2. |
| `MAX_QUEUE_MESSAGES` | `1000` | Positive queue limit; supervise backpressure. |

| Inverter suffix after `SMAB_INVERTER<N>_` | Default | Meaning / validation |
| --- | --- | --- |
| `ENABLED` | `false` | Independent bridge access gate. |
| `HOST` | empty | Required local Modbus TCP address when enabled. |
| `PORT`, `UNIT_ID` | `502`, `3` | Modbus connection settings; register functions/types come from profile. |
| `PROFILE` | model ID for slots 1–3; otherwise empty | Reusable profile ID or `file:<name>.json`; require validated mappings when enabled. |
| `EXPECTED_SERIAL` | empty | Optional identity check in addition to profile/model validation. |
| `HOMIE_ID` | `sma-inverter<N>` | Stable, unique Homie ID. |
| `POLL_INTERVAL_SECONDS` | `10` | Fallback interval; preserve imported profile intervals unless explicitly overridden. |
| `TIMEOUT_SECONDS` | `5` | Modbus I/O timeout. |
| `STALE_SECONDS` | `60` | Maximum measurement age; allow for the longest configured poll interval. |
| `COMMANDS_ENABLED` | `false` | Per-inverter write gate; no current inverter command allowlist. |

| Home Manager suffix after `SMAB_HOME_MANAGER_` | Default | Meaning / validation |
| --- | --- | --- |
| `ENABLED` | `false` | Explicitly enable the selected transport. |
| `TRANSPORT` | `udp` | `udp` or `modbus-tcp`; no automatic fallback or dual ownership. |
| `PROFILE` | `sma-home-manager-2-modbus` | Bundled ID or host `file:<name>.json`; used only for Modbus. |
| `HOST` | empty | Optional UDP source IP filter; required TCP hostname/address for Modbus. |
| `SERIAL` | empty | Required numeric serial selector/identity guard when enabled. |
| `MODBUS_PORT` | `502` | TCP port, 1–65535; independent of UDP PORT. |
| `POLL_INTERVAL_SECONDS` | `3` | Positive explicit JSON/ENV override for Unit 2 only; otherwise profile intervals apply. |
| `CONNECT_TIMEOUT_SECONDS` | `5` | Positive TCP connect timeout, seconds. |
| `TRANSACTION_DELAY_SECONDS` | `0.2` | Minimum pause after each completed transaction, seconds; zero allowed. |
| `AFTER_CONNECTION_DELAY_SECONDS` | `3` | Pause before session identity verification, seconds; zero allowed. |
| `RECONNECT_DELAY_SECONDS` | `5` | Minimum pause after closing a session, seconds; zero allowed, plus runtime error backoff. |
| `INTERFACE_ADDRESS`, `BIND_ADDRESS` | `0.0.0.0` | Multicast interface and UDP listening address; select a concrete LAN interface if needed. |
| `PORT` | `9522` | Energy-meter UDP port. |
| `MULTICAST_ENABLED` | `true` | Join multicast; `false` for separately configured direct delivery. |
| `MULTICAST_GROUP` | `239.12.255.254` | IPv4 multicast group. |
| `TIMEOUT_SECONDS`, `STALE_SECONDS` | `5`, `30` | Receive supervision and freshness thresholds. |
| `HOMIE_ID` | `sma-home-manager` | Stable Homie identity; no charging-control writes. |

| eCharger suffix after `SMAB_ECHARGER_` | Default | Meaning / validation |
| --- | --- | --- |
| `ENABLED` | `false` | Enable local charger API access. |
| `HOST`, `USERNAME`, `PASSWORD`, `PASSWORD_FILE` | empty | Local address and credentials; choose password or a file. |
| `PORT` | `443` | HTTPS port; TLS encryption remains active. |
| `TLS_CA_FILE` | empty | Trusted local certificate/CA; system trust if omitted. |
| `TLS_VERIFY` | `true` | Explicit `false` permits unverified local TLS without a CA file; never changes MQTT or portal verification. |
| `TLS_SERVER_NAME` | empty | Optional certificate DNS name while connecting to HOST/IP; empty verifies HOST. Relevant when verification is enabled. |
| `EXPECTED_SERIAL` | empty | Required local API serial guard; optional additional SEMP guard. |
| `API_POLL_INTERVAL_SECONDS` | `60` | Parameter/live-data schedule, separate from SEMP. |
| `SEMP_ENABLED` | `false` | Independently enable SEMP reads, without API credentials or implicit activation. |
| `SEMP_DEVICE_ID` | empty | Required SEMP identity selector when enabled. |
| `SEMP_PORT`, `SEMP_PATH` | `80`, `/SEMP/` | Local SEMP endpoint; validate response identity. |
| `SEMP_POLL_INTERVAL_SECONDS` | `30` | Local SEMP measurement schedule. |
| `TIMEOUT_SECONDS`, `STALE_SECONDS` | `10`, `180` | HTTP timeout and freshness threshold. |
| `HOMIE_ID` | `sma-echarger` | Shared charger identity for local and portal properties. |
| `COMMANDS_ENABLED` | `false` | Additional gate for the confirmed local command allowlist. |

| Portal suffix after `SMAB_PORTAL_` | Default | Meaning / validation |
| --- | --- | --- |
| `ENABLED` | `false` | Separate optional ennexOS adapter. |
| `BASE_URL` | `https://ennexos.sunnyportal.com` | HTTPS portal origin with mandatory verification. |
| `API_BASE_URL` | `https://uiapi.sunnyportal.com/api/v1` | Verified HTTPS API base. |
| `AUTH_BASE_URL` | `https://login.sma.energy/auth/realms/SMA` | Verified HTTPS realm; login actions must stay on this origin/path. |
| `CLIENT_ID` | `SPpbeOS` | Public OAuth client ID, not a developer credential. |
| `USERNAME`, `PASSWORD`, `PASSWORD_FILE` | empty | Separate portal account; choose password or a file. |
| `PLANT_ID`, `DEVICE_ID` | empty | Required installation selectors when enabled. |
| `TIMEOUT_SECONDS` | `15` | Request timeout. |
| `POLL_INTERVAL_SECONDS` | `0` | Explicit refresh by default; positive value enables periodic requests. |
| `STALE_SECONDS` | `180` | Positive freshness limit for explicitly retrieved preferences. |
| `COMMANDS_ENABLED` | `false` | Reserved gate; enabling it is rejected until command implementation. |

The option list is expandable as adapters are implemented; add settings, their defaults and validation here and in `smab.example.env` in the same change. Validate Homie IDs as lowercase letters, digits and internal hyphens; derive one MQTT connection/Last Will per advertised device. Command gates never override a missing allowlist, missing rights, invalid bounds or readback requirements. Do not expose an editable installer setting merely because its metadata is writable.

## Compose usage

Place only needed overrides in the root `smab.env`; no additional JSON file is mandatory. On a fresh installation, copy `smab.example.env` to `smab.env` and replace its placeholder broker host. Keep existing configuration intact. Both Compose files explicitly pass `smab.env` through the service's `env_file`. No extra flag is needed to load bridge settings with the default layout:

```bash
docker compose -f docker-compose.dev.yml run --rm sma-mqtt-bridge --check-config
docker compose -f docker-compose.dev.yml up -d --build
```

For Compose-only overrides such as host data paths, UID/GID or the deployment image version, pass `--env-file smab.env` before `-f`. Compose automatically reads only `.env` for variable interpolation; it does not automatically use service ENV files for this. Alternatively, an optional root `.env` can hold only these Compose settings while `smab.env` holds the bridge configuration. Avoid duplicating settings across the files.

```bash
docker compose --env-file smab.env -f docker-compose.dev.yml up -d --build
```

Both Compose files are standalone and carry identical runtime options. Development explicitly builds `Dockerfile-SMAB`; example uses the GHCR image instead. `python3 tests/compose_check.py` checks this parity with public settings and overrides. Use `--check-config` to validate all enabled sources without connecting. Starting without a diagnostic flag runs only explicitly enabled read sources. No command gate may be enabled in this milestone. The optional service ENV file requires Docker Compose 2.24 or newer. Diagnostics can render templates without any private file. To use another ENV file for both interpolation and service variables, set `SMAB_ENV_FILE` to that path in the shell and also pass `--env-file` with the same path. Home Manager multicast networking on the Raspberry Pi remains a separate deployment check; the bind mount alone does not establish UDP reachability.

References: [Docker Compose ENV files](https://docs.docker.com/compose/how-tos/environment-variables/set-environment-variables/), [Compose bind mounts](https://docs.docker.com/reference/compose-file/services/#volumes), [Homie 4 convention](https://homieiot.github.io/specification/spec-core-v4_0_0/).

## Implemented validation and lifecycle details

JSON uses `schemaVersion: 1` and the documented camelCase fields. Unknown keys, duplicate keys, non-finite numbers, malformed types and duplicate slots/IDs are errors. Passwords and account usernames belong in ENV; password files are alternative secret sources. Disabled adapters do not load password files, TLS trust or host profile files. TLS/key and password-source conflicts still fail structural validation. Neither the loader nor the service rewrites configuration.

Source activation is never inferred. No sources means no discovery as ready; the CLI exits with an actionable diagnostic unless a saved topic manifest needs MQTT retirement. That retirement requires broker configuration but performs no device I/O. The profile directory contains file-driven model metadata and verified polling definitions; it never supplies addresses, credentials or activation.

MQTT QoS is 1 or 2. Each advertised Homie device has a unique client ID and retained `lost` Will. Sources sharing the charger device retain independent status. Measurements remain non-settable. With both `SMAB_COMMANDS_ENABLED=true` and `SMAB_ECHARGER_COMMANDS_ENABLED=true`, the enabled local API advertises and subscribes only to the supported enum/boolean controls listed below. Portal/inverter write gates still reject `true`. All write defaults remain false. Source failures are isolated, authentication challenges block repeated login, and SIGTERM cancels pending readers after the configured grace period. The main-loop heartbeat distinguishes source freshness and MQTT availability from process liveness.

Local API measurements require a recent timezone-qualified timestamp; missing or old timestamps yield unavailable data. SEMP parameters use the same check for measurements. Settings are observations of the last successful read. Local plan energy and stop delay need matching `unit` metadata or the narrowly verified EVC22-3AC-20 / 2.6.37.R unit mapping documented in VALIDATION.md before publication. The local certificate must match the configured hostname; use its trusted DNS name and CA. The old JavaScript fingerprint/hostname exception has not been silently carried into Python.

Retained retirement uses `state/mqtt-topics.json`, containing owned topics only. Removed properties/devices and previous prefixes are cleared on reconnect. Fresh values are reannounced; unavailable current values are cleared first. The manifest cannot retire another broker's data after changing `HOST`/port. Keep the original broker available for a separate retirement step; no automatic cross-broker access occurs.

Every dataclass field in `ressources/sma_mqtt_bridge/config.py` has the documented ENV family and camelCase JSON name. `runtime` fields use `SMAB_`; `commands.enabled` maps to `SMAB_COMMANDS_ENABLED`, and its timeout maps to `SMAB_COMMAND_READBACK_TIMEOUT_SECONDS`. Numbered inverter IDs are JSON selectors, not ENV identity overrides. The Python CLI receives ENV from Compose; dotenv syntax is handled by Compose rather than a second parser.

## Migrating existing state from a bind mount

Stop the bridge before copying state. Copy the existing `heartbeat.json` and `mqtt-topics.json` into the Compose volume `data_smab_state`, retaining their contents and restrictive file modes; assign them to the configured container UID/GID. Do not overwrite a volume already in use. Start the bridge and verify its heartbeat and Docker health status. Keep the former host files as an inactive backup until verification. A new empty volume does not automatically import the state hidden under the parent bind mount. Preserve `mqtt-topics.json` to retain ownership of old topics for cleanup.

See [Docker volume lifecycle and migration](https://docs.docker.com/engine/storage/volumes/) and [Compose volume naming](https://docs.docker.com/reference/compose-file/volumes/).

## Local eCharger command milestone

The initial enum/boolean controls use `settings/<property>/set` under the configured charger Homie ID. Measurements, stop delay, energy/end-time planning and portal preference remain read-only at this milestone. Homie discovery and typed command payloads follow the official [openHAB Homie binding](https://www.openhab.org/addons/bindings/homie/) and [Homie 4 specification](https://homieiot.github.io/specification/spec-core-v4_0_0/).

| Property | Non-retained payload |
| --- | --- |
| `charge-mode` | `4718` fast, `4719` optimized PV, `4721` stop; `4720` is rejected until plan transactions exist |
| `charging-release` | `true` / `false` |
| `approval-required` | `true` / `false` |
| `stop-when-full` | `true` / `false` |
| `cable-lock` | `true` / `false` |
| `led-brightness` | `5191` low, `5190` medium, `5173` high |
| `ambient-brightness` | `5191` low, `5190` medium, `5173` high |
| `ambient-enabled` | `true` / `false` |

There are eight MQTT control properties in this allowlist. Current local identity, `state=Confirmed`, `editable=true` and offered `possibleValues` are checked before each action. A target already reported by the device produces `already-confirmed` without writing. Polling and commands share one API lock/session; commands arriving during an active operation or poll are rejected as busy rather than queued. A maximum 64-byte command is decoded as strict UTF-8. No MQTT command, token or authenticated error body is logged.

The bridge sends exactly one PUT in the working reference format and reads back until the exact target is `Confirmed`. HTTP success alone yields no confirmed property state. The command session disables aiohttp 3.14.4's internal persistent-connection PUT retry; a loopback regression verifies one server-side PUT when the response is lost. There is no command write on startup or reconnection. Stored retained MQTT commands are rejected. Send commands without retain; MQTT 3 cannot distinguish a retained publication delivered live from an ordinary live publication.

`commands/local-result` reports `pending`, `confirmed`, `already-confirmed`, `rejected`, `rejected-retained`, `rejected-disabled`, `rejected-busy`, `uncertain` or `blocked-uncertain`. Before sending, a mode-0600 journal is atomically saved and synced at `state/echarger-command-pending.json`. It is removed only after confirmed readback. Uncertain response, cancellation or crash leaves the journal in place and blocks subsequent writes across restarts; startup never replays it. To resolve manually, stop the bridge, inspect the actual setting locally and the saved target, then archive the journal only after reconciling the action. Preserve this guard alongside the topic manifest when migrating state.

Live command acceptance is still pending. The installation's private write gates were not enabled, and no device setting was changed. Home Manager remains the charging regulator; power limits, planned charging and portal writes are later milestones.
