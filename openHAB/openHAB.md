# openHAB eCharger controls

These examples configure existing MainUI Items linked to the SMA bridge. Keep existing
Item names, groups and persistence links. UI labels are German; the instructions are English.
Do not run legacy HTTP control rules alongside the new Homie command links.

## Item configuration in MainUI

Open **Settings → Items → your Item → Add Metadata**. Set **Auto-update = false**
for every writable Item: only device readback should confirm its state. Use the Standard
channel link profile. The channel suffixes below follow the bridge's compact Homie IDs.

| Channel suffix | Item type | Purpose |
| --- | --- | --- |
| `settings#chargemode` | String | Charging mode |
| `settings#ledbrightness` | String | Status LED brightness |
| `settings#ambientbrightness` | String | Ambient brightness |
| `portal#pvminimum` | Dimmer | Minimum PV percentage, integer 0–100 |
| `commands#plan` | String | Combined plan command and confirmed plan JSON |
| `commands#localresult` | String | Read-only local command feedback |
| `commands#portalresult` | String | Read-only portal command feedback |

For semantic modeling use **Setpoint** for adjustable settings/plan and **Status** for
feedback, inside your existing charger Equipment. Semantic tags do not grant write access.
Read-only `settings#planenergy`, `settings#planend` and `portal#gridshare` remain displays.

### Charging mode

Add these **State Description → Options** entries:

| Value | Label |
| --- | --- |
| 4718 | Schnellladen |
| 4719 | PV-Laden |
| 4720 | Zielvorgabenladen |
| 4721 | Stopp |

**Command Options** contains only 4718, 4719 and 4721 with the same labels.
Mode 4720 is activated by a complete plan, never by a direct mode command.
Use **Default List Widget = oh-list-item**, select the Item, set **Action = Options**
and **Action Item = the same Item**. Leave Action Options empty to use Command Options.
No MAP transformation file is required. For a standalone card, use `oh-label-card`
with the same Options action and Action Item.

### LED and ambient brightness

Both Items are Strings. Add the following to both **State Description → Options**
and **Command Options**:

| Value | Label |
| --- | --- |
| 5191 | Niedrig |
| 5190 | Mittel |
| 5173 | Hoch |

Configure `oh-list-item` / `oh-label-card` with the Options action as above.

### Minimum PV percentage

Use **Dimmer**, with no Dimension and no Unit metadata. In openHAB 5.2.1, the Homie
binding handles a settable `%` property as a percentage/Dimmer value. Linking it to a
Number:Dimensionless Item caused an observed factor-of-100 error; Andreas confirmed that
switching to Dimmer corrected it. Do not compensate by scaling the MQTT value.

State Description: minimum **0**, maximum **100**, step **1**, pattern **`%.0f %%`**.
Default List Widget `oh-input-item` and Default Standalone Widget `oh-input-card`:

```yaml
type: number
min: 0
max: 100
step: 1
sendButton: true
useDisplayState: false
```

Select the existing PV Item in both widgets. Input `60` means 60% minimum PV and at most
40% grid share. A Dimmer normally suggests a slider, but the input widget provides explicit
submission and avoids sending every intermediate change. `autoupdate=false` remains required.

## Install the charging-plan widgets

Copy **only [charging-plan.yml](charging-plan.yml)** into `$OPENHAB_CONF/yaml/`.
With Docker, copy it to the host directory mounted as `/openhab/conf/yaml/`.
Do not place it in the SMA bridge data directory. openHAB 5.2 supports file-defined widgets;
these definitions are read-only in MainUI. The file creates `smabChargingPlan` (card) and
`smabChargingPlanList` (popup opener) without creating Items or rules.

On your existing String Item linked to `commands#plan`, add:

- **Auto-update:** false.
- **Default List Widget:** `smabChargingPlanList`.
- **Default Standalone Widget:** `smabChargingPlan`.

For both widgets select the three parameters in MainUI:

| Parameter | Select your Item linked to |
| --- | --- |
| `item` | `commands#plan` |
| `modeItem` | `settings#chargemode` |
| `resultItem` | `commands#localresult` |

All names are configurable; no installation-specific Item or Thing UID is embedded.
The same card can be added to a custom page through **Personal Widgets**.
For manual MainUI import instead of file installation, create two widgets in
**Developer Tools → Widgets**: use each body below `widgets.<UID>`, add `uid: <UID>`
at its root, and omit the outer `version`/`widgets` keys. Do not install duplicate UIDs.

