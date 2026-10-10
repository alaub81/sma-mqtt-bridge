# Foundation validation

Performed locally on 2026-10-10. This evidence covers project preparation and the diagnostic scaffold. It does not establish that SMA adapters or Homie publishing exist.

## Passed checks

- All lint categories: text/file coverage, JSON, dotenv examples, ShellCheck, Hadolint, YAML, GitHub Actions, Ruff, cppcheck and Markdown.
- Five offline foundation tests: compiled CLI version/status, explicit failure for the unimplemented runtime, rejection of unsupported commands and both Compose templates rendered without personal configuration.
- Alpine 3.24 and Debian trixie-slim Docker images built successfully for `linux/arm64`.
- Both images ran diagnostic commands with Docker networking disabled. Alpine version, status, explicit runtime exit code 78 and absence of private/config files were checked. Debian project-status was checked.
- The copied portal reference's 42 simulated protocol/rule tests passed. These test the previous openHAB script, not a new C++ portal adapter or live Java/GraalJS behavior.
- All 15 unchanged BMW foundation files match the checksums recorded in `baseline-manifest.json`.
- The public parameter catalog contains 85 metadata entries. The initial migration ledger contains 45 non-group Items from the existing wallbox/portal packages.
- Installation-specific IP/plant/device identifiers and captured authentication-header markers were absent from the public file set. Private references and incoming exports are ignored by Git and excluded from Docker.

## Local commands and tool environment

`./tests/test-check.sh` passed in the new project. The first complete lint run used the already installed pinned BMW lint tools through a temporary PATH, with `RUFF_NO_CACHE=true` and `PYTHONDONTWRITEBYTECODE=1` because this preparation task had restricted write access outside its original workspace. The SMA repository does not contain permanent links to that environment. Follow the README lint setup instructions to install independent local tools.

The two local image tags are `sma-mqtt-bridge:bootstrap-check` and `sma-mqtt-bridge:bootstrap-debian-check`. These are development diagnostics, not published release images.

## Remaining validation

GitHub-hosted CI, Trivy scanning, release publishing and `linux/amd64` builds have not been run. Live SMA/MQTT integration has not been tested because the runtime adapters are not implemented. Inverter/Home Manager exports, deployment networking and a complete capability comparison remain necessary before migration.
