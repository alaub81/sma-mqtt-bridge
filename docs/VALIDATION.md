# Validation evidence

## Initial Python milestone on 2026-10-10

The first read-only Python runtime is implemented. Bundled inverter profiles remain identity-only; hardware acceptance is pending. Historical evidence is preserved in [the scaffold archive](archive/scaffold-validation.md).

Current checks: Python configuration/profile/protocol/runtime regressions, real MQTT library against a deterministic loopback broker, full repository lint, arm64 container build/tests and public Compose rendering. All 65 tests passed locally and in the arm64 container with external networking disabled. Both arm64 and amd64 images built, and the amd64 configuration smoke passed. Both public Compose renders and all lint categories across 71 files passed. Detailed results are recorded in todo.md. Offline transport tests use a temporary loopback endpoint with synthetic values, never installation credentials or a private broker.

Not certified: actual SMA reads, MQTT TLS against the installation broker, Pi multicast/VLAN/encryption, local parameter units, device firmware/register compatibility and openHAB migration continuity. No writes or publication occurred. GitHub CI and Trivy remain unexecuted locally.

The Python workflow has no C++ compiler, cppcheck, vendor header or historical diagnostic runtime. BMW/MIT attribution and the original baseline manifest are retained as historical provenance, not checksums of the current tree.

## Cleanup checkpoint on 2026-10-10

Both Compose files are standalone, with identical runtime options and explicit local-build/GHCR-image selection. `tests/compose_check.py` passed default and UID/GID/data-path/version override checks against public ENV only. The Dockerfile is `Dockerfile-SMAB`; the optional JSON example and Docker lint config live under `ressources/`.

All 65 offline tests passed locally and in the final Linux arm64 and amd64 images with external networking disabled. The standalone development Compose build and explicit amd64 build passed. The complete lint run covers 68 public files, with no compiler/vendor checks. The first lint run caught Markdown spacing/heading issues in the new archive; these were corrected and the final full run passed. `git diff --check` passed.

All 100 original Item/channel/topic mappings are preserved. SHA-256 comparisons confirmed 158 protected files unchanged, including private references, root ENV, host data, LICENSE and original baseline records. This checkpoint is local only: no actual SMA/broker access, hosted CI/security scan, device writes, push or release.

## Corrected image-input layout on 2026-10-10

`ressources/` now contains image inputs only: Python runtime, bundled profile JSONs and runtime requirements. Configuration example and Hadolint settings are back at the root; profile documentation lives in `docs/PROFILES.md`. All 19 moved runtime/profile/dependency files are byte-for-byte identical; no adapter behavior changed.

The complete lint run, 65 local tests, the same 65 tests in arm64 and amd64 containers, both image builds, Compose parity, local CLI and Compose configuration diagnostics passed. Image inspection confirmed that `/app` contains only the package, profiles and requirements, with no examples, tooling, private files or local bytecode caches. All 158 protected files remain unchanged. No device connections or publication occurred.

## Read runtime and ENV naming checkpoint on 2026-10-10

Subsequent implementation supersedes the initial identity-only and no-live-read status above. All three bundled profiles now contain verified mappings for the 41 existing inverter channels, with model/firmware/serial guards and documented units. Read-only device/broker verification published 69 values across three inverters and the eCharger SEMP source. Two Sunny Boy phase registers returned SMA unavailable markers and were omitted, not replaced with zero. This does not certify complete openHAB migration or every catalogue entry.

The private root ENV file is now `smab.env`; the public reference is `smab.example.env`. Both Compose files explicitly load the former via service `env_file`. Compose-only interpolation uses `--env-file smab.env`, shell variables or an optional separate `.env`. The private service-file path was adjusted without changing other assignments or mode 0600. Git excludes private ENV and data; only image inputs enter the Docker build context. All 154 private original reference files retain their recorded SHA-256 hashes.

All 75 offline tests passed locally and in the rebuilt Linux arm64 and amd64 images with external networking disabled. The full lint check covers 73 public files; standalone Compose parity and override checks passed. Development Compose rebuilt and started with the renamed file; in-container configuration validation reports four enabled read-only sources, and heartbeat confirms MQTT connectivity and ready inverter/SEMP sources.

Home Manager remains disabled on the Mac because it is outside the meter network; Pi multicast/serial selection remains pending. Local eCharger API and portal credentials are still pending, so those sources remain disabled. Wallbox certificate/name validation passed with configured trust. MQTT verification is explicitly disabled by the user for this installation while TLS encryption remains enabled; defaults continue to verify and portal verification remains mandatory. Device writes, hosted CI/security scans, push and container release remain outside this checkpoint.

