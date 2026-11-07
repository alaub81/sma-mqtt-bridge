# Charging-plan widgets

The optional `smabChargingPlan` card prepares target energy and departure time
for the SMA eCharger. `smabChargingPlanList` opens that card in a popup. Both use
the same three Items. The [eCharger comfort widget](echarger-comfort.md) already
contains an inline plan form, so this pair is useful for separate cards or Item
list entries.

## Install

Choose one installation method per UID:

- Copy [charging-plan.yml](yaml/widgets/charging-plan.yml) into
  `$OPENHAB_CONF/yaml/widgets/`. With Docker, use the host directory mounted at
  `/openhab/conf/yaml/widgets/`. This one file installs both UIDs.
- Follow the [MainUI import guide](mainui/README.md), importing
  [smabChargingPlan.yaml](mainui/widgets/smabChargingPlan.yaml) first and then
  [smabChargingPlanList.yaml](mainui/widgets/smabChargingPlanList.yaml).
  Keep both supplied UIDs so the popup dependency resolves.

Installation creates no Items or rules. Unlike the comfort widget, this pair
has no demo mode or `enableControls` switch. Editing the input fields sends no
command; submission requires the button and its confirmation dialog.

## Link Items and configure the widget

Follow the [openHAB Item guide](openHAB.md) to discover the eCharger channels.
Use String Items with the following links:

| Parameter | Channel | Purpose |
| --- | --- | --- |
| `item` | `commands#plan` | Combined plan command and confirmed plan JSON |
| `modeItem` | `settings#chargemode` | Current confirmed charging mode |
| `resultItem` | `commands#localresult` | Local command feedback |

Use the Standard link profile and set `autoupdate=false` on writable Items so
readback supplies confirmed state. For an Item list, select
`smabChargingPlanList` as the plan Item's **Default List Widget**. For a standalone
view, select `smabChargingPlan` as its **Default Standalone Widget**, or add the
card to a Page through Personal widgets. Configure all three parameters for each
widget instance.

Example Page component with fictional Item names:

```yaml
component: widget:smabChargingPlan
config:
  item: Example_Charger_Plan
  modeItem: Example_Charger_Mode
  resultItem: Example_Charger_LocalResult
```

Local commands require the enabled local eCharger adapter and both bridge gates:
`SMAB_COMMANDS_ENABLED=true` and `SMAB_ECHARGER_COMMANDS_ENABLED=true`.
The widget does not enable them. The standalone plan uses the local API; it
does not require the portal's PV-percentage command path. See the
[command contract](../docs/CONFIGURATION.md#combined-charging-plan-and-portal-pv-commands).

## Prepare and submit a plan

1. Enter positive target energy in kWh and a future local end date/time.
2. Check **Endzeit mit Zeitzone**. It uses the browser's timezone and shows the
   UTC offset. Review it around daylight-saving transitions.
3. Select **Ladeplan übernehmen** and confirm to send one JSON command containing
   both `energyKWh` and `endTime`.
4. Read the local feedback and the confirmed plan. The bridge validates device
   bounds and permissions, reads back both settings, then activates target mode.
   Charging release remains separate.

The button allows known non-plan modes `4718`, `4719` and `4721`. To change an
active plan (`4720`), first explicitly select PV, fast or stop mode using your
existing mode control. Input fields start empty and are not populated from an
old plan. Opening, typing in or reloading the card does not submit a plan.

## Feedback and unavailable controls

The card displays the last confirmed plan and raw local feedback. These are
not confirmation of the currently staged input. `pending` means work is in
progress; `confirmed` and `already-confirmed` indicate successful readback.
`rejected*` indicates that a command was not accepted. Unknown mode or feedback
values and pending/uncertain commands disable submission. NULL/UNDEF feedback
is allowed before the first command.

For `uncertain`, `blocked-uncertain` or `blocked-corrupt`, follow the
[command recovery guide](../docs/CONFIGURATION.md); do not submit repeated copies
to guess whether a change succeeded. UI validation does not replace the bridge's
current metadata, permissions and readback checks, and feedback alone does not
establish that the vehicle reached its energy target.

For a first UI check, verify Item selection, popup opening, time preview and
button gating without submitting. A real plan submission changes device settings.

Official references: [personal widgets](https://www.openhab.org/docs/ui/personal-widgets)
and [file-defined widgets](https://www.openhab.org/docs/configuration/yaml/widgets.html).
