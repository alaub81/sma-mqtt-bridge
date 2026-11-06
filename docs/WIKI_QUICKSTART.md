# Set up SMA MQTT Bridge with Docker

Start with one device, verify its MQTT values, then add the other sources you need.
Each source is independent; no additional JSON configuration is required. All
sources and device-write gates default to disabled.

## 1. Prepare the host

You need Docker with Compose **2.24 or newer**, Git and a reachable MQTT broker.
The images support Linux amd64 and arm64, including 64-bit Raspberry Pi systems.
The bridge does not install a broker or provide a web dashboard.

Check your device's exact model and firmware against the
[supported devices](../README.md#supported-devices). Enable its required local
interface before connecting; inverter Modbus TCP is a device setting.

For a new installation:

```sh
git clone https://github.com/alaub81/sma-mqtt-bridge.git
cd sma-mqtt-bridge
mkdir -p data/sma-mqtt-bridge
touch smab.env
chmod 600 smab.env
docker compose version
```

Edit `smab.env` with a text editor. Keep existing files when updating.
[smab.example.env](../smab.example.env) lists every option; you only need the
settings relevant to your installation. Paths below refer to the default layout.

## 2. Configure MQTT

Add your broker's hostname or IP:

```dotenv
SMAB_MQTT_HOST=mqtt.example.invalid
```

Replace the example address with one reachable **from the container**. `localhost`
inside the container refers to the bridge container. A service name such as
`mosquitto` requires a shared Docker network; the standalone template creates its
own network. See [network variants](CONFIGURATION.md#compose-network-variants).

MQTT defaults to TLS on port **8883**, with certificate verification. For a private
CA, place the trusted CA at `data/sma-mqtt-bridge/certificates/mqtt-ca.crt` and add:

```dotenv
SMAB_MQTT_TLS_CA_FILE=/data/sma-mqtt-bridge/config/certificates/mqtt-ca.crt
```

For a deliberately plaintext broker, explicitly add both settings instead:

```dotenv
SMAB_MQTT_TLS=false
SMAB_MQTT_PORT=1883
```

Add authentication only if your broker requires it. Single-quote passwords
containing `$` or `#` so Compose preserves them literally:

```dotenv
SMAB_MQTT_USERNAME=bridge-user
SMAB_MQTT_PASSWORD='REPLACE_WITH_MQTT_PASSWORD'
```

The default container user is UID/GID 10001. Mounted directories must be traversable
and any CA/password files readable by that user. The host-only `smab.env` stays
mode 600; Compose reads it before starting the container.

## 3. Add a source

Copy only the blocks for equipment you actually have, replacing every placeholder.
An address or password alone never enables a source.

### One inverter

```dotenv
SMAB_INVERTER1_ENABLED=true
SMAB_INVERTER1_HOST=inverter.example.invalid
SMAB_INVERTER1_PROFILE=sma-stp8-0-3av-40
```

Choose the [profile](PROFILES.md) matching the exact model/firmware. To add more
inverters, repeat the block with `INVERTER2`, `INVERTER3`, etc. A profile can be used
in any slot. For the bundled three-model setup, select `sma-stp8-0-3av-40`,
`sma-sbs3-7-10` and `sma-sb4-0-1av-41` respectively.

### Sunny Home Manager 2.0

```dotenv
SMAB_HOME_MANAGER_ENABLED=true
SMAB_HOME_MANAGER_HOST=home-manager.example.invalid
SMAB_HOME_MANAGER_SERIAL=REPLACE_WITH_NUMERIC_SERIAL
```

The default is Modbus TCP. It provides grid totals; UDP provides phase readings
and can also be selected as the main transport. Linux UDP multicast requires the
[host-network template and transport settings](HOME_MANAGER_MODBUS.md#phase-measurements).
The bridge never enables the device's Modbus server or sends a Grid Guard login.

### SMA eCharger local API

```dotenv
SMAB_ECHARGER_ENABLED=true
SMAB_ECHARGER_HOST=echarger.example.invalid
SMAB_ECHARGER_USERNAME=REPLACE_WITH_LOCAL_USER
SMAB_ECHARGER_PASSWORD='REPLACE_WITH_LOCAL_PASSWORD'
SMAB_ECHARGER_EXPECTED_SERIAL=REPLACE_WITH_CHARGER_SERIAL
```

Use the local charger account, independently of any Sunny Portal account. TLS
verification is enabled. If system trust does not cover the charger, supply its
trusted certificate/CA in `data/sma-mqtt-bridge/certificates/echarger-ca.crt`:

```dotenv
SMAB_ECHARGER_TLS_CA_FILE=/data/sma-mqtt-bridge/config/certificates/echarger-ca.crt
```

The certificate must match the host. For connection by IP with a certificate for
a DNS name, use `SMAB_ECHARGER_TLS_SERVER_NAME` as documented in
[configuration](CONFIGURATION.md#minimal-deployment-overrides). A CA alone does not
fix a hostname mismatch. SEMP and portal access are separate optional readers.

### BYD Battery-Box

For the separately supported four-module HVS layout, add the two settings in the
[BYD guide](BYD.md#configuration). Check its strict firmware/topology requirements
first; support does not extend to arbitrary HVS/HVM systems.

## 4. Validate and start

Use the standalone published-image template for the default TCP setup:

```sh
docker compose -f compose.example.yml pull
docker compose -f compose.example.yml run --rm --no-deps sma-mqtt-bridge --check-config
docker compose -f compose.example.yml up -d
docker compose -f compose.example.yml ps sma-mqtt-bridge
docker compose -f compose.example.yml logs --tail=100 sma-mqtt-bridge
```

Only start after a successful configuration check. With one inverter and the
broker configured, expect `{"valid": true, "enabledSources": 1, "readOnly": true}`.
The check validates settings and local files without connecting to devices or the
broker. `enabledSources: 0` means there is no active source, even if settings are valid.

Allow up to two minutes for initial reads. Check health and logs, then inspect
your broker with an MQTT viewer: the default inverter root is
`homie/sma-inverter1/`, with discovery metadata, `$state` and measurement nodes.
Health alone does not establish fresh device values; follow
[operation and troubleshooting](OPERATIONS.md).

Published images come from `ghcr.io/alaub81/sma-mqtt-bridge`. `latest` follows the
newest published stable image; a source checkout can be newer. For an exact image
version, set `SMAB_BRIDGE_VERSION` in optional root `.env`, using
[.env.example](../.env.example) as a reference. Bridge/device settings belong in
`smab.env`. To build the checked-out source instead, see [building](BUILDING.md).

## 5. Add optional features

Add only what you need, then repeat the configuration check and `up -d`.
Use the same Compose file, project name and `data_smab_state` volume throughout.

| Feature | Settings / guide |
| --- | --- |
| German discovery labels | `SMAB_LANGUAGE=de`; [translations](TRANSLATIONS.md) |
| Plant and daily energy balances | `SMAB_PLANT_ENABLED=true`, with an already enabled grid source and configured contributors; [plant setup](CONFIGURATION.md#plant-aggregates-and-energy-state) |
| More technical channels | Independent `ADVANCED_CHANNELS_ENABLED` and `DIAGNOSTICS_ENABLED` switches; [topic groups](TOPIC_GROUPS.md) |
| SEMP charger reader | `SMAB_ECHARGER_SEMP_ENABLED=true` and actual `SMAB_ECHARGER_SEMP_DEVICE_ID`; [configuration](CONFIGURATION.md) |
| ennexOS minimum-PV preference | Separate portal activation, account, plant/device selectors; [portal settings](CONFIGURATION.md#minimal-deployment-overrides) |
| Charger controls and plans | Global and source-specific write gates; [local controls](CONFIGURATION.md#local-echarger-controls) and [plan/portal commands](CONFIGURATION.md#combined-charging-plan-and-portal-pv-commands) |
| openHAB dashboards | [Homie discovery and Items](../openHAB/openHAB.md), then [widgets](../openHAB/README.md) |

Home Manager remains the charging controller. Initial counter-based day values
cover the period since the first saved baseline and report `partial`; they are
not reconstructed full-day totals. Tariffs and offsets are optional.

Before the first update, follow [backups and safe upgrades](UPDATING.md).
[Diagnostic tools](TOOLS.md) are available when investigating a problem.
