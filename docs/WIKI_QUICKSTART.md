# Quick start: three inverters, Home Manager and eCharger

This example uses the updated defaults: Modbus TCP, Basic channels, English labels
and read-only device access. Copy the first block into a private root `smab.env`
and replace every installation placeholder. No JSON configuration is required.
Descriptions and typed defaults below come from [smab.example.env](../smab.example.env).

The bundled inverter selections are STP8.0-3AV-40 (slot 1), SBS3.7-10 (slot 2)
and SB4.0-1AV-41 (slot 3). For different hardware, explicitly select a matching
verified `SMAB_INVERTER<N>_PROFILE`. Remove or disable any adapter you do not have;
addresses alone never activate one. Enable Modbus access on the devices beforehand.
Remove MQTT username/password if your broker does not require authentication.

## Minimal installation configuration

```dotenv
# Broker hostname/IP; empty default, required for active publishing. Replace the placeholder.
# Type: string; default: empty.
SMAB_MQTT_HOST=mqtt.example.invalid

# Optional broker authentication username.
# Type: string; default: empty.
SMAB_MQTT_USERNAME=bridge-user

# Account password; use either PASSWORD or PASSWORD_FILE, never both.
# Type: string; default: empty.
SMAB_MQTT_PASSWORD='REPLACE_WITH_MQTT_PASSWORD'

# Enable this source explicitly; addresses or credentials never activate it.
# Type: boolean; default: false.
SMAB_INVERTER1_ENABLED=true

# Device hostname/IP; required only for this enabled source.
# Type: string; default: empty.
SMAB_INVERTER1_HOST=inverter1.example.invalid

# Enable this source explicitly; addresses or credentials never activate it.
# Type: boolean; default: false.
SMAB_INVERTER2_ENABLED=true

# Device hostname/IP; required only for this enabled source.
# Type: string; default: empty.
SMAB_INVERTER2_HOST=inverter2.example.invalid

# Enable this source explicitly; addresses or credentials never activate it.
# Type: boolean; default: false.
SMAB_INVERTER3_ENABLED=true

# Device hostname/IP; required only for this enabled source.
# Type: string; default: empty.
SMAB_INVERTER3_HOST=inverter3.example.invalid

# Enable this source explicitly; addresses or credentials never activate it.
# Type: boolean; default: false.
SMAB_HOME_MANAGER_ENABLED=true

# Optional UDP sender IPv4 filter; required TCP host for modbus-tcp.
# Type: string; default: empty.
SMAB_HOME_MANAGER_HOST=home-manager.example.invalid

# Required decimal serial selector when enabled; verifies telegrams or Modbus identity.
# Type: string; default: empty.
SMAB_HOME_MANAGER_SERIAL=REPLACE_WITH_NUMERIC_SERIAL

# Enable local HTTPS API reads only; does not enable SEMP.
# Type: boolean; default: false.
SMAB_ECHARGER_ENABLED=true

# Trusted certificate DNS name/IP of the local charger; shared by API and SEMP.
# Type: string; default: empty.
SMAB_ECHARGER_HOST=echarger.example.invalid

# Local charger account; separate from the portal account.
# Type: string; default: empty.
SMAB_ECHARGER_USERNAME=REPLACE_WITH_LOCAL_USER

# Account password; use either PASSWORD or PASSWORD_FILE, never both.
# Type: string; default: empty.
SMAB_ECHARGER_PASSWORD='REPLACE_WITH_LOCAL_PASSWORD'

# Required serial guard for local API; optional additional SEMP identity check.
# Type: string; default: empty.
SMAB_ECHARGER_EXPECTED_SERIAL=REPLACE_WITH_CHARGER_SERIAL

# Enable a separate logical Homie plant with an explicitly selected enabled grid source.
# With the local eCharger API enabled, also publish daily kWh on the eCharger
# and household daily kWh without Wallbox on the plant (household AC gate still applies).
# Type: boolean; default: false.
SMAB_PLANT_ENABLED=true
```

TLS and certificate/name verification are enabled for MQTT and the local eCharger.
The MQTT port defaults to 8883. Use reachable certificate names above.
If certificates use a private CA, add the relevant settings below and place the
CA files in the mounted host `data/sma-mqtt-bridge/certificates/` directory.
The certificate must match the configured host; a CA file alone does not fix
a name mismatch. MQTT and eCharger each have independent trust settings.

