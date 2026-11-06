# Updating and backups

Back up both private configuration and the active Docker state volume before
replacing an image. A backup of `data/sma-mqtt-bridge/` does not include the named
state volume. Keep the same Compose project name, volume and state mount.

## Published images and version selection

Published images use `ghcr.io/alaub81/sma-mqtt-bridge` for Linux amd64 and arm64.
Docker selects the matching platform. Image tags omit the Git release tag's `v`:
Git tag `vX.Y.Z` corresponds to image tag `X.Y.Z`. The default `latest` follows the
newest successfully published stable release; source changes can precede image
publication. Choose a verified compatible release for reproducible deployments.

On a fresh installation, optionally copy [.env.example](../.env.example) to `.env`
and set `SMAB_BRIDGE_VERSION=X.Y.Z` to the chosen published version. Edit an existing
`.env` in place rather than replacing its overrides. Compose reads `.env` for image,
path and UID/GID interpolation and passes `smab.env` as the service environment.
See [Docker's ENV guidance](https://docs.docker.com/compose/how-tos/environment-variables/set-environment-variables/)
and [bridge configuration](CONFIGURATION.md#compose-usage).

## Replace the container

Use the backup procedure below before changing the image tag.

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

Battery daily accounting adds `batterycharge` and `batterydischarge` accounts to
`energy-balances.json` without rebasing existing accounts or changing the binding
fingerprint. Older builds that do not recognize these account names cannot read
the extended ledger. Before downgrading, use a compatible build or restore the
complete matching pre-upgrade state backup; do not delete individual accounts or
reset the state volume as a routine update step.

## Create a backup

For the default paths and `compose.example.yml`, run from the project directory.
This briefly stops polling so the state files form a consistent backup. Use your
active Compose file if it differs. Keep any custom profiles, certificates and
password files under the configuration directory included here.

```sh
(
set -eu
umask 077
smab_backup_dir="private/backups/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$smab_backup_dir"
cp -p smab.env compose.example.yml "$smab_backup_dir/"
cp -Rp data/sma-mqtt-bridge "$smab_backup_dir/config"
if [ -f .env ]; then cp -p .env "$smab_backup_dir/.env"; fi
docker compose -f compose.example.yml stop sma-mqtt-bridge
docker compose -f compose.example.yml run --rm --no-deps --entrypoint tar \
  sma-mqtt-bridge -C /data/sma-mqtt-bridge/state -czf - . \
  > "$smab_backup_dir/state.tar.gz"
tar -tzf "$smab_backup_dir/state.tar.gz"
docker compose -f compose.example.yml up -d
)
```

The block stops on the first error. The one-off container runs only
`tar`, never the bridge or device readers. Its state mount is the same project
volume; it includes the ledger, topic manifest, command journals, price preferences
and session history. The archive preserves container ownership and permissions.
If archiving or verification fails, preserve the existing volume and investigate;
do not treat a partial archive as a usable backup.
The original service can remain stopped after an error; once the cause is resolved,
resume it with `docker compose -f compose.example.yml up -d`.

The backup contains secrets and installation data. It is ignored by Git and
excluded from image builds, but still needs a protected copy outside this checkout.
If you override `SMAB_DATA_DIR`, `SMAB_ENV_FILE`, state mounts or the Compose file,
adapt the paths and include those exact files. Keep a note of the active image
version and Compose project name with the backup.

For recovery, stop the service and restore the **complete matching configuration
and state** with an image compatible with that state schema. Restore into an empty
state destination with the correct numeric ownership (default UID/GID 10001);
overlaying an older archive onto newer state can leave incompatible journals/files.
Check the archive before replacing any existing state, preserve the failed state
separately, and keep the original Compose project/volume association. Validate
configuration and verify health, source availability and MQTT after restarting.
Do not restore a single old energy ledger alongside unrelated newer command state.
