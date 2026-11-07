# openHAB integration files

This directory separates installable YAML widget sources, generated manual imports
and setup documentation. Widget UIDs and behavior are independent of file locations.
The canonical, editable widget sources are maintained only in this repository
under `yaml/widgets/`. Make changes here first and deploy from these files;
do not maintain separate editable copies in other project directories.

```text
openHAB/
  README.md
  openHAB.md
  echarger-comfort.md
  yaml/
    widgets/
      charging-plan.yml
      daily-energy-overview.yml
      echarger-comfort.yml
      live-energy-flow.yml
      pv-roof-production.yml
      pv-forecast.yml
  mainui/
    README.md
    widgets/          # Generated MainUI imports, one YAML per widget UID
```

## File-defined widgets

The files under `yaml/widgets/` use `version: 1` and a `widgets:` map. Copy only
selected files to `$OPENHAB_CONF/yaml/widgets/`. With Docker, use the host directory
mounted at `/openhab/conf/yaml/widgets/`. These files belong to openHAB, not the
SMA bridge configuration directory. Configure their Item parameters for your own
installation. File-defined widgets are read-only in MainUI.

| File | Widget UID(s) | Purpose |
| --- | --- | --- |
| [echarger-comfort.yml](yaml/widgets/echarger-comfort.yml) | `sma_echarger_comfort_list` | Charger controls and session display |
| [charging-plan.yml](yaml/widgets/charging-plan.yml) | `smabChargingPlan`, `smabChargingPlanList` | Optional standalone charging-plan card and popup opener |
| [live-energy-flow.yml](yaml/widgets/live-energy-flow.yml) | `live_energy_flow` | Current power flow |
| [daily-energy-overview.yml](yaml/widgets/daily-energy-overview.yml) | `daily_energy_overview` | Daily energy overview |
| [pv-roof-production.yml](yaml/widgets/pv-roof-production.yml) | `pv_roof_production` | DC production for three configured roof areas |
| [pv-forecast.yml](yaml/widgets/pv-forecast.yml) | `pv_forecast` | Four-day PV forecast with configurable traffic thresholds and house average |

Forecast widgets display forecast Items supplied by your setup; the bridge does
not calculate a weather-based PV forecast. The widget files let you select your
own Items and display options. Install each widget UID only once.

### Battery directions in the daily energy widget

In `daily_energy_overview`, select the Items linked to the plant's new kWh
channels:

| Widget parameter | Meaning | Plant channel |
| --- | --- | --- |
| `batteryChargeEnergyItem` | Charged today | `battery/dailychargeenergy` |
| `batteryEnergyItem` | Discharged today | `battery/dailydischargeenergy` |

Both values are displayed separately, like grid import and export. The existing
`batteryEnergyItem` parameter keeps its name and meaning. The charge Item is
optional; leaving it empty preserves the discharge-only display. If only the
charge Item is configured, the battery remains visible with that direction.
Do not select cumulative charge/discharge counters for these daily inputs.

Charge uses green and an arrow toward the battery; discharge uses orange and an
arrow toward the house. Both directions share a striped line when their displayed
values are positive, with a neutral battery icon in muted yellow-green (`#98B831`).
Values that round to zero at the
selected precision keep an inactive arrow/color. Unknown values show a dash and
do not activate a direction. Customize `batteryChargeColor`,
`batteryDischargeColor`, `batteryIconColor`, `batteryChargeIcon`,
`batteryDischargeIcon` and `batteryIcon` as needed. The analyzer includes both
configured Items. Daily differences are calculated by the bridge, not the widget.

## Manual MainUI import

[mainui/README.md](mainui/README.md) explains editor-based installation. All seven
widget UIDs have generated files under `mainui/widgets/`, each with a `uid:` root.
The file-defined sources above retain their `version`/`widgets` wrapper. Choose
one installation method per UID; copying both versions creates a duplicate.

Edit only the canonical sources under `yaml/widgets/`, then regenerate all exports:

```sh
python3 tools/export_openhab_widget.py
python3 tools/export_openhab_widget.py --check
```

Run from the repository root. The linter checks every export, including both
widgets in `charging-plan.yml`, and detects missing, changed or obsolete imports.
When updating an installed MainUI copy, compare its current definition first so
local changes are preserved.

## Guides

- [MainUI and Item setup](openHAB.md)
- [eCharger comfort widget](echarger-comfort.md)
- [PV roof production widget](pv-roof-production.md)
- [PV forecast traffic-light widget](pv-forecast.md)
- [Official openHAB YAML widget documentation](https://www.openhab.org/docs/configuration/yaml/widgets.html)
