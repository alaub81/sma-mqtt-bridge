# Home Manager NSD availability check

The user requested a local commit before a complete read-only Home Manager check.
Commit `1828a35` records the preceding eCharger audit and phase-power implementation.
The check then completed on 2026-10-12, approximately 10:28:56–10:29:16 Europe/Berlin.

The explicitly enabled Modbus transport, configured profile, address and serial guard
were used without changing root ENV or device configuration. Advanced inventory was
already enabled. One paced TCP session validated Home Manager model, class,
manufacturer and both serial properties before plant and assignment reads.
No firmware gate is claimed: this documented profile has no firmware identity register.

Only FC04 was sent. Unit 1 register 43090 was read using its documented unlocked-device
count semantics; no Grid Guard code was sent, no login/logout or other write occurred.
No MQTT connection, profile/group change or openHAB change was made.

## Results

| Section | Checked | Value | Valid zero | SMA NaN | Rejected/error |
| --- | ---: | ---: | ---: | ---: | ---: |
| Unit 1/2 fixed properties | 16 | 13 | 3 | 0 | 0 |
| Delegated parameter properties | 48 | 3 | 0 | 45 | 0 |

All 245 assignment slots were read in the nine documented blocks. Three occupied
slots had valid units 3–247; each received all sixteen delegated template reads.
There were no duplicate queried units, inaccessible assignment blocks, undecoded
enums, transport failures or untested in-scope properties.

The three fixed zero values are data-change counter, unlocked-device count and grid
export power. Zero is a valid observation and is not substituted for missing values.
Both plant meter energy counters, import power, plant status/time, system time and
all fixed metadata properties returned valid values under the existing decoder.

Delegated register 30233 returned a valid value in occupied slots 1, 23 and 24,
under device1/permanentpowerlimit, device23/permanentpowerlimit and
device24/permanentpowerlimit. The other fifteen delegated parameters returned SMA
NaN in each of those three slots. They are unavailable in this snapshot; these were
not Modbus exception responses. No automatic login or replacement register was tried.
Whether access restrictions, model support or a particular operating state explains
these NaN readings is unresolved. Do not permanently erase their documentary evidence.

The [complete public status matrix](home-manager-availability-2026-10-12.csv) contains
unit/register/topic suffix/type/unit/status only, without serial values, network
addresses, meter readings or other installation identities. Identity and assignment
records were used internally; raw authenticated/device responses were not logged.

## Scope and limits

This covers all readable fixed properties and assignment/delegated entries of the
currently selected known NSD profile, as defined in
[the Home Manager mapping](HOME_MANAGER_MODBUS.md). Empty slots were read but do not
produce delegated requests. Write-only plant commands were not queried. Registers
outside this document, UDP meter quantities and portal settings were not scanned.

The identity and register availability evidence is now live-tested for this read
session. It does not accept MQTT publication, openHAB/persistence migration, UDP
multicast, changing assignments, outage recovery, device writes or every operating
state. No new topics were introduced by this check. Existing group filters and
retained last-known-value policy remain unchanged. Optional unavailable delegated
parameters must not be treated as fabricated zero readings.

Next, accept broker/source metadata and meter history separately. Keep the fifteen
NaN delegated mappings per assigned device as documented/unavailable in the current
state; any future targeted access/semantic investigation needs its own read-only
scope and must preserve Home Manager's controller ownership.

Validation: all 217 offline tests and the complete lint check over 126 project
files passed; `git diff --check` passed. The status matrix has 64 unique unit/register
observations and the topic-choice list has 25 unique device/topic entries.
