# SMA MQTT Bridge project instructions

Read `docs/CONTEXT.md`, `docs/IMPLEMENTATION_PLAN.md`, and `docs/MIGRATION.md` before implementation.
Also read `private/CONTEXT.local.md` and the working references in `private/reference/` when present.
The private directory is deliberately excluded from Git and Docker build contexts.

## User requirements

- Communicate with Andreas in German. Use English for source comments and public repository documentation, except `todo.md`, which is maintained in German.
- Build one Docker service providing Homie 4 MQTT for three SMA inverters, Sunny Home Manager 2.0 and SMA eCharger.
- Implement the bridge in Python. Reuse BMW-MQTT-Bridge operational lessons for connection supervision, TLS, Homie, health checks, Docker, CI, releases, linting and testing; the inherited C++ scaffold is historical preparation, not the target runtime.
- Use the newest available stable official Python Docker image. Verify published tags before choosing a version; exclude prereleases and document updates.
- Follow `docs/CONFIGURATION.md`: use `SMAB_` for every project environment variable, with documented typed defaults and environment overrides for all operational settings.
- Configure each inverter, Home Manager, eCharger and portal adapter independently: enabled flag, address where applicable, identity/profile, connection settings and intervals. Disabled adapters perform no device I/O. Do not infer device activation from an address or supplied credentials.
- Select reusable inverter model profiles by configured ID, with bundled defaults and host file overrides under the profile directory; see `docs/PROFILES.md`. New supported models must be addable through files without model-specific adapter code. Identity-only descriptors are not validated polling profiles; reject them for normal polling until their mappings are verified.
- Store the private `.env` in the repository root, next to the Compose files; document all supported variables in `.env.example`. Store optional JSON configuration, per-device profiles, certificates, password files and persistent state under `./data/sma-mqtt-bridge/`, bind-mounted to `/data/sma-mqtt-bridge`. A minimal `.env` must suffice; additional JSON configuration is optional. Addresses, secrets and device identity have empty defaults and are required only for enabled adapters that need them.
- Keep both Compose files standalone with identical runtime settings. Development builds `Dockerfile-SMAB`; the example pulls the GHCR image. `tests/compose_check.py` verifies parity. `ressources/` contains only image inputs: the Python package, bundled profiles and runtime requirements. The Dockerfile copies its contents into `/app`. Compose, root ENV, configuration examples and lint settings remain outside `ressources/`.
- Validate configuration before connecting. Use precedence built-in/profile defaults < optional JSON configuration < explicit environment values; never persist resolved credentials or environment secrets into generated configuration.
- Maintain `todo.md` as the project diary: record decisions, inventory findings, all unresolved questions, pending tasks and validation results. Preserve earlier entries and mark resolved questions explicitly. Keep diary entries in German and omit private identifiers and secrets.
- Prefer local measurements and local eCharger settings. Use the existing ennexOS web-portal API only where needed, initially the minimum PV percentage.
- Do not introduce a paid SMA Developer API integration or replace Home Manager charging regulation with evcc unless Andreas changes the scope.
- Preserve all existing openHAB capabilities after the incoming inverter and Home Manager configurations have been inventoried. Do not silently drop channels, calculations, rules, persistence or units.
- Always consult official openHAB documentation. Use the openHAB community as supporting context.

## Implementation and validation

- The Python read runtime is offline tested. Do not claim live SMA/MQTT acceptance or complete openHAB migration until verified. Bundled identity-only profiles remain blocked for polling.
- The working openHAB JavaScript references are evidence and protocol examples. Port their behavior; they depend on the openHAB runtime and cannot run unchanged in the Python service.
- Private references are read-only. Update public documentation and migration mappings, not original openHAB exports.
- Only expose confirmed writable parameters through Homie `/set`. Read-only measurements remain non-settable. Do not expose every editable installer parameter automatically.
- Validate parameter metadata, device identity, command bounds and units. Read back changes before publishing a confirmed state. An HTTP success is not proof of a completed device action.
- Avoid retained-command replay, writes on startup/reconnection, duplicate write retries after uncertain responses, and competing charging controllers.
- Keep credentials/tokens out of source, images, test fixtures and logs. Do not print raw authenticated requests/responses or copy captured Bearer headers from chat history.
- Keep TLS verification for the portal and MQTT. Configure trust for the wallbox's local certificate explicitly; do not globally disable certificate checks.
- Local API sessions and portal sessions are separate. Do not assume one uniform SMA API or that the Home Manager serves all configuration via Modbus.
- Run `./tests/linter-check.sh` and `./tests/test-check.sh` for relevant changes. Use deterministic protocol fixtures for automated tests; live writes require an explicit user-requested action.
- Keep MIT attribution for inherited BMW code and nlohmann/json. Preserve `docs/BASELINE.md` provenance.
- GitHub publication and container release are later milestones. The current task authorizes local preparation, not creating a remote repository or pushing secrets/private data.
