# Configuration contract

Andreas requested this contract on 2026-10-10. It is binding for the Python implementation. **The current C++ diagnostic scaffold does not load these settings.** Compose already uses the host directory and `SMAB_` deployment variables; runtime validation and defaults are implementation work.

## Host files and precedence

All installation files belong under `./data/sma-mqtt-bridge/` relative to the Compose project directory. Bind-mount that directory to `/data/sma-mqtt-bridge` in the container:

```text
data/sma-mqtt-bridge/
  .env                 # Explicit overrides and installation credentials
  config.json          # Optional non-secret configuration
  profiles/            # Verified register profiles, one or more per inverter
  certs/               # CA certificates and optional client certificate/key
  secrets/             # Optional password files
  state/               # Heartbeat and necessary non-secret persistent state
```

The directory is excluded from Git and Docker build contexts. Keep `.env`, secret files and private keys readable only by the owner/container user. Never generate a configuration file containing resolved passwords or session tokens. Do not rewrite user configuration automatically.

The future loader uses built-in defaults and selected profile connection defaults, then optional `config.json`, then explicit `SMAB_` environment values. Resolve the profile selector from configuration/ENV first; its defaults never override explicit installation settings. Missing default `config.json` is valid; an explicitly selected missing file or invalid JSON is an error. Profiles supply protocol metadata and per-poller intervals, not credentials or device activation. A device-level interval explicitly set in JSON or ENV overrides all its pollers; otherwise preserve profile intervals and use the default only for pollers without an interval.

Every operational option must be overridable through ENV and documented with type, default and validation. Unknown runtime `SMAB_` keys, malformed values, duplicate device/Homie IDs and conflicting password/password-file settings must fail validation before any connection. Recognize Compose-only variables without treating them as runtime options. An absent variable uses the previous layer; an empty value clears only optional strings. Empty booleans or numbers are errors. Accept boolean `true`/`false` case-insensitively, validate finite positive durations, ports 1–65535 and Modbus unit IDs 1–247. Only portal polling accepts zero to mean no periodic polling.

JSON is optional, not a second mandatory setup step. JSON names use camelCase as illustrated in [config.example.json](../config.example.json); runtime fields live under `runtime`, MQTT fields under `mqtt`, device fields under their respective sections, and global command settings under `commands`. Compose-only settings are not JSON fields. Credentials use ENV or optional password files.

## Minimal deployment overrides

A broker address and each enabled device's required installation values suffice. All sources and write paths are disabled by default; setting a host or credentials does not enable a source. Enabling an adapter enables bridge access, not the physical inverter/charger itself. A disabled source creates no device sessions, polling, subscriptions to its commands or writes, and must not advertise its unavailable properties as fresh. A Homie device with no enabled sources must not be advertised as ready. Sources sharing one Homie device retain independent availability; disabling one does not implicitly enable or disable the other. Previously retained discovery/state must have an explicit retirement policy when a source is disabled.

For one inverter, the future runtime needs only:

```dotenv
SMAB_MQTT_HOST=mqtt.example.invalid
SMAB_INVERTER1_ENABLED=true
SMAB_INVERTER1_HOST=inverter.example.invalid
SMAB_INVERTER1_PROFILE=sma-stp8-0-3av-40
```

Add broker authentication/CA overrides if required by that installation. Select a reusable model profile by ID; the repository now provides three identity-only default descriptors under [profiles/](../profiles/README.md), but does not yet bundle validated complete register mappings for the installed devices. Never invent an IP address, password, serial number or register mapping as a working default.

Each inverter is independent. The first three slots default respectively to `sma-stp8-0-3av-40`, `sma-sbs3-7-10` and `sma-sb4-0-1av-41`, and each selection can be overridden. A profile is reusable across slots; slot number does not determine the connected model. Further slots use the same `SMAB_INVERTER<N>_` family, with an empty profile default requiring explicit selection, without another hard-coded adapter. A disabled slot does not require a host or profile. An enabled slot requires a host and validated matching profile; validate discovered device identity against the profile and an optional expected serial number before accepting data.

