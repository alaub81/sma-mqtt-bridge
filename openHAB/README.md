# openHAB integration files

This directory separates installable YAML widget sources, generated manual imports
and setup documentation. Widget UIDs and behavior are independent of file locations.

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
  imports/
    widgets/
      sma_echarger_comfort_list.yaml
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

## Manual MainUI import

[imports/widgets/sma_echarger_comfort_list.yaml](imports/widgets/sma_echarger_comfort_list.yaml)
is the generated alternative for manual MainUI editor import. It has a `uid:`
root rather than the file-loader wrapper. Do not copy it into the openHAB YAML
configuration directory or install it alongside the file-defined copy of the same UID.

Edit the canonical source under `yaml/widgets/echarger-comfort.yml`, then regenerate:

```sh
python3 tools/export_openhab_widget.py
python3 tools/export_openhab_widget.py --check
```

Run these commands from the repository root. The project linter checks that the
manual import matches the canonical definition. The other widgets currently have
file-install sources only; no duplicate manual exports are maintained.

## Guides

- [MainUI and Item setup](openHAB.md)
- [eCharger comfort widget](echarger-comfort.md)
- [PV roof production widget](pv-roof-production.md)
- [PV forecast traffic-light widget](pv-forecast.md)
- [Official openHAB YAML widget documentation](https://www.openhab.org/docs/configuration/yaml/widgets.html)
