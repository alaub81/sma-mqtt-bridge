# First installation test on macOS

The first installation test runs on the Mac. The service has offline-tested read adapters; installation acceptance and device commands are still pending. Keep the current openHAB integration running for value comparison. Do not remove links, rules or persistence.

## Prepare private configuration

Preserve the existing root `.env` and its MQTT settings. Add only missing installation values. Store local API credentials separately from portal credentials and use a password file when preferred. Never paste credentials into chat or protocol fixtures.

For eCharger HTTPS reads, configure `SMAB_ECHARGER_HOST`, `SMAB_ECHARGER_USERNAME`, `SMAB_ECHARGER_PASSWORD` or `SMAB_ECHARGER_PASSWORD_FILE`, and `SMAB_ECHARGER_EXPECTED_SERIAL`. Copy the trusted local certificate into `data/sma-mqtt-bridge/certificates/` and set `SMAB_ECHARGER_TLS_CA_FILE` to its container path under `/data/sma-mqtt-bridge/certificates/`. The certificate must also match the configured hostname/IP; trusting a certificate does not bypass hostname validation. Only enable `SMAB_ECHARGER_ENABLED=true` after these values are ready. Leave other source flags false for this first test.

SEMP is independent and additionally requires its known device ID through `SMAB_ECHARGER_SEMP_DEVICE_ID`; use `SMAB_ECHARGER_SEMP_ENABLED` only when testing that reader. Home Manager requires `SMAB_HOME_MANAGER_SERIAL` and suitable UDP delivery. Inverter host addresses already exist in the private Things exports, but bundled identity-only profiles remain blocked until mappings are verified. No additional profiles are currently available from the user.

Keep all command flags false. Local credentials alone never activate a source or enable a write.

## Earliest read test: SEMP only

The independently enabled SEMP reader uses local HTTP and needs no charger API login or HTTPS trust. With the private charger host, captured device ID and expected serial already prepared, set only `SMAB_ECHARGER_SEMP_ENABLED=true`; keep `SMAB_ECHARGER_ENABLED` and all other sources false. This tests the existing charger power, session energy and status properties through Homie. It does not test authenticated settings, additional API measurements or device commands.

The MQTT connection still requires its own configuration and TLS trust. A populated `SMAB_MQTT_TLS_CA_FILE` is usable only if that file exists inside the container. Put the broker CA under `data/sma-mqtt-bridge/certificates/` and configure the corresponding `/data/sma-mqtt-bridge/certificates/` path, or use system trust when appropriate for the actual broker certificate. Preserve verification; do not substitute the charger certificate for the broker CA. The current private SEMP-only configuration passes validation in the actual container, including MQTT trust loading. No broker CA/path change is required for that offline check. A native Mac check cannot establish whether a container path exists; live broker TLS/authentication and topic permissions remain to be tested.

## Validate and start

The Compose service uses host networking. On Docker Desktop 4.34 or later, enable **Settings > Resources > Network > Enable host networking**, then restart Desktop. Docker documents TCP/UDP support but no direct access to native host interfaces; independently verify LAN multicast reception. See [Docker host networking](https://docs.docker.com/engine/network/drivers/host/).

Once configuration is ready, run from the repository root:

```sh
docker compose -f docker-compose.dev.yml run --rm --build sma-mqtt-bridge --check-config
docker compose -f docker-compose.dev.yml up --build -d
docker compose -f docker-compose.dev.yml logs --tail=100 -f
```

The first command validates configuration without device or broker I/O. The second starts live read/publish activity for explicitly enabled sources. With all sources disabled, configuration validation succeeds but the runtime exits with an actionable message. A running container alone does not establish adapter acceptance.

Inspect `homie/sma-echarger/` on the configured broker. Verify discovery, source diagnostics, fresh settings and measurement values against the local SMA interface/openHAB. Missing, invalid and stale values must disappear instead of becoming zero. Verify TLS, disconnect/reconnect, Last Will and graceful stop. Commands are not yet available under `/set`.

If Home Manager telegrams do not reach Docker Desktop, first test the same existing Python receiver natively on macOS with appropriate local file paths and an explicit interface address. Do not substitute guessed grid readings. Linux/arm64 and Pi multicast acceptance remain separate later checks.

## Next functional acceptance

Validate local eCharger identity, metadata, measurement timestamps and units. Then implement confirmed enum/boolean controls with fresh metadata, rights checks, bounded command handling and readback. Energy/time planning needs a confirmed transaction; local energy and delay units are still open. Maximum charging power needs its own confirmed parameter mapping and limits. Home Manager remains the charging controller. Live writes require a specific requested action and target value.