For an ID, the planned resolver checks `<id>.json` under `SMAB_PROFILE_DIR` before the bundled resource. An invalid override must fail instead of silently falling back. `file:custom-name.json` selects only a host file, with no bundled fallback; reject directory traversal and absolute paths. Model profiles contain model/firmware compatibility evidence, protocol defaults, register definitions and Homie metadata, not installation credentials or addresses. Add future supported inverters as profile files rather than code branches. See the profile README for the draft schema and validation gate.

Home Manager requires a serial selector to distinguish meter telegrams. Its host/IP is an optional additional sender filter; UDP reception does not establish a TCP connection to that host. Interface/bind address, multicast group and timeout remain configurable. Do not enable its NSD Modbus server merely to read meter data. Encrypted Speedwire support must be verified separately before promising compatibility.

eCharger requires a host, local account credentials and a trusted certificate/CA, unless its certificate is already trusted by the system store. Its API and SEMP schedules are separate. The portal remains separately enabled and uses separate credentials, plant/device IDs and session handling. It initially supplies minimum PV percentage for the configured eCharger Homie device, independently of local API availability. Home Manager remains the charging controller.

## ENV options and defaults

All names below include the `SMAB_` prefix. Empty strings are the default for optional strings and installation-specific values. Paths refer to the container except the Compose-only host paths. Boolean flags, integer ports/IDs/counts and numeric durations follow the validation above; other entries are strings.

| Variable | Default | Meaning / validation |
| --- | --- | --- |
| `SMAB_BRIDGE_VERSION` | `latest` | Compose image tag; select a published version for deployment. No release exists yet. |
| `SMAB_DATA_DIR` | `./data/sma-mqtt-bridge` | Compose host bind directory. |
| `SMAB_ENV_FILE` | `./data/sma-mqtt-bridge/.env` | Compose service ENV file; optional for diagnostics. |
| `SMAB_CONFIG_FILE` | `/data/sma-mqtt-bridge/config.json` | Optional JSON configuration. |
| `SMAB_PROFILE_DIR` | `/data/sma-mqtt-bridge/profiles` | Verified device profile directory. |
| `SMAB_STATE_DIR` | `/data/sma-mqtt-bridge/state` | Non-secret persistent state and heartbeat. |
| `SMAB_TIMEZONE` | `Europe/Berlin` | IANA timezone for timestamps and day boundaries. |
| `SMAB_LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`; redact secrets at every level. |
| `SMAB_HEALTH_INTERVAL_SECONDS` | `10` | Main-loop heartbeat interval. |
| `SMAB_HEALTH_STALE_SECONDS` | `60` | Heartbeat failure threshold; greater than heartbeat interval. |
| `SMAB_SHUTDOWN_TIMEOUT_SECONDS` | `10` | Bounded graceful shutdown. |
| `SMAB_RECONNECT_MIN_SECONDS` | `1` | Initial supervised reconnection delay, with jitter. |
| `SMAB_RECONNECT_MAX_SECONDS` | `60` | Maximum delay; at least the minimum. No uncertain write retries. |
| `SMAB_COMMANDS_ENABLED` | `false` | Global gate for confirmed command allowlists. |
| `SMAB_COMMAND_READBACK_TIMEOUT_SECONDS` | `30` | Time limit to confirm a command through readback. |

