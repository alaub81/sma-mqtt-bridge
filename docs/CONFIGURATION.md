# Configuration contract

Andreas requested this contract on 2026-10-10. It is binding for the Python implementation. **Implemented by the Python loader.** Inverter and SEMP reads have been checked against the installation; complete hardware/openHAB acceptance remains pending. See [register validation](REGISTER_VALIDATION.md).

## Host files and precedence

The private `smab.env` belongs in the repository root next to the Compose files. Keep the agreed name `smab.env`; a leading dot only hides a file and does not protect secrets. A name such as `.smab.env` has no automatic Compose loading behavior. Only `.env` is automatically used for Compose interpolation; our service environment file is explicitly selected by `env_file`. `smab.example.env` documents every available variable, including its purpose, type and default. Store other installation files under `./data/sma-mqtt-bridge/` relative to the Compose project directory; bind-mount that directory to `/data/sma-mqtt-bridge` in the container:

```text
smab.env               # Explicit overrides and installation credentials, host only
smab.example.env       # Public defaults reference with a broker placeholder
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

## Optional channel groups

All channel groups are enabled by default. Each inverter slot, Home Manager and eCharger supports
`SMAB_<DEVICE>_ADVANCED_CHANNELS_ENABLED` and `SMAB_<DEVICE>_DIAGNOSTICS_ENABLED` (boolean, default `true`).
The portal supports its own `SMAB_PORTAL_DIAGNOSTICS_ENABLED` flag. JSON equivalents are
`advancedChannelsEnabled` and `diagnosticsEnabled` in the respective device section.

For example, a reduced Home Manager production configuration is:

```dotenv
SMAB_HOME_MANAGER_ADVANCED_CHANNELS_ENABLED=false
SMAB_HOME_MANAGER_DIAGNOSTICS_ENABLED=false
```

Use `INVERTER1`, `INVERTER2`, `INVERTER3` (or another configured slot), or `ECHARGER` in place of
`HOME_MANAGER` to select another device independently. The eCharger flags apply to both API and SEMP;
the independently configured portal retains its PV-share channels.

| Group | Disabled behavior |
| --- | --- |
| Home Manager advanced | Omit Advanced Unit 1 metadata, assignment-table reads and all delegated `device-*` channels. Keep the six Unit 2 plant/grid readings. The two core protocol diagnostics follow Diagnostics independently. UDP currently exposes only basic readings. |
| Inverter advanced | Omit published identity channels and explicitly tagged supplementary properties, including Sunny Boy type and power-limit parameters. Keep the existing energy, power, phase, battery, internal temperature and operating-status measurements. |
| eCharger advanced | Omit firmware, SEMP control setpoints and raw parameter duplicates. Keep charging measurements, vehicle-status text/code, readable charging settings and command feedback. |
| Diagnostics | Keep operational source status and seven Basic plant/Wallbox coverage-status properties. Hide detailed calculation inputs, accounting timestamps/date/boundary, last-success timestamps and optional failure/timeout/outage metrics, Home Manager protocol diagnostics/rejected-block count and SEMP raw health/event/registration/mode codes. |

Operational availability is always advertised for enabled measurement sources, including
`diagnostics#apistatus`, `diagnostics#sempstatus` and `portal#status` used by the garage widget.
Existing Channel IDs and labels are preserved; the `diagnostics` node name does not make these
status properties optional. They remain read-only and report `init`, `ready`, `stale` or `error`
from the same freshness/error policy used by supervision. Disabled adapters still perform no I/O
and do not advertise source status. Optional diagnostic channels are retired through the existing
persistent topic manifest when disabled; operational status channels remain owned and published.
Source readiness does not certify every property's timestamp or immediate broker reachability.

Classification, not the topic path alone, controls visibility. A profile explicitly
marking `diagnostics/deratingreason` as Basic keeps that measurement available
when diagnostics are disabled. All Advanced-classified channels follow their
device Advanced flag. The plant currently has no Advanced channels.
The [classification guide](TOPIC_GROUPS.md) lists the seven Basic coverage channels,
the two Home Manager Diagnostics reclassifications and the generated topic catalog.
Plant day accounting, freshness, readiness and debug logging continue internally
when optional MQTT diagnostics are hidden; debug flags never reenable topics.
Recreate the container with the updated ENV; a restart alone does not reload ENV.
The existing state volume/manifest must be preserved for retained retirement.

Filters apply before Modbus scheduling and value decoding: blocks containing only disabled properties
are not polled. Blocks shared with enabled values and mandatory identity checks are still read;
disabled values are not decoded for publication. HTTP/SEMP APIs return bulk responses, so transport
parsing and identity validation remain necessary, while disabled output values are not converted
or advertised. No additional selective HTTP endpoint is assumed.

Device identity gates, freshness checks, connection supervision, logs, Docker health checks and
Homie `$state`/Last Will remain active. This setting never enables writes or changes command permissions.
After changing ENV, recreate the container (a restart alone keeps its old environment); development
also needs a rebuilt image for new code. On reconnect/startup, the persisted topic manifest removes
previously owned retained values and metadata for disabled channels. Preserve the state volume.
Consumers linked to intentionally disabled channels will stop receiving those values.

