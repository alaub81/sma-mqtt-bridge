# Sunny Home Manager 2.0 reads

Select UDP or Modbus TCP explicitly; only one transport owns the meter values.
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