## Named state volume checkpoint on 2026-10-10

Both standalone Compose files now use `data_smab_state` at `/data/sma-mqtt-bridge/state`; configuration/profile/certificate files retain their host bind mount. A deterministic Docker check confirmed atomic writes with mode 0600 as UID 10001 on a fresh volume and persistence across container replacement. The temporary fixture volume was removed afterward.

The two existing host state files were imported byte-for-byte into the project-scoped volume while the bridge was stopped, with matching container ownership. Former host files remain as inactive backups. Container inspection confirms the named state mount, Docker health is healthy, and all three inverter sources plus SEMP and their MQTT connections are ready. Existing private ENV, device settings and original references were not changed. Full local offline tests, repository lint, image build and public Compose parity passed.

## Authenticated API and portal read checkpoint on 2026-10-10

Local eCharger authentication, configured model/serial identity and verified TLS passed. Fresh phase currents, voltages and total energy were read. Live entries use `time`; both `time` and the previously supported `timestamp` are accepted with the same timezone/freshness checks, while conflicting fields are rejected. Local parameter metadata contains no unit for plan energy or stop delay, so engineering-unit properties remain unavailable. Frequency, session energy and health were unavailable in the isolated API read; no replacement channel was guessed.

The portal's single credential POST form currently lacks an ID. The parser supports this observed shape while retaining trusted-origin/path, interactive-challenge and PKCE/state checks. Device identity and optional-demand fields passed; minimum PV was 70%, allowed grid preference 30%, and edit permission was present. No device setting was changed.

Both sources were explicitly enabled in private ENV. The service was recreated with an explicitly requested `--refresh-portal` for this start; polling remains zero. Selected API and portal values were verified retained on the installation broker. Heartbeat reported all six sources ready and all four MQTT devices connected. A one-shot portal observation expires after the configured 180 seconds; this is not continuous portal telemetry. The current container retains the explicit refresh argument on Docker restart; regular Compose Up without the temporary override restores the default command.

All 76 local offline tests and full repository lint passed; the loopback MQTT test needed execution outside the socket-restricted sandbox. The development image was built and live read adapters verified. Full openHAB continuity, unresolved local units, Pi acceptance and commands remain pending.

## Direct local unit and channel verification on 2026-10-10

The eCharger firmware 2.6.37.R serves WebUI 1.46.0 under `/webui/`. Its main bundle registers the metadata loader from module 63194 (chunk 3194, hash `4c0f0d12e9cf8ed1`). That local SMA metadata assigns `Parameter.Chrg.Plan.En` unit tag 8, scalar type and precision 1; `Parameter.Chrg.StpWhenFlTm` unit tag 34, scalar type and precision 0. The German metadata translation module 63462 (chunk 3462, hash `63198e778e99e887`) resolves tags 8 to kWh and 34 to min. The main bundle's scalar formatter passes `Number(value)` with the resolved input unit to the formatter, without a raw scaling multiplier. The generic Duration formatter has a separate seconds-oriented rendering path, so that path alone is not used as the unit evidence.

Read-only local parameter inspection reported confirmed target energy 0 and stop delay 15, with delay bounds 5–1440. Engineering units are therefore verified from the local device's own metadata, not inferred from portal labels. The runtime fallback is restricted to the verified EVC22-3AC-20 model and 2.6.37.R firmware; contradictory explicit units and unknown firmware remain unavailable. No nonzero target energy was written or live-tested. Deterministic tests verify unscaled decimal handling and model/firmware/unit guards.

The local measurement inventory contains session energy and both device/vehicle health channels. Session energy was 8047.875 Wh (8.047875 kWh), with a source timestamp predating the current freshness window; device health was code 307 with a September timestamp. These channels are present and are suppressed as stale, rather than missing. The API appears to retain some values with change timestamps; full timestamp semantics remain unverified and freshness policy is unchanged. Neither frequency channel is present in the current live inventory, although generic WebUI metadata defines frequency channels. Static metadata is not evidence that the device exposes them.

All 77 offline tests and full repository lint passed. The local unit fallback was deployed; actual retained MQTT publication confirmed plan energy 0 with kWh and stop delay 15 with min. Regular Compose Up restored the default command without an automatic portal refresh. No device writes were executed.
