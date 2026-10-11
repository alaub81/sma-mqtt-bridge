# eCharger maximum charging power and winter phase switching

Evidence date: 2026-10-11. Device: EVC22-3AC-20, firmware 2.6.37.R.
The command path is implemented and offline tested. Device inspection was read-only;
no limit, minimum current, wiring, phase configuration or charging mode was changed.

## Homie command and mapping

| Field | Value |
| --- | --- |
| State topic with default ID | `homie/sma-echarger/settings/maxchargepower` |
| Command topic | `homie/sma-echarger/settings/maxchargepower/set` |
| Local parameter | `Parameter.Inverter.WMaxIn` |
| Datatype / unit | integer / W |
| German channel label | Maximale Ladeleistung |
| openHAB channel suffix / Item | `settings#maxchargepower` / Number:Power, Unit W |
| Observed current bounds | 4500–22000 W, confirmed and editable |
| Command gates | `SMAB_COMMANDS_ENABLED=true`, `SMAB_ECHARGER_COMMANDS_ENABLED=true`, independently enabled local API |

Publish only an explicit, non-retained whole-watt command. `4500` means 4.5 kW;
`4000` is rejected with the observed bounds, never rounded. The existing local result,
serialized API session, identity guard, durable uncertainty journal and one-attempt
PUT/readback mechanism apply. No write occurs on startup/reconnect. The setting is
available even when supplementary/diagnostic channels are disabled. SEMP does not
advertise an unavailable substitute. See [openHAB setup](../openHAB/openHAB.md#maximum-charging-power).

Fresh metadata must be confirmed/writable and provide valid min/max within this
model's documented WebUI envelope (1380–22000 W). Any offered step/choices also apply.
The unit must be W, explicitly supplied or verified for this exact model/firmware.
Missing bounds or unverified units fail closed; unknown firmware cannot use the unit fallback. Only confirmed integral
observations are published; an HTTP success or pending value does not confirm a state.

The installed official WebUI 1.46.0 uses `/api/v1/evcharger/config` for its configuration
screen. Its `maxChargePower` control uses label metadata 12195 and unit tag 18.
Local metadata maps these to `Parameter.Inverter.WMaxIn`, **Nennwirkleistung WMaxIn**,
and W. The scalar formatter applies no scale multiplier. A read-only configuration
comparison matched `maxChargePower` to the catalog's WMaxIn value; identity was checked
against the private serial guard. WMax instead uses metadata 10159 (**Nennwirkleistung
WMaxOut**) and is not a fallback setter. No current private values or identifiers are
included in public fixtures.

The WebUI validates 4500–22000 W for three-phase configurations and 1380–7400 W for
single-phase configurations. The present device catalog confirms the three-phase
bounds and offers no explicit unit or step. Integer watts follow the WebUI precision 0;
actual acceptance of all watt increments and writes during charging remain unverified.
The generic parameter PUT is the existing local write protocol. Its readback and
physical limiting effect for this newly added parameter still require a requested
live action; configuration-screen mapping alone does not establish that acceptance.

## Does a power limit hold single-phase charging?

**A 4.5 kW limit alone cannot be relied on to do so.** SMA says the eCharger automatic
phase switching is always active. With a 6 A minimum current, the switching threshold
is approximately 4.14 kW. A 4.5 kW upper limit still permits operation above that
threshold. A hypothetical effective cap below it would exclude the normal three-phase
minimum at nominal voltage, but 4000 W is outside this device's current allowed range.
This arithmetic does not establish the controller's actual phase-selection behavior.
Source: [official SMA eCharger FAQ](https://www.sma-sunny.com/sma-e-charger-haeufige-fragen/).

SMA documents an approximately 120-second pause between one- and three-phase charging
and an integrated hysteresis. It does not publish the full phase-selection algorithm
or hysteresis thresholds in these sources.
Source: [charging modes and automatic switching](https://manuals.sma.de/EVCxx20/en-US/14505538315.html).

The separate **minimum charging current** is relevant to the winter goal: SMA states
that raising it from 6 to 10 A shifts the switching threshold from approximately
4.14 to 6.9 kW. The local setting is `Parameter.Chrg.AMinCha`, unit tag 3 (A), precision
1; current metadata is confirmed/editable with bounds 6–32 A. This is different from
`Parameter.Inverter.AcALim`, which SMA describes as the circuit-breaker/current limit.
Source: [SMA device configuration](https://manuals.sma.de/EVCxx20/de-DE/14505536395.html).

**A possible controlled trial is a 4.5 kW cap together with 10 A minimum current.**
If phase selection uses the effectively limited power, the cap would remain below
the nominal 6.9 kW threshold. This is an inference, not a verified recipe or guaranteed
phase lock. Raising the minimum also raises the one-phase charging floor to about
2.3 kW at 230 V (from about 1.38 kW), so low-surplus periods may stop charging sooner.
Voltage, vehicle acceptance, the Home Manager's PV preference and controller behavior
matter. No minimum-current or phase-configuration setter was added in this milestone.

For permanently single-phase operation, SMA describes connecting **and configuring**
the station as single-phase. The phase-assignment field is an installation setting
and must match the electrical connection and meter phase assignment; merely changing
it through an MQTT seasonal switch is not an established solution.
Source: [SMA FAQ](https://www.sma-sunny.com/sma-e-charger-haeufige-fragen/) and
[configuration procedure](https://manuals.sma.de/EVCxx20/de-DE/14505536395.html).

## Remaining acceptance

- On an explicitly requested valid limit, confirm current identity/rights/bounds,
  exactly one PUT, confirmed WMaxIn readback and the observed physical charging cap.
- Compare phase currents L1/L2/L3 and charging power across sufficient PV variation,
  including Home Manager planning; do not infer phases from total power alone.
- A separate requested minimum-current trial needs concrete old/new settings, readback
  and observations of interruptions and the increased one-phase charging floor.
- Preserve Home Manager control, existing openHAB names/links/persistence and all
  uncertainty guards. No periodic competing SEMP power controller is introduced.
