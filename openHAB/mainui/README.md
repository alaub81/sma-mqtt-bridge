# Install widgets through MainUI

Use these generated definitions when you prefer pasting a widget into openHAB's
editor. Each file under `widgets/` contains one complete widget with its own `uid`.
The canonical, editable repository sources remain under [../yaml/widgets/](../yaml/widgets/).

| Import file | Guide |
| --- | --- |
| [live_energy_flow.yaml](widgets/live_energy_flow.yaml) | [Live energy flow](../live-energy-flow.md) |
| [daily_energy_overview.yaml](widgets/daily_energy_overview.yaml) | [Daily energy overview](../daily-energy-overview.md) |
| [pv_roof_production.yaml](widgets/pv_roof_production.yaml) | [DC roof production](../pv-roof-production.md) |
| [pv_forecast.yaml](widgets/pv_forecast.yaml) | [PV forecast display](../pv-forecast.md) |
| [sma_echarger_comfort_list.yaml](widgets/sma_echarger_comfort_list.yaml) | [eCharger controls and session display](../echarger-comfort.md) |
| [smabChargingPlan.yaml](widgets/smabChargingPlan.yaml) | [Standalone charging-plan card](../charging-plan.md) |
| [smabChargingPlanList.yaml](widgets/smabChargingPlanList.yaml) | [Charging-plan popup opener](../charging-plan.md); also install `smabChargingPlan` |

## Import

1. Sign in to openHAB as administrator and open **Developer Tools → Widgets**.
2. Use **+** to create a widget and replace the editor's entire default YAML with
   the contents of one import file. Keep its supplied UID, especially for the two
   charging-plan widgets, whose dependency uses that UID.
3. Save, then add the widget to a Page from **Personal widgets** and configure its
   Item properties for your installation. Preview properties in the editor do not
   configure every later Page instance.
4. Repeat for other widgets you want. Import `smabChargingPlan` before its list
   opener. The eCharger comfort widget already includes its own inline plan form;
   the standalone plan pair is optional.

Install each UID once. If the same widget is already installed through a file
under `$OPENHAB_CONF/yaml/widgets/`, use that definition. Do not also import a copy
into MainUI. These import files do not belong in the openHAB YAML configuration
folder. See [file installation and Item guides](../README.md).

Installing a widget creates no Items, links or rules. Choose existing Items or
create/link them using the [openHAB setup guide](../openHAB.md). Device commands
still require the bridge's documented source/global gates. Forecast widgets need
forecast Items from your setup. Turn demo mode off when using real readings.

## Updates and generation

These are generated deployment files. Edit the repository sources under
`openHAB/yaml/widgets/`, then run from the repository root:

```sh
python3 tools/export_openhab_widget.py
python3 tools/export_openhab_widget.py --check
```

The exporter handles all source files and separates multi-widget files into one
import per UID. It preserves expressions, properties and layout without YAML
reformatting. The linter rejects missing, changed or obsolete export files.
Before replacing an installed MainUI definition, compare and back up that copy to
preserve any local changes.

Official guides: [personal widgets](https://www.openhab.org/docs/ui/personal-widgets)
and [file-based YAML widgets](https://www.openhab.org/docs/configuration/yaml/widgets.html).
