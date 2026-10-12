# Installation acceptance on macOS and the target host

Use this procedure for the next installation checks. The
[current acceptance matrix](VALIDATION.md) records already completed checks; it
supersedes earlier activation assumptions in the [archived Mac notes](archive/2026-10-11/MAC_TEST.md).
Keep the current openHAB integration running for aligned comparisons until migration
is accepted. Use actual configured device IDs and Channel UIDs.

## Prepare private configuration

Preserve root `smab.env`; add only necessary changes using
[smab.example.env](../smab.example.env) and [CONFIGURATION.md](CONFIGURATION.md).
Do not copy an example over an existing private file. Configure each source and
transport explicitly. Local eCharger and portal credentials are separate. Addresses,
serials and passwords belong only in private configuration or password files.

TLS verification defaults to true. Supply actual trusted CA/certificate files and
matching hostnames where needed. Local wallbox and MQTT accept their explicit
`SMAB_ECHARGER_TLS_VERIFY=false` / `SMAB_MQTT_TLS_VERIFY=false` overrides; portal
verification remains mandatory. An ENV change requires container recreation.

For read acceptance, leave all command gates false in the test configuration.
Use one service instance per state directory. Preserve `data_smab_state`, including
its topic manifest and uncertainty journals; do not start parallel runtimes sharing
that state. Existing source credentials do not imply activation or write permission.

## Check network and configuration

Home Manager Modbus TCP requires direct host/serial configuration and device-side
access. It does not depend on receiving UDP multicast. The UDP transport instead
requires the correct meter network, interface, serial and multicast delivery. A Mac
in another network cannot establish Pi UDP acceptance.

