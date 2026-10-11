# Polling, timeouts and alarm acceptance

## Effective installation limits

Run against the updated image in the existing service, without stopping it:

```sh
docker compose exec -T sma-mqtt-bridge python -m sma_mqtt_bridge.operational_limits
```

This validates and reads the container configuration/profile files with normal
precedence, but performs no device or broker requests. Output is allowlisted:
source slots, enabled-source scheduling, timeouts, property expiry and readiness
keys. Addresses, credentials, serial numbers and configured MQTT identities are
excluded. Configuration errors disclose only the exception class.
The command requires an image containing this module; it is not in older images.

Repository defaults (not evidence of the installation's effective configuration):

| Source | Poll interval | Request timeout | Source expiry |
| --- | --- | --- | --- |
| Inverters | Profile pollers unless explicitly overridden; fallback 10 s | 5 s | 60 s; individual properties can have longer profile-derived expiry |
| Home Manager Modbus | 3 s; transactions are paced | 5 s; connect 5 s | 30 s |
| Local eCharger API | 60 s | 10 s | 180 s |
| SEMP | 30 s | 10 s | 180 s |
| Portal | 0 s: periodic polling disabled | 15 s | 180 s |

Whole-read watchdog defaults to 120 s, retry backoff to 1–60 s, outage log
summaries to 300 s, heartbeat to 10 s and heartbeat expiry to 60 s.
MQTT connect timeout defaults to 10 s and keepalive to 60 s.
The log summary interval is not an alarm delay. A polling wait can follow the
request duration; the configured interval alone is not a precise detection bound.
Authentication failures deliberately stop automatic retries until resolved/restarted.
Per-property expiry and paced Home Manager reads must be considered separately.

## Target-host procedure

1. Save the limit report and the external monitoring conditions, delay, repeat
   interval and recovery condition. Do not change thresholds until compared.
2. Observe a full day including inverter wake-up and natural charging changes.
   Keep timestamp recording enabled. Capture logs with:

   ```sh
   docker compose logs --since 24h --timestamps sma-mqtt-bridge > smab-operation.log
   ```

3. Agree on a single read source and maintenance window before a controlled
   interruption. Do not interrupt Home Manager charging regulation or power off
   equipment during charging. Use a reversible network restriction limited to the
   bridge-to-device read connection, with broker/other sources left reachable.
   The exact restriction depends on the host/network and is not prescribed here.
4. Record interruption time, first source error/stale state, external alarm time,
   connection restoration, source ready and alarm clearance. Restore the restriction
   even if the test fails. Verify independent sources keep updating, the bridge
   stays alive, last-known values are preserved and no write is replayed.
5. Compare observed times against effective polling, request/whole-cycle limits,
   backoff, property expiry and external alarm delay. Avoid promises that a device
   outage always waits for expiry: a failed read can report error immediately.

Docker health is process liveness, not proof that all devices or MQTT are available.
External alarms must distinguish those signals. Sleeping inverters need their
accepted readiness policy; missing night production alone is not an outage.
UDP/interface/multicast tests are required only when the UDP transport is selected.
Device timestamp semantics and the remaining freshness correction are pending the
separate recording review. No threshold changes or live interruptions are performed
by this procedure's implementation.

## Automated evidence and limits

Existing fixtures cover hung reads, swallowed cancellation, session reset,
partial/invalid samples, source isolation, authentication, MQTT reconnection and
health semantics. New cases simulate twelve hours of partial samples using explicit
monotonic times and sixty repeated timeout/retry cycles without real waiting.
They check bounded outage summaries, retained last-known values, independent fresh
zero readings, bounded retry delays and recovery. This is not a twelve-hour live
load test, memory/connection soak, or external alarm delivery test.
