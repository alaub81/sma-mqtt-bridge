# eCharger garage list widget

The garage entry shows vehicle connection, power and a timestamped session display together with
charging permission (Ladeberechtigung) and checked mode buttons with icons beside the labels. Selecting PV reveals the staged PV
percentage slider directly below the modes. Target charging expands the energy/departure form below the modes. Additional
settings expand in the same entry; there is no custom popup. UI labels are German. No Items, links, rules,
bridge settings or device settings are created by installing the widgets.

## Source and manual import

[echarger-comfort.yml](yaml/widgets/echarger-comfort.yml) is the only editable source.
[sma_echarger_comfort_list.yaml](sma_echarger_comfort_list.yaml) is generated for
manual import into MainUI's widget editor. Both represent the same widget UID,
properties and behavior. Install one version per openHAB instance.

After editing the source, regenerate the import file from the repository root:

```sh
python3 tools/export_openhab_widget.py
python3 tools/export_openhab_widget.py --check
```

The exporter changes only the YAML wrapper and indentation; expressions and layout
remain unchanged. The repository linter checks that the generated file is current.
For manual import, paste the generated file into the MainUI widget editor instead
of also installing the file configuration below.

## Target-plan feedback compatibility

If the target-plan feedback shows `Error: 'String' is not a function`, update the
existing widget from the regenerated manual-import file or canonical YAML above.
Both energy-state conversions now use `'' + value`; MainUI does not expose the
`String()` constructor in its expression context. The kWh/Wh validation and
confirmed energy/end-time comparison are preserved. See the official
[expression documentation](https://www.openhab.org/docs/ui/widget-expressions-variables.html).
Updating the widget requires no charging command.

## Shared expressions and update check

The existing `oh-context` defines `localWriteAllowed`, `portalWriteAllowed` and
`chargingMode`. These functions preserve the previous expressions and are
reevaluated on each call and dependency change, as described in the official
[context documentation](https://www.openhab.org/docs/ui/components/oh-context.html).
Device-specific Item checks, plan/PV input validation, demo actions and command
payloads remain at their original controls.

Before replacing an installed widget, save its current YAML. Update the existing
UID through the same installation method, keeping its configured props. Check
layout, demo mode changes, PV/plan staging and settings expansion. With real Items,
check that missing Items, unavailable API/portal and running or uncertain commands
still block the corresponding controls; check status changes without reloading.
A visual/gating check does not require sending a device command. Restore the saved
YAML through the same method if rendering or reactive updates differ.

## Install for a first visual review

Copy the single file [echarger-comfort.yml](yaml/widgets/echarger-comfort.yml) to
`$OPENHAB_CONF/yaml/widgets/echarger-comfort.yml`. With Docker, use the host directory
mounted at `/openhab/conf/yaml/widgets/`. Create the `widgets` subdirectory if needed.

The file contains `version: 1` and the complete `sma_echarger_comfort_list` widget definition under `widgets:`.
openHAB reads YAML configuration recursively, so no manual MainUI import or additional
widget file is needed. File-defined widgets are read-only in MainUI.
Do not install another copy of the same widget UIDs. If the previous draft was imported
manually, remove those manual definitions before loading the file version. The obsolete
`sma_echarger_details` popup is no longer part of this bundle.

Append this entry after the two existing BMW entries in the Garage card's
`slots.default` array:

```yaml
- component: widget:sma_echarger_comfort_list
  config:
    chargerName: SMA eCharger
    demoMode: true
    enableControls: false
```

No Item selection is needed in demo mode. The sample shows 4.2 kW, 8.0 kWh and PV
charging. The inline release/mode buttons change local demo variables; selecting fast or stop
hides the PV slider, selecting PV shows it again. Plan/PV submissions only show a
demo message. Additional settings are read-only demo examples.
Widget variables are isolated per instance using `oh-context`.

## Connect existing Items later

Set `demoMode: false` and select the existing Items through the widget properties.
`enableControls: false` keeps the widget in display mode. Missing/NULL/UNDEF Items
show placeholders, never fabricated zeros. Set power display metadata to kW if
preferred; the widget uses `displayState` and preserves the source quantity/unit.
Session energy is not used as a charging-plan progress bar.

| Property | German Item label / search term | Homie channel suffix / Item type |
| --- | --- | --- |
| `statusItem` | Fahrzeugstatus | `measurements#vehiclestatus` / String |
| `powerItem` | Ladeleistung | `measurements#power` / Number:Power |
| `sessionEnergyItem` | Energie der Ladesitzung | `measurements#sessionenergy` / Number:Energy |
| `sessionStateItem` | Zustand der Ladesitzung | `session#status` / String |
| `sessionDisplayEnergyItem` | Gespeicherte Sitzungsenergie | `session#energy` / Number:Energy |
| `sessionEnergyTimeItem` | Messzeitpunkt der Sitzungsenergie | `session#energytime` / DateTime or String |
| `modeItem` | Lademodus | `settings#chargemode` / String |
| `releaseItem` | Ladefreigabe | `settings#chargingrelease` / Switch |
| `planItem` | Bestätigter Ladeplan | `commands#plan` / String |
| `planEnergyItem` | Geplante Ladeenergie | `settings#planenergy` / Number:Energy |
| `planEndItem` | Geplantes Ladeende | `settings#planend` / DateTime or String |
| `pvMinimumItem` | Minimaler PV-Anteil | `portal#pvminimum` / Dimmer, integer 0–100 |
| `localResultItem` | Ergebnis des lokalen Befehls | `commands#localresult` / String |
| `portalResultItem` | Ergebnis des Portalbefehls | `commands#portalresult` / String |
| `measurementStatusItem` | Verfügbarkeit der Datenquelle | `diagnostics#sempstatus` when SEMP owns measurements; otherwise `diagnostics#apistatus` / String |
| `apiStatusItem` | Verfügbarkeit der Datenquelle | `diagnostics#apistatus` / String |
| `portalStatusItem` | Verfügbarkeit der Datenquelle | `portal#status` / String |
| `approvalRequiredItem` | Freigabe erforderlich | `settings#approvalrequired` / Switch |
| `cableLockItem` | Dauerhafte Kabelverriegelung | `settings#cablelock` / Switch |
| `stopWhenFullItem` | Bei vollem Fahrzeug beenden | `settings#stopwhenfull` / Switch |
| `ledBrightnessItem` | Helligkeit der Statusbeleuchtung | `settings#ledbrightness` / String |
| `ambientEnabledItem` | Umgebungsbeleuchtung aktiviert | `settings#ambientenabled` / Switch |
| `ambientBrightnessItem` | Helligkeit der Umgebungsbeleuchtung | `settings#ambientbrightness` / String |

### Session display after charging

After rebuilding/recreating the bridge, link the three new session properties to
Items and select them in the widget. Keep the old sessionEnergyItem and its history;
no relinking or rescaling of the existing raw channel is required. Set energy unit
to kWh. A DateTime Item with a local date/time display pattern is convenient for
sessionEnergyTimeItem; a String Item displays the source's UTC timestamp directly.
The additional session#endedat channel is optional for other views and records
observed disconnection rather than the last watt of charging.

The widget shows **Geladen** while charging, **Laden pausiert · bisher** during
connected idle, and **Letzte Ladung** after a sampled disconnection. It always
includes the captured amount's source time when the new view is configured. A
resumed charge remains the same session. Abstecken is the completion boundary;
zero power, the 180-second raw-value expiry or target mode alone do not establish
completion. An offline/unknown state uses **Letzter Stand** and an unconfirmed
connection notice rather than a live charging label. Waiting without a captured
amount shows **Noch keine Sitzungsenergie**. If only the legacy Item is configured,
the fallback explicitly says **Letzter Messwert**, without claiming session state.

Persisted history survives restart/disconnect in the bridge's existing state
volume. If a fresh session amount has never been captured by this version, it does
not invent one from expired raw values. The amount is the last observed value,
not proof of complete metering across outages, vehicle SOC or target achievement.
No Item, persistence, rule or installed widget is changed by the repository export;
reselect the new Items after installing the updated widget. Follow the official
[MainUI widget documentation](https://www.openhab.org/docs/ui/building-pages.html)
and [Homie channel documentation](https://www.openhab.org/addons/bindings/homie/).

Preserve existing names, semantic groups, persistence and links. Writable Items
need `autoupdate=false` and the Standard link profile; only device readback should
confirm state. See [existing control configuration](openHAB.md) for mode/light
options and the confirmed Dimmer mapping for PV percentage. The brightness options
are low=5191, medium=5190 and high=5173. Switch commands are ON/OFF, translated by
the Homie binding to boolean payloads.

## Command behavior

When explicitly enabling live controls, local commands require `apiStatusItem=ready`
and a configured local result Item without pending/uncertain/unknown feedback.
Portal commands use the independently configured portal status/result instead.
The bridge's existing command gates and identity/rights/readback checks remain
mandatory. The widget does not change any bridge gate.

Permission and charging mode are independent: Erlauben grants charging permission;
Sperren revokes it while keeping the selected mode. Ladestopp is a mode that stops
the charging process. Permission alone does not force charging during PV waiting.
The persistent approval-required setting is a separate access-control preference.

Mode buttons are checked from device readback (or local demo selection). The PV
slider is shown only for mode 4719; live mode changes become visible after readback.
Target charging toggles the inline plan form rather than sending mode 4720 directly.
An active mode-4720 plan keeps the form visible. Opening the form is labeled as a
draft while another mode remains active; only Apply can activate the device mode.
Selecting PV/fast/stop closes a manually opened plan draft; fields remain staged.
Further settings expand through the header link or the settings button.
The PV draft starts from the observed percentage at widget creation; subsequent
device updates do not overwrite an unsent draft.

Editing the energy/date fields or moving the PV slider changes only widget variables.
Explicit Apply submits the combined plan JSON or integer PV percentage. There is
no direct mode-4720 command and no separate plan-energy or plan-end setter.
An active target plan must first be left explicitly before replacing it.
The browser timezone and UTC offset are shown before plan submission.

The PV section contains only percentage, slider and Apply. PV minimum is a preference,
not a measured solar fraction. The plan section contains energy, departure and Apply;
the date input title includes its UTC offset. An active-plan notice remains compact.

The large feedback card is removed. Small status marks appear beside Apply: a check,
pending ellipsis, or a short error/uncertainty notice. Tooltips describe these as the
last source feedback. A success check requires fresh source readiness, a confirmed
result and matching current inputs/readback. Plan checks additionally require active
mode 4720, matching energy (kWh or Wh) and the same end instant. A previous confirmed
result alone never confirms changed inputs. These marks show matching current device
settings; the shared result cannot correlate a particular command invocation.
Demo checks are explicitly labeled Demo and compare against local submitted drafts.
Uncertain results continue to block further commands; the widget performs no retry.

The station icon defaults to `iconify:mdi:ev-station`. Set `chargerIcon` to
`iconify:tabler:charging-pile` or `iconify:mdi:ev-plug-type2` for alternatives.
It is green while charging, gray otherwise, red for a reported charging-point error,
and orange if measurement-source readiness is unknown/stale. Iconify needs an online
connection for uncached icons. Further settings use neutral gray (`#8e8e93`).

The availability Items are regular operational values and remain published when the source
DIAGNOSTICS_ENABLED flag is false. Their existing Channel IDs are unchanged.
Source readiness is not per-property freshness or MQTT connection freshness.
Last-known session/status values may be older than power. An absent/non-ready
measurement source is marked as unknown/last values. A per-property age display
and immediate broker-offline detection remain future improvements.

## Validation boundary

YAML lint and offline expression/command checks do not certify MainUI rendering.
Review desktop/mobile layout, plan expansion and settings expansion in the actual openHAB instance,
initially in demo mode. User-reported live PV acceptance covered 90 → 70 → 90, confirmed readback, draft initialization after reopening and absence of HTTP 415. This does not certify every control or remaining iOS layout checks.
The existing BMW widget source was not supplied; exact visual matching remains pending.

## Official references

- [Personal widgets](https://www.openhab.org/docs/ui/personal-widgets.html)
- [File-defined widgets](https://www.openhab.org/docs/configuration/yaml/widgets)
- [List Item](https://www.openhab.org/docs/ui/components/oh-list-item.html)
- [Input variables](https://www.openhab.org/docs/ui/components/oh-input.html)
- [Slider variables](https://www.openhab.org/docs/ui/components/oh-slider.html)
- [Widget expressions](https://www.openhab.org/docs/ui/widget-expressions-variables.html)
- [Button actions](https://www.openhab.org/docs/ui/components/oh-button)

- [Iconify support and icon colors](https://www.openhab.org/docs/ui/components/oh-icon)
- [SMA charging authorization](https://manuals.sma.de/EVCxx20/de-DE/14065364491.html)

## Mobile layout trial and vehicle connection

The target-mode button always reads **Zielladen**; the short draft notice remains
inside the plan form. Buttons use their default content slot: an icon directly beside
the label, centered together, and 40 px height. Permission/mode rows use two equal
columns with no minimum column width. Mode order is PV, fast, target, then stop.
Labels remain single-line with an ellipsis as an overflow fallback. Additional
settings keep a short constant label too. This layout is a trial for iOS MainUI;
actual device rendering and larger accessibility fonts still need review.

A paired car (`iconify:mdi:car-outline`) and Type-2 plug
(`iconify:mdi:ev-plug-type2`) indicator below the header shows
Auto angeschlossen, Kein Auto angeschlossen, Gesperrt, Ladefehler or Status unbekannt. It uses the
existing `statusItem` and `measurementStatusItem`; no extra Item is required.
Only fresh Verbunden / wartend and Lädt states prove connection; Nicht verbunden
proves disconnection. Fresh Gesperrt and Fehler am Ladepunkt states show the short labels Gesperrt and
Ladefehler, retaining the orange indicator because attachment is not established.
Unknown or non-ready sources show Status unbekannt. Charging permission and zero power are never used as
attachment evidence. Per-property age remains unavailable in the existing bridge
interface, so source readiness alone cannot guarantee the vehicle status timestamp.
Set `demoConnected: false` to preview a disconnected vehicle without any device I/O.

The settings list overrides nested-list and item padding to avoid wasted indentation.
The PV slider shows scale markers every 10% while retaining 1% input steps.

Item-selector captions follow the bundled German bridge translations exactly.
For the three source-availability Items, select the matching measurement, local API
or portal source using the German field description. Custom host translations or
existing manually named Items may use different labels.

The PV slider context is created only when the selected Item has a valid integer
percentage (0–100). Its initial draft is the current raw Item state, including
late-arriving states after opening the widget. Moving the slider only edits that
draft; subsequent Item updates do not overwrite it. Reopening the PV section
initializes a new draft from the current Item. Missing values show a placeholder
without a slider. Demo initialization remains 70%.

PV and charging-plan submissions use the explicit apply button without a second
confirmation dialog. PV commands use expression-supported string concatenation;
the MainUI expression context does not provide the JavaScript String constructor.

Apply buttons are compact (32 px high, 11 px text, 14 px icons). The PV slider
reserves 24 px below it for the scale, separating the scale labels from the button.
