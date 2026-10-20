# SMA MQTT Bridge

A Python Docker service publishing SMA measurements and charging preferences through
Homie 4 MQTT, with optional guarded eCharger controls. Target: Raspberry Pi 5,
Linux arm64. Sunny Home Manager remains the charging controller.

Use the [user guide](docs/README.md) for setup, MQTT properties, operation and updates.

## Install the published image

Preserve any existing root `smab.env`. On a fresh installation, copy
[smab.example.env](smab.example.env) to `smab.env` and configure only required settings.
Sources and command gates default to disabled. Additional JSON is optional.
Copy [.env.example](.env.example) to `.env` only if you need Compose overrides
(image version, paths or container UID/GID).
See [configuration, TLS and state storage](docs/CONFIGURATION.md).
A compact commented installation example is available in the [Wiki quick start](docs/WIKI_QUICKSTART.md).

Published images are available at `ghcr.io/alaub81/sma-mqtt-bridge` for Linux
amd64 and arm64. For a reproducible deployment, pin `SMAB_BRIDGE_VERSION` in `.env`
to a verified published release compatible with your configuration and persisted
state; image tags omit the Git tag's `v`. The default `latest` follows the newest
successfully published stable release. Repository changes can precede publication;
check [update instructions](docs/UPDATING.md) before upgrading or downgrading.

```sh
docker compose -f compose.example.yml pull
docker compose -f compose.example.yml run --rm --no-deps sma-mqtt-bridge --check-config
docker compose -f compose.example.yml up -d
```

Follow [the operating guide](docs/OPERATIONS.md) for enabled
sources. Both Compose files are standalone and share runtime settings: development
builds `Dockerfile-SMAB`; the example pulls the published GHCR image.
Compose automatically reads `.env` for interpolation and passes `smab.env` to the
service. Existing explicit `--env-file smab.env` invocations remain supported.
The default uses one `app-nw` bridge network for Modbus, local HTTP and portal access.
For Linux Home Manager UDP multicast, see the [network variants](docs/CONFIGURATION.md#compose-network-variants).
Keep the `data_smab_state` volume when replacing a container.

Optional plant calculations use explicit per-inverter roles and existing local
samples, with no additional device queries. PV/storage sums appear only for two
or more configured enabled contributors; household power and grid day counters
are separate calculated properties. See [plant setup and topics](docs/CONFIGURATION.md#plant-aggregates-and-energy-state)
and [plant calculations and coverage](docs/PLANT.md).
The feature is disabled by default. Preserve its energy ledger during upgrades;
older releases may not understand the current fine-counter state schema.

## Local development

```sh
./tools/build_image.sh
docker compose --env-file smab.env -f compose.dev.yml run --rm sma-mqtt-bridge --check-config
```

For native diagnostics and offline tests, use Python 3.15 to match the image and CI.
Python 3.14 remains compatible with the runtime tests; the standalone Linux host
resource recorder supports Python 3.9+.

```sh
python3.15 -m venv .venv
.venv/bin/python -m pip install --requirement ressources/requirements.txt
(cd ressources && ../.venv/bin/python -m sma_mqtt_bridge --check-config)
./tests/test-check.sh
```

The Python CLI reads process environment variables, not `smab.env`. It never rewrites
private configuration. The pinned stable official image and its digest are in
[Dockerfile-SMAB](Dockerfile-SMAB); verify published stable tags before an update.

## Lint checks and CI

```sh
python3.15 -m venv .lint-venv
.lint-venv/bin/python -m pip install --requirement tests/requirements-lint.txt
.lint-venv/bin/python tests/install_lint_tools.py
./tests/linter-check.sh
python3.15 tests/compose_check.py
```

The lint check rejects Python tool versions that differ from the CI pins. After
changing `tests/requirements-lint.txt`, rerun the pip install command above.
Creating the Python 3.15 lint environment currently needs a C++ compiler to build
the pinned `pyjson5` helper. The application runtime image needs no compiler.

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
export parity and local Markdown file links, including archives, are checked.
The link check covers inline links/images and reference definitions; heading anchors
and external URLs are outside its scope. Offline tests use deterministic fixtures
and local test servers.
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
| [Configuration](docs/CONFIGURATION.md), [ENV example](smab.example.env), [JSON example](docs/config.example.json) | Supported settings, defaults, deployment and command contracts |
| [Profiles](docs/PROFILES.md) | Supported models and host profile selection |
| [Operation](docs/OPERATIONS.md), [updates](docs/UPDATING.md) | Health, recovery, backups and image replacement |
| [Plant](docs/PLANT.md), [value catalog](docs/WERTEKATALOG.md) | Calculations, coverage, MQTT properties and units |
| [openHAB directory](openHAB/README.md), [MainUI guide](openHAB/openHAB.md), [garage widget](openHAB/echarger-comfort.md) | Existing Item setup and widget installation |
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