## Use and verify the plan dialog

Enter target energy in kWh and a future local date/time. Inputs only modify widget variables;
opening the widget, editing a field, or reloading a page sends nothing. The browser's timezone
is used and the generated ISO end time, including its UTC offset, is shown before submission.
Check that offset, particularly around daylight-saving changes; ambiguous/nonexistent local
clock times are interpreted by the browser. Whole seconds are included in the JSON payload.

Press **Ladeplan übernehmen** and confirm. The command is exactly one JSON object:

```json
{"energyKWh":12.5,"endTime":"2030-01-01T07:00:00+01:00"}
```

The button requires positive finite energy, a future end time, a known non-plan charging mode,
and no pending/uncertain command feedback. NULL/UNDEF feedback is allowed before the first
command. Unknown modes/results disable submission. Inputs are not initialized from an old plan.
To change an active plan (4720), first explicitly switch to PV, fast or stop mode.

The bridge validates device metadata, supported bounds/units and current permissions, confirms
both plan parameters, then activates mode 4720. UI validation is only a convenience; bridge
validation remains authoritative. Charging release is separate. Local commands require
`SMAB_COMMANDS_ENABLED=true` and `SMAB_ECHARGER_COMMANDS_ENABLED=true`; PV commands additionally
need the independently enabled portal adapter and `SMAB_PORTAL_COMMANDS_ENABLED=true`.

Read feedback: `pending` means in progress; `confirmed` / `already-confirmed` means readback
succeeded; `rejected*` means the command was not accepted. `uncertain`, `blocked-uncertain`
and `blocked-corrupt` require reconciliation according to
[the command journal documentation](../docs/CONFIGURATION.md). Do not retry blindly.
The widget displays raw feedback and the confirmed JSON plan, rather than an optimistic success.

Offline YAML/contract checks are separate from acceptance in a real MainUI. Verify file loading,
parameter selection, popup rendering, input validation and timezone preview without pressing Send.
A device write is a separate intentional user action. No live plan acceptance is claimed.

## Widget source

The following is the complete deployable file, including both widgets.

