# Inverter profiles

> Current MQTT node/property IDs remove hyphens at the publication boundary. Internal profile and
> readiness keys keep their spelling; historical examples below may use the former IDs. See
> [compact IDs and display translations](CONFIGURATION.md#display-language-and-compact-channel-ids).

The public JSON files under `ressources/profiles/` are packaged directly in the Docker image. They contain no installation addresses, serial numbers or credentials. **The three supplied profiles cover the original 41 read channels plus 22 selected additional measurement channels**, checked against official model-specific SMA lists and local model/firmware/serial reads. See [register validation](REGISTER_VALIDATION.md) for units, type corrections, source hashes and remaining parallel acceptance.

| Profile ID | Model | Observed firmware | Default slot |
| --- | --- | --- | --- |
| `sma-stp8-0-3av-40` | STP8.0-3AV-40 | 4.10.10.R | inverter1 |
| `sma-sbs3-7-10` | SBS3.7-10 | 4.07.31.R | inverter2 |
| `sma-sb4-0-1av-41` | SB4.0-1AV-41 | 4.10.10.R | inverter3 |

Select an ID through `SMAB_INVERTER<N>_PROFILE` or the inverter's JSON `profile` field. A profile belongs to a model, not a slot; the same model can be selected for multiple independently configured devices. An observed firmware version is evidence of installed hardware, not a compatibility guarantee.

The Docker image packages these defaults as resources. For a bare profile ID, resolve `<id>.json` in the host profile directory first, then the bundled resource directory. A malformed or incompatible host override is an error; do not fall back silently. Require the file's `id` to match its selected ID. Use `file:custom-name.json` to select only a file in the host profile directory, without bundled fallback. Reject absolute paths and traversal outside that directory. Additional slots have no default model and require explicit selection.

Custom installation files belong under `./data/sma-mqtt-bridge/profiles/`. Future reusable, sanitized model profiles can be added under `ressources/profiles/`. The loader/adapter must use profile data rather than model-specific branches, so adding a supported model needs no new adapter implementation.

The schema separates device identity, protocol defaults, evidence/validation, pollers, property definitions and command allowlists. When completing it, describe register functions and zero-based addresses, lengths, data types, word/byte order, scaling, units, invalid sentinels, source channels, per-poller intervals and Homie metadata. Keep installation connection overrides separate from model defaults. Define the final schema and validate it in Python before using profiles.

The original descriptors were `identity-only`; unsupported new descriptors must still have empty mappings and remain blocked. The supplied profiles are now `validated` for the explicitly listed locally checked firmware. A Sunny Boy -40 document alone never validates a -41, Tripower or Storage model. Full openHAB acceptance remains separate from profile validation.

See [the configuration contract](CONFIGURATION.md), [the value catalogue](WERTEKATALOG.md) and [migration requirements](MIGRATION.md).

## Existing Things evidence

[The sanitized inventory](../reference/inverter-things-inventory.json) is derived from the user's two existing Things exports: 14/11/16 active channels across 6/7/6 pollers. It preserves FC04 ranges, zero-based addresses/offsets, signed/unsigned decoding, JS transform references and original 3–180 second intervals. Addresses, labels, credentials and device serials are excluded. Reproduce it locally with:

```sh
.venv/bin/python tests/inventory_things.py private/things/sma.things private/things/sma-sunnyboy.things --output reference/inverter-things-inventory.json
```

This deliberately narrow importer rejects unsupported syntax, write mappings, unknown transforms, duplicate definitions and out-of-range values rather than silently dropping them. It performs no network access and does not rewrite private originals. `migration-evidence-only` is not a runtime profile status; the profile loader rejects the inventory. The reconciliation is now recorded in REGISTER_VALIDATION.md; the original evidence keeps the original signed types and transforms rather than being rewritten as runtime definitions. Do not infer units or scaling solely from Item labels.

## Version 1 polling schema

The loader rejects unknown fields and non-standard JSON numbers. Required top-level fields: `schemaVersion` (integer 1), `id`, `device`, `protocol`, `validation`, `pollers`, `properties`, `commands`. `identity` is additionally required for a validated polling profile.

| Object | Fields and rules |
| --- | --- |
| `device` | `manufacturer` = `SMA`; nonempty `models` list; `observedFirmware` list; `supportedFirmware` nonempty list for validated profiles. Observations alone do not approve firmware. |
| `protocol` | `type` = `modbus-tcp`, `addressing` = `zero-based`; `defaults.port` 1–65535, `unitId` 1–247; optional positive `pollIntervalSeconds`, `timeoutSeconds`, `staleSeconds`. |
| `validation` | `status` is `identity-only` or `validated`; nonempty `reason`; `evidence` required for validated profiles. |
| `identity` | `model`, `firmware`, `serial` reference defined property IDs. Identity blocks are read and checked before measurement blocks on each TCP session. |
| `pollers[]` | Unique `id`, read `function` 3 or 4, `start` 0–65535, `count` 1–125 with no address overflow; optional positive `intervalSeconds`. |
| `properties[]` | Unique `id`, Homie `node`, `name`, `poller` reference, register `offset`, `length`, `type`, explicit `byteOrder`/`wordOrder`, finite `scale`, `unit`, raw `invalid` list, Homie `datatype`; optional `valueMap`, `minimum`, `maximum`, `format`, `channelGroup`, boolean `requiredForReady`. |
| `commands` | Must be empty; inverter write paths are not implemented. |

Register types: `uint16`, `int16`, `uint32`, `int32`, `uint64`, `int64`, `float32`, `string`. Numeric lengths must match the type; ASCII strings use their explicit register length. Order is `big` or `little`. Homie datatypes are `integer`, `float`, `string`, `boolean`, `enum`; enums/booleans require `valueMap`; boolean map values are `true`/`false`. Unknown enum codes are unavailable, never guessed. Maps can preserve existing openHAB status strings. Sentinel checks precede mapping/scaling; floating-point NaN is always unavailable. Bounds apply to scaled numbers.

The identity gate compares decoded model and firmware against the profile and optionally serial against `EXPECTED_SERIAL`. Define model maps and firmware encoding from verified register evidence. `format=sma-firmware` requires U32, string datatype, scale 1 and no value map: it decodes BCD major/minor, binary build and release type. Malformed BCD is unavailable. No universal identification registers are invented. Identity-only profiles must have empty mapping arrays. Merely changing their status fails validation.

Profile poller intervals are preserved unless an installation-level JSON/ENV interval was explicitly set. Scheduling uses each poller's next deadline. The supplied profiles preserve existing 3-/5-second cycles and all slower pollers; a generic fallback of 10 seconds does not override them. Properties expire after the larger of the configured stale threshold and twice their effective polling interval.

Host filenames use lowercase letters, digits and internal hyphens followed by `.json`; IDs follow the same name without the extension. Symlink files, absolute selectors and directory traversal are rejected. A custom `file:` filename may differ from the internal profile ID. The synthetic profile in `tests/helpers.py` documents executable schema usage and is **not a device profile**.

## Home Manager Modbus read profile

The separate `sma-home-manager-2-modbus` profile uses `kind=home-manager-modbus-read` and is selected with `SMAB_HOME_MANAGER_PROFILE`. It shares the register decoder/mapping validation with inverter profiles, but has an explicit Unit 1 identity gate instead of inventing a firmware register. It cannot be loaded as an inverter profile. Host overrides and `file:` selection follow the same path restrictions.

Its schema has `schemaVersion`, `id`, `kind`, `evidence`, `identity`, `pollers`, `properties`, `inventory`, `delegated`, and empty `commands`. Core pollers require `unitId` 1 or 2. `identity` references five distinct unscaled U32 properties on Unit 1: `model`, `serial`, `serialCopy`, `deviceClass`, `manufacturer`. The adapter checks model 9343, class 8128, manufacturer 461 and both serial registers against the configured serial before any plant or assignment reads. There is no claimed firmware validation or hardware acceptance.

`inventory` defines the assignment table start, number of four-register slots (at most 245), and positive `intervalSeconds`. `delegated` holds reusable poller/property templates without a fixed unit ID. Only assigned units 3–247 are queried, using the freshly read table; duplicate units follow SMA's first-slot rule. Both mapping sections use the documented numeric/enum/scaling/sentinel rules above. Unit 2 intervals can be explicitly overridden; identity, inventory and delegated intervals remain profile-defined. All mappings are read-only, including source registers documented RW. See [coverage and acceptance](HOME_MANAGER_MODBUS.md).

## Plant contribution mappings

An optional inverter-profile `plant` object supplies model-independent semantic
references for explicit configured roles. Existing profiles without it remain
usable with role `none`; participating roles require complete enabled mappings.
No device activation, role or physical measurement boundary is inferred from
the profile's model name.

```json
{
  "evidence": "Reference establishing these AC PV contributions",
  "pv": {
    "activepower": "measurements/active-power",
    "dayyield": "measurements/day-yield",
    "totalyield": "measurements/total-yield"
  }
}
```

`pv` requires the three fields above, in W/kWh/kWh respectively. `battery`
requires `presbatcharge`, `presbattdischarge`, `batterychargeenergy`,
`batterydischargeenergy` references in W/W/kWh/kWh, plus `energyBoundary` of
`unverified`, `ac` or `dc`. A confirmed `ac`/`dc` boundary requires nonempty
`energyEvidence`. The bundled SBS references the existing four battery properties
and declares the boundary `ac`, with the observed installation's
[charge/discharge comparison](BATTERY_ENERGY_BOUNDARY_2026-10-15.md) as energy evidence.
A property name/unit alone does not prove AC. House energy uses confirmed compatible
AC storage counters, no storage, or the explicit provisional override for other
unverified mappings. Host overrides must carry their own matching declaration/evidence.

Optional `grid` requires distinct `powerimport`, `powerexport`, `energyimport`,
`energyexport` references in W/W/kWh/kWh. Select that inverter explicitly as the
single plant grid source. Home Manager's existing four meter properties are
selected through `gridSource=home-manager` instead. Directional flows and all
energy counters must be nonnegative; signed PV AC power is preserved.

Every reference names an existing numeric `node/property`, with matching unit.
Unknown, duplicate, overlapping and filtered selected references fail before
connections. `hybridSeparated=true` additionally requires both PV and battery
groups with distinct independently verified contributions. Do not map a hybrid's
combined AC output as PV and add its battery output again. Host files provide
new mappings without model-specific adapter code; no new register read is added
by a contribution reference alone. See [plant configuration](CONFIGURATION.md#plant-aggregates-and-energy-state).

## Channel groups

`requiredForReady=true` marks a critical fresh value for source availability. All enabled marked
properties must be fresh for `ready`; slow metadata and optional readings cannot mask stale critical
measurements. No marks means all enabled `measurements/` properties. Installation `READY_PROPERTIES`
overrides replace this selection without changing register decoding or write rights. See
[critical freshness](CONFIGURATION.md#critical-freshness-and-diagnostics).

A property may specify `channelGroup`: `basic`, `advanced`, or `diagnostics`. Unknown groups fail
validation. Without an explicit group, `identity` and `parameters` nodes are advanced, `diagnostics`
nodes are diagnostics, and other nodes are basic. Device ENV flags select these groups before
polling and decoding; mandatory identity checks always use the complete profile. Shared register
blocks still serve enabled properties. Bundled inverter internal-temperature readings are explicitly tagged
`basic` and remain enabled with either filter disabled; Sunny Boy type/max-power/set-max-power are tagged `advanced`. Default flags enable
every existing channel. See [channel configuration](CONFIGURATION.md#optional-channel-groups).

## Explicit Sunny Boy L2/L3 channels

The Sunny Boy profile additionally provides measurements/powerl2, powerl3, voltg2,
voltg3, currentl2 and currentl3. See the
[register extension](REGISTER_VALIDATION.md#sunny-boy-l2l3-profile-extension-2026-10-12)
for units, scaling and polling. Existing L1 mappings are preserved. Inactive-phase
NaN yields no new MQTT measurement; the last valid retained observation, if any,
remains under the usual retention rules. The source status property remains the
readiness criterion; these new phase measurements are not required for ready.

The packaged extension follows the existing phase-channel basic default. General
channel-group review remains future work. Host profile overrides take precedence:
update a host copy explicitly if one is selected; a rebuilt image cannot replace
that copy. No new environment setting is needed and existing explicit poll-interval
overrides continue to apply to all profile blocks. Rebuild/recreate the bridge to
load the bundled extension. Production publication and openHAB links require a
separate installation check; no running service or instance was changed here.

## Type/limits, frequency and selected AC/battery measurements

Tripower and Storage now additionally publish measurements/type, maxpower and
setmaxpower, using the existing Sunny Boy advanced-group convention. All three
provide measurements/frequency. Tripower adds currentl1/currentl2/currentl3;
Storage adds currentl1, activepower, batterycurrent and batteryvoltage. These new
measurements use the basic default. See the
[complete extension table](REGISTER_VALIDATION.md#small-inverter-measurement-extension-2026-10-12)
for addresses, units, intervals, source evidence and acceptance limits.
No new configuration switch or setter is introduced; host override precedence,
explicit interval overrides and required status-based readiness remain unchanged.

## Selected counter and diagnostic properties

The three bundled inverter profiles add advanced `operating-time` and
`feed-in-time` measurements in seconds, plus basic `derating-reason` under the unchanged
`diagnostics` node. Since 2026-10-13 it remains available with both optional
groups disabled; a node name does not determine the explicit channel group.
The Storage profile adds basic `battery-charge-energy` and
`battery-discharge-energy` in kWh (source Wh divided by 1000). Existing yield and
status blocks retain their intervals; Storage energy uses a separate 60-second
eight-register FC04 block. All properties are optional, read-only and group
filtered. Host profile overrides must incorporate the mappings explicitly. See
[register evidence](REGISTER_VALIDATION.md#selected-counters-and-derating-extension-2026-10-12).

## Unix seconds as ISO text

`format: unix-time-iso` converts an unscaled uint32 value to an ISO 8601 UTC
string with whole seconds and `Z`. It requires datatype string, scale 1, an empty
unit, and no valueMap/minimum/maximum. Explicit raw invalid sentinels are applied
before conversion. The Home Manager profile uses it for an additional Basic
plant-time-iso mapping alongside Advanced raw plant-time, without another poll.
