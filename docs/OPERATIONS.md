# Operation and troubleshooting

## Validate and start

For the published-image Compose file:

```sh
docker compose -f compose.example.yml run --rm --no-deps sma-mqtt-bridge --check-config
docker compose -f compose.example.yml up -d
docker compose -f compose.example.yml ps sma-mqtt-bridge
docker compose -f compose.example.yml logs --tail=100 sma-mqtt-bridge
```

Configure only intended sources and verify their identities/profile, reachable
addresses and TLS trust. Addresses or credentials alone do not enable a source.
Use [configuration](CONFIGURATION.md) for supported settings and typed defaults.
Changing environment settings requires container recreation; restart alone retains
the old environment.

## Health and unavailable measurements

Container health checks process progress. Source status and Homie device state
report different aspects of availability; a healthy container can have an offline
device. MQTT retains the last valid observation, which may remain visible after
expiry. Never interpret a retained number alone as fresh data or missing data as zero.
Check [topic groups](TOPIC_GROUPS.md) and [plant coverage](PLANT.md).

Unchanged Homie device `$state` messages repeat every 10 seconds by default;
configure positive `SMAB_MQTT_STATE_PUBLISH_INTERVAL_SECONDS` to change this interval.
Actual state changes and the first state after connection are published on the next
publisher pass without waiting for that interval. Measurement publication, device
polling, health checks and the retained `lost` Last Will use their own schedules.

For missing values, check adapter activation, source status, identity errors,
model/profile support, channel-group filters, units and timestamps. Bulk API reads
can succeed while individual values are unavailable. Repeated old device timestamps
do not establish fresh observations. Clock-lead tolerance must not be used to
accept genuinely stale data. API and SEMP have separate enable flags and status.

For TLS failures, check hostname matching, CA files and container paths. Verification
is enabled by default. Portal verification is mandatory. Consult the explicit local
MQTT/eCharger overrides only when deliberately changing their trust policy.

## Recovery and commands

Back up configuration and the complete state volume before replacing an image;
see the [backup procedure](UPDATING.md#create-a-backup). Optional CLI, host sampling
and offline export tools are described in the [tool guide](TOOLS.md).

Sources and MQTT reconnect independently with bounded backoff. Authentication
failures block repeated login attempts. Preserve the state volume, topic manifest
and uncertainty journals during recovery. Source or broker recovery does not
require resending commands.

Command feedback must confirm device readback; HTTP success alone is insufficient.
For `uncertain` or blocked journal status, inspect actual device state and reconcile
the saved action before allowing another command. Do not resend blindly or delete
the state volume to clear a guard. Measurements are read-only; device writes require
explicit command gates, current rights, units, bounds and supported allowlists.

## Common setup problems

| Symptom | Check / next step |
| --- | --- |
| Compose rejects `env_file` or `required` | Use Docker Compose 2.24 or newer (`docker compose version`). |
| Configuration validates with `enabledSources: 0` | Explicitly enable at least one source in root `smab.env`; addresses do not enable devices. |
| Broker connection fails | Check address, port, credentials and TLS. Default is verified TLS on 8883; plaintext requires both `SMAB_MQTT_TLS=false` and port 1883. `localhost` refers to the bridge container. |
| Certificate verification fails | Check the trusted CA, certificate hostname and container-readable mount paths. The eCharger can use a separate `TLS_SERVER_NAME`. |
| Inverter reports an identity error | Match the exact model/firmware/profile and optional serial guard. A related model or a schema-valid custom file does not establish compatibility. |
| Home Manager has totals but no phases | Modbus provides totals. Enable supplemental UDP for phases and verify Linux host networking/multicast reception; see [Home Manager](HOME_MANAGER_MODBUS.md). |
| eCharger local login fails | Use the local account and expected charger serial, independently of portal credentials. After correcting an authentication block, recreate the service. |
| A file cannot be read | The container user is UID/GID 10001 by default. Check parent-directory access and file permissions for mounted CA/profile/password files. Compose reads host-only `smab.env`, which stays mode 600. |
| Changed ENV has no effect | Run `docker compose -f compose.example.yml up -d` to recreate the container; `restart` keeps the old environment. |
| New source-code feature is missing | Check the running image with `--version`; `latest` follows published images, not every main-branch commit. Use a matching release or [build the checkout](BUILDING.md). |
| Healthy container, old values | Health checks process liveness. Inspect source availability and freshness; retained values remain last-known observations. |
| First daily value is incomplete | Initial counter-based day deltas start at the saved first baseline and report `partial`. Allow a covered midnight for complete-day coverage. |
| openHAB does not discover devices | Confirm both use the same broker, install/configure the MQTT binding and broker Thing, then check the Inbox; see [openHAB setup](../openHAB/openHAB.md). |

For a bug report, include the bridge image version, host architecture, Docker
Compose version, exact device model/firmware, expected behavior and a short
sanitized log excerpt. Do not attach `smab.env`, authentication responses, tokens,
state backups or unreviewed recordings. General problems can be reported through
[GitHub issues](https://github.com/alaub81/sma-mqtt-bridge/issues).
