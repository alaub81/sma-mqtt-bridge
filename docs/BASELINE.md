# BMW project baseline

Source: the user's local BMW-MQTT-Bridge checkout, commit `7f7e932e27b6c29b1a5ae89a869a9ceb422f9834`, inspected on 2026-10-10. The source checkout was clean and was not modified.

## Reused foundation

- C++17 with libmosquitto, libcurl and vendored nlohmann/json.
- Alpine 3.24 multi-stage build; alternative Debian trixie-slim build.
- Compose deployment template plus development override.
- CI lint jobs, Compose validation, image build/security scan and offline tests.
- Release-on-tag pipeline with amd64/arm64 GHCR images and manual rebuild support.
- Pinned tools: ShellCheck, Hadolint, yamllint, actionlint, Ruff, cppcheck and pymarkdown.
- Shared lint/test runners, tool installer, formatting configuration and Dependabot setup.
- MIT license and original attribution.

The BMW authentication flow, vehicle credentials, account identifiers, token files, deployment configuration, Git history and remote origin were not transferred. No timed container-release schedule was introduced. Source files copied unchanged are listed with checksums in `baseline-manifest.json`; other files were adapted for SMA.

Read-only BMW C++/Homie source references are available privately for future refactoring. They are not production SMA adapters.