Homie channel discovery is based on advertised properties; see the
[official openHAB Homie binding documentation](https://www.openhab.org/addons/bindings/homie/).

## ENV options and defaults

All names below include the `SMAB_` prefix. Empty strings are the default for optional strings and installation-specific values. Paths refer to the container except the Compose-only host paths. Boolean flags, integer ports/IDs/counts and numeric durations follow the validation above; other entries are strings.

| Variable | Default | Meaning / validation |
| --- | --- | --- |
| `SMAB_BRIDGE_VERSION` | `latest` | Compose image tag; pin a published version such as `0.3.6` for deployment. Image tags omit the Git tag’s `v`; see [release notes](RELEASES.md). |
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
| `SMAB_MAX_PAYLOAD_BYTES` | `4096` | Positive integer UTF-8 observation payload limit; JSON `runtime.maxPayloadBytes`. Reject oversized values before publication, including fixed-point exponent expansion. |
| `SMAB_MAX_STATE_BYTES` | `1048576` | Positive integer size limit per topic manifest/command journal; oversized state fails closed. |
| `SMAB_READ_CYCLE_TIMEOUT_SECONDS` | `120` | Positive whole read-cycle watchdog in seconds; excludes poll/backoff/idle waits. |
| `SMAB_FAILURE_LOG_INTERVAL_SECONDS` | `300` | Positive interval between repeated outage log summaries in seconds; transitions are immediate. |
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
| `TIMESTAMP_DIAGNOSTICS_ENABLED` | `false` | Observe existing API/SEMP samples in the state volume; independent of Homie diagnostics, no additional requests. |
| `TIMESTAMP_DIAGNOSTICS_MAX_BYTES` | `1048576` | Integer file rotation limit, 4096–16777216 bytes; one backup. |
| `TIMESTAMP_DIAGNOSTICS_SUMMARY_INTERVAL_SECONDS` | `300` | Positive seconds between summaries of unchanged samples; changes are recorded immediately. |
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

### eCharger measurement lifetime

The existing API/SEMP `STALE_SECONDS` limits also bound the total device age of
verified periodically refreshed observations: charging power, API phase current,
API primary total-energy counter, vehicle status (text and code), and the three
SEMP plant-control setpoints. Device age is preserved through decoding; monotonic
processing time consumes the remaining lifetime. Repeated receipt of the same
device timestamp cannot rejuvenate these values. See the
[channel evidence](ECHARGER_TIMESTAMP_ANALYSIS_2026-10-12.md).

Phase voltage/power, alternative energy channels, session energy and unresolved
health/event/mode/authorization observations retain the existing timestamp filter
and receipt-based runtime lifetime pending their separate classification. Confirmed
settings keep their separate readback contract. No new environment option is needed.
Source readiness follows its required fresh properties; aggregate device readiness
does not certify every source. Expiry preserves MQTT's last retained observation
and does not publish a replacement zero or delete its topic.

### Temporary eCharger timestamp observation

Set `SMAB_ECHARGER_TIMESTAMP_DIAGNOSTICS_ENABLED=true` in the private root
`smab.env` and recreate the service with the rebuilt image. Only already enabled
API/SEMP readers participate. No adapter is implicitly enabled, no additional
requests or commands are sent, and freshness/publication policies are unchanged.
JSON equivalents under `echarger` are `timestampDiagnosticsEnabled`,
`timestampDiagnosticsMaxBytes`, and `timestampDiagnosticsSummaryIntervalSeconds`.

The diagnostic file is `echarger-timestamps.jsonl` under `SMAB_STATE_DIR`, normally
`/data/sma-mqtt-bridge/state` in the existing `data_smab_state` Compose volume.
There is one rotated backup, `echarger-timestamps.jsonl.1`: default storage is
approximately 2 MiB maximum for files created with these limits. Files use mode
0600. They are private runtime evidence and must not be committed or published.
Disabling observation stops recording and preserves both files for evaluation.

Each JSON line contains source (`api`/`semp`), an allowlisted protocol channel,
UTC processing/receipt time, normalized device timestamp, device age in seconds,
configured freshness limit and timestamp quality (`fresh`, `stale`, `future`,
`invalid`). The value is a numeric string in the original protocol units: for
example energy channels remain raw Wh here, while MQTT uses converted kWh.
`valueValid` indicates numeric validity. Invalid strings, identities, credentials,
headers, parameter catalogs and complete responses are never copied into this file.

`valueChanged` compares numeric values (0 and 0.0 are equal); `timestampChanged`
compares normalized UTC timestamps. Both are null for the first observation after
startup. Unchanged value/timestamp/quality combinations are suppressed until the
summary interval; `repeatedSamples` counts the summarized observations including
the previous emitted observation. `suppressedSamples` reports preceding observations
omitted since the last emitted line. A transition from fresh to stale is recorded
even when value and timestamp stay unchanged. API and SEMP histories are separate.
Only observed channels are recorded; this is not a device-I/O watchdog and silence
does not establish either health or failure. Use source diagnostics for outages.

Storage is best effort: a write failure emits a warning containing only its exception
type and defers retries for the summary interval, without failing the device read.
Records are not fsynced individually; abrupt shutdown can lose the final records.
Read the rotated backup before the current file when evaluating time order. Do not
infer acquisition/change semantics from a single old timestamp; follow the
[observation and acceptance criteria](VALIDATION.md#measurement-freshness-investigation-2026-10-11).

## Compose usage

CLI diagnostics distinguish project capabilities from resolved installation settings:
`--project-status` is static and does not load configuration or connect. Its
`readOnly=false` means this code supports optional writes; `commandsEnabledByDefault=false`
means the default command gates are closed. `liveVerified=false` does not claim
complete installation acceptance. Use `--check-config` to validate JSON/ENV and
local profile/password/certificate files without device connections. Its `readOnly`
field describes the effective global and per-adapter command gates of that validated
configuration. Neither diagnostic sends a command or activates an adapter.

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

MQTT QoS is 1 or 2. Each advertised Homie device has a unique client ID and retained `lost` Will. Sources sharing the charger device retain independent status. Measurements remain non-settable. With both `SMAB_COMMANDS_ENABLED=true` and `SMAB_ECHARGER_COMMANDS_ENABLED=true`, the enabled local API advertises and subscribes only to the supported enum/boolean controls listed below. Portal writes require their own enabled adapter and `SMAB_PORTAL_COMMANDS_ENABLED=true` in addition to the global gate. Inverter write gates still reject `true`. All write defaults remain false. Source failures are isolated, authentication challenges block repeated login, and SIGTERM cancels pending readers after the configured grace period. The main-loop heartbeat distinguishes source freshness and MQTT availability from process liveness.

Local API measurements require a recent timezone-qualified timestamp; missing or old timestamps yield unavailable data. SEMP parameters use the same check for measurements. Settings are observations of the last successful read. API settings require `state=Confirmed` individually, including the manual-approval display alias; Pending, absent or invalid confirmation metadata produces no new observation. The last retained confirmed value remains available as history, rather than publishing a pending target or a fabricated zero. SEMP has no API confirmation metadata and keeps its separate raw-parameter read contract.

Local plan energy, stop delay and plan end need matching `unit` metadata or the narrowly verified EVC22-3AC-20 / 2.6.37.R mapping before API publication: kWh, min and epoch seconds respectively. Contradictory explicit units block the affected value. Plan command readback verifies units as well as Confirmed state and numeric equality; a matching number with a wrong unit leaves the command uncertain and preserves its journal. SEMP keeps its established epoch-second plan-end conversion without claiming API confirmation. See [unit evidence](VALIDATION.md#unit-and-protocol-evidence). The local certificate must match the configured hostname; use its trusted DNS name and CA. The old JavaScript fingerprint/hostname exception has not been silently carried into Python.

Retained retirement uses `state/mqtt-topics.json`, containing owned topics only. Removed properties/devices and previous prefixes are cleared on reconnect. Fresh values are reannounced; unavailable current values are cleared first. The manifest cannot retire another broker's data after changing `HOST`/port. Keep the original broker available for a separate retirement step; no automatic cross-broker access occurs.

Every dataclass field in `ressources/sma_mqtt_bridge/config.py` has the documented ENV family and camelCase JSON name. `runtime` fields use `SMAB_`; `commands.enabled` maps to `SMAB_COMMANDS_ENABLED`, and its timeout maps to `SMAB_COMMAND_READBACK_TIMEOUT_SECONDS`. Numbered inverter IDs are JSON selectors, not ENV identity overrides. The Python CLI receives ENV from Compose; dotenv syntax is handled by Compose rather than a second parser.

## Migrating existing state from a bind mount

Stop the bridge before copying state. Copy the existing `heartbeat.json` and `mqtt-topics.json` into the Compose volume `data_smab_state`, retaining their contents and restrictive file modes; assign them to the configured container UID/GID. Do not overwrite a volume already in use. Start the bridge and verify its heartbeat and Docker health status. Keep the former host files as an inactive backup until verification. A new empty volume does not automatically import the state hidden under the parent bind mount. Preserve `mqtt-topics.json` to retain ownership of old topics for cleanup.

See [Docker volume lifecycle and migration](https://docs.docker.com/engine/storage/volumes/) and [Compose volume naming](https://docs.docker.com/reference/compose-file/volumes/).

## Failure supervision and healthcheck

Observation payloads are limited by `SMAB_MAX_PAYLOAD_BYTES` (default 4096 UTF-8
bytes), also configurable as JSON `runtime.maxPayloadBytes`. Numeric fixed-point
length is checked before expansion, so a short extreme exponent cannot allocate
an arbitrarily large payload. Oversized values and invalid Unicode are invalid
samples: they do not refresh readiness or replace previously retained observations
with zero. This does not change topic IDs, units, command bounds or device polling.
Choose a limit sufficient for normal device values; a deliberately small override
can make otherwise valid samples unavailable. Discovery labels retain their own
metadata validation and are outside this observation limit.

Runtime log records start with an ISO 8601 timestamp including milliseconds and
the UTC offset, followed by severity and message. `SMAB_TIMEZONE` (default
`Europe/Berlin`) controls the log timezone, including daylight-saving changes.
Example: `2026-10-11T14:30:00.123+02:00 WARNING Source portal unavailable (stale)`.

The Home Manager Modbus source remains `init` while its first paced reads
collect the required fresh properties. This initial phase is bounded by
`SMAB_READ_CYCLE_TIMEOUT_SECONDS` (default 120 seconds) from source creation.
Missing required values then produce `stale`; request errors produce `error`
immediately and end initialization. Once ready, ordinary freshness checks apply
without another initialization grace period on reconnect.

The Docker probe runs `python -m sma_mqtt_bridge --healthcheck`. It validates configuration
without device I/O and reads `state/heartbeat.json`. A successful probe requires schema 2,
`status=running`, a positive PID still present in the same PID namespace, and a finite monotonic
heartbeat age between zero and `SMAB_HEALTH_STALE_SECONDS` (default 60 seconds).
The main loop writes every `SMAB_HEALTH_INTERVAL_SECONDS` (default 10 seconds).
Wall-clock adjustments do not affect liveness. Old-schema, missing, stopped, malformed,
future or expired heartbeat files fail the probe. A rebuild/recreation writes the new schema;
preserve the topic manifest and command journals when upgrading.

This is a **liveness** check, not confirmation that all sources or MQTT are available.
The heartbeat separately records each source status and each Homie client's connection flag.
A healthy process can be recovering from a complete broker or device outage.
These connection flags do not certify delivery of every measurement. Each active read cycle has
an additional configurable 120-second watchdog, including non-network waits. An expired cycle is
cancelled, its read session is reset and polling resumes with bounded backoff. A session locked by
an active command is never closed by this recovery; uncertain writes stay journal-blocked.
Polling delays, authentication-blocked sources and an idle portal with interval zero are excluded.
The watchdog needs a running event loop; a blocked event loop still requires external monitoring.
Unexpected failed, cancelled or silently completed supervisors
with active sources terminate the runtime, close sibling sessions and mark the heartbeat stopped.

| Failure | Behavior |
| --- | --- |
| Device/network read failure | Only that source reports `error`; other sources continue. Retry with bounded exponential backoff and jitter, default 1–60 seconds. Valid receipt restores availability. |
| Expired or missing measurement | Each property's own age is checked. Keep previously published retained observations when values expire or become invalid; never replace missing data with zero. Freshness remains tracked internally. |
| Invalid credentials, denied access, MFA/login challenge | Source remains `error` without repeated logins until restart after resolving the cause. Local API and portal renew expired sessions independently. |
| Portal login HTTP 408/429/5xx | Retryable service failure at every PKCE phase, rather than a permanent authentication block. Polling interval zero still disables automatic reads; requested refresh retries transient failures. |
| Broker outage or lost publish acknowledgement | Rebuild each affected MQTT client after bounded backoff. The configured MQTT timeout (default 10 seconds) bounds acknowledgement waits as well as connection attempts. Reannounce discovery, retire owned obsolete topics, preserve current retained observations and publish only fresh samples. |
| Abrupt MQTT loss | Broker publishes retained `$state=lost` through the Last Will once it detects loss; graceful shutdown confirms `$state=disconnected`. Detection is not instantaneous. |
| Uncertain command response | Preserve the durable uncertainty journal and block further writes; no automatic command replay on reconnect/restart. |

Homie `$state` is `ready` if at least one source of that device is ready, otherwise `alert`.
Command feedback does not contribute to availability; an old successful command cannot keep a device ready.
For the eCharger, a ready SEMP reader therefore does not establish API/portal availability.
Monitor individual source status/last-success topics when diagnostics are enabled.
During a broker outage those topics cannot report new failures; monitor broker availability
externally and inspect the local heartbeat/logs. Retained values cannot be cleared while the
broker is unreachable, so consumers must observe connection state and freshness too.
See the [official openHAB Homie documentation](https://www.openhab.org/addons/bindings/homie/).

Compose uses `restart: unless-stopped` for process exits. Docker marks a failed probe `unhealthy`,
but Compose does not restart a still-running unhealthy container automatically. External monitoring
must alert on this state; automatic recovery from an event-loop hang needs an external supervisor.
Do not restart the bridge repeatedly merely because a device or broker is offline.
See [Docker restart policy](https://docs.docker.com/reference/compose-file/services/#restart).

Recovery-state writes (command journals and the topic manifest) sync file contents
and the parent directory after atomic rename. Heartbeats use the same complete-file
atomic replacement without `fsync`: they report current process liveness and do not
need to survive a host power failure. Their interval, schema, PID and monotonic age
checks remain unchanged. A filesystem write/rename error still fails the runtime;
an old heartbeat expires normally. At the default 10-second interval, this avoids
17,280 explicit sync calls per day; it does not eliminate file writes or guarantee
zero physical disk activity. A process-lifetime
exclusive `state/bridge.lock` lease rejects a second runtime using the same state directory before
device/MQTT I/O. The kernel releases it on process death; never delete/replace that file while running.
This protects shared state, not separate volumes using duplicate MQTT client IDs. Keep the state
filesystem writable. Full production acceptance
still requires controlled target-host outage/recovery, broker restart, TLS trust, container shutdown
and openHAB freshness/dependency comparisons. Offline tests do not certify those installation cases.

### Critical freshness and diagnostics

A source is ready only with fresh values and **all critical keys** fresh and valid. Partial updates
never refresh omitted measurements. Invalid sentinels remove a value. Fresh metadata or slow energy
readings cannot mask expired critical measurements. Property-specific expiry intervals remain in force.

| Source | Default critical keys |
| --- | --- |
| Tripower / Sunny Boy profiles | `measurements/status` |
| Sunny Boy Storage profile | `measurements/status` |
| Home Manager UDP / Modbus | `measurements/power-import`, `measurements/power-export` |
| eCharger SEMP | `measurements/power` |
| eCharger API | `measurements/current-l1`, `measurements/voltage-l1`; also `measurements/power` when API owns baseline measurements without SEMP |
| Portal | `portal/pv-minimum` |

Bundled Modbus profiles mark these keys with boolean `requiredForReady`. Unmarked profiles default
to all advertised `measurements/` properties. Without measurements or marks, any fresh value suffices.
Unreadable nighttime power does not affect inverter readiness while the identity-checked status is fresh.
The last published power remains retained; no zero is synthesized. A stale status or communication
error still changes availability. Status values such as warning/error remain visible on their channel;
readiness describes communication availability, not fault-free equipment operation.

Optional string variables `SMAB_INVERTER<N>_READY_PROPERTIES`, `SMAB_HOME_MANAGER_READY_PROPERTIES`,
`SMAB_PORTAL_READY_PROPERTIES`, `SMAB_ECHARGER_API_READY_PROPERTIES` and
`SMAB_ECHARGER_SEMP_READY_PROPERTIES` default to empty (the rules above). A nonempty comma-separated
`node/property` list replaces defaults for that source. JSON uses `readyProperties`, or
`apiReadyProperties` / `sempReadyProperties`. Duplicate, malformed, unknown or filtered keys fail
before device I/O. Choose appropriate fresh status or measurement keys when overriding this policy.

Outage/recovery transitions are logged immediately. Ongoing identical failures produce one summary
per `SMAB_FAILURE_LOG_INTERVAL_SECONDS`: failure/consecutive-failure/timeout counts, outage duration
and last exception class, never authenticated exception text. Counters reset on process restart.
Missing-critical freshness is separate from transport failure counts.

The heartbeat includes `sourceDiagnostics` and `mqttDiagnostics`: counters, outage duration,
last success, phase and monotonic progress age; source entries also list missing critical keys.
MQTT last-success timestamps advance only after the entire publication batch completes its QoS
acknowledgements; this does not prove processing by openHAB. With diagnostics enabled, additional
source properties use `diagnostics/<source>-` or `portal/`: `failures`, `consecutive-failures`,
`timeouts`, `outage-seconds` (s), `phase`, `missing-critical` (count). Filtering these properties does
not disable internal supervision or heartbeat diagnostics.

### Corrupt persistent state

Manifests/journals must be bounded regular JSON files without symlinks, duplicate keys or non-standard
numbers. Missing files are distinct from JSON null and unreadable files. A malformed/unreadable/oversized
`mqtt-topics.json` stops startup before connections; it is never replaced with an empty manifest.
Restore a known-good manifest or reconcile its owned retained topics manually before restarting.
Preserve the original file for investigation.
Writes also enforce the size limit before replacing existing state or sending a device PUT.
An undersized configured limit therefore rejects a command without sending it.

An existing valid journal yields `blocked-uncertain`; a malformed/unreadable/oversized journal yields
`blocked-corrupt` for the corresponding local/portal command source. Startup logs the guard even when
writes are disabled. Telemetry can continue, but no command preflight, PUT or automatic journal deletion
takes place. Stop the bridge, verify the actual device setting and reconcile the journal before archiving
it. A corrupt journal is not permission to repeat its action.

## Homie node discovery

Every node publishes retained `$name`, `$type` and `$properties` metadata before
the device becomes ready, as required by the
[Homie 4 node contract](https://homieiot.github.io/specification/spec-core-v4_0_0/#node-attributes).
The type is the stable internal node ID, such as `measurements`, `settings` or a
custom profile node. Delegated Home Manager `device-<number>` nodes share type
`device`; their slot number stays in the compact topic ID. Types are never translated.
Display-name changes do not change types or Channel IDs. Existing topic-manifest
ownership also covers `$type`, including retirement when nodes disappear.

## Homie integer payloads

Integer properties publish canonical decimal whole numbers without a decimal point
or exponent, including API readback such as `4500.0` becoming `4500`. The
[Homie 4 payload contract](https://homieiot.github.io/specification/spec-core-v4_0_0/#integer)
requires signed 64-bit values: -9223372036854775808 through 9223372036854775807.
Out-of-range, fractional, boolean and nonfinite numeric inputs are unavailable;
they are never rounded or replaced with zero. Last-known retained observations
follow the existing availability policy. Float property formatting is unchanged.

## Local eCharger command milestone

The initial enum/boolean controls use `settings/<property>/set` under the configured charger Homie ID. Measurements and stop delay remain read-only. Energy/end-time planning uses the combined command below; portal preference has its own write gate. Homie discovery and typed command payloads follow the official [openHAB Homie binding](https://www.openhab.org/addons/bindings/homie/) and [Homie 4 specification](https://homieiot.github.io/specification/spec-core-v4_0_0/).

| Property | Non-retained payload |
| --- | --- |
| `chargemode` | `4718` fast, `4719` optimized PV, `4721` stop; direct `4720` is rejected; activate target charging through the combined plan command |
| `chargingrelease` | `true` / `false` |
| `approvalrequired` | `true` / `false` |
| `stopwhenfull` | `true` / `false` |
| `cablelock` | `true` / `false` |
| `ledbrightness` | `5191` low, `5190` medium, `5173` high |
| `ambientbrightness` | `5191` low, `5190` medium, `5173` high |
| `ambientenabled` | `true` / `false` |
| `maxchargepower` | Whole watts, e.g. `4500` or `11000`; current device min/max/step apply; `4000` is rejected by the observed three-phase configuration |

There are nine MQTT control properties in this allowlist. The power limit additionally requires verified watts, fresh numeric bounds and any offered step. Current local identity, `state=Confirmed`, `editable=true` and offered `possibleValues` are checked before each action. A target already reported by the device produces `already-confirmed` without writing. Polling and commands share one API lock/session; commands arriving during an active operation or poll are rejected as busy rather than queued. Enum/boolean commands accept at most 64 bytes decoded as strict UTF-8; the combined plan accepts at most 512 bytes. No MQTT command, token or authenticated error body is logged.

The bridge sends exactly one PUT in the working reference format and reads back until the exact target is `Confirmed`. HTTP success alone yields no confirmed property state. The command session disables aiohttp 3.14.4's internal persistent-connection PUT retry; a loopback regression verifies one server-side PUT when the response is lost. There is no command write on startup or reconnection. Stored retained MQTT commands are rejected. Send commands without retain; MQTT 3 cannot distinguish a retained publication delivered live from an ordinary live publication.

`commands/localresult` reports `pending`, `confirmed`, `already-confirmed`, `rejected`, `rejected-retained`, `rejected-disabled`, `rejected-busy`, `uncertain`, `blocked-uncertain` or `blocked-corrupt`. Existing guards are reported immediately when the command controller starts. Before sending, a mode-0600 journal is atomically saved and synced at `state/echarger-command-pending.json`. It is removed only after confirmed readback. Uncertain response, cancellation or crash leaves the journal in place and blocks subsequent writes across restarts; startup never replays it. To resolve manually, stop the bridge, inspect the actual setting locally and the saved target, then archive the journal only after reconciling the action. Preserve this guard alongside the topic manifest when migrating state.

Selected live actions have user-reported acceptance: status-light brightness, combined plan transmission/mode activation and portal PV changes. This does not certify every local command or completed target charging. Home Manager remains the charging regulator. The [maximum charging power command](ECHARGER_POWER_LIMIT.md) is offline tested with read-only installation mapping evidence; its physical effect and phase behavior remain pending live acceptance. Stop-delay writes remain a later milestone; planned charging and minimum PV writes are described below.

## Combined charging plan and portal PV commands

Planning uses `commands/plan/set` under the charger Homie ID. Its string payload is one JSON object containing exactly `energyKWh` (positive finite JSON number) and `endTime` (future ISO 8601 time with explicit timezone and whole seconds), for example `{"energyKWh":12.5,"endTime":"2030-01-01T07:00:00+01:00"}`. Choose an actual future deadline. Both global and local API command gates must be enabled. Individual `settings/planenergy/set`, `settings/planend/set` and direct `charge-mode=4720` remain unsupported, so separate input edits cannot start charging.

The bridge validates both fields and mode permission against a fresh identity-checked catalog, including Confirmed/editable flags, every offered numeric bound and possible value, verified kWh and epoch-second units. The observed reference catalog has a minimum but no maximum; absent device bounds are not invented. Unitless metadata is accepted only for the locally verified EVC22-3AC-20 / 2.6.37.R mapping. Changed plan fields share one PUT with one timestamp; this does not assume atomic device acceptance. Both fields must then read back as Confirmed and equal before a separate PUT activates mode 4720. The deadline and current mode permission are checked again before activation. Activation readback must still match both plan fields and the mode.

A changed plan is rejected while target mode 4720 is already active: leave that mode using an explicitly requested fast/PV/stop command before replacing the plan. An identical complete active plan needs no write. Charging release remains a separate action. `commands/plan` publishes only the confirmed combined plan; original plan setting topics remain available. The local journal covers both phases without an intermediate removal. Partial acceptance, expired deadline, changed permission or response loss leaves the operation uncertain and blocks future local writes; no rollback, mode activation after partial confirmation or automatic write retry is attempted.

Portal activation is independent of the local API:

| Setting | Effect |
| --- | --- |
| `SMAB_PORTAL_ENABLED=false` | No portal session, reads, subscriptions or writes. |
| `SMAB_PORTAL_ENABLED=true`, `SMAB_PORTAL_COMMANDS_ENABLED=false` | Portal reads only. |
| Both portal flags and `SMAB_COMMANDS_ENABLED=true` | Advertise `portal/pvminimum/set`, accepting integer payloads 0–100. |
| `SMAB_PORTAL_POLL_INTERVAL_SECONDS=0` | Disable periodic reads; explicit refresh and command preflight/readback still read when requested. |

For periodic portal reads, configure `SMAB_PORTAL_STALE_SECONDS` above
`SMAB_PORTAL_POLL_INTERVAL_SECONDS`, allowing time for requests and scheduling.
For example, a 900-second polling interval with a 1800-second freshness limit
keeps successful observations fresh between reads. Keeping the default 180-second
limit with that interval produces roughly 720 seconds of `stale` status per cycle,
even when all requests succeed. Request failures still set source status to `error`
immediately; increasing freshness does not suppress those errors. With interval
zero, observations still expire after the configured freshness limit.

`portal/pvminimum/set` takes minimum PV share, not grid share. `portal/gridshare` remains read-only and equals 100 minus the confirmed minimum. A fresh device read verifies configured plant/device IDs, product 19143, EVehicle consumer type, optional-consumer state and edit permission. An empty edit-link array is valid. All four demand fields must be present. Cost-limit mode or `pvSurplusOnly=true` rejects the percentage write without changing modes.

One PUT to `/optionalenergydemand` sends only `minPvPercentage`, preserved `pvSurplusOnly`, preserved `usePriceLimit` and preserved `priceLimit`. Feed-in limits and other settings are excluded. HTTP success does not confirm the action: readback must match all four fields before publication. Portal polling and commands share a separate portal session/lock; tokens and journals are independent of the local API. `commands/portalresult` uses the same outcome vocabulary as the local result. A separate synced mode-0600 `state/portal-command-pending.json` survives uncertain replies/cancellation/restarts and must be preserved during migration. Manual reconciliation follows the local journal procedure; startup never replays it.

All write gates stay false by default. Plan transmission/mode activation and portal PV changes have user-reported live evidence in todo.md. Completed physical target charging and its session-energy semantics remain pending. Further live actions require explicit concrete targets. No installation activation or deployment is implied by implementing the command paths.

## Display language and compact channel IDs

`SMAB_LANGUAGE` (string, default `en`; JSON `runtime.language`) selects bundled English or German
(`de`) display labels. `SMAB_TRANSLATE_DIR` (container path, default
`/data/sma-mqtt-bridge/translate`; JSON `runtime.translateDir`) selects host translation overrides.
The image includes `ressources/translate/en.json` and `de.json`. Copy `translate/example.json` to
`data/sma-mqtt-bridge/translate/de.json` to customize German labels, or to `fr.json` and select `fr`
to add another language. The host directory is covered by the existing data bind mount; it is not
created or overwritten automatically. The container user must be able to read the files.

Files contain exactly `schemaVersion: 1` and `labels`, a dictionary mapping the original English
label to its translated display text. These English source labels are translation keys; custom
profiles can add their own labels without adapter changes. Loading precedence is bundled English,
bundled selected language, then the selected host file. Missing keys fall back to English or the
original profile label. `Device {number}` must retain its placeholder for assigned Home Manager
nodes. Custom language names use lowercase language codes, optionally with hyphen-separated
lowercase region subtags. Unavailable languages, duplicate JSON keys, invalid schemas, symlink
files and files over 1 MiB are rejected before connections. Labels are nonempty single-line strings
of at most 256 characters. Translation applies only to Homie `$name` metadata, including device and
node names; property units, values, enums and command payloads are never translated.

Homie node and property IDs now remove internal hyphens at the MQTT boundary: `power-a-input`
becomes `powerainput`, `internal-temperature` becomes `internaltemperature`, `device-1` becomes
`device1`, and `settings/charge-mode/set` becomes `settings/chargemode/set`. Configured device IDs
and the Homie prefix stay unchanged. Internal profile IDs, ready-property selectors and adapter
keys retain their original spelling. Colliding compact keys fail closed rather than merge values.
The persistent topic manifest retires former retained values and metadata on the same broker.
Preserve the state volume during upgrades. Update openHAB channel links and external command
publishers to the compact IDs; changing language alone does not change any channel link.
Existing customized openHAB Item labels are managed separately and are not rewritten by the bridge.
Recreate the container after changing ENV or translation files; inspect discovery after startup.

## Last-known retained observations

Invalid or expired individual values cause no MQTT value publication and no retained deletion.
Previously published observations stay on the broker across reconnects and container restarts.
A never-valid property has no invented initial value. New valid observations update its topic.
Consumers, including openHAB, may continue to display a historical value; use source status and
freshness diagnostics to distinguish it from a current observation. Internal freshness and command
preflight/readback still exclude invalid/expired samples. Commands never use retained broker values
as proof of device state. Explicit channel/source retirement still removes owned retained values
and metadata using the persistent manifest, including inventory changes and renamed IDs.
Bundled inverter profiles now mark measurements/status as critical instead of production power.
Host profile overrides and explicit READY_PROPERTIES selections retain their configured policy;
update those files/selectors if they still require nighttime power.

## Initial startup log summary

The runtime logs one INFO startup summary when all enabled measurement sources are ready and
all configured Homie MQTT connections are connected. If startup remains incomplete, the summary
is emitted at the next health loop after `SMAB_READ_CYCLE_TIMEOUT_SECONDS` (default 120 seconds).
It reports each source status (`init`, `ready`, `stale`, `error`, or `disabled`) and MQTT connection
status without credentials or device addresses. This observation does not terminate the service
or trigger device commands. A portal configured without periodic polling or an explicit refresh
can remain `init`. Command result sources do not count as measurement readiness.

## Wallbox total-energy unit

`measurements/totalenergy` is a read-only float in kWh. The API's primary and fallback
Wh counters are divided by 1000 once; no ENV scale override is needed. Update openHAB
unit metadata and remove any duplicate Wh-to-kWh link conversion. Follow the
[history migration guide](../openHAB/openHAB.md#wallbox-total-energy-migration-to-kwh)
for retained values and persistence before deployment. Session-energy scaling is unchanged.

## Plant aggregates and energy state

Plant calculations are optional, read-only and disabled by default. Keep the
existing adapter enable flags, addresses, identity guards and command gates.
After installing a version containing this feature, this minimal addition enables
the three-inverter installation described in the migration inventory:

```dotenv
SMAB_PLANT_ENABLED=true
SMAB_INVERTER1_ROLE=pv
SMAB_INVERTER2_ROLE=battery
SMAB_INVERTER3_ROLE=pv
SMAB_PLANT_GRID_SOURCE=home-manager
```

Home Manager and the participating inverters must already be independently
enabled. A role never activates device I/O. Host profile overrides must explicitly
contain the [contribution mappings](PROFILES.md#plant-contribution-mappings);
old overrides without them fail validation before any connection. No extra
device polling or InfluxDB credentials are required.

| ENV | Default | Contract |
| --- | --- | --- |
| `SMAB_INVERTER<n>_ROLE` | `none` | `none`, `pv`, `battery` or `hybrid`; applies to any numbered inverter slot. |
| `SMAB_PLANT_ENABLED` | `false` | Boolean; independently activates local calculations. |
| `SMAB_PLANT_HOMIE_ID` | `sma-plant` | Valid unique Homie device ID. |
| `SMAB_PLANT_GRID_SOURCE` | `home-manager` | One enabled grid source; alternatively an enabled inverter slot with complete verified `grid` mappings. |
| `SMAB_PLANT_UPDATE_INTERVAL_SECONDS` | `1` | Positive seconds; maximum wait for expiry/calendar/checkpoint checks. New source receipts/errors wake calculation immediately. |
| `SMAB_PLANT_MAX_SKEW_SECONDS` | `240` | Positive seconds, at most 3600; maximum spread of contributing observation times, in addition to individual freshness. |
| `SMAB_PLANT_BOUNDARY_TOLERANCE_SECONDS` | `240` | Positive seconds, at most 900; bounded uncertainty for real counter snapshots around local midnight. No extrapolation. |
| `SMAB_PLANT_CHECKPOINT_INTERVAL_SECONDS` | `300` | Positive seconds; regular durable energy snapshot/publication cadence. Initial baselines, boundary transitions and resets are saved immediately. |
| `SMAB_PLANT_INITIAL_CONSUMPTION_KWH` | `0` | Deprecated compatibility setting, finite nonnegative number. Retained for existing ledger fingerprints/internal fields; no household lifetime topic is published. Leave existing values unchanged to preserve ledger compatibility. |
| `SMAB_PLANT_ASSUME_AC_BATTERY_ENERGY` | `false` | Boolean; explicitly treat an unverified battery counter boundary as AC for provisional household kWh. Diagnostic boundary becomes `assumed-ac`; documented DC mappings remain blocked. |
| `SMAB_PLANT_PUBLISH_PARTIAL_DAY` | `false` | Boolean; test mode publishing initial partial-day counter deltas from the first valid saved snapshot. Status remains `partial`. Does not override gaps, resets, battery-boundary or input-validity guards. |
| `SMAB_PLANT_DEBUG_ENABLED` | `false` | Boolean; opt into calculation and selected register evidence. Requires enabled plant and `SMAB_LOG_LEVEL=DEBUG` to emit logs. No extra device reads. |
| `SMAB_PLANT_DEBUG_INTERVAL_SECONDS` | `60` | Positive number of seconds; minimum interval between calculation reports and between reports per selected register. No immediate log on every change. |
| `SMAB_PLANT_DIAGNOSTICS_ENABLED` | `true` | Boolean; publish detailed plant diagnostics including dates, boundaries, input status and accounting timestamps. False retires their metadata/retained values; operational plantstatus and Basic day/average coverage statuses remain. |

JSON uses `plant.enabled`, `homieId`, `gridSource`, `updateIntervalSeconds`,
`maxSkewSeconds`, `boundaryToleranceSeconds`, `checkpointIntervalSeconds`,
`initialConsumptionKwh`, `assumeAcBatteryEnergy`, `publishPartialDay`, `debugEnabled`,
`debugIntervalSeconds`, `diagnosticsEnabled`; each inverter gains `role`.
The normal defaults < optional JSON < explicit ENV precedence applies.
Calendar accounting reuses `SMAB_TIMEZONE`, default `Europe/Berlin`.

The [topic table](PV_AGGREGATION_DESIGN.md#implemented-homie-layout) documents the
compact wire IDs. PV/storage sum topics are declared only with at least two
configured enabled contributors in that group. A failed contributor does not
reduce the sum's membership or become zero. Household power is computed even with
one PV/storage contributor; `consumptionwithcharging` preserves the distinct old
power balance including battery charging. Negative household results and negative
separate directional flows are unavailable rather than clamped. Current PV active
power remains signed. Inverter/PV/storage units and hybrid separation are validated.

Power sums and direct PV/storage counter sums update from received source samples;
durable grid/house balances publish only committed snapshots. Their actual oldest
input time is retained, not renewed on calculation or MQTT reconnect. All required
inputs must remain fresh and within skew limits; last-known retained values remain
distinct from current validity. Existing per-device topics are unchanged.

Counter accounting persists `energy-balances.json` under `SMAB_STATE_DIR`, normally
`/data/sma-mqtt-bridge/state/energy-balances.json` in volume `data_smab_state`.
It holds UTC snapshot/start times, local accounting dates, counter baselines,
confirmed values and configuration/hardware fingerprints. It contains no account
credentials, tokens, addresses or raw serials. Saves use atomic replacement with
file/directory sync; checkpoint publication follows successful persistence. The
topic manifest and command journals retain their existing independent files.

By default the first partial day is unavailable, not zero. Subsequent full days require
bounded observations around local midnight, including 23/25-hour DST days. A
midnight-spanning outage gives `gap`; do not interpret retained yesterday values as
today's measurement. `reset` blocks affected lifetime accounting until manual
reconciliation; daily accounting can start again at a covered next midnight.
Backward wall-clock observations give `clock-error`. Nonmonotone derived house
energy gives `inconsistent`, with no fabricated zero or lower confirmed counter.

Changed configuration/membership/timezone or hardware produces
`configuration-changed` without overwriting the old baselines; current power sums
continue independently. A corrupt/unreadable/symlink/oversize state file stops
startup before connections. Preserve the file for reconciliation. Starting a new
ledger deliberately requires stopping the service, backing up the old file and
choosing a verified opening value; keep the volume, manifests and command journals.

`diagnostics/importdaystatus`, `exportdaystatus`, `houseenergystatus`, `localdate`,
`batteryenergyboundary`, `importenergytime`, `exportenergytime`, `houseenergytime`
and `houseenergystart` expose coverage and scope. `diagnostics/validproperties`
lists the currently usable measurement topic paths, including freshness checks.
`diagnostics/powerinputstatus` is a JSON object naming blocked power inputs by
logical source and internal property key. Reasons distinguish `missing-or-invalid`,
`stale`, `source-error`, `unit-or-type-mismatch`, `invalid`,
`negative-directional-flow` and `sample-skew`; negative household results are
identified by `house/consumption` or `house/consumptionwithcharging` with
`negative-balance`. With no blocking input/balance it reports `{"status":"ready"}`.
This diagnostic follows `SMAB_PLANT_DIAGNOSTICS_ENABLED`, like all optional plant diagnostics.
A retained device value is not evidence of a currently valid source observation.
Invalid PV power blocks both PV power sums and household W, including at night;
calendar darkness alone never converts an invalid register into a measured zero. Values can include `partial`,
`complete`, `gap`, `reset`, `clock-error`, `configuration-changed`, `inconsistent`,
`unavailable`, `invalid`, `init` and `unsupported-battery-boundary`. `complete` means
covered within configured sampling tolerance, not an exact midnight meter read.

The bundled Storage mapping declares `energyBoundary=ac` based on the
[observed charge/discharge comparison](BATTERY_ENERGY_BOUNDARY_2026-10-15.md).
Its diagnostic reports `ac`; remove the now-unnecessary assumption override for
this profile. Reconcile host profile copies too: an old override still declaring
unverified takes precedence over the new bundled file. Counter IDs/scales and
the calculation itself are unchanged from the prior AC assumption.

Other unverified mappings still block household kWh by default. For provisional
comparison, SMAB_PLANT_ASSUME_AC_BATTERY_ENERGY=true explicitly treats them as AC
and reports assumed-ac; turning it off blocks those provisional values again.
Documented DC mappings, freshness, reset, negative-balance and midnight guards
remain enforced. Whole-kWh PV precision and full-day comparisons remain separate
acceptance questions. Previously recorded data is not automatically rewritten.

### Explicit energy-baseline restart after profile changes

The plant fingerprint includes complete profile contents. Therefore loading the
new AC profile against an old ledger deliberately reports configuration-changed.
Andreas approved starting new energy bases for this upgrade. After installing the
new build and reconciling any profile override, use the same Compose file/project
and state volume as the existing deployment:

```bash
(
set -e
docker compose run --rm --no-deps sma-mqtt-bridge --check-config
docker compose run --rm --no-deps sma-mqtt-bridge --help | grep -q -- '--reset-energy-baselines'
docker compose run --rm --no-deps --entrypoint python sma-mqtt-bridge -c 'from sma_mqtt_bridge.config import load_config; from sma_mqtt_bridge.plant import plant_plan; boundary = plant_plan(load_config())[2]; print(boundary); assert boundary == "ac", "Selected battery profile is not AC"'
docker compose stop sma-mqtt-bridge
docker compose run --rm --no-deps sma-mqtt-bridge --reset-energy-baselines
docker compose up -d sma-mqtt-bridge
)
```

The offline profile check must print ac before retiring bases. The explicit reset
command makes no device/MQTT/portal connections. It validates and atomically renames
only energy-balances.json to a unique timestamped backup in the same directory,
syncs the directory and prints reset plus the backup basename as JSON. The normal
exclusive bridge lock rejects concurrent service operation. Missing state returns
reset=false/backup=null without creating a ledger; invalid/symlink state is rejected.
Keep the backup, topic manifest, command journals and entire state volume.

All five energy accounts restart: grid import/export, house, Wallbox and house
without Wallbox. With SMAB_PLANT_PUBLISH_PARTIAL_DAY=true, first valid counter
snapshots become the new bases and publish zero deltas with partial status.
Otherwise partial-day values remain unavailable until a covered midnight.
Actual device lifetime counters, PV yield sums and current powers are unchanged.
Existing InfluxDB samples are preserved, but new daily values can create a midday
drop in the same series; compare only periods sharing the new start. These
commands require the new image; an older published image lacks the reset option.

The additional `house/totalconsumption` topic was removed at Andreas' request.
It had no identified legacy Item counterpart and counted only from a bridge
baseline. Existing ledger fields and the legacy opening-value setting remain
compatible so this topic removal does not reset daily accounts. The owned retained
value and metadata retire through the topic manifest after loading the new build;
preserve the state volume. No existing openHAB Item or history is changed.

### Initial partial-day test values

Set `SMAB_PLANT_PUBLISH_PARTIAL_DAY=true` to test counter-based day values without
waiting for midnight. New accounts save the first valid common counter vector as
their baseline and publish a real zero delta, then consumption since that snapshot.
This applies to grid daily import/export, house daily consumption, Wallbox daily
consumption and house daily consumption without Wallbox. The direct PV day-yield
sum retains its device-provided calendar-day meaning and is not rebased.

Coverage diagnostics remain `partial`: these are measured partial-day differences,
not full calendar-day totals or reconstructed midnight values. Existing partial
accounts reuse their already saved first snapshot; enabling the flag never resets
them or changes the ledger signature. Restarts reuse the same baseline. With a
covered midnight the normal daily baseline takes over automatically and reports
`complete`; missed midnights remain `gap` and do not publish test values. Accounts
already marked complete continue normal daily accounting.

All input freshness/skew, units, identity, AC-boundary, reset, clock and negative/
decreasing-balance guards still apply. Only committed snapshots are published at
the normal checkpoint cadence. Disable the flag to stop publishing partial-day
results; this does not erase baselines or last-known retained MQTT observations.
Current eligibility remains visible in coverage diagnostics and validproperties.
The flag defaults to false and requires no state-file/schema migration.

### Calculation debug logs

To investigate unavailable plant values, temporarily configure:

```dotenv
SMAB_LOG_LEVEL=DEBUG
SMAB_PLANT_DEBUG_ENABLED=true
SMAB_PLANT_DEBUG_INTERVAL_SECONDS=60
```

Recreate the service with the updated build/configuration. Search its container
logs for `Plant calculation debug` and `Plant register debug`. Calculation reports
contain logical input keys, numeric values/units, observation age, freshness,
source-error flags, signed power/energy recipes, available derived values, coverage
statuses and the effective battery boundary. Account evidence includes local dates,
UTC observation/start times, numeric day/total baselines and current counters,
plus separately committed values/times and pending checkpoint state. Available
values describe current internal eligibility, not broker acknowledgement.

Register reports use only already-read, identity-verified inverter responses:
numeric plant contributions plus existing measurements/status and grid-contactor,
when those properties are enabled and due. They include register address, register
words, numeric decoded value, validity, scale and byte/word order. Enum status
values have raw words and validity but no numeric decoded value. Identity registers,
strings, addresses, serial guards, credentials, fingerprints and authenticated
HTTP payloads are excluded. Polling frequency and measurement validity do not change.
No reads or raw register logs are added for the Home Manager or eCharger; their
existing decoded plant inputs appear in the calculation report.

Reports are periodic: one calculation report per configured interval, and at most
one report per selected register per interval, only when its existing poller runs.
An intervening transition may therefore not appear. Transport/identity failures
remain in normal source diagnostics; they cannot produce a successful raw-register
report. Logs stay on standard output under existing container log retention;
no additional debug file or energy-state mutation is introduced. Disable the plant
debug flag and return the log level to INFO after collecting the evidence.

### Wallbox daily consumption

With both `SMAB_PLANT_ENABLED=true` and the independently enabled local API
`SMAB_ECHARGER_ENABLED=true`, two further read-only kWh properties are declared:

| Topic (default device IDs) | Meaning |
| --- | --- |
| `homie/sma-echarger/measurements/dailyconsumption` | Change in the local API `measurements/totalenergy` counter over the covered local day. |
| `homie/sma-plant/house/dailyconsumptionwithoutwallbox` | The household counter balance minus that Wallbox counter change, using one shared baseline vector. |

No additional ENV flag, InfluxDB connection, API call, command or polling interval
is introduced. API-only and API+SEMP installations use the same local total-energy
counter. SEMP-only/disabled API configurations do not declare these properties;
a missing/stale/invalid enabled counter never becomes zero. Session-energy resets
and session boundaries do not define a calendar day.

Wallbox daily consumption is independent of the battery AC/DC gate. Household
consumption without Wallbox has the same AC boundary requirement or explicit
provisional AC override as household kWh. Both use SMAB_TIMEZONE, existing checkpoint cadence, initial partial-day,
midnight coverage, DST, reset and clock guards. The subtraction uses aligned
counter snapshots, not independently initialized daily results. A late enable
starts new partial Wallbox accounts while preserving existing grid/house baselines.
Negative or decreasing derived daily energy is unavailable/inconsistent, never
clamped. No assumption about unmetered Wallbox standby consumption is added;
this property has the scope of the existing Wallbox total-energy measurement.

The Wallbox value and its `diagnostics/wallboxdaystatus` / `wallboxenergytime`
properties use the configured eCharger Homie device ID, alongside totalenergy
and sessionenergy. Wallbox day status is Basic; only its snapshot timestamp follows
`SMAB_ECHARGER_DIAGNOSTICS_ENABLED`, independently of the plant flag.
The plant retains `diagnostics/housewithoutwallboxdaystatus`
and `housewithoutwallboxenergytime`. Diagnostics report coverage and oldest
committed input UTC time. A partial Wallbox day does not degrade charger readiness.
The previous plant wallbox node and its two diagnostics are retired through the
existing topic manifest on upgrade; the same persisted wallbox account/baseline
is reused. Keep existing openHAB Item identity/history when updating a link. The observed API serial is validated before a hashed identity is
passed to the ledger together with the selected primary/fallback counter channel;
identity, endpoint or counter-channel changes block only affected Wallbox accounts.
State uses additional `wallbox` and `housewithoutwallbox` accounts in the same
energy-balances.json file, preserving existing accounts and the topic manifest.
Earlier builds recognizing only the original account names reject this extended
ledger on downgrade; retain a matching state-volume backup for rollback rather
than deleting baselines or command journals. Existing openHAB rules, Shelly
histories and the seven-day Wallbox-ON exclusion stay unchanged until comparison.

## Manual portal read refresh

When `SMAB_PORTAL_ENABLED=true`, Homie `portal/refresh/set` accepts the exact
non-retained string `refresh`. This read-only action needs neither the global
command gate nor the portal preference-write gate. It is always available for
an enabled portal adapter, independent of optional channel groups; no new ENV
setting is required. Disabled portal adapters expose no refresh property and
perform no portal I/O.

The existing supervisor handles the request, retaining read-cycle timeouts,
authentication blocking, session locking and bounded failure backoff. Pending
requests are coalesced and a running read satisfies repeated requests. Successful
reads update the existing preference topics and restart the configured polling
wait. Interval zero waits for an explicit refresh rather than reading on startup
(unless the existing CLI one-shot refresh is selected). MQTT reconnect does not
request a refresh; retained requests are rejected.

The retained `portal/refresh` string reports `queued`, `reading`, `completed`,
`failed`, `auth-blocked`, `rejected`, `rejected-retained` or `rejected-busy`.
It contributes no device readiness. `completed` confirms a validated read,
not a preference write or physical charging action. See the
[openHAB setup](../openHAB/openHAB.md#manual-portal-refresh).

## Yield remuneration and seven-day household averages

Each inverter supports `SMAB_INVERTER<n>_YIELD_TARIFF_PER_KWH` (finite
nonnegative float, default `0`, slots 1–3). `SMAB_PLANT_CURRENCY` is a nonempty
string of at most 16 characters, default `€`. JSON equivalents are
`yieldTariffPerKwh` in each inverter and `currency` in `plant`; normal precedence
applies. No private tariffs are supplied by the bridge.

With plant enabled, `pv/totalearnings` sums each enabled PV contributor's
**entire lifetime PV yield × its individual tariff**. It includes self-consumed
production and is not a measurement of actual feed-in payments. Battery-only
inverters are excluded. Discovery and values exist only if at least one enabled
PV contributor has an explicitly configured tariff in ENV or optional JSON.
An explicit zero is valid and activates that contributor; an omitted tariff does
not contribute and its counter does not gate remuneration availability. Removing
all applicable tariffs retires the channel and its retained metadata through the
existing topic manifest. All configured contributors' counters must be fresh and
valid, including explicit zero-rate contributors. Preserve explicit zero tariffs
when simplifying configuration: omission and explicit zero have different meaning. Currency is the Homie unit; tariffs are in that currency per kWh,
not cents. Changing a tariff recalculates the entire historical yield at that rate;
there is no tariff-period accounting or currency conversion.

Only the plant exposes `house/averagedailyconsumption` and, with local Wallbox
API enabled, `house/averagedailyconsumptionwithoutwallbox`, float `kWh/d`.
They average the seven preceding completed local calendar days, excluding today.
The latter subtracts measured Wallbox consumption; charging days remain included.
All seven dates must be present; missing/partial/reset/gap days never count as zero.
A 23/25-hour daylight-saving day counts as one calendar day. Existing boundary
tolerance still applies; no interpolation or InfluxDB backfill is performed.

Seven bounded historical day values per house account are saved in the existing
energy ledger, as optional `history` fields. Existing ledgers load without rebasing;
collection begins with the next complete day. Seven full days are required after
upgrade before the first average. New state remains schema 1, but older binaries
reject the added field: restore a matching pre-upgrade backup for rollback. The
existing energy-baseline reset archives this history with the ledger. Averages
use committed history only; failed durable writes cannot publish new averages.
Coverage diagnostics are `diagnostics/averagedaystatus` and
`diagnostics/averagewithoutwallboxdaystatus` (`complete`/`insufficient-history`).
Both coverage properties are Basic and remain published with Diagnostics disabled.
All added properties are read-only; no device I/O or openHAB changes are introduced.
