# openHAB setup and eCharger controls

This guide connects the SMA MQTT Bridge to openHAB through Homie discovery and configures
MainUI widgets with your own Items. No generated `.items` file or sitemap is required.
Item names and complete Thing/Channel UIDs belong to your installation; this guide never
assumes a broker Thing ID. Keep existing names, groups, rules and persistence where possible.
UI labels are German; repository instructions are English.

## Before you start

Use openHAB 5.2+ for the supplied file-defined widgets; the documented percentage mapping
and MainUI behavior were checked with 5.2.1. The bridge must already publish to a broker
reachable by openHAB. Bridge and openHAB each need their own broker connection settings.
MQTT credentials, TLS trust and topic permissions are configured independently in each.
See [bridge configuration](../docs/CONFIGURATION.md) for `smab.env` and source activation.

Start with reads. All bridge sources and command gates default to disabled; providing an
address or credentials never enables an adapter. Enable only the sources you have configured.
Use `SMAB_LANGUAGE=de` for the German bridge labels used in the widget Item selectors.
The Home Manager remains the charging regulator. Do not run legacy HTTP control rules
alongside new Homie command links for the same settings.

## Discover Things and link Items

1. Install the **MQTT binding** in MainUI and configure an MQTT Broker Thing, or reuse your
   existing broker Thing. Verify its connection before adding device Things.
2. Start the bridge with the intended read sources enabled. Scan the MQTT binding in the
   Inbox and add the discovered Homie devices under the correct broker. The default Homie
   prefix is `homie`; match a changed prefix in the Homie configuration. Each inverter,
   Home Manager and eCharger is a separate Homie device, even though one container serves them.
3. Open **Settings → Things → the discovered device → Channels**. Link each needed channel
   to a suitable existing Item, or create an Item through MainUI. The suffixes below identify
   channels; copy the full UID from your actual Thing if it is needed elsewhere.
4. Check a few readings before configuring controls. Confirm Item type, source unit and
   update behavior. Use `Number:Power` for power and `Number:Energy` for energy. Display-unit
   metadata can change presentation; do not add another transformation to values already
   converted by the bridge. For inverter/Home Manager coverage use the
   [value catalogue](../docs/WERTEKATALOG.md) and [migration guide](../docs/MIGRATION.md).
5. Retain existing Item names and persistence history when migrating a link. Compare the old
   and new readings before switching; avoid two active measurement links updating one Item.
   Existing calculations, offsets, maps and rules are not migrated by Homie discovery.

A visible retained reading is a last-known observation, not proof of current communication.
Check source-availability Items as well as Thing status. These operational statuses remain
published with diagnostics disabled; existing availability Channel IDs are unchanged. An ONLINE Thing does not certify every
property's freshness. Missing values must not be replaced with invented zeros.

## Choose a MainUI widget

The [garage list widget](echarger-comfort.md) is the main integrated control/display option.
It combines power, session energy, vehicle connection, charging release, mode buttons,
PV preference, target charging and additional settings in one expandable entry.
The standalone charging-plan card below is optional; install it only if you also want
that separate dialog. Neither widget creates Items or channel links.

For the garage widget:

1. Copy [echarger-comfort.yml](yaml/widgets/echarger-comfort.yml) into
   `$OPENHAB_CONF/yaml/widgets/echarger-comfort.yml`. In Docker use the host directory
   mounted at `/openhab/conf`. Keep one definition per widget UID.
2. Add `sma_echarger_comfort_list` to a list on your MainUI page. First use
   `demoMode: true` and `enableControls: false` to inspect the layout without device I/O.
