# Updating and backups

Back up both private configuration and the active Docker state volume before
replacing an image. A backup of `data/sma-mqtt-bridge/` does not include the named
state volume. Keep the same Compose project name, volume and state mount.

## Replace the container

1. Read the target version's changes and check configuration/profile overrides.
   Back up private configuration and persistent state using the installation's
   existing procedure. Preserve the same Compose project and state volume;
   the topic manifest and command uncertainty journals must survive replacement.
2. Set `SMAB_BRIDGE_VERSION` in root `.env` to the exact compatible image version.
   With the standalone example file:

   ```sh
   docker compose -f compose.example.yml pull
   docker compose -f compose.example.yml run --rm --no-deps sma-mqtt-bridge --check-config
   docker compose -f compose.example.yml up -d
   docker compose -f compose.example.yml exec -T sma-mqtt-bridge python -m sma_mqtt_bridge --version
   docker compose -f compose.example.yml ps sma-mqtt-bridge
   ```

3. Verify expected image version, healthy container, configured sources and MQTT
   recovery. Compare selected openHAB values/history and read-back settings;
   preserve existing Items, units, offsets and rules. A successful startup does
   not confirm physical charging behavior.
4. If an upgrade fails, use a previous image only when it supports the current
   configuration and state schema. If a release changes the state schema, follow
   its backup/restore procedure before downgrading; do not run older code against
   unsupported state. Keep the same Compose project and mounts. Investigate uncertainty journals before
   requesting any command retry. Do not remove the state volume with `down -v`.

A restart alone does not apply a changed image/environment. No command or charge
plan needs to be resent as part of an upgrade. Host profile/translation overrides
can mask bundled additions and need an explicit independent review.
