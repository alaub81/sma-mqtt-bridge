# SMA MQTT Bridge

A Python Docker service publishing read-only SMA measurements and charging preferences through Homie 4 MQTT. Target: Raspberry Pi 5, Linux arm64. Sunny Home Manager remains the charging controller.

**Status: first Python implementation, offline tested.** Configuration, profile validation, generic Modbus reads, Home Manager meter reception, local eCharger API/SEMP reads, optional ennexOS reads and Homie publishing are implemented. Hardware/network acceptance and full openHAB migration remain pending. The three bundled inverter profiles are identity-only; enabling them deliberately fails before any network connection. No command subscriptions or device writes are implemented.

The runtime uses the verified official `python:3.14.8-slim-trixie` multi-platform digest in `Dockerfile-SMAB`. On 2026-10-10 the stable `3.15.0-slim-trixie` tag was still absent. The obsolete C++ diagnostic sources/toolchain have been removed; [baseline provenance](docs/BASELINE.md) and [third-party attribution](docs/THIRD_PARTY.md) are preserved.

## Local setup and diagnostics

Use Python 3.14+ and the pinned dependencies:

```bash
python3.14 -m venv .venv
.venv/bin/python -m pip install --requirement requirements.txt
.venv/bin/python -m sma_mqtt_bridge --version
.venv/bin/python -m sma_mqtt_bridge --project-status
.venv/bin/python -m sma_mqtt_bridge --check-config
.venv/bin/python -m sma_mqtt_bridge --check-profile sma-stp8-0-3av-40
./tests/test-check.sh
```

The Python CLI consumes process environment variables; it does not read or rewrite `.env`. Compose passes the host file into the service. Additional JSON is optional. Diagnostics show counts/status only, never resolved settings or credentials. A profile schema check can succeed while `pollingValidated` remains false.

Read [configuration and defaults](docs/CONFIGURATION.md), [profile schema](profiles/README.md), [migration coverage](docs/MIGRATION.md), [the value catalogue](docs/WERTEKATALOG.md) and [validation evidence](docs/VALIDATION.md). Outstanding inputs and decisions are preserved in [todo.md](todo.md).

## Docker on the Raspberry Pi

Build locally; no GHCR image has been released:

```bash
docker compose -f docker-compose.dev.yml build
docker compose -f docker-compose.dev.yml run --rm sma-mqtt-bridge --check-config
docker compose -f docker-compose.dev.yml up -d
```

Both Compose files are standalone. You can start `docker-compose.dev.yml` directly with VS Code's Compose Up command; its build settings select `Dockerfile-SMAB` and build the local image automatically. `docker-compose.example.yml` has the same runtime options, but pulls `ghcr.io/alaub81/sma-mqtt-bridge` with the selected `SMAB_BRIDGE_VERSION`. The deployment template becomes usable once an image has been published. [Compose's build specification](https://docs.docker.com/reference/compose-file/build/) describes the build/image selection.

Prepare `.env` in the repository root only on a fresh installation; preserve any existing file. [.env.example](.env.example) documents every available variable with purpose, type and default. Copy it to `.env` on a fresh installation and change only the required settings. Compose automatically reads the root `.env` for interpolation and passes it into the service; no `--env-file` flag is needed. Optional JSON, profiles, certificates, password files and state remain under `data/sma-mqtt-bridge/`. All sources default to disabled. Enabling an inverter needs a validated host profile with local identity mappings. Home Manager needs its serial selector; SEMP needs its device ID. The local API requires separate credentials, expected serial and verified TLS trust. No addresses or credentials are invented.

Files are bind-mounted at `/data/sma-mqtt-bridge`. The container runs as UID/GID 10001; set Compose-only `SMAB_UID`/`SMAB_GID` to the host account IDs where required. The chosen account must read configured profiles/certificates/password files and write the `state/` subdirectory. Keep `.env` and secrets at mode 0600. Do not make the entire configuration directory world-writable. Compose requires version 2.24+.

The template uses Linux host networking for multicast. Receiving actual Home Manager telegrams on the Pi, interface/VLAN routing and encrypted Speedwire remain acceptance checks. Docker Desktop does not certify this network behavior.

The process records a main-loop heartbeat and independent MQTT/source availability. Docker health tests liveness, not successful device communication. MQTT outages rebuild clients with bounded backoff; expired or invalid values lose their retained payload instead of becoming zero. Source diagnostic timestamps are UTC receipt times. A manifest records only owned MQTT topic names for retirement after disabling a source, changing IDs or changing the prefix. Preserve this file to clean up old discovery; changing brokers requires separate retirement on the old broker.

Portal polling defaults to zero and performs no login or read on startup. A positive interval enables periodic reads. `--refresh-portal` explicitly requests one read in an enabled zero-interval service; the process then continues serving Homie and expires that sample normally. Restart with this option to request another read. MFA/CAPTCHA is unsupported; authentication rejection blocks that source until configuration is corrected and the service restarted.

## Lint and CI

```bash
python3.14 -m venv .lint-venv
.lint-venv/bin/python -m pip install --requirement tests/requirements-lint.txt
.lint-venv/bin/python tests/install_lint_tools.py
./tests/linter-check.sh
```

All repository files receive hygiene checks; Python, shell, Docker, YAML, Actions, JSON and Markdown receive their relevant linters. Offline tests require Python and runtime libraries, without a compiler, Docker, SMA devices or a broker. With Docker Compose installed, run `python3 tests/compose_check.py` to check both standalone files, runtime parity and deployment overrides using public settings only. CI runs that check and builds/tests amd64 and arm64 images. Local execution does not prove that GitHub CI or an image security scan has run.

## Repository layout

- `sma_mqtt_bridge/`: Python runtime and read adapters.
- `profiles/`: bundled inverter model descriptors and profile schema.
- `ressources/`: optional [JSON configuration example](ressources/config.example.json) and Docker lint configuration.
- `tests/`: deterministic offline tests, Compose parity and lint tooling.
- `docs/`: current configuration, values, migration and implementation documentation; historical evidence is explicitly archived.
- Root: `Dockerfile-SMAB`, both standalone Compose files, `.env.example`, private ignored `.env`, and Python dependency pins in `requirements.txt`.

GitHub publication, pushes and container releases remain later milestones. No paid SMA Developer API or alternative charging controller is used.

## License

MIT. Inherited BMW attribution remains in [LICENSE](LICENSE); historical nlohmann/json attribution is preserved in [THIRD_PARTY.md](docs/THIRD_PARTY.md). [BASELINE.md](docs/BASELINE.md) remains the original provenance record. This project is not affiliated with SMA.
