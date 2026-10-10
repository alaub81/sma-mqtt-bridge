# Validation evidence

## Python milestone on 2026-10-10

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
