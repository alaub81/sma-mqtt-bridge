# Inverter profiles

These public JSON files define the starting profile format for the future Python loader. They contain no installation addresses, serial numbers or credentials. **They are model descriptors, not validated polling profiles.** The current diagnostic executable does not load them.

| Profile ID | Model | Observed firmware | Default slot |
| --- | --- | --- | --- |
| `sma-stp8-0-3av-40` | STP8.0-3AV-40 | 4.10.10.R | inverter1 |
| `sma-sbs3-7-10` | SBS3.7-10 | 4.07.31.R | inverter2 |
| `sma-sb4-0-1av-41` | SB4.0-1AV-41 | 4.10.10.R | inverter3 |

Select an ID through `SMAB_INVERTER<N>_PROFILE` or the inverter's JSON `profile` field. A profile belongs to a model, not a slot; the same model can be selected for multiple independently configured devices. An observed firmware version is evidence of installed hardware, not a compatibility guarantee.

The Python implementation must package these defaults as resources. For a bare profile ID, resolve `<id>.json` in the host profile directory first, then the bundled resource directory. A malformed or incompatible host override is an error; do not fall back silently. Require the file's `id` to match its selected ID. Use `file:custom-name.json` to select only a file in the host profile directory, without bundled fallback. Reject absolute paths and traversal outside that directory. Additional slots have no default model and require explicit selection.

Custom installation files belong under `./data/sma-mqtt-bridge/profiles/`. Future reusable, sanitized model profiles can be added here. The loader/adapter must use profile data rather than model-specific branches, so adding a supported model needs no new adapter implementation.

The draft schema separates device identity, protocol defaults, evidence/validation, pollers, property definitions and command allowlists. When completing it, describe register functions and zero-based addresses, lengths, data types, word/byte order, scaling, units, invalid sentinels, source channels, per-poller intervals and Homie metadata. Keep installation connection overrides separate from model defaults. Define the final schema and validate it in Python before using profiles.

All initial descriptors have `validation.status=identity-only` and empty poller/property/command arrays. The loader must reject them for normal polling until confirmed register definitions are added and the status is explicitly changed to `validated` after offline verification. Do not assume that a Sunny Boy -40 register document validates a -41, Tripower or Storage model. Preserve existing mappings as migration evidence while reconciling their types and units.

See [the configuration contract](../docs/CONFIGURATION.md), [the value catalogue](../docs/WERTEKATALOG.md) and [migration requirements](../docs/MIGRATION.md).
