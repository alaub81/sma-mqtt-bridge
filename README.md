# SMA MQTT Bridge

A Python Docker service publishing SMA measurements and charging preferences through
Homie 4 MQTT, with optional guarded eCharger controls. Target: Raspberry Pi 5,
Linux arm64. Sunny Home Manager remains the charging controller.

Reads and allowlisted controls are implemented and offline tested. Selected installation
checks have passed; full production acceptance and openHAB migration remain pending.
See the [current acceptance matrix](docs/VALIDATION.md) for dated evidence and gaps.

## Local setup

Preserve any existing root `smab.env`. On a fresh installation, copy
[smab.example.env](smab.example.env) to `smab.env` and configure only required settings.
Sources and command gates default to disabled. Additional JSON is optional.
See [configuration, TLS and state storage](docs/CONFIGURATION.md).

Build and validate locally; GHCR publication remains a later milestone:

```sh
docker compose --env-file smab.env -f docker-compose.dev.yml build
docker compose --env-file smab.env -f docker-compose.dev.yml run --rm sma-mqtt-bridge --check-config
```

To start selected, explicitly enabled sources, follow
[the installation acceptance procedure](docs/MAC_TEST.md).
Both Compose files are standalone and share runtime settings: development builds
`Dockerfile-SMAB`; the example pulls the selected GHCR version after publication.
`--env-file smab.env` also applies Compose interpolation settings such as data path,
UID/GID and image version. Preserve the `data_smab_state` volume when replacing a container.

For native diagnostics and offline tests, use Python 3.14+:

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install --requirement ressources/requirements.txt
(cd ressources && ../.venv/bin/python -m sma_mqtt_bridge --check-config)
./tests/test-check.sh
```

The Python CLI reads process environment variables, not `smab.env`. It never rewrites
private configuration. The pinned stable official image and its digest are in
[Dockerfile-SMAB](Dockerfile-SMAB); verify published stable tags before an update.

## Lint checks and CI

```sh
python3.14 -m venv .lint-venv
.lint-venv/bin/python -m pip install --requirement tests/requirements-lint.txt
.lint-venv/bin/python tests/install_lint_tools.py
./tests/linter-check.sh
python3 tests/compose_check.py
```

All public repository files receive hygiene checks and applicable language linters.
Ruff uses E4/E7/E9/F; Pylint checks errors/fatal diagnostics. Widget export parity is
included. Offline tests use deterministic fixtures and local test servers.
CI is prepared for Compose parity and amd64/arm64 image tests; local checks do not
prove that hosted CI, security scans or release jobs have run.

## Documentation and layout

| Location | Purpose |
| --- | --- |
| [Configuration](docs/CONFIGURATION.md), [ENV example](smab.example.env), [JSON example](config.example.json) | Supported settings, defaults, deployment and command contracts |
| [Profiles](docs/PROFILES.md), [register evidence](docs/REGISTER_VALIDATION.md) | Reusable model mappings and polling validation |
| [Architecture](docs/CONTEXT.md) | Scope and durable design decisions |
| [Validation](docs/VALIDATION.md) | Current acceptance status and evidence |
| [Plan](docs/IMPLEMENTATION_PLAN.md), [todo.md](todo.md) | Future milestones, active German tasks and diary |
| [Archive](docs/archive/README.md) | Preserved earlier working documents and diary entries |
| [Migration](docs/MIGRATION.md), [ledger](docs/migration-coverage.csv), [value catalogue](docs/WERTEKATALOG.md) | Existing openHAB capabilities, units and remaining continuity checks |
| [MainUI guide](openHAB/openHAB.md), [garage widget](openHAB/echarger-comfort.md) | Existing Item setup and widget installation |
| [Translations](translate/README.md) | English/German display labels and host overrides |
| `ressources/` | Image inputs only: Python package, bundled profiles and runtime requirements |
| `tests/`, `tools/` | Offline checks, lint/Compose tooling and widget exporter |

Private `smab.env`, installation data and original references stay outside Git and
Docker image inputs. Configuration, tests and documents stay outside `ressources/`.
Publication and releases require a separate milestone. No paid SMA Developer API or
replacement charging controller is used.

## License

MIT. See [LICENSE](LICENSE). This project is not affiliated with SMA.
