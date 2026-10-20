# PV forecast traffic-light widget

The file-defined `pv_forecast` widget presents four daily PV-energy forecasts,
today's remaining forecast and average daily house consumption. It uses the
same expandable Framework7 card shell, native cell margins and theme corners as
the energy overview widgets. The closed view is 120 px high and supports narrow
cell columns; selecting a day adds its details below the overview.

## Installation

Copy [yaml/widgets/pv-forecast.yml](yaml/widgets/pv-forecast.yml) to
`$OPENHAB_CONF/yaml/widgets/` (Docker: the directory mounted at
`/openhab/conf/yaml/widgets/`). Add `widget:pv_forecast` directly inside an
`oh-grid-cells` component and configure its Item parameters. Do not install a
second definition of the same UID. File-defined widgets are read-only in MainUI.

```yaml
component: oh-grid-cells
config: {}
slots:
  default:
    - component: widget:pv_forecast
      config:
        todayItem: PVForecastToday
        tomorrowItem: PVForecastTomorrow
        day2Item: PVForecastDay2
        day3Item: PVForecastDay3
        remainingItem: PVForecastRemainingToday
        averageItem: HouseAverageDailyConsumption
        greenPercent: 110
        orangePercent: 70
        remainingReference: house
        remainingGreenPercent: 50
        remainingOrangePercent: 20
        demoMode: false
```

These Item names are examples; use your existing Items. The widget performs no
Item commands and does not modify forecast calculations or historical data.

## Options

| Parameter | Default | Purpose |
| --- | --- | --- |
| `title` | PV-Prognose | Title text |
| `icon` / `iconColor` | f7:bolt_circle / #FFD60A | Independently configurable title icon and color; 12 px |
| `showTitle` | true | Show title and its icon |
| `showRemaining` / `showAverage` | true / true | Show footer values |
| `decimals` | 1 | Energy fractional digits, 0–3; remaining-energy footer always uses one decimal; values use a decimal comma |
| `averageDecimals` | 1 | Separate house-average fractional digits, 0–3 |
| `dayFontSize` | 10 | Day-label font size in px, 7–16 |
| `locale` | de | Weekday label locale |
| `todayLabel` / `tomorrowLabel` | Heute / Morgen | First two day labels |
| `day2Label` / `day3Label` | empty | Overrides; otherwise short local weekday names |
| `trafficIconSize` | 20 | Daily traffic-light height in px, 8–32 |
| `trafficGlow` | true | Brighter active lamp with a small colored glow; false restores flat colors |
| `trafficInactiveOpacity` | 0.25 | Inactive-lamp opacity, 0–1 |
| `trafficHousingColor` | Theme secondary color at 55% | Mini traffic-light housing |
| `greenPercent` / `orangePercent` | 110 / 70 | Configurable relative traffic-light thresholds |
| `showRemainingTraffic` | true | Show a small traffic light before Rest |
| `remainingReference` | house | Compare remaining energy with `house` average or `today` total forecast |
| `remainingGreenPercent` / `remainingOrangePercent` | 50 / 20 | Independent relative thresholds for remaining energy |
| `remainingTrafficIconSize` | 9 | Separate remaining-energy traffic-light size in px, 8–16; matches the house icon |
| `greenColor` / `orangeColor` / `redColor` | #34C759 / #FFD60A / #FF3B30 | Configurable green/yellow/red colors |
| `unknownColor` | Theme secondary text | Missing or invalid comparison color |
| `textColor` / `backgroundColor` | Theme text / card | Appearance |
| `forecastChartItems` | empty | Common forecast curve Items for the analyzer |
| `day3ChartItems` | empty | Optional different analyzer Items for the fourth day |
| `demoMode` | false | Explicit local example values, marked Demo |

The house icon before the average symbol is 9 px, smaller than the title icon.
Each day places its traffic light above the day label and energy value. The
default mini traffic light has a neutral housing and three circular lamps:
red at the top, yellow in the middle and green at the bottom. Only the active
lamp has full opacity; the other two default to 25%. Unknown comparisons show
three equally dim gray lamps. The brighter neutral housing follows the theme
and remains distinct against dark cards. Status tooltips retain the color name.
Active lamps also receive a restrained colored glow and a brightness/saturation
boost. Disable this visual emphasis with `trafficGlow: false`; active opacity
remains 100% in both modes. Inactive and unknown lamps receive no glow or boost.
The native mini traffic lights use ordinary MainUI elements and CSS; they need
no icon downloads or embedded scripts. The existing size parameters set their
total height directly, with 20 px daily and 9 px Rest defaults.
The earlier icon representation and its selector/icon parameters have been
removed, so the editor also contains only one traffic light per value. Old
`trafficStyle`, `greenIcon`, `orangeIcon`, `redIcon` and `unknownIcon` values in a
page configuration can be removed; they have no effect. An explicit
`trafficIconSize` still overrides the default; remove it or set it to 20 to use
the new daily size. Day and footer
typography adapts to the cell width. Long custom day labels are
ellipsized; their full label and traffic status remain available in the tooltip.

