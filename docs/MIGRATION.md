# Existing openHAB capability migration

The goal is to preserve the user's complete existing integration, including calculations and automation, not only a selection of dashboard values.

## Files to provide

Place relevant exports under `private/incoming/openhab/`, keeping useful names/subdirectories:

- `.things` definitions for all inverter Modbus bridges, pollers/data Things and the Home Manager.
- `.items` including units, profiles, transformations, channel links and Item metadata.
- Referenced `.map`, `.js`, `.scale`, JSONPath/XPath and other transformations.
- Rules/scripts that calculate totals, consumption, day counters or use/command SMA Items.
- Persistence configuration and restore-on-startup requirements.
- Relevant sitemaps/MainUI YAML; Item names matter for preserving widgets.
- MainUI-managed Things/Items/links as exports if they are not represented by text files.
- Inverter model/firmware information and Home Manager identity/firmware.

Credentials and tokens must not be copied into public fixtures. The incoming folder is excluded from Git and Docker. Preserve original exports there as read-only references; create sanitized derived examples separately.

## Coverage ledger

`migration-coverage.csv` starts with every non-group Item from our current wallbox and portal packages. No runtime support is claimed yet. Extend it with every incoming inverter/Home Manager Item and derived capability.

Required mapping fields: original Item/channel, data source, source register/channel, type/unit, scaling/invalid handling, read/write capability, proposed Homie topic, dependent rules/widgets/persistence, verification evidence and migration status.

The bridge may publish all required raw values while an existing openHAB rule continues to calculate a derived value. Record that explicitly. A capability counts as migrated only after units, timestamps, behavior and dependencies are checked.
