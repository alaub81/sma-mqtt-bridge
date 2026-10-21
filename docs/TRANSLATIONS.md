# Display languages and custom translations

The bridge includes English (`en`, the default) and German (`de`) MQTT discovery
labels. Choose German by setting this in your private root `smab.env`:

```dotenv
SMAB_LANGUAGE=de
```

Recreate the container to load the setting. MQTT device, node and property labels
use the selected language. Topic IDs, units, measurement values, enums and command
payloads remain unchanged. Existing openHAB Item labels and widget text are managed
separately; this setting does not translate them.

## Override bundled labels

Create the host directory and copy the [template](../translate/example.json):

```sh
mkdir -p data/sma-mqtt-bridge/translate
cp translate/example.json data/sma-mqtt-bridge/translate/de.json
```

Edit only the labels you want to customize. Use an existing host file directly
rather than overwriting it when updating.

```json
{
  "schemaVersion": 1,
  "labels": {
    "Inverter": "Wechselrichter",
    "Measurements": "Messwerte",
    "Device {number}": "Gerät {number}"
  }
}
```

Original English labels are lookup keys. The complete dictionaries under
[ressources/translate/](../ressources/translate/) list the current built-in keys.
Keep the `{number}` placeholder in `Device {number}`. Custom profile labels can
also be translated through the same dictionary.

## Add another language

Save a dictionary as, for example,
`data/sma-mqtt-bridge/translate/fr.json`, translate its values and set
`SMAB_LANGUAGE=fr`. Language names use lowercase codes, optionally with
hyphen-separated lowercase region subtags. A host dictionary enables a language
without changing the Python adapters or rebuilding the image.

Loading precedence is bundled English, bundled selected language, then the
selected host dictionary. Missing keys fall back to English or the original
profile label. Customization files are never created or overwritten by the bridge.

## Paths and validation

The default `SMAB_TRANSLATE_DIR` is
`/data/sma-mqtt-bridge/config/translate` inside the container; the normal read-only
configuration bind mount exposes the host directory above at that location.
The container user must be able to read the files. JSON uses `runtime.language`
and `runtime.translateDir` as alternatives to ENV; explicit ENV takes precedence.

Files must contain exactly `schemaVersion: 1` and `labels`. Labels are nonempty
single-line strings up to 256 characters. Duplicate keys, invalid schemas,
symlinks, unavailable languages and files over 1 MiB are rejected before connecting.
See the [configuration contract](CONFIGURATION.md#display-language-and-compact-channel-ids)
for the complete setting and MQTT naming rules.
