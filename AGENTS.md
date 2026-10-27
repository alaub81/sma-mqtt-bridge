# SMA MQTT Bridge project instructions

Read `docs/README.md`, `docs/CONFIGURATION.md` and `docs/PROFILES.md` for the current
user-facing contract. Before implementation, read `private/CONTEXT.local.md`,
`private/project-documentation/README.md`, `private/project-documentation/todo.local.md`,
and the context, plan, migration and validation documents under
`private/project-documentation/working/` when present. Also consult the read-only
working references in `private/reference/` when relevant. Public `docs/` contains
only instructions for using the current bridge; do not recreate public project
memory, development diaries, migration worksheets or historical conversion guides.
The private directory is deliberately excluded from Git and Docker build contexts.

## User requirements

- Communicate with Andreas in German. Use English for source comments and public repository documentation, except `todo.md`, which is maintained in German.
- Build one Docker service providing Homie 4 MQTT for three SMA inverters, Sunny Home Manager 2.0 and SMA eCharger.
- Implement the bridge in Python. Reuse BMW-MQTT-Bridge operational lessons for connection supervision, TLS, Homie, health checks, Docker, CI, releases, linting and testing; the inherited C++ scaffold is historical preparation, not the target runtime.
- Track stable Python 3.15 patches with the official `python:3.15-slim-trixie` tag, without a patch-version or SHA digest pin, as requested by Andreas. Pull the current base during builds; keep the slim/Trixie variant. Verify published tags before changing the selected Python feature line or OS variant, exclude prereleases and document updates.
- Follow `docs/CONFIGURATION.md`: use `SMAB_` for every project environment variable, with documented typed defaults and environment overrides for all operational settings.
- Configure each inverter, Home Manager, eCharger and portal adapter independently: enabled flag, address where applicable, identity/profile, connection settings and intervals. Disabled adapters perform no device I/O. Do not infer device activation from an address or supplied credentials.
- Select reusable inverter model profiles by configured ID, with bundled defaults and host file overrides under the profile directory; see `docs/PROFILES.md`. New supported models must be addable through files without model-specific adapter code. Identity-only descriptors are not validated polling profiles; reject them for normal polling until their mappings are verified.
- Store the private `smab.env` in the repository root, next to the Compose files; document all supported variables in `smab.example.env`. Store optional JSON configuration, per-device profiles, certificates and password files under `./data/sma-mqtt-bridge/`, bind-mounted read-only to `/data/sma-mqtt-bridge/config`. Persist runtime state in the Compose volume `data_smab_state`, mounted at `/data/sma-mqtt-bridge/state`; preserve the topic manifest when changing storage. A minimal `smab.env` must suffice; additional JSON configuration is optional. Addresses, secrets and device identity have empty defaults and are required only for enabled adapters that need them.
- Keep both Compose files standalone with identical runtime settings. Development builds `Dockerfile-SMAB`; the example pulls the GHCR image. `tests/compose_check.py` verifies parity. `ressources/` contains only image inputs: the Python package, bundled profiles and runtime requirements. The Dockerfile copies its contents into `/app`. Compose, root ENV, configuration examples and lint settings remain outside `ressources/`.
- Validate configuration before connecting. Use precedence built-in/profile defaults < optional JSON configuration < explicit environment values; never persist resolved credentials or environment secrets into generated configuration.
- Maintain the active German diary in `private/project-documentation/todo.local.md`.
  Keep decisions, unresolved questions, plans, architecture context, validation evidence,
  migration records and historical diaries under `private/project-documentation/`.
  Preserve earlier entries in dated private snapshots and mark resolved questions explicitly.
  Public `docs/` is exclusively the current user guide; installation and development
  memory must not be placed there or in a public root diary.
- Prefer local measurements and local eCharger settings. Use the existing ennexOS web-portal API only where needed, initially the minimum PV percentage.
- Do not introduce a paid SMA Developer API integration or replace Home Manager charging regulation with evcc unless Andreas changes the scope.
- Preserve all existing openHAB capabilities after the incoming inverter and Home Manager configurations have been inventoried. Do not silently drop channels, calculations, rules, persistence or units.
- Always consult official openHAB documentation. Use the openHAB community as supporting context.

## Implementation and validation

- The Python read runtime is offline tested. Do not claim live SMA/MQTT acceptance or complete openHAB migration until verified. Bundled identity-only profiles remain blocked for polling.
- The working openHAB JavaScript references are evidence and protocol examples. Port their behavior; they depend on the openHAB runtime and cannot run unchanged in the Python service.
- SMA private references and original openHAB exports are read-only. Update public documentation and migration mappings, not those originals. The obsolete private BMW source copies were removed with user approval on 2026-10-10; do not restore them.
- Only expose confirmed writable parameters through Homie `/set`. Read-only measurements remain non-settable. Do not expose every editable installer parameter automatically.
- Validate parameter metadata, device identity, command bounds and units. Read back changes before publishing a confirmed state. An HTTP success is not proof of a completed device action.
- Avoid retained-command replay, writes on startup/reconnection, duplicate write retries after uncertain responses, and competing charging controllers.
- Keep credentials/tokens out of source, images, test fixtures and logs. Do not print raw authenticated requests/responses or copy captured Bearer headers from chat history.
- TLS verification defaults to enabled. Andreas explicitly requested configurable unverified TLS for the local wallbox and MQTT; permit only their explicit `SMAB_ECHARGER_TLS_VERIFY=false` / `SMAB_MQTT_TLS_VERIFY=false` overrides. Portal verification remains mandatory. Do not globally disable certificate checks or automatically trust a downloaded certificate.
- Local API sessions and portal sessions are separate. Do not assume one uniform SMA API or that the Home Manager serves all configuration via Modbus.
- Run `./tests/linter-check.sh` and `./tests/test-check.sh` for relevant changes. Use deterministic protocol fixtures for automated tests; live writes require an explicit user-requested action.
- The BMW bridge served as an initial structural reference. At Andreas' request, obsolete BMW sources, attribution documentation, baseline/import manifest and scaffold validation archive were removed. Do not restore these historical files; the root MIT license names the SMA project author.
- GitHub publication and container release are later milestones. The current task authorizes local preparation, not creating a remote repository or pushing secrets/private data.

## Widget source ownership

- Maintain installable widget definitions only in `openHAB/yaml/widgets/`. Treat installed openHAB widgets as deployment copies; compare live definitions before updates to preserve changes.
- Do not recreate parallel editable widget sources in ChatGPT project folders. Generate required manual imports from canonical repository files. Preserve private historical backups as evidence only.