3. Set `demoMode: false`, keep controls disabled and select your existing Items in the
   widget properties. The complete 20-parameter mapping, German search labels and exact
   channel suffixes are in the [Item mapping table](echarger-comfort.md#connect-existing-items-later).
   In particular, distinguish measurement availability (SEMP or API), local API availability
   and portal availability even when all three Items have the same German label.
4. Enable controls only after checking the writable Item metadata below and the independent
   bridge write gates. Local actions need `SMAB_COMMANDS_ENABLED=true`,
   `SMAB_ECHARGER_ENABLED=true` and `SMAB_ECHARGER_COMMANDS_ENABLED=true`.
   Portal PV actions need the global gate, `SMAB_PORTAL_ENABLED=true` and
   `SMAB_PORTAL_COMMANDS_ENABLED=true`. The widget does not enable these gates itself.

Use the Item selectors rather than copying another installation's Item names or broker UID.
The YAML files are reusable after this explicit mapping; they are not a zero-configuration
installation. Do not create duplicate definitions in both files and the MainUI widget editor.

## Item configuration in MainUI

Open **Settings → Items → your Item → Add Metadata**. Set **Auto-update = false**
for every writable Item: only device readback should confirm its state. Use the Standard
channel link profile. The channel suffixes below follow the bridge's compact Homie IDs.

| Channel suffix | Item type | Purpose |
| --- | --- | --- |
| `settings#chargemode` | String | Charging mode |
| `settings#ledbrightness` | String | Status LED brightness |
| `settings#ambientbrightness` | String | Ambient brightness |
| `settings#maxchargepower` | Number:Power | Maximum charging power, W; German channel label: Maximale Ladeleistung |
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
Keep **Auto-update = false** and the Standard channel-link profile.

For **Default List Widget**, use the following widget metadata:

```yaml
value: oh-slider-item
config:
  min: 0
  max: 100
  step: 1
  ignoreDisplayState: false
  releaseOnly: true
  label: true
```

Use the existing PV Dimmer Item. A list component added directly to a custom page
also needs its `item` set to that Item; the metadata above selects the Item's
default list widget. `label` shows the selected value above the handle.
With the integer-percent State Description, keep `ignoreDisplayState: false`
to retain the formatted percent display. Raw-state mode is only needed if a
display transformation or rounding makes the slider misinterpret the value.
Do not set `unit: "%"`: the bridge expects a plain integer percentage command.
Input `60` means 60% minimum PV and at most 40% allowed grid share, not a measured
charging mix.

`releaseOnly: true` prevents commands during dragging and sends on release.
It does not require a separate Apply button. `type`, `sendButton` and
`useDisplayState` belong to the input-widget configuration and are not supported
slider-item settings. Use `ignoreDisplayState` to choose between display and
raw state; false preserves this percent display.
See the official [oh-slider-item options](https://www.openhab.org/docs/ui/components/oh-slider-item.html).

For **Default Standalone Widget**, use a slider card with the same send policy:

```yaml
value: oh-slider-card
config:
  step: 1
  min: 0
  max: 100
  ignoreDisplayState: false
  releaseOnly: true
  label: true
  scaleSteps: 10
  scale: true
```

`scale`/`scaleSteps` add visual scale markers; `step: 1` still controls the
selectable values. If used directly on a page instead of as default Item metadata,
use `component: oh-slider-card` and set `config.item` to the existing PV Dimmer.
See the official [oh-slider-card options](https://www.openhab.org/docs/ui/components/oh-slider-card.html).

For explicit submission, retain the input widget or use the comfort widget's
variable-based PV slider plus **Apply**. Its slider changes only a draft and
portal availability/command feedback gates the actual command. The standard
slider item above sends immediately on release and does not inherit those custom
widget gates; bridge validation and write gates remain authoritative.

Default List Widget `oh-input-item` / Default Standalone Widget `oh-input-card`
remain alternatives with `type: number`, `min: 0`, `max: 100`, `step: 1`,
`sendButton: true` and `useDisplayState: false`. Choose the existing PV Item.

### Maximum charging power

After rebuilding/recreating the bridge, the existing charger Homie Thing exposes
`settings#maxchargepower`, labeled **Maximale Ladeleistung** with `SMAB_LANGUAGE=de`.
The local API must be enabled. The existing global/local write gates enable its setter;
SEMP alone does not supply this parameter. Homie provides the channel automatically.
If the running Thing keeps old channel metadata, disable/re-enable it and check again,
preserving existing Item links.

Link a **Number:Power** Item with Unit **W**, Auto-update **false**, and the Standard
profile. Use label **Maximale Ladeleistung**, semantic **Setpoint**, and State Description
pattern **`%.0f W`**. For the observed three-phase configuration, set minimum **4500**,
maximum **22000**, step **1**. These UI bounds describe current installation evidence;
the bridge validates fresh device bounds on every command.

Default List Widget `oh-input-item` / Standalone Widget `oh-input-card`:

```yaml
type: number
min: 4500
max: 22000
step: 1
sendButton: true
useDisplayState: false
```

Enter **4500** for 4.5 kW, **11000** for 11 kW. Keep the input unit W; display conversion
alone is insufficient for a numeric input. No MAP/JS scaling is needed. The Homie
integer channel sends whole watts. Confirm readback and `commands#localresult` rather
than predicting success in openHAB. A 4 kW command is outside current device bounds.
This is a persistent upper limit, not a promise of single-phase operation; see
[the phase-switching investigation](../docs/ECHARGER_POWER_LIMIT.md).

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
A device write is a separate intentional user action. User tests confirmed this standalone
widget's rendering and timezone preview, plan transmission/mode activation, and garage-widget
PV changes. Completed physical target charging and the exact session-energy semantics remain
pending; see [the project diary](../todo.md).

## First checks and troubleshooting

| Symptom | Check |
| --- | --- |
| No Homie devices in the Inbox | Broker Thing connection, matching Homie prefix, enabled bridge sources and retained discovery/topic permissions. |
| Widget has placeholders | Selected Items, raw NULL/UNDEF states and the correct source-availability Items; installing YAML does not create links. |
| Timezone preview says “Bitte Endzeit wählen” | Actually select a complete date/time. Native browser date segments can be visible before the widget has a value. Verify the ISO offset after selection. |
| PV percentage differs by a factor of 100 | Use Dimmer with no Unit metadata, raw 0–100 values and the Standard link profile; do not compensate with another scale. |
| PV slider shows an old draft | An open draft is intentionally preserved. Reopen the PV section to initialize from the latest valid Item state. |
| Old `confirmed` result is visible | Local results are shared by local settings and plans; portal results are separate. Neither identifies a specific new command. Compare fresh readback to your intended values. |
| Target mode disappears quickly | Check result and mode history plus already delivered session energy. The wallbox returns to PV mode after target completion; local API total-versus-additional semantics are not fully accepted yet. |
| Apply is disabled | Check controls enabled, source readiness, mode, valid positive energy/future deadline and pending/uncertain/unknown feedback. Leave an active target plan explicitly before replacing it. |
| PV submission reports HTTP 415 | Update both the installed widget and any old editor copy. The corrected command uses supported text concatenation, not the unavailable `String()` expression constructor. |
| Command outcome is uncertain | Inspect actual device state and reconcile the durable journal as documented; do not resend or delete the guard blindly. |

For a PV test, record the initial percentage, move the draft without submitting, verify that
readback has not changed, then intentionally Apply one agreed value. Check portal feedback and
actual readback, reopen the widget and finally restore the initial setting. The user-reported
90 → 70 → 90 test passed, including initialization after reopening and no HTTP 415.

For a plan test, use an agreed energy and future deadline with a vehicle able to accept charge.
Verify both plan values and mode 4720, then observe actual charging and automatic return to PV.
Charging permission is separate. Do not automatically add session energy to the target or
repeatedly force target mode based on an old retained result.

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

## Wallbox total-energy migration to kWh

The local API total counter at `measurements#totalenergy` now publishes kWh with float
metadata. Both API source channels (`Measurement.Metering.GridMs.TotWhIn.ChaSta` and
`Measurement.Metering.GridMs.TotWhIn`) report Wh; the bridge divides the first fresh valid
value by 1000 exactly once. For example, 1234567.89 Wh becomes 1234.56789 kWh. The primary
channel retains priority; missing, invalid or stale values are not replaced with zero.
Session energy was already in kWh and is unchanged. The counter is read-only; no device
counter is reset and the existing MQTT topic, Channel UID and Item name can be retained.

### Upgrade the live Item

1. Record the deployment boundary, current counter and unit; back up the persistence store.
   Inspect the actual Item, link transformations, persistence aliases and affected rules.
2. During the update, pause affected persistence/rules or temporarily unlink the counter so
   the old retained Wh number cannot be recorded as kWh after the metadata update. Keep the
   MQTT topic manifest and state volume. Do not clear all retained topics or delete history.
3. Rebuild/recreate the bridge container. Wait for a fresh valid API reading, then verify
   MQTT `$unit=kWh` and the value divided by 1000 against the device's Wh counter. An old
   retained number during a source outage is not evidence that conversion has completed.
4. Keep the openHAB Item as `Number:Energy`, set Unit metadata to `kWh` and optionally set
   the State Description pattern to `%.3f kWh`. Remove a link/rule transformation that divides
   this new bridge value by 1000; retain unrelated historical offsets in their proper unit.
   Check the linked Channel metadata after discovery updates before resuming persistence.
5. Compare a new reading and a subsequent energy difference before resuming daily-energy
   rules or charts. Do not interpret a scaling boundary as a reset or huge energy change.

### Treat existing history according to its actual storage

Changing Item metadata or the bridge unit does not perform a database migration. Inspect
representative stored samples and the persistence service's unit configuration first:

- If old samples were already stored as kWh, preserve them unchanged.
- If old samples are raw Wh and new samples are kWh, normalize the old segment only, using
  a recorded timestamp boundary. For a read-only chart/query divide that segment by 1000;
  never apply the conversion to the entire mixed series or to new samples.
- If storage keeps everything in Wh despite the live display unit, keep a consistent Wh
  series and convert at query/display time rather than assuming a database unit change.
- Incorrectly labeled samples require independent evidence of their numeric scale before
  any correction. If the boundary is unknown, keep the original series and use a separate
  normalized series/alias after checking rule and chart dependencies.

Check `restoreOnStartup`, daily differences, offset calculations, Grafana/InfluxDB queries
and rules that strip units using plain numbers. A last historic numeric value must not be
restored with a different assumed scale. Query old/new endpoints in the same unit before
calculating a difference. Preserve Item names/aliases and original records where possible.
No database rewrite is performed by this bridge change. The installation-specific audit
and any chosen migration remain pending until actual persistence samples are inspected.
See official [Item units](https://www.openhab.org/docs/configuration/items.html) and
[persistence](https://www.openhab.org/docs/configuration/persistence.html) documentation.

## Home Manager plant time: display and rules

The bridge's `measurements#planttime` reports Unix seconds (UTC) from register
30193, not elapsed operating time. Keep the existing linked Number/Number:Time
Item, its seconds unit, parent groups and numeric persistence unchanged. A numeric
Item's date-format pattern alone cannot turn epoch seconds into a timestamp.

For display, use the original Item's State Description `pattern`. JavaScript
Scripting must be installed. This inline transformation accepts whole nonnegative
seconds, optionally with a trailing `s`, rejects invalid input/the SMA U32 sentinel,
and formats the instant in `Europe/Berlin` including daylight-saving changes:

```text
JS(|(function(i){var m=String(i).trim().match(/^([0-9]+)(?:\.0+)?(?:\s+s)?$/);if(!m)return 'Unbekannt';var n=Number(m[1]);if(!Number.isSafeInteger(n)||n<0||n>=4294967295)return 'Unbekannt';var t=Java.type('java.time.Instant').ofEpochSecond(n).atZone(Java.type('java.time.ZoneId').of('Europe/Berlin'));return Java.type('java.time.format.DateTimeFormatter').ofPattern('dd.MM.yyyy HH:mm:ss z').format(t);})(input)):%s
```

Paste the pattern directly into the UI field; its regular-expression backslashes
are literal script characters. No channel profile is changed on the
original Item. Display transformations leave the underlying numeric state intact.

For comparisons/rules, create a separate DateTime Item with its own name. Add
it to the appropriate equipment group without copying numeric persistence groups
or replacing the original Item. Link it to the same existing Homie planttime
channel. Select **SCRIPT ECMAScript** (`transform:JS`) and set only the Thing-to-Item
transformation (`toItemScript`):

```javascript
|(function(i) {
  var m = String(i).trim().match(/^([0-9]+)(?:\.0+)?(?:\s+s)?$/);
  if (!m) return 'UNDEF';
  var n = Number(m[1]);
  if (!Number.isSafeInteger(n) || n < 0 || n >= 4294967295) return 'UNDEF';
  return Java.type('java.time.Instant').ofEpochSecond(n)
    .atZone(Java.type('java.time.ZoneId').of('Europe/Berlin'))
    .toOffsetDateTime().toString();
})(input)
```

Leave both Item-command-to-Thing and Item-state-to-Thing transformations blank,
so nothing is propagated back to the read-only channel. Set the companion's
State Description pattern to `%1$td.%1$tm.%1$tY %1$tH:%1$tM:%1$tS`, readOnly to
true and autoupdate to false. It receives a real DateTime state from the source
instant, rather than the wall clock when an update happened. Do not select a
"timestamp on update/change" profile: that would represent receipt time.

The companion can be used in DateTime comparisons. Check its source availability
and timestamp age in any rule; a retained plant-time value is not proof of a live
Home Manager. No rule, device command, polling or bridge restart is required for
this link conversion. The existing numeric history remains the original series;
companion persistence, if needed, is configured separately.

References: official [transformations and script profiles](https://www.openhab.org/docs/configuration/transformations.html),
[JavaScript Scripting](https://www.openhab.org/addons/automation/jsscripting/) and
[Item types](https://www.openhab.org/docs/configuration/items.html).

## Manual portal refresh

With the portal adapter enabled, `portal/refresh` is a settable Homie string
property, independent of Advanced/Diagnostics and preference-write gates. Send
the exact non-retained payload `refresh` to
`<prefix>/<echarger-id>/portal/refresh/set`. This only requests a read; it never
changes the minimum PV preference or charging mode.

In MainUI, link a **String** Item to `portal#refresh` using the standard profile
and set `autoupdate=false`. Do not add restore-on-startup or a rule that sends
commands when this Item receives a state update. The same Item receives progress:
`queued`, `reading`, `completed`, `failed`, `auth-blocked`, or a rejection
(`rejected`, `rejected-retained`, `rejected-busy`). These states are feedback,
not commands. Existing PV Items keep their links and receive validated readback
on their existing topics.

Use this button inside an existing page/widget, replacing the example Item name:

```yaml
component: oh-button
config:
  text: Portal aktualisieren
  iconF7: arrow_clockwise
  action: command
  actionItem: ECharger_Portal_Refresh
  actionCommand: refresh
```

The existing portal supervisor performs the read with its normal authentication,
identity validation, timeout and retry policy. Repeated requests before a read
are merged; requests during a read share that read. A portal preference write
uses the same reader lock, so requests cannot perform concurrent portal I/O.
The MQTT consumer can reject a refresh while another command is in progress.
Authentication failures stay blocked until the service is restarted after fixing
the credentials or permissions; refresh does not bypass that protection.

Periodic polling remains enabled at its configured interval, counted from the
most recent successful read. With an interval of zero, refresh works without a
startup read unless the existing one-shot CLI option is explicitly used. Transient
failures retain normal bounded retries; clicks do not bypass retry delays.

This addition requires a future bridge deployment. Broker discovery and live
openHAB acceptance are still pending; the running resource baseline is unchanged.
Sources: [Homie binding](https://www.openhab.org/addons/bindings/homie/) and
[MainUI button](https://www.openhab.org/docs/ui/components/oh-button.html).
