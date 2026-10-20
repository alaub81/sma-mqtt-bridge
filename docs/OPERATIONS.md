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

For missing values, check adapter activation, source status, identity errors,
model/profile support, channel-group filters, units and timestamps. Bulk API reads
can succeed while individual values are unavailable. Repeated old device timestamps
do not establish fresh observations. Clock-lead tolerance must not be used to
accept genuinely stale data. API and SEMP have separate enable flags and status.

For TLS failures, check hostname matching, CA files and container paths. Verification
is enabled by default. Portal verification is mandatory. Consult the explicit local
MQTT/eCharger overrides only when deliberately changing their trust policy.

## Recovery and commands

Sources and MQTT reconnect independently with bounded backoff. Authentication
failures block repeated login attempts. Preserve the state volume, topic manifest
and uncertainty journals during recovery. Source or broker recovery does not
require resending commands.

Command feedback must confirm device readback; HTTP success alone is insufficient.
For `uncertain` or blocked journal status, inspect actual device state and reconcile
the saved action before allowing another command. Do not resend blindly or delete
the state volume to clear a guard. Measurements are read-only; device writes require
explicit command gates, current rights, units, bounds and supported allowlists.
