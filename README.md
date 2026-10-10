# SMA MQTT Bridge

A project foundation for a Docker service that publishes SMA system measurements and confirmed writable charging settings using Homie 4 MQTT for openHAB.

**Status: bootstrap only.** Docker images and development checks are prepared. Inverter, Home Manager, wallbox, portal and MQTT runtime adapters are not implemented yet. Starting the executable without a diagnostic command deliberately fails instead of pretending to run a bridge.

## Intended integration

- Three SMA inverters: existing local Modbus configurations will define the required measurements.
- Sunny Home Manager 2.0: local meter telegrams, with the exact existing openHAB configuration still to be supplied.
- SMA eCharger EVC22-3AC-20: local API and SEMP measurements/settings.
- Sunny Portal powered by ennexOS: existing normal-account web API for minimum PV percentage.
- Homie 4: one consistent MQTT interface for openHAB.

No paid SMA Developer API subscription is planned. Home Manager remains responsible for charging regulation.

## Start here

1. Read [the collected findings](docs/CONTEXT.md).
2. Read [the implementation plan](docs/IMPLEMENTATION_PLAN.md).
3. Add existing openHAB exports to `private/incoming/openhab/` as described in [the migration checklist](docs/MIGRATION.md).
4. Use [the prepared Codex start prompt](docs/CODEX_START.md) in the new local project.

The private handoff contains original working references and installation-specific metadata. It is excluded from Git and the Docker image. Public files contain placeholders instead of actual credentials and plant identifiers.

## Docker foundation

The foundation follows BMW-MQTT-Bridge: C++17, libcurl, libmosquitto, nlohmann/json, Alpine multi-stage builds, an alternative Debian build, Compose and amd64/arm64 releases. See [baseline provenance](docs/BASELINE.md).

Build and run bootstrap diagnostics:

```bash
docker compose -f docker-compose.dev.yml build
docker compose -f docker-compose.dev.yml run --rm sma-mqtt-bridge --version
docker compose -f docker-compose.dev.yml run --rm sma-mqtt-bridge --project-status
```

`docker-compose.example.yml` prepares the future deployment image name. That GHCR image has not been published yet. The `.env.sample` and `config.example.json` describe planned configuration; the bootstrap executable does not consume them.

## Lint checks

```bash
python3 -m venv .lint-venv
.lint-venv/bin/python -m pip install --requirement tests/requirements-lint.txt
.lint-venv/bin/python tests/install_lint_tools.py
./tests/linter-check.sh
```

The inherited runner checks text, JSON, dotenv examples, shell scripts, Dockerfiles, YAML, GitHub Actions, Python, C++ and Markdown. CLI tools are pinned in `lint-tools.json` and Python tools in `tests/requirements-lint.txt`. The vendored JSON header keeps upstream formatting and license text.

## Tests and CI

```bash
./tests/test-check.sh
```

Tests compile the CLI and render both Compose templates without connecting to SMA devices or MQTT. Docker Compose and a C++17 compiler are required. CI prepares linting, Compose validation, image build/security scan and offline tests. The inherited release pipeline builds amd64/arm64 images when a release tag is pushed. GitHub publication remains a later step.

See [local validation evidence and remaining checks](docs/VALIDATION.md).

## License

MIT; inherited BMW project attribution is preserved in [LICENSE](LICENSE). The vendored nlohmann/json header retains its own MIT notice. This project is not affiliated with SMA.