```dotenv
# Container path to a trusted broker CA; empty uses system trust.
# Type: string; default: empty.
SMAB_MQTT_TLS_CA_FILE=/data/sma-mqtt-bridge/config/certificates/mqtt-ca.crt

# Container path to trusted local charger certificate/CA; empty uses system trust.
# Type: string; default: empty.
SMAB_ECHARGER_TLS_CA_FILE=/data/sma-mqtt-bridge/config/certificates/echarger-ca.crt
```

## Optional additions

Add only the options needed by your installation. Advanced and detailed diagnostic
channels remain disabled; operational status and Basic measurements remain available.

For German display labels:

```dotenv
# Display labels only; IDs, units, enum values and commands remain language-independent.
# Type: string; default: en. Bundled: en/de; custom language needs <language>.json.
SMAB_LANGUAGE=de
```

For the separate SEMP reader (use the device's actual SEMP ID):

```dotenv
# Enable local SEMP reads independently; no local API credentials required.
# Type: boolean; default: false.
SMAB_ECHARGER_SEMP_ENABLED=true

# Required SEMP device ID selector when SEMP is enabled.
# Type: string; default: empty.
SMAB_ECHARGER_SEMP_DEVICE_ID=REPLACE_WITH_SEMP_DEVICE_ID
```

For the ennexOS minimum-PV-percentage reader, add the separate portal account and
selectors. Refresh defaults to 900 seconds; freshness defaults to 1800 seconds.

```dotenv
# Enable optional ennexOS minimum-PV reader separately from all local sources.
# Type: boolean; default: false.
SMAB_PORTAL_ENABLED=true

# Normal portal account username; separate from local charger credentials.
# Type: string; default: empty.
SMAB_PORTAL_USERNAME=REPLACE_WITH_PORTAL_USER

# Account password; use either PASSWORD or PASSWORD_FILE, never both.
# Type: string; default: empty.
SMAB_PORTAL_PASSWORD='REPLACE_WITH_PORTAL_PASSWORD'

# Required portal plant selector when this source is enabled.
# Type: string; default: empty.
SMAB_PORTAL_PLANT_ID=REPLACE_WITH_PLANT_ID

# Required portal charger device selector when this source is enabled.
# Type: string; default: empty.
SMAB_PORTAL_DEVICE_ID=REPLACE_WITH_PORTAL_DEVICE_ID
```

To intentionally allow supported charger commands, add the first two gates below.
Add the portal gate only when the portal adapter is configured and portal PV writes
are wanted. Reading settings does not require these gates. Home Manager remains
the charging controller; the bridge does not write commands on startup.

```dotenv
# Global write gate; local controls also require SMAB_ECHARGER_COMMANDS_ENABLED and the API.
# Type: boolean; default: false.
SMAB_COMMANDS_ENABLED=true

# Local command gate; also requires SMAB_COMMANDS_ENABLED and enabled local API.
# Type: boolean; default: false.
SMAB_ECHARGER_COMMANDS_ENABLED=true

# Portal PV write gate; also requires SMAB_COMMANDS_ENABLED and SMAB_PORTAL_ENABLED.
# Type: boolean; default: false.
SMAB_PORTAL_COMMANDS_ENABLED=true
```

Tariffs, energy offsets, identity overrides, special TLS settings and temporary
timestamp recording are installation-specific options, not required quick-start
settings. See the complete ENV reference before adding them. Initial daily deltas
have `partial` coverage until a covered midnight; existing energy state is preserved.

## Start

Use [compose.example.yml](../compose.example.yml) for one `app-nw` network, or
[compose.dev.yml](../compose.dev.yml) to build locally. Optional Compose values
(image tag, paths, UID/GID) belong in `.env`; see [.env.example](../.env.example).
The standalone template expects an existing reachable MQTT broker. A Docker
service name such as `mosquitto` works only on a shared network.

```sh
chmod 600 smab.env
docker compose -f compose.example.yml pull
docker compose -f compose.example.yml run --rm --no-deps sma-mqtt-bridge --check-config
docker compose -f compose.example.yml up -d
docker compose -f compose.example.yml logs --tail=100 sma-mqtt-bridge
```

For updates, keep the existing
Compose project name and state volume and do not run a second writer instance.
Check configuration successfully before starting the service. Verify container
health, MQTT source availability and measurements after startup.

Direct Home Manager UDP multicast on Linux uses the separate
[host-network template](../compose.host.example.yml) and requires an explicit
`SMAB_HOME_MANAGER_TRANSPORT=udp` override plus a host-reachable broker address.
The default Modbus setup above uses the bridge-network template.
