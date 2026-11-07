# Live energy-flow widget

`live_energy_flow` displays current PV production, household consumption, grid
exchange, battery power and state of charge. Optional branches show an eCharger
and a heat pump. A separate optional value shows the PV power forecast for now.
The widget displays existing Item states; it does not calculate household power
or control devices.

## Install and start

Choose one installation method for this UID:

- Copy [live-energy-flow.yml](yaml/widgets/live-energy-flow.yml) into
  `$OPENHAB_CONF/yaml/widgets/`. For Docker, use the corresponding host directory
  mounted at `/openhab/conf/yaml/widgets/`.
- Import [live_energy_flow.yaml](mainui/widgets/live_energy_flow.yaml) through
  MainUI using the [manual import guide](mainui/README.md).

Add the widget to an `oh-grid-cells` component on your Page. Select existing
Items in that Page instance's widget properties. The following names are
fictional; replace them with your own linked Items:

```yaml
component: oh-grid-cells
config: {}
slots:
  default:
    - component: widget:live_energy_flow
      config:
        pvPowerItem: Example_PV_Power
        housePowerItem: Example_House_Power
        gridImportItem: Example_Grid_ImportPower
        gridExportItem: Example_Grid_ExportPower
        batteryChargeItem: Example_Battery_ChargePower
        batteryDischargeItem: Example_Battery_DischargePower
        batterySocItem: Example_Battery_SOC
        demoMode: false
```

Start with the measurements you have and leave unused Item properties empty.
Enable `demoMode` explicitly for a visual preview without Items, then disable it
before displaying real measurements. Installation creates no Items or rules.

## Item selection and direction

Use `Number:Power` Items for power and `Number:Dimensionless` for battery SOC.
Find the available channels in the [value catalog](../docs/WERTEKATALOG.md) and
follow the [Item setup guide](openHAB.md). Plant aggregate channels depend on
configured contributors; a single device's existing measurement may be the
appropriate source instead.

| Parameter | Measurement |
| --- | --- |
| `pvPowerItem` | Current PV AC production; plant `pv#totalactivepower` when available |
| `housePowerItem` | Household consumption; plant `house#consumptionpower` when available |
| `gridImportItem` / `gridExportItem` | Separate positive import / export power |
| `gridPowerItem` | Alternative signed grid power; takes precedence over separate Items |
| `batteryChargeItem` / `batteryDischargeItem` | Separate positive charge / discharge power |
| `batteryPowerItem` | Alternative signed battery power; takes precedence over separate Items |
| `batterySocItem` | State of charge in percent |
| `wallboxPowerItem` / `heatPumpPowerItem` | Optional consumption branches |
| `pvForecastPowerItem` | Optional current forecast power from your forecast provider |

For a signed grid Item, the default `gridPositiveImport: true` means positive
import and negative export. Set it to `false` if your source uses the reverse
convention. For a signed battery Item, `batteryPositiveCharge: true` means
positive charge and negative discharge. Set it to `false` for positive discharge.
Confirm these conventions against known readings before interpreting the arrows.
An invalid selected signed Item does not fall back to the separate Items.

The house value is used as supplied. Wallbox and heat-pump branches are displayed
separately without adding to or subtracting from it. Select a house Item that
already represents the intended consumption boundary. Forecast power needs an
external forecast Item; the bridge does not generate a weather-based forecast.

## Values and display options

Power states accept W, kW or MW; unitless numbers mean W. Decimal commas and
scientific notation are supported. Missing Items, NULL/UNDEF, malformed values
and wrong units display a dash. Zero remains zero. Displayed power is an absolute
magnitude; grid and battery direction follows the selected convention. SOC is
clamped to 0–100 for display.

| Parameter | Default | Effect |
| --- | --- | --- |
| `flowThreshold` | 0 W | Direction arrows, active colors and animation above this magnitude |
| `animate` | true | Animate active flow paths |
| `wallboxThreshold` | 10 W | Show the optional wallbox branch above this magnitude |
| `heatPumpThreshold` | 100 W | Show the optional heat-pump branch above this magnitude |
| `socWarningThreshold` / `socCriticalThreshold` | 30 / 20% | SOC warning colors below each threshold; critical takes precedence |
| `showTrend` | true | Show a historical trend for `trendItem`, falling back to `pvPowerItem` |
| `demoMode` | false | Use labeled local example values |

Trends need historical data in openHAB's default persistence service. Tapping the
cell opens the analyzer for selected measurement Items by default; the Action
property group allows a custom action. Title, icons, colors and trend appearance
are configurable in the widget properties.

The widget has no independent timestamp or source-status check. A valid retained
Item value can still be old. Check bridge/source availability alongside the
display; see [operation and freshness](../docs/OPERATIONS.md).

Official references: [personal widgets](https://www.openhab.org/docs/ui/personal-widgets)
and [file-defined widgets](https://www.openhab.org/docs/configuration/yaml/widgets.html).
