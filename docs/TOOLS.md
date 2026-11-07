# Diagnostic and maintenance tools

The normal Docker setup needs no Python installation on the host. Bridge CLI
checks run inside the image; the other tools below run from a source checkout.
They are optional and do not participate in ordinary device polling.

## Bridge CLI

Run checks against the configured image with:

```sh
docker compose -f compose.example.yml run --rm --no-deps sma-mqtt-bridge --check-config
docker compose -f compose.example.yml run --rm --no-deps sma-mqtt-bridge --check-profile sma-stp8-0-3av-40
```

| Option | Purpose / effect |
| --- | --- |
| `--help` | List supported arguments. |
| `--version` | Report the image's embedded version. For an existing running service, use `docker compose -f compose.example.yml exec -T sma-mqtt-bridge python -m sma_mqtt_bridge --version`. |
| `--check-config` | Validate configuration and local files without device/broker connections; report enabled source count and effective device-write gates. |
| `--check-profile ID` | Validate an inverter profile's schema and polling status; does not establish device/firmware compatibility through a live read. |
| `--check-home-manager-profile ID` | Validate a Home Manager Modbus profile without connecting. |
| `--project-status` | Report static code capabilities; `liveVerified=false` is not a live status check of your installation. |
| `--healthcheck` | Check the local heartbeat and configuration; normally invoked by Docker inside the running service. Use `exec`, not a new one-off container with a different PID namespace. |
| `--refresh-portal` | Start the normal bridge runtime and explicitly request a portal read, including when periodic polling is zero. Requires an enabled portal. Do not start a second runtime against an active state volume; for a running service use the [MQTT refresh channel](CONFIGURATION.md#manual-portal-read-refresh). |
| `--reset-energy-baselines` | Offline recovery action: archive the energy ledger. Stop the service and back up all state first. This deliberately discards accounting continuity on the next startup; never use it to solve a routine setup or freshness problem. |

The default action without a diagnostic option starts the runtime. Diagnostic
checks do not test broker authentication, network reachability or physical device
actions. Native Python calls read process ENV, not `smab.env`.

## Tools for a source checkout

Use Python 3.15, or compatible Python 3.14, for source tools. Prepare `.venv` with
[the building guide](BUILDING.md#native-python-and-offline-tests). The Linux host
resource recorder is separately compatible with Python 3.9+ and needs no third-party
Python packages. All paths below are relative to the repository root.

| Tool | Purpose | Connections / writes |
| --- | --- | --- |
| `tools/build_image.sh` | Build a local image with the checkout version and current base. | Downloads image/dependencies; creates a local image, without deploying or publishing it. |
| `tools/create_release_notes.py` | Generate notes from stable tags/direct commits with versioned setup links. | Local Git reads and an explicit output file only; publication belongs to the release workflow. See [release automation](BUILDING.md#ci-and-image-publication). |
| `tools/export_topic_catalog.py` | Generate `docs/topic-catalog.csv` from bundled profiles/runtime metadata. | Offline; `--check` verifies without replacing the catalog. |
| `tools/export_openhab_widget.py` | Generate all MainUI widget imports under `openHAB/mainui/widgets/`. | Offline; `--check` verifies every UID/file without replacing imports. |
| `tests/compose_check.py` | Verify standalone Compose runtime parity, host networking and overrides. | Requires Docker Compose; renders public examples without starting services or reading private ENV settings. |
| `tests/resource_soak.py` | Bounded CPU/memory/I/O sampling on the Linux Docker host. | Reads local Docker/process/cgroup data; creates a new JSONL file. Does not connect to SMA or MQTT. |
| `tests/runtime_benchmark.py` | Synthetic publication/heartbeat CPU comparison. | Offline; temporary state only. Not a measurement of actual device polling or production resource usage. |
| `tests/inventory_things.py` | Extract supported Modbus mappings from local openHAB `.things` files. | Offline; writes an inventory, without generating an authorized polling profile or changing openHAB. |
| `tools/influx2_copy_item.py` | Generate reviewable Flux for one InfluxDB 2 Item measurement. | Offline query generation only; it never executes a database request. Generated copy queries write only if you separately execute them. |

The catalog and widget exporters are maintenance tools: they generate public
documentation/import artifacts and therefore live under `tools/`. Tests reuse them
to verify those artifacts remain current.

The `tests/` location includes reusable diagnostic helpers as well as the regression
suite. Keep them available when collecting evidence; they are not installed in the
runtime image.

### Check generated files

```sh
.venv/bin/python tools/export_topic_catalog.py --check
.venv/bin/python tools/export_openhab_widget.py --check
.venv/bin/python tests/compose_check.py
```

Omit `--check` only when intentionally regenerating a catalog/import. Edit widget
sources under `openHAB/yaml/widgets/`; the generated import is a deployment alternative.

### Record host resource use

Run on the **Linux Docker host**, from the Compose project directory, with permission
to inspect Docker and `/proc`:

```sh
python3 tests/resource_soak.py --compose-file compose.example.yml \
  --duration-seconds 600 --interval-seconds 10 \
  --output smab-resource-soak-review.jsonl
```

The output path must not exist. Duration is 1–86400 seconds; interval is 1–3600
seconds. Default duration/interval are 86400/60 seconds. Missing host/cgroup metrics
remain null; they are not zero. CPU percentages refer to one core. Process RSS is
not the entire container memory or Python heap. Changing process/container identity
invalidates continuity-dependent rates. Review output privately before sharing.

### Inspect an existing Modbus Things file

```sh
mkdir -p private/diagnostics
.venv/bin/python tests/inventory_things.py /path/to/inverters.things \
  --output private/diagnostics/modbus-inventory.json
```

This accepts only its documented subset: `inverter<N>` TCP bridges, input-register
pollers, int32/uint32 channels and recognized transforms. Unsupported syntax fails
for manual review; it does not silently drop unsupported channels. Addresses and
free-text labels are omitted, but mapping IDs can still identify an installation.
The output is migration evidence, not proof of model, units or firmware support.
Keep original files and current Items/rules/history intact while comparing sources.

### Preview an InfluxDB 2 Item copy

```sh
.venv/bin/python tools/influx2_copy_item.py \
  --bucket history --org home --old Old_Item --new New_Item \
  --start 2026-01-01T00:00:00Z --stop 2026-02-01T00:00:00Z \
  > private/diagnostics/item-preview.flux
```

Create `private/diagnostics/` first if needed. Preview is the default and contains
read-only counts/first/last queries. Time bounds must be explicit UTC; stop is
exclusive. It assumes the default openHAB measurement = Item-name layout and an
optional matching `item` tag. Custom persistence mappings require manual review.

`--mode copy` generates a query guarded against a populated target interval,
an empty source and unexpected item tags. It preserves source data and does not
convert units or merge overlapping series. Before separately executing any copy,
back up the database, verify layout/units and review preview results. Compare
counts/timestamps/values afterwards. This tool is not an automated migration service.
See [openHAB InfluxDB persistence](https://www.openhab.org/addons/persistence/influxdb/).

## Temporary runtime recorders

The [plant frame recorder](CONFIGURATION.md#joint-power-and-status-recorder) and
[eCharger timestamp recorder](CONFIGURATION.md#temporary-echarger-timestamp-observation)
observe already acquired data. They are disabled by default, rotate bounded files
in the state volume and add no device reads. Enable them only for an investigation,
copy the relevant files promptly and disable recording afterwards. Their output
is private diagnostic evidence, not required setup configuration.
