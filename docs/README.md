# User guide

Start with the [quick start](WIKI_QUICKSTART.md), then configure the sources you use.
All device adapters and device-write gates require explicit activation. A minimal
private `smab.env` is sufficient; additional JSON configuration is optional.

| Guide | What it covers |
| --- | --- |
| [Configuration](CONFIGURATION.md) | Settings, defaults, credentials, TLS, storage and commands |
| [Profiles](PROFILES.md) | Supported inverter models and adding custom mappings |
| [Translations](TRANSLATIONS.md) | Display languages, label overrides and new dictionaries |
| [Home Manager](HOME_MANAGER_MODBUS.md) | Meter transports and identity requirements |
| [Charger power limit](ECHARGER_POWER_LIMIT.md) | Command requirements and phase-switching limits |
| [Plant calculations](PLANT.md) | Aggregation, daily balances and coverage status |
| [Topic groups](TOPIC_GROUPS.md) | Basic, Advanced and Diagnostics properties |
| [Value catalog](WERTEKATALOG.md) | Supported MQTT properties and units |
| [Operation](OPERATIONS.md) | Startup checks, health, unavailable values and recovery |
| [Updating and backups](UPDATING.md) | Container replacement and persistent-state protection |
| [openHAB setup](../openHAB/openHAB.md), [widget overview](../openHAB/README.md) | Discovery, Item types and widget installation |
| [Building and checks](BUILDING.md) | Custom images, native diagnostics, tests, lint and CI |

Model profiles describe supported hardware; they do not activate connected devices.
Keep credentials, device identities and installation configuration out of Git.
