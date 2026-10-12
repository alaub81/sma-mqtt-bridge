# eCharger plant-control observations

## Publication contract

All three properties are implemented read-only in the **Advanced** group and
owned by the SEMP reader, although the local API also returns the raw channels:

| Compact MQTT property | Raw channel suffix | Current interpretation |
| --- | --- | --- |
| `control/activechargingcount` | `PlantControl.PCC.ChrgActCnt` | Candidate Home Manager active-station count; not an instantaneous charging flag |
| `control/powersetpointmaxpercent` | `PlantControl.Inverter.WModCfg.WCtlComCfg.WSptMaxNom` | Candidate upper normalized power-control observation; unit/reference/effect unresolved |
| `control/powersetpointminpercent` | `PlantControl.Inverter.WModCfg.WCtlComCfg.WSptMinNom` | Candidate lower normalized power-control observation; unit/reference/effect unresolved |

The full raw channels start with `Setpoint.`. Publication requires explicitly
enabled SEMP and `SMAB_ECHARGER_ADVANCED_CHANNELS_ENABLED=true`. Diagnostics is
independent and is not required for these control-node properties. The Advanced
flag defaults to true, but an explicit ENV/JSON setting may disable it. Credentials
or a host address do not enable SEMP. Enabling API alone does not provide these
three supplemental MQTT mappings.

Their existing Homie metadata is float, without unit and with `$settable=false`.
The `percent` suffix is an existing ID, not proof of engineering units. Do not
rename topics or infer a percent-to-watts conversion from that name. Other-device
Modbus channels with matching names are comparative context, not a verified
mapping for this eCharger model/firmware.

## Observation evidence, 2026-10-12

The two supplied timestamp files were rechecked in rotation order, separately for
API and SEMP. Counts and freshness behavior are recorded in the
[timestamp matrix](echarger-timestamp-classification-2026-10-12.csv). Each control
channel has 202 API and 270 SEMP records. ChrgActCnt changes twice in each
transport; both power-limit observations have one unchanged value throughout.
Original private files remain unchanged. No new live request was sent.

The count becomes nonzero around the connected/charging transition and returns
to zero around the later disconnected transition. Crucially, it stays nonzero
through observed waiting states and zero charging power, including a substantial
idle interval after the second positive-power period. This directly rules out
using that observed value as an instantaneous local "currently drawing charging
power" flag. Use the confirmed vehicle-status and charging-power measurements
for that purpose instead, with their independent source freshness.

The [official SMA Multi-EVC description](https://manuals.sma.de/EVCxx20/de-DE/14332681099.html)
says the Home Manager supplies the active-station count once per minute and uses
it to divide the maximum charging current among active stations. Its discussion
also covers phase symmetry and fallback when controller communication fails.
This supplies a plausible functional explanation for ChrgActCnt. It does not name
that raw channel or define the exact membership of "active" in the supplied local
responses. Treat the channel association as an inference until matching metadata
or an explicit manufacturer contract confirms it. A single observed charging
station does not establish plant-wide counting or multi-station behavior.

Both normalized-limit candidates remain unchanged across idle, positive-power
and waiting observations, while their timestamps refresh regularly. The recorded
API metadata contains no unit for these channels, and the retained SEMP XML gives
value/timestamp but no engineering-unit/reference-power contract. Exact-name
web searches did not yield a matching official channel definition in this review.
Consequently, the evidence does not determine their norm basis, sign convention,
control activation or whether this operating mode applies them at all.

## Separate settings and remaining questions

These observations are distinct from:

- `portal/pvminimum`: the configured minimum PV preference, not measured supply mix;
- `settings/maxchargepower`: the separately verified local WMaxIn limit in watts;
- instantaneous `measurements/power` and vehicle-status observations.

The [official SEMP description](https://manuals.sma.de/EVCxx20/en-US/15906683019.html)
confirms the Home Manager's load-control role, but does not specify these
channel-level units. Preserve the Home Manager as controller. No setter or
competing regulation follows from these observations.

Still open: exact active-station membership and scope, direct raw-channel mapping
to Multi-EVC count, normalized-limit units/reference/sign and when they affect
charging. Continue with matching local metadata or targeted observations during
naturally occurring operating states. Do not trigger charging, alter limits or
change channel groups to manufacture evidence. Do not enable additional groups
midway through the current resource baseline without an explicit decision to
start a new measurement segment.
