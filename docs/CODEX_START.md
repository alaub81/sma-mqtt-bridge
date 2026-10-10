# Start prompt for the new Codex project

Continue the SMA MQTT Bridge project in this repository. Read AGENTS.md, docs/CONTEXT.md, docs/BASELINE.md, docs/IMPLEMENTATION_PLAN.md and docs/MIGRATION.md first. Also read private/CONTEXT.local.md and private/reference/ when available; those files contain the working previous openHAB integration and installation-specific information.

The user wants a Docker bridge based on BMW-MQTT-Bridge, exposing three SMA inverters, Sunny Home Manager 2.0 and SMA eCharger EVC22-3AC-20 through Homie 4 MQTT for openHAB 5.2.1. Use local Modbus/meter/wallbox interfaces and the existing normal-account ennexOS portal API for the SMA minimum PV percentage. No paid SMA Developer API subscription and no replacement charging regulator are desired.

The source layout, Docker, CI/release templates and linter foundations are prepared. The C++ executable is only a diagnostic scaffold, not a functioning bridge. Check the recorded local validation evidence before claiming any checks have run.

First inventory all files in private/incoming/openhab/ and update the migration coverage ledger so every existing value, setting, rule, transformation, widget dependency and persistence requirement is covered. If the incoming configurations are not yet supplied, identify the missing inputs and proceed with work that does not require guessed device mappings.

Then implement adapters and Homie publishing incrementally according to the plan, preserving the confirmed protocol behavior in the working reference scripts. Communicate in German. Keep private credentials, identifiers and raw source captures out of Git and image layers. GitHub publication is a later, separately authorized step.
