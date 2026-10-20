# PV roof production widget

[pv-roof-production.yml](yaml/widgets/pv-roof-production.yml) defines the file-based
MainUI widget `pv_roof_production`. It shows instantaneous DC power on three
module surfaces, with a combined total and tap-to-open DC details.

The schematic looks toward the house from the south: the SW gable and the shaded
SO side wall are visible, with the SW carport in front. The largely hidden NW
roof has a leader line to its reading. There are exactly two equally sized
gable windows without crossbars. The diagram has no house-wall/carport captions.
Module counts and geometry are illustrative, not a physical installation plan.

## Install

Copy the file into `$OPENHAB_CONF/yaml/widgets/pv-roof-production.yml`.
For Docker, use the corresponding host directory mounted under
`/openhab/conf/yaml/widgets/`. No SMA bridge rebuild is needed.
The file uses the openHAB YAML loader wrapper; do not paste the whole file into
the MainUI single-widget editor. Avoid installing the same UID twice.

After the widget appears in MainUI, add `pv_roof_production` to a responsive
page and choose its Item parameters. No Items, rules or device commands are
created by the widget. This change only prepares the file; installation and
integration into a page are separate steps.

## Example Item selection

The following names are fictional. Select the matching DC input Items and verify
orientation/wiring locally. The widget source has no installation Item defaults.

```yaml
- component: widget:pv_roof_production
  config:
    soPowerItem: Example_SouthEast_Power
    soVoltageItem: Example_SouthEast_Voltage
    soCurrentItem: Example_SouthEast_Current
    nwPowerItem: Example_NorthWest_Power
    nwVoltageItem: Example_NorthWest_Voltage
    nwCurrentItem: Example_NorthWest_Current
    swPowerItem: Example_SouthWest_Power
    swVoltageItem: Example_SouthWest_Voltage
    swCurrentItem: Example_SouthWest_Current
    roofStatusItem: Example_Roof_SourceStatus
    carportStatusItem: Example_Secondary_SourceStatus
```

Only the three power Items are required. Voltage/current and source status Items
are optional. Tapping a value shows that area's DC power, voltage and current;
`Schließen` or tapping the same area closes the details. These actions only
change widget-local variables. The voltage/current fields show a dash when absent.

## Values and availability

- Power accepts nonnegative W, kW or MW; unitless numbers mean W. Decimal commas
  and scientific notation are supported. Energy units such as kWh are rejected.
- Voltage/current accept nonnegative V/A respectively; unitless values use those
  units. A missing Item, NULL/UNDEF, nonfinite, malformed or wrong-unit state is
  unavailable. Negative DC inputs are rejected rather than silently reversed.
- Actual zero remains `0 W`. Missing values do not become invented zeros.
- The total uses all three independently normalized DC power readings. If any
  power is unavailable, the total is a dash and an incomplete-input note appears.
  It is not AC power, daily yield or an estimate derived from voltage/current.
- When a source-status Item is selected, only `ready` permits its values.
  A missing or non-ready selected status suppresses those source values. Without
  a status selection, only Item state validity is checked.
- Source ready does not prove per-channel freshness. Already retained Item values
  are not timestamp-validated by this widget, and no receipt timestamp is invented.

`demoMode` defaults to false. Enable it explicitly for the illustrated values;
all demo values are local and do not write Item states. Reset it before using
real measurements. The heading marks demo values while the title is visible.

## Sizing and appearance

Place the widget directly inside `oh-grid-cells`, as with the energy overview
widgets. The Framework7 expandable-card shell and oh-cell class supply the same
platform-dependent corners, shadow, and native margins (10 px vertically,
5 px horizontally) as the energy cells. Automatic card opening is prevented;
the existing area links control details. No custom width or margin overrides
are applied. Title text uses the same clamp(7.5px, 4.8cqw, 11px), 18 px line
height and 12 px icon as the energy widgets.
The closed overview has a fixed 120 px height matching the energy cells. The
house occupies a centered 160 by 80 px scene; title and total use compact rows.
Its 156 by 88 px drawing is uniformly scaled by 1.2, preserving the existing
proportions while enlarging both axes by 20%. The drawing clips excess ground and
post ends to keep the title and total rows clear within the existing cell height.
The readings are repositioned over the SO roof and SW carport; NW retains its
separate reading. The southern
perspective uses separate shaded wall and roof polygons and aligned module grids.
Selecting a module area adds its details below that overview, with 8 px side
insets and 12 px bottom padding to keep text clear of the rounded card edges. The former
sceneAspectRatio option is removed because the overview no longer scales in
height with the cell width.
There are no scripts, embedded SVG documents or external assets required by the
widget. Power labels use fixed 56 px widths and a 26 px minimum height, with
separate positions for NW, SO and SW. Their 10 px values fit two-decimal kW
readings, including `12,34 kW`, in narrow two-column grid cells. The total uses one compact row, and its
value and unit stay together. Details use normal MainUI
links and scoped variables. For larger touch targets, use a full-width grid row.

Choose `showTitle`, `showTotal` and `showGrid` independently.
Configure `soLabel`, `nwLabel` and `swLabel` to rename the areas. Defaults are
SO, NW and SW; these labels appear on the diagram, in tooltips and as detail
headings. Long diagram labels are truncated to fit the compact measurement box.
The title icon defaults to `f7:bolt_circle` in `#FFD60A`; configure these through
`icon` and `iconColor`, independently of the PV accent color. The card uses the
standard Framework7 expandable-card corner radius without a widget-specific override.
The outer card has no border or interaction-hint footer;
the compact total caption is “DC gesamt”. PV accent, text,
background, roof, wall and window colors are configurable; defaults follow the
MainUI theme. Measurement-label backgrounds mix the theme card color at 60%
opacity, allowing the panel grid to show through without fading the text.
Each area's module fill and grid lines follow its own valid DC power: production
above zero uses `pvColor` (default bright yellow, `#FFD60A`); exactly zero uses `pvIdleColor`
(default vivid blue, `#0A84FF`). Missing/invalid values or a non-ready configured
source use neutral gray, preserving the distinction between idle and unavailable.
Colors use the normalized, unrounded power, so a small positive input remains
active. The color does not assert physical relay state or independent per-channel
freshness. Producing yellow and idle blue panels both use 28% fill and 75% grid opacity
for stronger visibility. Unavailable gray retains 16% fill and 48% grid opacity.
Keep the containing column wide enough for the
card; let the native cell grid assign its width instead of wrapping it in an
additional wide grid column.

The locally rendered YAML was inspected at 320 and 620 px including detail
selection. All 35 expressions were evaluated across eight selection/demo states;
34 targeted calculation cases cover units, invalid values, zero, source status
and incomplete sums. These checks do not replace the first real MainUI/iOS
installation and touch/orientation acceptance.

## References

- [File-defined YAML widgets](https://www.openhab.org/docs/configuration/yaml/widgets.html)
- [Widget expressions and functions](https://www.openhab.org/docs/ui/widget-expressions-variables.html)
- [oh-context scoped variables](https://www.openhab.org/docs/ui/components/oh-context.html)
- [oh-link variable actions](https://www.openhab.org/docs/ui/components/oh-link.html)

The detail row shows measurements with their units, without separate
power/voltage/current captions. Detail measurements use zero fractional digits (equivalent to `%.0f`) in W and V,
and one fractional digit (`%.1f`) in A. Invalid values remain “—”; only the
display is rounded.
