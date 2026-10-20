# eCharger maximum charging power

The allowlisted local parameter is `Parameter.Inverter.WMaxIn`. Its Homie state is
`settings/maxchargepower`, integer W; commands use `/set` with an explicit,
non-retained whole-watt payload. The local API and both global/local command gates
must be enabled independently. SEMP is not a fallback setter.

Require confirmed writable metadata, identity, units and current bounds/choices.
A narrowly verified model/firmware unit fallback does not authorize other devices.
Missing or contradictory metadata fails closed. Serialize one PUT, preserve
uncertainty after ambiguous responses and confirm device readback before reporting
success. Startup and reconnection must not resend commands.

## Phase switching

A maximum-power preference is not a guaranteed single-phase lock. Phase behavior
also depends on minimum current, voltage, vehicle acceptance and the SMA controller.
Do not change phase assignment as a seasonal MQTT shortcut; it must match physical
installation. No automatic phase/minimum-current setter is introduced by this control.
Home Manager remains the charging regulator.

Consult the [SMA FAQ](https://www.sma-sunny.com/sma-e-charger-haeufige-fragen/) and
[official charging-mode documentation](https://manuals.sma.de/EVCxx20/en-US/14505538315.html).
Validate any explicitly requested live limit against current device metadata and
observed physical effect. Keep installation values and trial records private.
