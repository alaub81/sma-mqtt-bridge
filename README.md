# SMA MQTT Bridge

A Python Docker service publishing SMA measurements and charging preferences through
Homie 4 MQTT, with optional guarded eCharger controls. Target: Raspberry Pi 5,
Linux arm64. Sunny Home Manager remains the charging controller.

Reads and allowlisted controls are implemented and offline tested. Selected installation
checks have passed; full production acceptance and openHAB migration remain pending.
See the [current acceptance matrix](docs/VALIDATION.md) for dated evidence and gaps.

## Install the published image

Preserve any existing root `smab.env`. On a fresh installation, copy
[smab.example.env](smab.example.env) to `smab.env` and configure only required settings.
Sources and command gates default to disabled. Additional JSON is optional.
See [configuration, TLS and state storage](docs/CONFIGURATION.md).

Published images are available at `ghcr.io/alaub81/sma-mqtt-bridge` for Linux
amd64 and arm64. Release v0.3.6 is reported deployed and healthy on the target
installation. For a reproducible deployment, set `SMAB_BRIDGE_VERSION=0.3.6` in
`smab.env`; image tags omit the Git tag's `v`. The default `latest` follows the
newest successfully published stable release. See [release and upgrade notes](docs/RELEASES.md).

```sh
docker compose --env-file smab.env -f docker-compose.example.yml pull
docker compose --env-file smab.env -f docker-compose.example.yml run --rm --no-deps sma-mqtt-bridge --check-config
docker compose --env-file smab.env -f docker-compose.example.yml up -d
```

Follow [the installation acceptance procedure](docs/MAC_TEST.md) for enabled
sources. Both Compose files are standalone and share runtime settings: development
builds `Dockerfile-SMAB`; the example pulls the published GHCR image.
`--env-file smab.env` applies Compose interpolation settings such as data path,
UID/GID and image version as well as preserving the documented service ENV file.
Keep the `data_smab_state` volume when replacing a container.

Optional plant calculations use explicit per-inverter roles and existing local
samples, with no additional device queries. PV/storage sums appear only for two
or more configured enabled contributors; household power and grid day counters
are separate calculated properties. See [plant setup and topics](docs/CONFIGURATION.md#plant-aggregates-and-energy-state)
and [the inventory and accounting contract](docs/PV_AGGREGATION_DESIGN.md).
The feature is disabled by default and not included in the published v0.3.11.

## Local development

```sh
./tools/build_image.sh
docker compose --env-file smab.env -f docker-compose.dev.yml run --rm sma-mqtt-bridge --check-config
```

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
python3.14 tests/compose_check.py
```

The lint check rejects Python tool versions that differ from the CI pins. After
changing `tests/requirements-lint.txt`, rerun the pip install command above.

All public repository files receive hygiene checks and applicable language linters.
Ruff uses E4/E7/E9/F/I plus the focused correctness rules listed in `ruff.toml`:
B006/B008 (shared defaults), B012 (exception suppression in finally), B018/B032
(discarded expressions or accidental annotations), B020/B023 (loop bindings),
B025 (duplicate handlers), RUF006 (unreferenced asyncio tasks), and RUF100 (stale
noqa suppressions). Broad style/modernization families remain opt-in. See the
[rule reference](https://docs.astral.sh/ruff/rules/), especially
[loop callbacks](https://docs.astral.sh/ruff/rules/function-uses-loop-variable/)
and [async task references](https://docs.astral.sh/ruff/rules/asyncio-dangling-task/).
Python formatting uses a 100-column target, double quotes and four-space
indentation. Pylint checks errors/fatal diagnostics. Widget
export parity is included. Offline tests use deterministic fixtures and local test servers.
CI runs on main-branch pushes and pull requests. Stable tag pushes invoke the
release workflow, which requires reusable CI before building/scanning and publishing
GHCR images. This includes Compose parity and amd64/arm64 image checks. Local test
success is separate from a hosted workflow result.

To apply only import ordering and formatting with the pinned local Ruff:

```sh
.lint-venv/bin/ruff check --select I --fix ressources tests tools
.lint-venv/bin/ruff format ressources tests tools
```

The linter-check command itself remains read-only.

## Documentation and layout

| Location | Purpose |
| --- | --- |
| [Configuration](docs/CONFIGURATION.md), [ENV example](smab.example.env), [JSON example](config.example.json) | Supported settings, defaults, deployment and command contracts |
| [Profiles](docs/PROFILES.md), [register evidence](docs/REGISTER_VALIDATION.md) | Reusable model mappings and polling validation |
| [Architecture](docs/CONTEXT.md) | Scope and durable design decisions |
| [Validation](docs/VALIDATION.md) | Current acceptance status and evidence |
| [Releases](docs/RELEASES.md) | Published/unreleased changes, image tags and upgrade checks |
| [Plan](docs/IMPLEMENTATION_PLAN.md), [todo.md](todo.md) | Future milestones, active German tasks and diary |
| [Archive](docs/archive/README.md) | Preserved earlier working documents and diary entries |
| [Migration](docs/MIGRATION.md), [ledger](docs/migration-coverage.csv), [value catalogue](docs/WERTEKATALOG.md) | Existing openHAB capabilities, units and remaining continuity checks |
| [MainUI guide](openHAB/openHAB.md), [garage widget](openHAB/echarger-comfort.md) | Existing Item setup and widget installation |
| [Translations](translate/README.md) | English/German display labels and host overrides |
| `ressources/` | Image inputs only: Python package, bundled profiles and runtime requirements |
| `tests/`, `tools/` | Offline checks, lint/Compose tooling and widget exporter |

Private `smab.env`, installation data and original references stay outside Git and
Docker image inputs. Configuration, tests and documents stay outside `ressources/`.
Publication of new commits/tags is explicit release work; local changes are not
automatically published. No paid SMA Developer API or replacement charging
controller is used.

## License

MIT. See [LICENSE](LICENSE). This project is not affiliated with SMA.

## Build versions

Local Python calls derive their version from Git: a clean stable tag reports its
release version; later commits or tracked edits report a dev version with commit
identity and an optional dirty suffix. Use `./tools/build_image.sh` for local image
builds to embed that version without sending Git or private files to Docker.
Plain Compose/Docker builds without `SMAB_BUILD_VERSION` report `0.0.0+unknown`.
Release builds receive the version from their stable tag and verify the CLI output
before publication. An embedded image version takes precedence over local Git.

The runtime image removes build-only `pip` and its `ensurepip` bootstrap copy after
installing and validating the pinned dependencies. Install dependency changes by
rebuilding the image; package installation inside a running container is unsupported.
