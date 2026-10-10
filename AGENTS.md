# SMA MQTT Bridge project instructions

Read `docs/CONTEXT.md`, `docs/IMPLEMENTATION_PLAN.md`, and `docs/MIGRATION.md` before implementation.
Also read `private/CONTEXT.local.md` and the working references in `private/reference/` when present.
The private directory is deliberately excluded from Git and Docker build contexts.

## User requirements

- Communicate with Andreas in German. Use English for source comments and public repository documentation.
- Build one Docker service providing Homie 4 MQTT for three SMA inverters, Sunny Home Manager 2.0 and SMA eCharger.
- Use the BMW-MQTT-Bridge foundation for C++17, Docker builds, CI, releases, linting and testing.
- Prefer local measurements and local eCharger settings. Use the existing ennexOS web-portal API only where needed, initially the minimum PV percentage.
- Do not introduce a paid SMA Developer API integration or replace Home Manager charging regulation with evcc unless Andreas changes the scope.
- Preserve all existing openHAB capabilities after the incoming inverter and Home Manager configurations have been inventoried. Do not silently drop channels, calculations, rules, persistence or units.
- Always consult official openHAB documentation. Use the openHAB community as supporting context.

## Implementation and validation

- This initial repository is a buildable scaffold, not a functioning SMA/MQTT runtime. Keep that distinction explicit until adapters are implemented and verified.
- The working openHAB JavaScript references are evidence and protocol examples. Port their behavior; they depend on the openHAB runtime and cannot run unchanged in the C++ service.
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