```yaml
version: 1
widgets:
  smabChargingPlan:
    props:
      parameters:
        - name: item
          label: Ladeplan-Item (commands#plan)
          type: TEXT
          context: item
          required: true
        - name: modeItem
          label: Lademodus-Item (settings#chargemode)
          type: TEXT
          context: item
          required: true
        - name: resultItem
          label: Befehlsrückmeldung (commands#localresult)
          type: TEXT
          context: item
          required: true
    component: f7-card
    config: {}
    slots:
      default:
        - component: f7-card-header
          config: {}
          slots:
            default:
              - component: Label
                config:
                  text: Ladeplan vorbereiten
        - component: f7-card-content
          slots:
            default:
              - component: f7-list
                slots:
                  default:
                    - component: oh-input-item
                      config:
                        title: Zielenergie (kWh)
                        type: number
                        variable: energy
                        min: 0
                        step: 0.1
                        required: true
                        outline: true
                        style:
                          margin-top: 0
                          margin-bottom: 8px
                          --f7-input-height: 36px
                          --f7-list-item-padding-vertical: 4px
                    - component: oh-input-item
                      config:
                        title: Endzeit (Browser-Zeitzone)
                        type: datetime-local
                        variable: end
                        required: true
                        outline: true
                        style:
                          margin-top: 0
                          margin-bottom: 8px
                          --f7-input-height: 36px
                          --f7-list-item-padding-vertical: 4px
                config:
                  style:
                    margin-top: 0
                    margin-bottom: 8px
              - component: f7-list
                config:
                  mediaList: true
                  style:
                    margin-top: 0
                    margin-bottom: 8px
                slots:
                  default:
                    - component: oh-list-item
                      config:
                        title: Endzeit mit Zeitzone
                        subtitle: '=vars.end && dayjs(vars.end).isValid() ? dayjs(vars.end).format(''YYYY-MM-DDTHH:mm:ssZ'')
                          : ''Bitte Endzeit wählen'''
                    - component: oh-list-item
                      config:
                        title: Zuletzt bestätigter Plan
                        subtitle: '=props.item ? items[props.item].state : ''Ladeplan-Item auswählen'''
                    - component: oh-list-item
                      config:
                        title: Letzte lokale Rückmeldung
                        subtitle: '=props.resultItem ? items[props.resultItem].state + '' · keine Bestätigung dieser Eingabe'' : ''Rückmeldungs-Item auswählen'''
              - component: Label
                config:
                  style:
                    display: block
                    white-space: normal
                    line-height: 1.5
                    margin-bottom: 8px
                  text: '=props.modeItem && items[props.modeItem].state === ''4720'' ? ''Zum Ändern zuerst auf PV-Laden,
                    Schnellladen oder Stopp wechseln.'' : ''Positive Zielenergie und eine zukünftige Endzeit eingeben.
                    Die Ladefreigabe bleibt separat.'''
              - component: oh-button
                config:
                  text: Ladeplan übernehmen
                  fill: true
                  disabled: =!(props.item && props.modeItem && props.resultItem && Number.isFinite(vars.energy *
                    1) && vars.energy * 1 > 0 && vars.end && dayjs(vars.end).isValid() && dayjs(vars.end).isAfter(dayjs())
                    && ['4718', '4719', '4721'].includes(items[props.modeItem].state) && ['NULL', 'UNDEF', 'confirmed',
                    'already-confirmed', 'rejected', 'rejected-retained', 'rejected-disabled', 'rejected-busy'].includes(items[props.resultItem].state))
                  action: '=(props.item && props.modeItem && props.resultItem && Number.isFinite(vars.energy * 1)
                    && vars.energy * 1 > 0 && vars.end && dayjs(vars.end).isValid() && dayjs(vars.end).isAfter(dayjs())
                    && [''4718'', ''4719'', ''4721''].includes(items[props.modeItem].state) && [''NULL'', ''UNDEF'',
                    ''confirmed'', ''already-confirmed'', ''rejected'', ''rejected-retained'', ''rejected-disabled'',
                    ''rejected-busy''].includes(items[props.resultItem].state)) ? ''command'' : ''none'''
                  actionItem: =props.item
                  actionCommand: '=JSON.stringify({energyKWh: vars.energy * 1, endTime: dayjs(vars.end).format(''YYYY-MM-DDTHH:mm:ssZ'')})'
                  actionConfirmation: Der vorbereitete Ladeplan wird an die Wallbox gesendet und Zielvorgabenladen
                    nach Bestätigung aktiviert. Fortfahren?
          config: {}
  smabChargingPlanList:
    props:
      parameters:
        - name: item
          label: Ladeplan-Item (commands#plan)
          type: TEXT
          context: item
          required: true
        - name: modeItem
          label: Lademodus-Item (settings#chargemode)
          type: TEXT
          context: item
          required: true
        - name: resultItem
          label: Befehlsrückmeldung (commands#localresult)
          type: TEXT
          context: item
          required: true
    component: oh-list-item
    config:
      title: Ladeplan konfigurieren
      icon: oh:time
      subtitle: Zielenergie und Endzeit gemeinsam übernehmen
      action: popup
      actionModal: widget:smabChargingPlan
      actionModalConfig:
        item: =props.item
        modeItem: =props.modeItem
        resultItem: =props.resultItem
```

## Official references

- [File-defined widgets](https://www.openhab.org/docs/configuration/yaml/widgets)
- [YAML configuration directory](https://www.openhab.org/docs/configuration/yaml/)
- [Default Item widgets and metadata](https://www.openhab.org/docs/tutorial/item_widgets.html)
- [Input widgets](https://www.openhab.org/docs/ui/components/oh-input-item.html)
- [Widget expressions and local variables](https://www.openhab.org/docs/ui/widget-expressions-variables.html)
- [Button actions and confirmation](https://www.openhab.org/docs/ui/components/oh-button.html)
- [Homie percentage-channel implementation](https://github.com/openhab/openhab-addons/blob/5.2.1/bundles/org.openhab.binding.homie/src/main/java/org/openhab/binding/mqtt/homie/internal/homie300/Property.java)

The local command result is shared by the combined plan and local settings commands, and may describe an earlier action. Portal commands have a separate result. Neither the last local result nor the last confirmed plan confirms the current unsent inputs.