## Forecast inputs and comparison

Use energy Items for `todayItem`, `tomorrowItem`, `day2Item`, `day3Item`,
`remainingItem` and `averageItem`. The widget accepts nonnegative values in
kWh, Wh and MWh; values without units mean kWh. Units are normalized to kWh before
comparison and display. Decimal commas and scientific notation are accepted.
Wrong units, NULL, UNDEF, missing Items and nonfinite values render as “—”. Valid
zero forecasts render as zero. The average must be positive to classify a day.

Each day's forecast is compared with average daily house consumption:

- Green when forecast >= average × greenPercent / 100.
- Yellow when forecast >= average × orangePercent / 100, below the green limit.
- Red below the yellow limit.
- Unknown when either value is invalid, average <= 0, or threshold configuration
  is invalid. Thresholds must be finite, nonnegative, and green > orange.

At an average of 11.5 kWh, the defaults mean green from 12.65 kWh and yellow from
8.05 kWh. Classification uses the unrounded energy; changing decimals cannot
change a traffic-light color. The former list's absolute 8/3 kWh thresholds for
remaining energy are not used for the daily indicators.

### Remaining-energy traffic light

A separate small traffic light precedes Rest, using the same representation
and colors as the daily indicators. Its independent defaults are green
from 50%, yellow from 20%, and red below 20% of the selected reference. The
comparison uses unrounded, normalized energy. With the default `house` reference
and an average of 11.5 kWh, green starts at 5.75 kWh and yellow at 2.3 kWh.
This expresses how much of a typical full day's house energy is still expected
as PV production. It does not estimate the house's remaining demand.

Set `remainingReference: today` to compare with the current `todayItem` total
forecast instead. At a forecast of 17 kWh, the defaults become 8.5/3.4 kWh.
This mode indicates what fraction of the forecast remains and naturally tends
towards red as the day ends, even on a good production day. It follows forecast
revisions; the widget does not save a fixed morning forecast. Both modes use
current Item states without additional storage, rules or Items.

Configure `remainingGreenPercent` and `remainingOrangePercent` freely, with
finite nonnegative thresholds and green strictly above orange. Missing/invalid
energy, a zero or invalid reference, an unsupported reference selection or
invalid thresholds produces the neutral unknown display. Valid zero remaining
energy stays zero and follows the thresholds. Hide the icon independently with
`showRemainingTraffic: false`, or adjust `remainingTrafficIconSize` (default
9 px, matching the house icon). The Rest link still opens the existing analyzer target.

The middle lamp defaults to yellow. Parameter names `orangeColor`, `orangePercent`
and `remainingOrangePercent` are preserved for compatibility. Existing explicitly
configured colors and percentages still apply; the new yellow default does not
override a saved custom orange color.

The comparison indicates an energy-volume relationship, not guaranteed
self-sufficiency: timing, battery state and intraday load are not considered.
The widget uses current Item states; it does not independently detect stale but
valid stored forecast values. It does not invent unavailable forecast timestamps.

## Details and existing analyzer behavior

Selecting a day opens its forecast, house average and relative percentage.
The separate traffic-color text row is omitted; day tooltips retain the status. Select it again or choose Schließen to close. The detail link opens the
existing analyzer with `forecastChartItems`, or `day3ChartItems` for the fourth
day if supplied. Without a nonempty list, it falls back to that day's energy Item. Analyzer
Item lists are selected directly in the action expression, without a helper
function or JavaScript type/global checks.
Today uses the day chart, later days the week chart; the coordinate system is time.
The remaining-energy footer opens the forecast curves in a day chart. The house
average opens its existing Item in an ISO-week chart. No data is written.

## Validation limits

The actual YAML functions and expressions are checked locally, including exact
threshold boundaries, unit conversion, invalid readings, zero, optional chart
fallbacks, custom thresholds/colors and explicit demo mode. Local rendering is
inspected at 180/320 px host widths. These checks do not replace installation,
MainUI analyzer navigation and native iPhone acceptance.

## Official references

- [YAML widget installation](https://www.openhab.org/docs/configuration/yaml/widgets.html)
- [Widget expressions](https://www.openhab.org/docs/ui/widget-expressions-variables.html)
- [Scoped widget context](https://www.openhab.org/docs/ui/components/oh-context.html)
- [Link and analyzer actions](https://www.openhab.org/docs/ui/components/oh-link.html)
