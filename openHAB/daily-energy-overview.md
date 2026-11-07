# Daily energy-overview widget

`daily_energy_overview` shows today's PV yield, household consumption, grid import
and export, and battery charge and discharge. Optional branches show daily wallbox
and heat-pump consumption; an optional forecast value shows today's remaining PV
energy. These are energy totals, not the instantaneous power shown by the
[live energy-flow widget](live-energy-flow.md).

## Install and start

Choose one installation method for this UID:

- Copy [daily-energy-overview.yml](yaml/widgets/daily-energy-overview.yml) into
  `$OPENHAB_CONF/yaml/widgets/`. With Docker, use the host directory mounted at
  `/openhab/conf/yaml/widgets/`.
- Import [daily_energy_overview.yaml](mainui/widgets/daily_energy_overview.yaml)
  using the [MainUI import guide](mainui/README.md).

Add the widget to an `oh-grid-cells` component and select your Items in the Page
instance's properties. This example uses fictional names:

```yaml
component: oh-grid-cells
config: {}
slots:
  default:
    - component: widget:daily_energy_overview
      config:
        pvEnergyItem: Example_PV_DailyYield
        houseEnergyItem: Example_House_DailyConsumption
        gridEnergyItem: Example_Grid_DailyImport
        gridExportEnergyItem: Example_Grid_DailyExport
        batteryChargeEnergyItem: Example_Battery_DailyCharge
        batteryEnergyItem: Example_Battery_DailyDischarge
        energyDecimals: 1
        demoMode: false
```

Leave unused Item properties empty. `demoMode: true` provides a labeled preview
without Items and does not change Item states. Turn it off for real readings.
Installation creates no Items, calculations, persistence or rules.

## Select daily energy Items

Use `Number:Energy` Items with nonnegative daily totals. Do not select W/kW
power readings, lifetime counters, a charging session's energy or battery SOC.
The widget does not derive daily deltas or reset counters at midnight.

| Parameter | Measurement / suggested channel |
| --- | --- |
| `pvEnergyItem` | PV daily yield; plant `pv#totaldailyyield` when available, otherwise a suitable device daily-yield Item |
| `houseEnergyItem` | Household daily consumption; plant `house#dailyconsumption` |
| `gridEnergyItem` | Daily import; plant `grid#dailyenergyimport` |
| `gridExportEnergyItem` | Daily export; plant `grid#dailyenergyexport` |
| `batteryChargeEnergyItem` | Daily charge; plant `battery#dailychargeenergy` |
| `batteryEnergyItem` | Daily discharge; plant `battery#dailydischargeenergy` |
| `wallboxEnergyItem` | Optional wallbox daily consumption, not session energy |
| `heatPumpEnergyItem` | Optional daily consumption from your heat-pump setup |
| `pvRemainingItem` | Optional remaining PV-energy forecast from your forecast provider |

Plant channels require the relevant configured sources and calculations. See
[plant accounting](../docs/PLANT.md), the [value catalog](../docs/WERTEKATALOG.md)
and [Item setup](openHAB.md). The wallbox and heat-pump branches do not change the
house total; choose that Item's measurement boundary deliberately.

Battery charge and discharge are displayed separately. The existing
`batteryEnergyItem` means discharge; the optional charge Item adds the other
direction. Either can be used alone. Grid import and export also remain separate;
they are not shown as a net daily balance.

## Units, unavailable values and coverage

Wh, kWh and MWh states are normalized to kWh. For unitless states only,
`energyUnit` selects Wh, kWh or MWh and defaults to kWh. This setting does not
override an explicit state unit. Decimal commas and scientific notation are
supported. Negative, malformed, wrong-unit, missing and NULL/UNDEF states show a
dash rather than zero. Unconfigured fields are hidden.

Daily totals may initially cover only part of a day. The widget does not interpret
coverage status or independently check Item timestamps. Check the bridge's day
coverage/status channels alongside its numbers, particularly after a first start,
outage or configuration change. Preserve the bridge state volume; see
[plant accounting](../docs/PLANT.md).

## Appearance, trends and analyzer

| Parameter | Default | Effect |
| --- | --- | --- |
| `energyDecimals` | 1 | Display precision, 0–3 decimal places |
| `wallboxEnergyThreshold` / `heatPumpEnergyThreshold` | 0 kWh | Show each optional branch only above its threshold |
| `showTrend` | false | Show historical `trendItem`, falling back to `pvEnergyItem` |
| `demoMode` | false | Use labeled local example values |

Direction arrows and colors activate only when the value rounded to the selected
precision is greater than zero. Battery charge is green toward the battery;
discharge is orange toward the house. When both are active, the connection is
striped and the neutral battery icon is muted yellow-green (`#98B831`). Grid
import/export also use separate directional colors and a striped connection
when both are active. Unknown values activate no direction.

Customize title, icons, directional colors and trend appearance in the widget
properties. Trends require historical data in the default persistence service.
Tapping the cell opens the analyzer for configured energy Items by default,
including both battery directions. The Action property group allows a custom action.

Official references: [personal widgets](https://www.openhab.org/docs/ui/personal-widgets)
and [file-defined widgets](https://www.openhab.org/docs/configuration/yaml/widgets.html).
