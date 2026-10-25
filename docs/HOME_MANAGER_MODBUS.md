# Sunny Home Manager 2.0 reads

Select UDP or Modbus TCP explicitly; only one transport owns the total power and energy counters.
An address never enables the adapter. A serial selector is required for both.
See [configuration](CONFIGURATION.md) for ports, intervals and network variants.

## Modbus identity and reads

The bundled `sma-home-manager-2-modbus` profile defines separate Unit 1 identity,
Unit 2 plant values, assignment discovery and delegated read templates. Check
model, class, manufacturer and both serial copies before downstream reads.
Discover delegated units through the fresh assignment table; do not assume fixed
installation assignments. Advanced controls delegated reads; mandatory identity
checks remain independent of publication groups. All mappings are read-only.

Modbus server enablement and access rights are installation prerequisites. The
bridge does not send a Grid Guard login or alter device configuration. The
[profile schema](PROFILES.md#home-manager-modbus-read-profile) describes the
identity fields, mapping rules and assignment limits. Protocol evidence is retained
in the bundled profile; no universal firmware register is invented.

## Transport limitations

Verify identity, units, import/export direction, unavailable sentinels, intervals
and recovery against the actual hardware. Successful Modbus reads do not accept
Linux UDP multicast/interface/VLAN behavior. Do not infer that Home Manager serves
all configuration or charger controls through either meter transport. Keep device assignment tables, serials and measured values private.

## Phase measurements

UDP publishes read-only Basic measurements for each phase L1–L3:
`measurements/powerdrawnl1` through `powerdrawnl3` (W),
`measurements/powergridfeedinl1` through `powergridfeedinl3` (W),
`measurements/currentl1` through `currentl3` (A), and
`measurements/voltagel1` through `voltagel3` (V).
Import and export are separate nonnegative observations. For signed net power,
subtract export from import for the same phase; never reconstruct phase power
by dividing a total by three. Missing channels remain unavailable, not zero.

The documented Home Manager NSD Modbus registers expose only all-phase totals.
To keep Modbus totals, identity and delegated reads while receiving phase values,
set these options in the private root `smab.env`:

```dotenv
SMAB_HOME_MANAGER_ENABLED=true
SMAB_HOME_MANAGER_TRANSPORT=modbus-tcp
SMAB_HOME_MANAGER_UDP_PHASES_ENABLED=true
```

The existing Modbus host and serial remain required. Optional
`SMAB_HOME_MANAGER_UDP_HOST` restricts supplemental UDP to one IPv4 sender;
it does not replace the mandatory serial check. UDP-only mode uses the existing
`SMAB_HOME_MANAGER_HOST` sender filter and includes phases without the new flag.
Optional JSON equivalents are `homeManager.udpPhasesEnabled` (boolean, default
false) and `homeManager.udpHost` (string, default empty); explicit ENV wins.

The supplemental source `home-manager-phases` shares the configured Homie device
but owns only phase properties. It runs and expires independently of Modbus.
Its failure cannot replace Modbus totals/counters, refresh phase values from
Modbus, or change the plant energy binding. It does not change the device's main
availability; enable Home Manager Diagnostics to inspect its separate source
status. The flag never activates a disabled Home Manager and does not add a
second listener in UDP-only mode.

UDP needs direct delivery or multicast reachability on the configured interface,
group and port, including when used beside Modbus. On Linux the standalone
`compose.host.example.yml` provides host networking. All existing Home Manager
UDP network/timeout/staleness settings apply. No device configuration or charging
control writes are performed.

Protocol references: [SMA meter protocol, sections 3.1 and 3.3](https://cdn.sma.de/fileadmin/content/www.developer.sma.de/docs/EMETER-Protokoll-TI-en-10.pdf),
[SMA Home Manager Modbus assignment tables](https://files.sma.de/downloads/HM-20-Modbus-NSD-TI-en-12.pdf),
and [openHAB Energy Meter channels](https://www.openhab.org/addons/bindings/smaenergymeter/).
