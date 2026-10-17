# Item display naming update, 2026-10-17

Andreas approved the proposed German labels and will recreate Items manually after
building/deploying. The [migration worksheet](item-label-migration-2026-10-17.csv)
lists all 14 relevant channels, previous and target Item names, labels and types.
Channel suffixes are relative to the existing Homie Thing; keep its actual UID.
Rows with identical previous/target names already follow the naming convention.
Historical inventory CSVs remain observations, not proof of this migration.

Only publication labels change. Protocol keys, MQTT topics, profile files/hashes,
units, calculations and energy baselines remain unchanged. Storage dailyyield is
labelled daily discharge based on the installation evidence in
[register validation](REGISTER_VALIDATION.md); its counter is not recalculated.
PV production applies to non-storage inverter inventories, including future slots.
Host translation overrides take precedence over bundled labels.

Before deleting Items, preserve required history and update dependent rules,
pages, groups and persistence for replacement names. Creating a new Item does not
transfer its old history or references. No live Item changes or history copy are
included. Status/relay value mappings remain unchanged.

The official [openHAB Item documentation](https://www.openhab.org/docs/configuration/items.html)
was consulted for the distinction between Item names and display labels.
