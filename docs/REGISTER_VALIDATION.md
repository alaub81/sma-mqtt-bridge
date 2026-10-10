# Register validation

Evidence date: 2026-10-10. The three bundled profiles now contain the existing 41 read channels plus three identity properties per device. Validation means that mappings were checked against official model-specific SMA lists, deterministic decoding tests and a bounded local FC04 read. It does not mean that openHAB migration or every operating state has been accepted.

## Source evidence

| Profile | Official register evidence | Installed firmware verified locally |
| --- | --- | --- |
| `sma-stp8-0-3av-40` | [Parameter-STP8-10-3AV-40 V13](https://files.sma.de/downloads/Parameter-STP8-10-3AV-40_V13.zip), [GG10 variant](https://files.sma.de/downloads/Parameter-STP8-10-3AV-40__GG10_V13.zip), valid from 4.00.61.R | 4.10.10.R |
| `sma-sbs3-7-10` | [MODBUS-HTML SBS3.7-6.0-10 V13](https://files.sma.de/downloads/MODBUS-HTML_SBS3.7-6.0-10-V13.zip), valid from 3.12.33.R | 4.07.31.R |
| `sma-sb4-0-1av-41` | [PARAMETER-HTML SBxx-1AV-41 V16](https://files.sma.de/downloads/PARAMETER-HTML_SBxx-1AV-41-V16.zip), [GG10 variant](https://files.sma.de/downloads/PARAMETER-HTML_SBxx-1AV-41-GG10_V16.zip), valid from 4.01.15.R | 4.10.10.R |

Public source archives were downloaded for verification; their original copyrighted documents and installation responses are not redistributed. The non-GG10/GG10 lists agree on the selected read mappings. No country dataset or Grid Guard setting was changed. Runtime compatibility is intentionally limited to the locally checked firmware versions. Additional firmware needs explicit profile evidence.

| Download | SHA-256 |
| --- | --- |
| `Parameter-STP8-10-3AV-40_V13.zip` | `bc5511e76a5a61315ecf5d5a5ccb07abaeaa6294a26f0efd3ddc0e6b1a059ec5` |
| `Parameter-STP8-10-3AV-40__GG10_V13.zip` | `55adb7dc2c662ff403d225fa24eec05c8534f6640af11e76d0f903b4ffa95218` |
| `MODBUS-HTML_SBS3.7-6.0-10-V13.zip` | `091458b2a64bf73f40fc60f689677ffe9d78e943dd9f77ce936d9f6094d42a18` |
| `PARAMETER-HTML_SBxx-1AV-41-V16.zip` | `55d68deb25789c4ba6480d2cf15e59ee8223d9b71019d264b2ba3f048c070c7a` |
| `PARAMETER-HTML_SBxx-1AV-41-GG10_V16.zip` | `677c247992d5ca8ed0c862160bebd230c883a9d7f66b4e585fa54cbf8646399a` |

## Encoding and migration corrections

The [official SMA Modbus interface description](https://files.sma.de/downloads/SMA-Modbus-TI-en-10.pdf), sections 3.5.4–3.5.8, defines big-endian words/bytes, numeric NaN sentinels, fixed-point scaling and firmware encoding. Firmware major/minor bytes use BCD; the build byte is binary and release code 4 is R. Identity uses model 30053, serial 30057 and firmware 30059; the model codes 9347/9356/9403 were confirmed both in the corresponding lists and at the configured local endpoints. The serial guards are stored only in the private `smab.env`.

Unsigned values formerly decoded as signed in some Things now use the documented U32 type. A counter above 2³¹ must remain valid. U32 invalid is 0xFFFFFFFF; S32 invalid is 0x80000000; unavailable status is 0xFFFFFD. Invalid or unsupported values remain unavailable rather than becoming zero. Existing German condition/contactor/battery strings are preserved. Genuine negative signed measurements remain signed, so their old negative-to-zero/UNDEF transforms must be reviewed during parallel acceptance.

**Energy units differ by model:** Tripower and Sunny Boy addresses 30531/30537 are whole kWh; Storage documents these addresses in Wh. Storage retains Wh on MQTT, allowing openHAB quantity conversion to kWh. The Tripower parameter UI leaves some measurement-unit cells blank: current/voltage/power/temperature dimensions are reconciled with the identified source channel, format and existing quantity Items; no new register is inferred from another model.

Each original FC04 block and 3–180-second poller interval is preserved. Each property expires after the larger of its configured stale threshold and twice its effective poller interval; slower energy polls do not extend the freshness of fast power channels.

## Implemented read mappings

| Device | Homie property under measurements | Address | Raw type | Scale | MQTT unit | Poll seconds |
| --- | --- | --- | --- | --- | --- | --- |
| inverter1 | status | 30201 | uint32 | 1 | — | 60.0 |
| inverter1 | grid-contactor | 30217 | uint32 | 1 | — | 60.0 |
| inverter1 | power-drawn | 30865 | int32 | 1 | W | 5.0 |
| inverter1 | power-grid-feed-in | 30867 | int32 | 1 | W | 5.0 |
| inverter1 | day-yield | 30537 | uint32 | 1 | kWh | 180.0 |
| inverter1 | total-yield | 30531 | uint32 | 1 | kWh | 180.0 |
| inverter1 | current-a-input | 30769 | int32 | 0.001 | A | 3.0 |
| inverter1 | voltage-a-input | 30771 | int32 | 0.01 | V | 3.0 |
| inverter1 | power-a-input | 30773 | int32 | 1 | W | 3.0 |
| inverter1 | active-power | 30775 | int32 | 1 | W | 3.0 |
| inverter1 | current-b-input | 30957 | int32 | 0.001 | A | 5.0 |
| inverter1 | voltage-b-input | 30959 | int32 | 0.01 | V | 5.0 |
| inverter1 | power-b-input | 30961 | int32 | 1 | W | 5.0 |
| inverter1 | internal-temperature | 34113 | int32 | 0.1 | °C | 120.0 |
| inverter2 | status | 30201 | uint32 | 1 | — | 60.0 |
| inverter2 | grid-contactor | 30217 | uint32 | 1 | — | 60.0 |
| inverter2 | day-yield | 30537 | uint32 | 1 | Wh | 180.0 |
| inverter2 | total-yield | 30531 | uint32 | 1 | Wh | 180.0 |
| inverter2 | current-bat-stat-charge | 30845 | uint32 | 1 | % | 30.0 |
| inverter2 | current-batcapacity | 30847 | uint32 | 1 | % | 30.0 |
| inverter2 | current-bat-temp | 30849 | int32 | 0.1 | °C | 120.0 |
| inverter2 | battery-status | 30955 | uint32 | 1 | — | 60.0 |
| inverter2 | pres-bat-charge | 31393 | uint32 | 1 | W | 5.0 |
| inverter2 | pres-batt-discharge | 31395 | uint32 | 1 | W | 5.0 |
| inverter2 | internal-temperature | 34113 | int32 | 0.1 | °C | 120.0 |
| inverter3 | type | 30053 | uint32 | 1 | — | 60.0 |
| inverter3 | status | 30201 | uint32 | 1 | — | 20.0 |
| inverter3 | grid-contactor | 30217 | uint32 | 1 | — | 20.0 |
| inverter3 | max-power | 30231 | uint32 | 1 | W | 20.0 |
| inverter3 | set-max-power | 30233 | uint32 | 1 | W | 20.0 |
| inverter3 | power-drawn | 30865 | int32 | 1 | W | 5.0 |
| inverter3 | power-grid-feed-in | 30867 | int32 | 1 | W | 5.0 |
| inverter3 | day-yield | 30537 | uint32 | 1 | kWh | 60.0 |
| inverter3 | total-yield | 30531 | uint32 | 1 | kWh | 60.0 |
| inverter3 | current-a-input | 30769 | int32 | 0.001 | A | 3.0 |
| inverter3 | voltage-a-input | 30771 | int32 | 0.01 | V | 3.0 |
| inverter3 | power-a-input | 30773 | int32 | 1 | W | 3.0 |
| inverter3 | active-power | 30775 | int32 | 1 | W | 3.0 |
| inverter3 | power-l1 | 30777 | int32 | 1 | W | 3.0 |
| inverter3 | volt-g1 | 30783 | uint32 | 0.01 | V | 3.0 |
| inverter3 | internal-temperature | 34113 | int32 | 0.1 | °C | 120.0 |

## Installation observations

The first bounded read returned 39 of the 41 measurement channels, plus all nine identity properties. Sunny Boy registers 30777 (`power-l1`) and 30783 (`volt-g1`) returned SMA NaN; their mappings remain declared but no value is published. Check again during daytime operation and compare with openHAB before classifying this as unsupported. SEMP identity matched the configured eCharger. Seven baseline SEMP values were usable; the device-health measurement had an old source timestamp and was withheld. Neither local API nor portal authentication was attempted without credentials. No device write was performed.

Home Manager remains disabled for the Mac: the Mac is on a different network and does not receive meter multicast. Complete sender/serial/interface configuration and acceptance on the Raspberry Pi in the device network. Existing openHAB rules, offsets, historical counter corrections and persistence remain untouched.
