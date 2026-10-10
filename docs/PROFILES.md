# Inverter profiles

The public JSON files under `ressources/profiles/` define the version-1 profile format used by the Python loader. They contain no installation addresses, serial numbers or credentials. **They are model descriptors, not validated polling profiles.** The Python loader validates them but rejects them for enabled polling.

| Profile ID | Model | Observed firmware | Default slot |
| --- | --- | --- | --- |
| `sma-stp8-0-3av-40` | STP8.0-3AV-40 | 4.10.10.R | inverter1 |
| `sma-sbs3-7-10` | SBS3.7-10 | 4.07.31.R | inverter2 |
| `sma-sb4-0-1av-41` | SB4.0-1AV-41 | 4.10.10.R | inverter3 |

Select an ID through `SMAB_INVERTER<N>_PROFILE` or the inverter's JSON `profile` field. A profile belongs to a model, not a slot; the same model can be selected for multiple independently configured devices. An observed firmware version is evidence of installed hardware, not a compatibility guarantee.

The Docker image packages these defaults as resources. For a bare profile ID, resolve `<id>.json` in the host profile directory first, then the bundled resource directory. A malformed or incompatible host override is an error; do not fall back silently. Require the file's `id` to match its selected ID. Use `file:custom-name.json` to select only a file in the host profile directory, without bundled fallback. Reject absolute paths and traversal outside that directory. Additional slots have no default model and require explicit selection.

Custom installation files belong under `./data/sma-mqtt-bridge/profiles/`. Future reusable, sanitized model profiles can be added under `ressources/profiles/`. The loader/adapter must use profile data rather than model-specific branches, so adding a supported model needs no new adapter implementation.

The schema separates device identity, protocol defaults, evidence/validation, pollers, property definitions and command allowlists. When completing it, describe register functions and zero-based addresses, lengths, data types, word/byte order, scaling, units, invalid sentinels, source channels, per-poller intervals and Homie metadata. Keep installation connection overrides separate from model defaults. Define the final schema and validate it in Python before using profiles.

All initial descriptors have `validation.status=identity-only` and empty poller/property/command arrays. The loader must reject them for normal polling until confirmed register definitions are added and the status is explicitly changed to `validated` after offline verification. Do not assume that a Sunny Boy -40 register document validates a -41, Tripower or Storage model. Preserve existing mappings as migration evidence while reconciling their types and units.

See [the configuration contract](CONFIGURATION.md), [the value catalogue](WERTEKATALOG.md) and [migration requirements](MIGRATION.md).

## Version 1 polling schema

The loader rejects unknown fields and non-standard JSON numbers. Required top-level fields: `schemaVersion` (integer 1), `id`, `device`, `protocol`, `validation`, `pollers`, `properties`, `commands`. `identity` is additionally required for a validated polling profile.

| Object | Fields and rules |
| --- | --- |
| `device` | `manufacturer` = `SMA`; nonempty `models` list; `observedFirmware` list; `supportedFirmware` nonempty list for validated profiles. Observations alone do not approve firmware. |
| `protocol` | `type` = `modbus-tcp`, `addressing` = `zero-based`; `defaults.port` 1–65535, `unitId` 1–247; optional positive `pollIntervalSeconds`, `timeoutSeconds`, `staleSeconds`. |
| `validation` | `status` is `identity-only` or `validated`; nonempty `reason`; `evidence` required for validated profiles. |
| `identity` | `model`, `firmware`, `serial` reference defined property IDs. Identity blocks are read and checked before measurement blocks on each TCP session. |
| `pollers[]` | Unique `id`, read `function` 3 or 4, `start` 0–65535, `count` 1–125 with no address overflow; optional positive `intervalSeconds`. |
| `properties[]` | Unique `id`, Homie `node`, `name`, `poller` reference, register `offset`, `length`, `type`, explicit `byteOrder`/`wordOrder`, finite `scale`, `unit`, raw `invalid` list, Homie `datatype`; optional `valueMap`, `minimum`, `maximum`. |
| `commands` | Must be empty in the read-only runtime. |

Register types: `uint16`, `int16`, `uint32`, `int32`, `uint64`, `int64`, `float32`, `string`. Numeric lengths must match the type; ASCII strings use their explicit register length. Order is `big` or `little`. Homie datatypes are `integer`, `float`, `string`, `boolean`, `enum`; enums/booleans require `valueMap`; boolean map values are `true`/`false`. Unknown enum codes are unavailable, never guessed. Maps can preserve existing openHAB status strings. Sentinel checks precede mapping/scaling; floating-point NaN is always unavailable. Bounds apply to scaled numbers.

The identity gate compares decoded model and firmware against the profile and optionally serial against `EXPECTED_SERIAL`. Define model/firmware maps from verified register evidence. No universal identification registers are invented. Identity-only profiles must have empty mapping arrays. Merely changing their status fails validation.

Profile poller intervals are preserved unless an installation-level JSON/ENV interval was explicitly set. Scheduling uses each poller's next deadline. Existing 3-/5-second cycles remain inventory obligations pending manufacturer validation; a generic fallback of 10 seconds does not override them.

Host filenames use lowercase letters, digits and internal hyphens followed by `.json`; IDs follow the same name without the extension. Symlink files, absolute selectors and directory traversal are rejected. A custom `file:` filename may differ from the internal profile ID. The synthetic profile in `tests/helpers.py` documents executable schema usage and is **not a device profile**.