The current Compose files use host networking. Docker Desktop host networking must
be enabled when using this setup; its TCP/UDP support does not establish native
interface or multicast behavior. See [Docker host networking](https://docs.docker.com/engine/network/drivers/host/).
The proposed Docker bridge-network change for Modbus remains planned work.

From the repository root, validate without device or broker network I/O:

```sh
docker compose --env-file smab.env -f docker-compose.dev.yml build
docker compose --env-file smab.env -f docker-compose.dev.yml run --rm sma-mqtt-bridge --check-config
```

If the intended container is already running, inspect its loaded configuration with
`docker compose --env-file smab.env -f docker-compose.dev.yml exec sma-mqtt-bridge python -m sma_mqtt_bridge --check-config`.
The CLI validates mounted files and the container environment, but does not print
resolved credentials or connect to devices. Configuration success does not prove live
acceptance. All sources disabled is valid configuration; a fresh deployment then
has no readings to serve. An existing topic manifest can still require retirement work.

## Start and compare selected reads

After checking which sources and command gates are enabled:

```sh
docker compose --env-file smab.env -f docker-compose.dev.yml up -d
docker compose --env-file smab.env -f docker-compose.dev.yml logs --tail=100 -f
```

This starts live activity for explicitly enabled sources. Examine the configured
MQTT prefix/device IDs, discovery and independent source status. Compare fresh
power, energy, settings and units with local SMA interfaces/openHAB at aligned times.
Record missing channels and sampling differences. Stale/invalid readings preserve
the last retained observation; they do not become zero or prove current availability.

Inspect health/heartbeat inside the container's state volume. A healthy process does
not prove broker/device readiness. Test controlled stop/start independently from
abrupt process failure, Last Will, broker restart and host reboot. Preserve the volume
through container replacement; follow [state migration](CONFIGURATION.md#migrating-existing-state-from-a-bind-mount)
when upgrading an older bind-mounted state layout.

## Portal and command acceptance

Portal interval zero performs no startup login or read. `--refresh-portal` explicitly
requests one read in an enabled zero-interval service; the sample expires normally.
A persistent Compose command override repeats that explicit refresh on restart;
record the override and remove it when restoring ordinary operation. Positive
intervals enable periodic reads; verify freshness over more than one cycle.

Implemented controls and their independent gates are documented in
[CONFIGURATION.md](CONFIGURATION.md#local-echarger-command-milestone).
A live write requires a specifically requested action and concrete target. Observe
metadata/identity/bounds checks, readback and uncertainty feedback. Do not retry an
uncertain command or infer physical charging completion from a confirmed setting.

Keep Home Manager as charging controller. Accept each remaining command and charging
scenario separately, using [VALIDATION.md](VALIDATION.md) and
[the power-limit evidence](ECHARGER_POWER_LIMIT.md) to identify current gaps.

## Finish the migration check

Compare all [migration-ledger](migration-coverage.csv) rows, including quantities,
negative values, maps, private offsets, calculations, UI and persistence. Use the
[MainUI guide](../openHAB/openHAB.md) and actual existing Items. Preserve historical
series and local day/DST behavior. Neither Homie discovery nor a successful Mac read
establishes complete openHAB migration or Raspberry Pi acceptance.

## Accept the 2026-10-12 topic extension

Preserve `smab.env`, host profile overrides and the existing state volume. If using
custom profile files, compare them with the updated bundled mappings before
deploying; an old override can hide the additions. For the requested GitHub
release, wait for the tag-triggered workflow to pass, then select
`SMAB_BRIDGE_VERSION=0.3.3`, pull and recreate using the example Compose file.
Preserve the existing Compose project name so the state volume remains the same.
A local commit alone does not update the GHCR image.

- [ ] Validate the actual deployment configuration with `--check-config` before
  starting normal polling. Confirm expected enabled sources and profile IDs.
- [ ] Container becomes healthy; enabled sources and MQTT recover without restart
  loops, identity failures, decoding errors or new recurring connection errors.
- [ ] All 25 new properties in the [approved selection](../todo.md#auswahl-der-25-neu-ergänzten-topics)
  have expected discovery metadata when their group is enabled. Inverter1/2
  `type`, `maxpower`, `setmaxpower` require the respective advanced flag; the
  other 19 are basic. Every new property has `$settable=false`.
- [ ] During PV production, compare inverter frequency (Hz), Tripower phase
  currents (A), Sunny Boy L3 power/voltage/current (W/V/A), and inverter1/2 type
  and power limits (raw model code/W) against aligned device observations.
  Preserve existing Sunny Boy L1 IDs and history; do not relabel them as L3.
  Sunny Boy L2 metadata without a value is expected from the observed SMA NaN.
- [ ] While the battery operates, compare Storage AC active power (W), L1 current
  (A), battery current (A) and voltage (V). Preserve valid zero and signed values;
  do not infer charging direction from an unverified sign convention.
- [ ] During vehicle charging, compare wallbox `powerl1`/`powerl2`/`powerl3` in W
  with local observations. Check plausible magnitudes without a factor-of-1000
  error. Existing total power remains independently sourced; timing differences
  can affect comparison with the phase sum.
- [ ] Home Manager core properties update. With advanced inventory enabled,
  compare assigned devices and available `permanentpowerlimit` observations.
  The live check found three assigned devices, each with register 30233 valid;
  the other 45 delegated observations were SMA NaN, not zero-valued sensors.
- [ ] Invalid/missing readings do not publish literal NaN or fabricated zero.
  Last retained valid values may remain; distinguish fresh updates from retained
  observations and check source availability separately.
- [ ] In openHAB, verify discovery of the new Homie properties, link any desired
  new Items with correct units, and compare fresh updates. Preserve old Item
  names, links, rules, offsets and persistence. Follow the
  [official Homie binding documentation](https://www.openhab.org/addons/bindings/homie/).
- [ ] A controlled service restart preserves state/history, resumes publication
  and sends no unsolicited device commands. Observe overnight sleep and morning
  wake-up separately; abrupt failures and broker/host reboot remain broader
  operational acceptance tasks.

Record observations, timestamp and any mismatches in the acceptance matrix. This
read-only checklist does not require exercising setters or changing device parameters.
