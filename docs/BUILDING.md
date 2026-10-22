# Building and checking the bridge

Use the [published-image quick start](../README.md#quick-start) for normal
installation. The commands below are for building a custom image, running native
diagnostics and checking source changes. Run them from the repository root.

## Build a local image

```sh
./tools/build_image.sh
docker compose --env-file smab.env -f compose.dev.yml run --rm sma-mqtt-bridge --check-config
```

Both Compose variants are standalone and share runtime settings.
[compose.dev.yml](../compose.dev.yml) builds [Dockerfile-SMAB](../Dockerfile-SMAB);
[compose.example.yml](../compose.example.yml) pulls the GHCR image. The normal
network uses `app-nw` for Modbus, local HTTP and portal traffic. Linux Home Manager
UDP multicast has a separate [network variant](CONFIGURATION.md#compose-network-variants).

Compose reads `smab.env` as the service environment file and `.env` for
interpolation. Explicit `--env-file smab.env` invocations remain supported.
See [configuration](CONFIGURATION.md#compose-usage) for the distinction.

## Native Python and offline tests

Use Python 3.15 to match the current image and CI. Python 3.14 remains compatible
with the runtime tests. The separately copied Linux resource recorder supports
Python 3.9+.

```sh
python3.15 -m venv .venv
.venv/bin/python -m pip install --requirement ressources/requirements.txt
(cd ressources && ../.venv/bin/python -m sma_mqtt_bridge --check-config)
./tests/test-check.sh
```

The Python CLI reads process environment variables, not `smab.env`. Supply needed
settings through the process environment for native checks; it does not rewrite
private configuration. Offline tests use deterministic fixtures and local test
servers without SMA-device or external-broker access. Local server tests require
permission to bind loopback sockets in restricted environments.

## Lint checks

```sh
./tests/linter-check.sh
python3.15 tests/compose_check.py
```

The script creates `.lint-venv` when missing (preferring `python3.15`, then
`python3.14`, then `python3`, requiring Python 3.14+), installs Python tools
when their versions differ from the CI pins, and prepares the pinned native
linters in `.lint-tools`. Existing matching tools are reused. Initial setup and
dependency updates require internet access. On macOS, install the pinned Hadolint
on PATH first (the installer reports the required version); no macOS release
binary is provided upstream. Use Python 3.15 to match CI. Creating
the Python 3.15 lint environment needs a C++ compiler to build the pinned
`pyjson5` helper. The application runtime image needs no compiler.

All public repository files receive text hygiene and applicable language checks.
Ruff uses E4/E7/E9/F/I and the correctness rules in [ruff.toml](../ruff.toml):
B006/B008 (shared defaults), B012 (exception suppression in finally), B018/B032
(discarded expressions or accidental annotations), B020/B023 (loop bindings),
B025 (duplicate handlers), RUF006 (unreferenced asyncio tasks), and RUF100 (stale
noqa suppressions). Broad style/modernization families remain opt-in. See the
[rule reference](https://docs.astral.sh/ruff/rules/), especially
[loop callbacks](https://docs.astral.sh/ruff/rules/function-uses-loop-variable/)
and [async task references](https://docs.astral.sh/ruff/rules/asyncio-dangling-task/).

Python formatting uses a 100-column target, double quotes and four-space
indentation. Pylint checks errors/fatal diagnostics. Widget export parity and
local Markdown file links are checked. Links into private records are rejected;
heading anchors and external URLs are outside the automated link check.

To apply only import ordering and formatting with the pinned Ruff:

```sh
.lint-venv/bin/ruff check --select I --fix ressources tests tools
.lint-venv/bin/ruff format ressources tests tools
```

The command prepares local tool directories but never fixes source files.

## Generated files

```sh
.venv/bin/python tools/export_topic_catalog.py --check
.venv/bin/python tools/export_openhab_widget.py --check
```

Omit `--check` to regenerate the topic catalog or manual widget import after a
source change. Edit the canonical eCharger widget under
`openHAB/yaml/widgets/echarger-comfort.yml`; see the
[widget guide](../openHAB/README.md) for the generated alternative.

## CI and image publication

[CI](../.github/workflows/ci.yml) runs on main-branch pushes and pull requests.
Stable tag pushes invoke the [release workflow](../.github/workflows/release.yml),
which requires reusable CI before building, scanning and publishing GHCR images.
Checks include Compose parity and amd64/arm64 images. Local test success does not
establish a successful hosted workflow or image publication.

The official Python image tag and multi-platform digest are pinned in
[Dockerfile-SMAB](../Dockerfile-SMAB). Verify published stable tags before changing
the base; exclude prereleases. Publishing new commits/tags is explicit release
work. Local builds and checks do not publish or deploy automatically.

## Build versions and dependencies

Local Python calls derive their version from Git. A clean stable tag reports its
release version; later commits or tracked edits report a dev version with commit
identity and an optional dirty suffix. `tools/build_image.sh` embeds that version
without sending Git or private files to Docker. Plain Compose/Docker builds without
`SMAB_BUILD_VERSION` report `0.0.0+unknown`. Release builds receive the version from
the stable tag and verify the CLI output before publication. An embedded image
version takes precedence over local Git.

The runtime image removes build-only `pip` and its `ensurepip` bootstrap copy after
installing and validating pinned dependencies. Change dependencies by rebuilding
the image; package installation inside a running container is unsupported.

## Repository layout

| Location | Contents |
| --- | --- |
| `ressources/sma_mqtt_bridge/` | Python runtime package |
| `ressources/profiles/` | Bundled model profiles |
| `ressources/translate/` | Bundled English/German discovery labels |
| `ressources/requirements.txt` | Pinned runtime dependencies |
| `docs/` | Current setup, configuration, operation and extension guides |
| `openHAB/` | MainUI widget sources, generated import and setup guides |
| `translate/` | Host translation template |
| `tests/`, `tools/` | Offline checks, lint/Compose tooling and exporters |

Only `ressources/` is sent as Docker image input and copied into `/app`.
Compose files, examples, configuration, tests and documentation remain outside it.
Root `smab.env`, `data/` and private records stay outside Git and Docker inputs.