| MQTT suffix after `SMAB_MQTT_` | Default | Meaning / validation |
| --- | --- | --- |
| `HOST` | empty | Required broker IP/hostname. |
| `PORT` | `8883` | TCP port, independently configurable. |
| `USERNAME`, `PASSWORD`, `PASSWORD_FILE` | empty | Optional broker authentication; choose direct password or a file. |
| `CLIENT_ID` | `sma-mqtt-bridge` | Base ID; derive unique clients for advertised Homie devices. |
| `HOMIE_PREFIX` | `homie` | One valid Homie topic level, without wildcards. |
| `TLS` | `true` | Use TLS; explicit `false` selects a plaintext broker connection. |
| `TLS_VERIFY` | `true` | Certificate verification; `false` is rejected. |
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
| `ENABLED` | `false` | Enable the meter receiver for this source. |
| `HOST` | empty | Optional source IP filter. |
| `SERIAL` | empty | Required telegram identity selector when enabled. |
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
| `PORT` | `443` | HTTPS port; local API always verifies TLS. |
| `TLS_CA_FILE` | empty | Trusted local certificate/CA; system trust if omitted. |
| `EXPECTED_SERIAL` | empty | Optional local device identity check. |
| `API_POLL_INTERVAL_SECONDS` | `60` | Parameter/live-data schedule, separate from SEMP. |
| `SEMP_ENABLED` | `true` | Enable local SEMP reads only when the parent source is enabled. |
| `SEMP_PORT`, `SEMP_PATH` | `80`, `/semp/` | Local SEMP endpoint; validate response identity. |
| `SEMP_POLL_INTERVAL_SECONDS` | `30` | Local SEMP measurement schedule. |
| `TIMEOUT_SECONDS`, `STALE_SECONDS` | `10`, `180` | HTTP timeout and freshness threshold. |
| `HOMIE_ID` | `sma-echarger` | Shared charger identity for local and portal properties. |
| `COMMANDS_ENABLED` | `false` | Additional gate for the confirmed local command allowlist. |

| Portal suffix after `SMAB_PORTAL_` | Default | Meaning / validation |
| --- | --- | --- |
| `ENABLED` | `false` | Separate optional ennexOS adapter. |
| `BASE_URL` | `https://ennexos.sunnyportal.com` | HTTPS origin with mandatory certificate verification. |
| `USERNAME`, `PASSWORD`, `PASSWORD_FILE` | empty | Separate portal account; choose password or a file. |
| `PLANT_ID`, `DEVICE_ID` | empty | Required installation selectors when enabled. |
| `TIMEOUT_SECONDS` | `15` | Request timeout. |
| `POLL_INTERVAL_SECONDS` | `0` | Explicit refresh by default; positive value enables periodic requests. |
| `COMMANDS_ENABLED` | `false` | Additional gate for confirmed minimum PV percentage writes. |

The option list is expandable as adapters are implemented; add settings, their defaults and validation here and in `.env.sample` in the same change. Validate Homie IDs as lowercase letters, digits and internal hyphens; derive one MQTT connection/Last Will per advertised device. Command gates never override a missing allowlist, missing rights, invalid bounds or readback requirements. Do not expose an editable installer setting merely because its metadata is writable.

## Compose usage

Place only needed overrides in `data/sma-mqtt-bridge/.env`; no additional JSON file is mandatory. When preparing a fresh installation, copy `.env.sample` there and replace its placeholder broker host. Keep existing configuration intact. The service's `env_file` passes those values into the container, while `--env-file` also supplies Compose interpolation, for example the image tag or an alternative host directory:

```bash
docker compose --env-file ./data/sma-mqtt-bridge/.env -f docker-compose.dev.yml run --rm sma-mqtt-bridge --project-status
```

This remains a diagnostic command until the Python runtime is implemented. The optional service ENV file requires Docker Compose 2.24 or newer. Diagnostics can render templates without any private file. Home Manager multicast networking on the Raspberry Pi remains a separate deployment check; the bind mount alone does not establish UDP reachability.

References: [Docker Compose ENV files](https://docs.docker.com/compose/how-tos/environment-variables/set-environment-variables/), [Compose bind mounts](https://docs.docker.com/reference/compose-file/services/#volumes), [Homie 4 convention](https://homieiot.github.io/specification/spec-core-v4_0_0/).
