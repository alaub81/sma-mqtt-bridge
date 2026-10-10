# First installation test on macOS

The first installation test runs on the Mac. Inverter and SEMP values have reached the installation broker; authenticated API/portal, full parallel acceptance and device commands are still pending. Keep the current openHAB integration running for value comparison. Do not remove links, rules or persistence.

## Prepare private configuration

Preserve the existing root `smab.env` and its MQTT settings. Add only missing installation values. Store local API credentials separately from portal credentials and use a password file when preferred. Never paste credentials into chat or protocol fixtures.

For eCharger HTTPS reads, configure `SMAB_ECHARGER_HOST`, `SMAB_ECHARGER_USERNAME`, `SMAB_ECHARGER_PASSWORD` or `SMAB_ECHARGER_PASSWORD_FILE`, and `SMAB_ECHARGER_EXPECTED_SERIAL`. Copy the trusted local certificate into `data/sma-mqtt-bridge/certificates/` and set `SMAB_ECHARGER_TLS_CA_FILE` to its container path under `/data/sma-mqtt-bridge/certificates/`. The certificate must match HOST or the explicitly configured `SMAB_ECHARGER_TLS_SERVER_NAME`. The current private setup uses the trusted certificate's DNS name while connecting to the wallbox IP; a real TLS handshake passed. An explicit `SMAB_ECHARGER_TLS_VERIFY=false` needs no certificate file and skips verification while retaining TLS encryption. Only enable `SMAB_ECHARGER_ENABLED=true` after credentials are ready.

SEMP is independent and additionally requires its known device ID through `SMAB_ECHARGER_SEMP_DEVICE_ID`; use `SMAB_ECHARGER_SEMP_ENABLED` only when testing that reader. Home Manager requires `SMAB_HOME_MANAGER_SERIAL` and suitable UDP delivery. **Leave `SMAB_HOME_MANAGER_ENABLED=false` on this Mac:** it runs on a different network from the meter. Finish serial/interface configuration and multicast acceptance on the Pi in the device network. The three bundled inverter profiles now cover the existing Things channels; private hosts and serial guards are configured, and all three are enabled for this test.

Keep all command flags false. Local credentials alone never activate a source or enable a write.

## Prepared inverter and SEMP test

The independently enabled SEMP reader uses local HTTP and needs no charger API login or HTTPS trust. The private charger host, device ID and serial are prepared; `SMAB_ECHARGER_SEMP_ENABLED=true` and all three inverter flags are enabled. Local API and portal stay disabled until their credentials are supplied. SEMP additionally reads confirmed settings and raw diagnostic codes, with unverified energy/delay units exposed only on explicitly named raw properties. It does not test authenticated additional measurements or device commands.

MQTT TLS verification defaults to true. Use a trusted broker CA under `data/sma-mqtt-bridge/certificates/` and its container path, or system trust. For this installation Andreas explicitly requested `SMAB_MQTT_TLS_VERIFY=false`; the private `smab.env` now uses it and real broker publication passed. TLS encryption, username/password authentication and local-wallbox/portal verification remain separate. Changing a TLS flag requires recreating the container, not merely restarting it.

## Validate and start

The Compose service uses host networking. On Docker Desktop 4.34 or later, enable **Settings > Resources > Network > Enable host networking**, then restart Desktop. Docker documents TCP/UDP support but no direct access to native host interfaces; independently verify LAN multicast reception. See [Docker host networking](https://docs.docker.com/engine/network/drivers/host/).

Once configuration is ready, run from the repository root:

```sh
docker compose -f docker-compose.dev.yml run --rm --build sma-mqtt-bridge --check-config
docker compose -f docker-compose.dev.yml up --build -d
docker compose -f docker-compose.dev.yml logs --tail=100 -f
```

The first command validates configuration without device or broker I/O. The second starts live read/publish activity for explicitly enabled sources. With all sources disabled, configuration validation succeeds but the runtime exits with an actionable message. A running container alone does not establish adapter acceptance.

Inspect `homie/sma-inverter1/`, `homie/sma-inverter2/`, `homie/sma-inverter3/` and `homie/sma-echarger/` on the configured broker. Verify discovery, source diagnostics, fresh settings and measurement values against the local SMA interface/openHAB. Missing, invalid and stale values must disappear instead of becoming zero. Verify TLS, disconnect/reconnect, Last Will and graceful stop. Commands are not yet available under `/set`.

Home Manager setup is intentionally deferred to the Raspberry Pi. Do not substitute guessed grid readings or activate it on the Mac. Linux/arm64 and Pi multicast acceptance are separate checks.

## Next functional acceptance

Validate local eCharger identity, metadata, measurement timestamps and units. Then implement confirmed enum/boolean controls with fresh metadata, rights checks, bounded command handling and readback. Energy/time planning needs a confirmed transaction; local energy and delay units are still open. Maximum charging power needs its own confirmed parameter mapping and limits. Home Manager remains the charging controller. Live writes require a specific requested action and target value.

## Configuration examples

The root `smab.example.env` lists every available variable with purpose/type/default. The optional `config.example.json` includes non-secret runtime/device options and documentation-only addresses; all sources remain disabled. It deliberately omits inverter interval overrides so per-poller intervals survive. Copy it to `data/sma-mqtt-bridge/config.json` only when needed; explicit ENV overrides still win. Account usernames/passwords use ENV or private password files.

Bundled model files under `ressources/profiles/` are directly usable examples for host overrides: copy one to `data/sma-mqtt-bridge/profiles/`, preserve its ID, or select a renamed file with `file:custom-name.json`. Never put installation addresses or passwords in a reusable profile. Certificates are public trust material rather than configuration templates; obtain the actual trusted certificate instead of copying a fabricated example.
