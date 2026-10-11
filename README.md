# SMA MQTT Bridge

A Python Docker service publishing SMA measurements and charging preferences through Homie 4 MQTT, with optional guarded local eCharger controls. Target: Raspberry Pi 5, Linux arm64. Sunny Home Manager remains the charging controller.

**Status: Python read service, first installation reads verified.** Configuration, profile validation, generic Modbus reads, Home Manager meter reception, local eCharger API/SEMP reads, optional ennexOS reads and Homie publishing are implemented. The three bundled inverter profiles cover the existing 41 channels and were checked against official model-specific lists and local identity reads. Inverters and SEMP have published real values to the installation broker. Authenticated API/portal reads and verified local setting units have also reached MQTT. Full openHAB comparison and Raspberry Pi/Home Manager acceptance remain pending. Local enum/boolean controls, combined charging plans and portal minimum PV writes are implemented and offline-tested behind independent disabled-by-default gates; no Python live device write has been accepted. See the [local command contract](docs/CONFIGURATION.md#local-echarger-command-milestone). See [register validation](docs/REGISTER_VALIDATION.md) and [Mac test instructions](docs/MAC_TEST.md).

The runtime uses the verified official `python:3.14.8-slim-trixie` multi-platform digest in `Dockerfile-SMAB`. On 2026-10-10 the stable `3.15.0-slim-trixie` tag was still absent. The obsolete C++ diagnostic sources/toolchain have been removed.

## Local setup and diagnostics

Use Python 3.14+ and the pinned dependencies:

```bash
python3.14 -m venv .venv
.venv/bin/python -m pip install --requirement ressources/requirements.txt
(cd ressources && ../.venv/bin/python -m sma_mqtt_bridge --version)
(cd ressources && ../.venv/bin/python -m sma_mqtt_bridge --project-status)
(cd ressources && ../.venv/bin/python -m sma_mqtt_bridge --check-config)
(cd ressources && ../.venv/bin/python -m sma_mqtt_bridge --check-profile sma-stp8-0-3av-40)
./tests/test-check.sh
```

The Python CLI consumes process environment variables; it does not read or rewrite `smab.env`. Compose passes the host file into the service. Additional JSON is optional. Diagnostics show counts/status only, never resolved settings or credentials. A profile schema check can succeed while `pollingValidated` remains false.

Read [configuration and defaults](docs/CONFIGURATION.md), [profile schema](docs/PROFILES.md), [migration coverage](docs/MIGRATION.md), [the value catalogue](docs/WERTEKATALOG.md) and [validation evidence](docs/VALIDATION.md). Outstanding inputs and decisions are preserved in [todo.md](todo.md).

## Docker on the Raspberry Pi

Build locally; no GHCR image has been released:

```bash
docker compose -f docker-compose.dev.yml build
docker compose -f docker-compose.dev.yml run --rm sma-mqtt-bridge --check-config
docker compose -f docker-compose.dev.yml up -d
```

Both Compose files are standalone. You can start `docker-compose.dev.yml` directly with VS Code's Compose Up command; its build settings select `Dockerfile-SMAB` and build the local image automatically. `docker-compose.example.yml` has the same runtime options, but pulls `ghcr.io/alaub81/sma-mqtt-bridge` with the selected `SMAB_BRIDGE_VERSION`. The deployment template becomes usable once an image has been published. [Compose's build specification](https://docs.docker.com/reference/compose-file/build/) describes the build/image selection.

Prepare `smab.env` in the repository root only on a fresh installation; preserve any existing file. [smab.example.env](smab.example.env) documents every available variable with purpose, type and default. Copy it to `smab.env` on a fresh installation and change only the required settings. Both Compose files explicitly load `smab.env` through the service's `env_file`; starting with the default layout needs no extra flag. To apply Compose-only settings from that file, such as `SMAB_DATA_DIR`, `SMAB_UID` or the deployment image version, use `docker compose --env-file smab.env -f docker-compose.dev.yml up -d`. Compose automatically looks only for `.env` for interpolation; an optional `.env` may hold Compose-only settings separately. Optional JSON, profiles, certificates and password files remain under `data/sma-mqtt-bridge/`; runtime state uses the named Compose volume `data_smab_state`. All sources default to disabled. Enabling an inverter needs a validated bundled or host profile with local identity mappings. Home Manager needs its serial selector; SEMP needs its device ID. The local API requires separate credentials, expected serial and verified TLS trust. No addresses or credentials are invented.

Files are bind-mounted at `/data/sma-mqtt-bridge`. The container runs as UID/GID 10001; set Compose-only `SMAB_UID`/`SMAB_GID` to the host account IDs where required. The chosen account must read configured profiles/certificates/password files and write the state volume mounted at `/data/sma-mqtt-bridge/state`. Fresh volumes use the image's UID/GID 10001; prepare volume ownership separately when overriding the user. Preserve the volume across container replacement; `docker compose down -v` deletes it. Follow the [state migration instructions](docs/CONFIGURATION.md#migrating-existing-state-from-a-bind-mount) for earlier bind-mounted state. Keep `smab.env` and secrets at mode 0600. Do not make the entire configuration directory world-writable. Compose requires version 2.24+.

The template uses Linux host networking for multicast. Receiving actual Home Manager telegrams on the Pi, interface/VLAN routing and encrypted Speedwire remain acceptance checks. Docker Desktop does not certify this network behavior.

The process records a main-loop heartbeat and independent MQTT/source availability. Docker health tests liveness, not successful device communication. MQTT outages rebuild clients with bounded backoff; expired or invalid values keep the last retained observation without publishing an invented zero. Retained measurements are last-known values; source diagnostics separately report freshness. Source diagnostic timestamps are UTC receipt times. A manifest records only owned MQTT topic names for retirement after disabling a source, changing IDs or changing the prefix. Preserve this file to clean up old discovery; changing brokers requires separate retirement on the old broker.

Portal polling defaults to zero and performs no login or read on startup. A positive interval enables periodic reads. `--refresh-portal` explicitly requests one read in an enabled zero-interval service; the process then continues serving Homie and expires that sample normally. Restart with this option to request another read. MFA/CAPTCHA is unsupported; authentication rejection blocks that source until configuration is corrected and the service restarted.

## Lint and CI

```bash
python3.14 -m venv .lint-venv
.lint-venv/bin/python -m pip install --requirement tests/requirements-lint.txt
.lint-venv/bin/python tests/install_lint_tools.py
./tests/linter-check.sh
```

Python files are checked with Ruff and Pylint 4.1.2 (`--errors-only`, configured in `.pylintrc`). Pylint covers fatal/error diagnostics; convention, refactoring and warning messages are not enabled initially. The lint requirements include runtime libraries for import inference; CI uses the same runner and pins. Missing Pylint or a failed check fails the lint run.

All repository files receive hygiene checks; Python, shell, Docker, YAML, Actions, JSON and Markdown receive their relevant linters. Offline tests require Python and runtime libraries, without a compiler, Docker, SMA devices or a broker. With Docker Compose installed, run `python3 tests/compose_check.py` to check both standalone files, runtime parity and deployment overrides using public settings only. CI runs that check and builds/tests amd64 and arm64 images. Local execution does not prove that GitHub CI or an image security scan has run.

## Repository layout

- `ressources/`: all image inputs, copied into `/app`: `sma_mqtt_bridge/`, bundled `profiles/` and pinned `requirements.txt`.
- `tests/`: deterministic offline tests, Compose parity and lint tooling.
- `docs/`: current configuration, [profile schema](docs/PROFILES.md), values, migration and implementation documentation; historical evidence is explicitly archived.
- Root: `Dockerfile-SMAB`, both standalone Compose files, `smab.example.env`, private ignored `smab.env`, optional [JSON configuration example](config.example.json) and lint settings including `.hadolint.yaml`.

`ressources/` is reserved for image contents. Examples, tests, documentation and private host files stay outside it. The Docker build context uses an allowlist for this directory and excludes Python bytecode caches.

GitHub publication, pushes and container releases remain later milestones. No paid SMA Developer API or alternative charging controller is used.

## License

MIT. See [LICENSE](LICENSE). This project is not affiliated with SMA.

Display labels support `SMAB_LANGUAGE=en` (default) or `de`, with bundled dictionaries and host
overrides under `data/sma-mqtt-bridge/translate/`. See [translation templates](translate/README.md).
Homie node/property IDs are compact lowercase names, such as `internaltemperature` and
`settings/chargemode/set`; configured device IDs stay unchanged. On upgrade preserve the state
volume for old retained-topic cleanup and update existing openHAB channel links and command
publishers. Language changes affect labels only. See [configuration](docs/CONFIGURATION.md#display-language-and-compact-channel-ids).

For MainUI charger Item metadata and a deployable charging-plan dialog, see
[the openHAB setup guide](openHAB/openHAB.md).
