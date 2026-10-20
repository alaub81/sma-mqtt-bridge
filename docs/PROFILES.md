# Inverter profiles

The JSON files under `ressources/profiles/` contain reusable protocol mappings,
not installation addresses, credentials or serials. Supported firmware and
identity constraints are declared in each file. Select a profile matching the
actual device; related model names do not establish compatibility.

| Profile ID | Model |
| --- | --- |
| `sma-stp8-0-3av-40` | STP8.0-3AV-40 |
| `sma-sbs3-7-10` | SBS3.7-10 |
| `sma-sb4-0-1av-41` | SB4.0-1AV-41 |

Select an ID through `SMAB_INVERTER<N>_PROFILE` or the inverter's JSON `profile` field. A profile belongs to a model, not a slot; the same model can be selected for multiple independently configured devices. An observed firmware version is evidence of installed hardware, not a compatibility guarantee.

The Docker image packages these defaults as resources. For a bare profile ID, resolve `<id>.json` in the host profile directory first, then the bundled resource directory. A malformed or incompatible host override is an error; do not fall back silently. Require the file's `id` to match its selected ID. Use `file:custom-name.json` to select only a file in the host profile directory, without bundled fallback. Reject absolute paths and traversal outside that directory. Additional slots have no default model and require explicit selection.

Custom installation files belong under `./data/sma-mqtt-bridge/profiles/`. Future reusable, sanitized model profiles can be added under `ressources/profiles/`. The loader/adapter must use profile data rather than model-specific branches, so adding a supported model needs no new adapter implementation.

The schema separates device identity, protocol defaults, evidence/validation, pollers, property definitions and command allowlists. It declares register functions and zero-based addresses, lengths, data types, word/byte order, scaling, units, invalid sentinels, source channels, per-poller intervals and Homie metadata. Keep installation connection overrides separate from model defaults. Profiles are validated before device access.

Profiles with `validation.status=identity-only` are blocked for polling. Validated
profiles require complete mappings and supported firmware constraints. A profile's
read mapping does not authorize inverter writes.

See [configuration](CONFIGURATION.md) and the [topic catalog](topic-catalog.csv).

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

`inventory` defines the assignment table start, number of four-register slots (at most 245), and positive `intervalSeconds`. `delegated` holds reusable poller/property templates without a fixed unit ID. Only assigned units 3–247 are queried, using the freshly read table; duplicate units follow SMA's first-slot rule. Both mapping sections use the documented numeric/enum/scaling/sentinel rules above. Unit 2 intervals can be explicitly overridden; identity, inventory and delegated intervals remain profile-defined. All mappings are read-only, including source registers documented RW. See [Home Manager reads](HOME_MANAGER_MODBUS.md).

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
and declares the boundary `ac`. Installation-specific source comparisons remain private;
the profile declares the physical boundary used by household accounting.
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
validation. All bundled mappings declare it explicitly; the offline suite checks new declarations.
Legacy host profiles remain compatible: without an explicit group, `identity` and `parameters` nodes are advanced, `diagnostics`
nodes are diagnostics, and other nodes are basic. Device ENV flags select these groups before
polling and decoding; mandatory identity checks always use the complete profile. Shared register
blocks still serve enabled properties. Bundled inverter internal-temperature readings are explicitly tagged
`basic` and remain enabled with either filter disabled; Sunny Boy type/max-power/set-max-power are tagged `advanced`. Default flags publish Basic channels; Advanced and optional Diagnostics require explicit activation. See [channel configuration](CONFIGURATION.md#optional-channel-groups).

## Model-specific properties

The [topic catalog](topic-catalog.csv) lists the properties supplied by each bundled
profile. Unsupported or inactive phases can remain unavailable; profile selection
does not establish wiring. SMA invalid sentinels do not become numeric observations
unless the profile explicitly declares one of the compatibility rules below.
Properties have independent units, groups and readiness requirements. Host profile
overrides take precedence over bundled files and require explicit maintenance.

## Unix seconds as ISO text

`format: unix-time-iso` converts an unscaled uint32 value to an ISO 8601 UTC
string with whole seconds and `Z`. It requires datatype string, scale 1, an empty
unit, and no valueMap/minimum/maximum. Explicit raw invalid sentinels are applied
before conversion. The Home Manager profile uses it for an additional Basic
plant-time-iso mapping alongside Advanced raw plant-time, without another poll.

## Explicit PV power sentinel compatibility

The bundled STP8 and SB4 profiles set `invalidAsZero: true` on active power
(register 30775). A successfully read raw int32 SMA sentinel `-2147483648` is
normalized to 0 W before publication and plant calculations. Other negative numeric readings
are preserved. This is an explicit compatibility rule, not inferred standby: the
status code 307 means OK and does not prove standby. No zero is generated for a
failed read, truncated response, identity mismatch or expired observation.

The optional boolean defaults to false. It is accepted only for numeric, unscaled
int32 power in W with the sole invalid sentinel `-2147483648` and no value map or
format. Energy counters, battery measurements and other invalid values retain
their existing behavior. Host profile overrides must carry this property explicitly;
updating only the container does not change an overriding profile file.

### Conditional DC current and power compatibility

The PV profiles additionally use `invalidAsZeroWhen` for DC input A current/power
and, on STP8 only, input B current/power. This optional map names other property
IDs and lists their accepted decoded values. All guards must match fresh reads
on the same identity-verified connection. Guard blocks are read even when their
normal publication interval is not due; cached MQTT/source values are never used.

The bundled guards require active AC power 0 W and condition `Ok (Ok)`. The AC
value includes the existing explicit 30775 sentinel compatibility. This is an
inferred no-production compatibility rule, not an independently measured DC zero
or a confirmed operating-status code. Operating-status register 40029 is not used as a gate; unavailable data does not
prove an operating mode.
Only a successfully read DC S32 sentinel is replaced. Other signed values remain
unchanged, and positive AC production, invalid guards, warning/fault status or
failed reads do not generate DC zeroes. DC voltages and inactive AC phases retain
unavailable handling.

Conditional zero is restricted to numeric int32 W at scale 1 or A at scale 0.001,
the sole sentinel -2147483648, bounds including zero, and no map/format or
unconditional zero option. References must exist, cannot refer to the same
property or another conditional rule, and must contain nonempty value lists.
Both power/current compatibility options are excluded from cumulative-energy
binding identity; counter definitions and other profile metadata remain protected.

## Default plant role

Enabled inverter profiles with exactly one PV or battery contribution supply that plant role
by default. An explicit JSON/ENV role overrides it, including `none`. Ambiguous profiles
require an explicit role; disabled adapters do not load profile files. Existing contribution
mappings and accounting fingerprints are preserved. No device is activated by its profile.
