# Custom display translations

Copy `example.json` into `data/sma-mqtt-bridge/translate/<language>.json` next to your Compose
installation, then set `SMAB_LANGUAGE=<language>` in `smab.env`. For example, use `de.json` to
customize the bundled German labels. This directory is a public template, not a runtime mount.

The complete dictionaries in `ressources/translate/en.json` and `de.json` provide every current
built-in display label. Original English labels are lookup keys; omit keys to use bundled defaults.
Keep `Device {number}`'s placeholder when overriding assigned-device labels. Only display labels
are translated; topic IDs, measurement values and commands remain stable across languages.
See [the configuration contract](../docs/CONFIGURATION.md#display-language-and-compact-channel-ids).
