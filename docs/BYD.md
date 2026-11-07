# BYD Battery-Box monitoring

The optional BYD adapter reads a Battery-Box directly over its LAN connection
and publishes a separate Homie 4 device. SMA inverter measurements and existing
plant energy accounting keep their existing ownership and physical boundaries.

## Supported read profile

The bundled `byd-hvs-4` profile supports one HVS tower with four modules,
128 cells and 48 temperature sensors, BMU firmware 3.16, active BMS firmware
3.24 and parameter table 9.2. Other models, topologies and active firmware
versions fail identity validation before measurement acceptance. This does not
provide general HVS/HVM or BCU-version compatibility.
Both BMU firmware banks must agree, because selecting an active BMU bank from
the reported raw bank code is not part of this validated layout.

BYD's local service protocol is RTU framing over TCP, normally on port 8080.
The bridge checks unit, function, response size and CRC. Cell and event reads
use fixed, allowlisted diagnostic buffer selectors, followed by readiness
readback and bounded page reads. These selectors do not change charging
parameters. There are no BYD Homie setters, firmware updates or charging commands.
No diagnostic selector is immediately retried after an uncertain response.

The protocol interpretation is based on the
[SmartHomeNG implementation](https://github.com/smarthomeNG/plugins/blob/develop/byd_bat/__init__.py)
and an [independent BYD implementation](https://github.com/redpomodoro/byd_battery_box/blob/main/custom_components/byd_battery_box/bydboxclient.py).
This is not an official, stable BYD monitoring API. Confirm compatibility before
updating battery firmware. Offline tests do not establish full installation,
broker, fault-transition or openHAB acceptance.

## Configuration

Add only the required overrides to the private root `smab.env`:

```dotenv
SMAB_BYD_ENABLED=true
SMAB_BYD_HOST=battery.example.invalid
```

The broker must also be configured as described in [Configuration](CONFIGURATION.md).
Every BYD setting has an ENV override under `SMAB_BYD_`; optional JSON uses the
`byd` section and camelCase names. Built-in defaults precede JSON and explicit ENV.
An address or serial alone never enables the adapter. Disabled adapters do no I/O.
The configured profile is loaded only for an enabled adapter.

| Suffix after `SMAB_BYD_` | Typed default | Meaning |
| --- | --- | --- |
| `ENABLED` | boolean `false` | Explicit adapter activation |
| `PAUSED` | boolean `false` | Pause all BYD I/O for service access |
| `HOST` | string, empty | Required address when enabled |
| `PORT`, `UNIT_ID` | integers `8080`, `1` | Port 1–65535, protocol unit 1–247 |
| `PROFILE` | string `byd-hvs-4` | Validated BYD profile selector |
| `EXPECTED_SERIAL` | string, empty | Optional additional exact identity guard |
| `HOMIE_ID` | string `byd-battery` | Unique independent device ID |
| `ADVANCED_CHANNELS_ENABLED` | boolean `false` | Technical identity and detail summaries |
| `DIAGNOSTICS_ENABLED` | boolean `false` | Individual values, events and troubleshooting |
| `READY_PROPERTIES` | string, empty | Optional unique comma-separated enabled node/property keys |
| `POLL_INTERVAL_SECONDS` | number `60` | Basic interval, minimum 30 s |
| `DETAIL_POLL_INTERVAL_SECONDS` | number `300` | Detail interval, minimum 60 s |
| `LOG_POLL_INTERVAL_SECONDS` | number `300` | Event interval, minimum 60 s |
| `TIMEOUT_SECONDS` | number `5` | Positive connection/frame/close timeout |
| `BUFFER_READY_TIMEOUT_SECONDS` | number `8` | Positive readiness deadline, maximum 60 s |
| `BUFFER_POLL_INTERVAL_SECONDS` | number `0.3` | Readiness pacing, minimum 0.1 s, no greater than the deadline |
| `STALE_SECONDS` | number `180` | Basic lifetime, at least the basic interval |
| `DETAIL_STALE_SECONDS` | number `900` | Detail lifetime, at least the detail interval |
| `LOG_STALE_SECONDS` | number `900` | Event lifetime, at least the event interval |

Profile resolution checks `<id>.json` in `SMAB_PROFILE_DIR` before the bundled
`ressources/profiles/` resource. BYD, inverter and Home Manager files share this
directory but retain their adapter-specific schemas and identity checks. Invalid overrides fail without fallback.
`file:name.json` selects only a host file. Path traversal and absolute selectors
are rejected. Layout 1 supports the fixed HVS cell/sensor arrangement for up to
128 cells; only the four-module profile is bundled. A host profile must declare
validated mapping evidence and explicit compatible firmware/table versions.
Identity-only profiles cannot authorize reads.

The connection closes after each acquisition. BYD accepts only one diagnostic
client at a time; pause this adapter before using Be Connect, and resume after
service. Recreate the container to apply changed ENV, including `PAUSED`.
Pausing does not renew sample ages or publish fabricated zero measurements.

## Topics and independent filters

The default root is `homie/byd-battery/`. Homie nodes map to openHAB Channel
Groups through the [official Homie binding](https://www.openhab.org/addons/bindings/homie/).
Every property is read-only. The generated [topic catalog](topic-catalog.csv)
contains all property suffixes, units and classifications.

| Advanced | Diagnostics | Property count with the bundled profile |
| --- | --- | --- |
| off | off | 16 Basic |
| on | off | 93: Basic + 77 Advanced |
| off | on | 394: Basic + 378 Diagnostics |
| on | on | 471 total |

Counts include source-supervision properties while running, but exclude Homie
discovery metadata. Operational `diagnostics/bydstatus` always remains Basic.
Mandatory identity checks are internal regardless of publication filters.

- Basic: SOC/SOH, voltage, output voltage, current, calculated signed/DC
  directional powers, inferred charging/discharging/idle state, temperatures,
  battery-side energy counters and the reported BMU condition.
- Advanced: identity, versions, topology, model-derived nominal energy,
  finer BMS SOC/counters, tower summaries and ten summary properties per module.
- Diagnostics: individual `tower1module<M>/cell<NN>voltage` and
  `cell<NN>balancing`, twelve `temperature<NN>` properties per module,
  comparison fields, raw/decoded error and warning fields, bounded recent events
  and acquisition diagnostics. Advanced is not required for Diagnostics.

Basic-only mode does not acquire cell or event buffers. Either optional filter
can require the shared detail buffer; only Diagnostics requires event reads.
Each returned block retains its own monotonic receipt time and lifetime. Repeated
basic reads do not refresh older details. Failed optional reads invalidate their
affected group; base readiness still depends on fresh configured critical basic
readings. Other optional groups keep their existing ages. Detailed receive-time
properties expire independently; failure/timeout metrics describe the supervised
base cycle. Inspect the log for optional acquisition failures.

## Interpretation and limits

Signed current/power are positive for discharge. Power is calculated from current
and output voltage, not measured AC power. The basic state is inferred from the
reported current direction, not a complete BMS operating-mode decoder.
SOH is a battery-reported value, not an independently measured capacity.

BMU energy counters have 100 Wh resolution, BMS tower counters 1 Wh. Both use
low-word-first encoding and publish kWh. They are battery-side counters;
do not substitute them for SMA AC counters or sum both into plant balances.
Long-term reset/overflow behavior and physical calibration require installation
verification. No new daily-account baseline or persisted plant state is created.

Array-derived cell/temperature extrema and separately reported header extrema
are distinct properties because acquisition times and internal rounding differ.
Cell numbers are 1-based protocol indices, not a verified physical location map.
Temperature index/switch/bank raw fields have no promised physical interpretation.
Balancing and fault bit meanings follow the references; no forced fault or active
balancing test is implied by the existence of these properties.

`events/bmuentry01` through `bmuentry20` and `tower1entry01` through
`tower1entry20` hold the latest fetched window, newest first, as bounded JSON
strings. Unused slots contain JSON `null`. Known observed payload classes include
historical limits, state changes, warning/fault snapshots and balancing records;
other payloads preserve code and bounded raw data without invented meanings.
Event values apply to the event time, including any reported charging limits.
Device-local time has no assumed UTC offset. Receipt times use UTC separately.
This window is not a full event archive or a lifetime cycle counter.

Retained values remain last-known observations; always check availability and
freshness. Preserve the state volume/topic manifest when changing filters so
previously owned optional topics are retired normally. The adapter does not
publish remaining-energy estimates, unsupported cycle counts, a claimed system
efficiency, current calibration state or live limits inferred from old events.
