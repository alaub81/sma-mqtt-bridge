# eCharger API/SEMP topic coverage audit

Audit date: 2026-10-12. One bounded read cycle of each explicitly enabled local
reader completed with the existing configuration, identity checks and TLS policy.
The local API returned 85 confirmed parameters and 44 measurement/setpoint channel
entries. SEMP returned 25 custom parameter entries and 19 standard XML leaf paths.
No settings were written, no interface was activated, no MQTT connection was made
and no portal session was opened. Raw authenticated responses and tokens were not
saved or printed; only sanitized channel metadata and value/freshness categories
were retained privately. No original private reference file was changed.

The [complete channel matrix](echarger-topic-audit-2026-10-12.csv) reconciles the
85-parameter and 25-channel references, the current offered channels, and executable
adapter property definitions. The [standard SEMP field matrix](echarger-semp-fields-2026-10-12.csv)
additionally inventories the fields outside the custom Parameters endpoint.
The channel matrix includes two configured API candidates absent from the current
response, so its 156 source/kind/channel rows exceed the 154 actually offered
entries. The same logical value can appear on more than one transport.

## Sources and method

- Private read-only references: parameter-catalog.json (85 metadata rows),
  sma-echarger-params.xml (25 channels), sma-echarger-semp.xml (standard SEMP XML),
  and the working local openHAB package.
- Current local reads: the existing API token, parameters/search and measurements/live
  routes, plus SEMP device identity and Parameters. POST search/live requests are
  reads; no parameter-write endpoint was invoked.
- Runtime definitions: API_SETTINGS, SETTINGS, EXTRA, BASE, SEMP_EXTRA,
  base_values/settings_values and the two reader constructors in echarger.py;
  source ownership in runtime.py; LOCAL_COMMANDS and command gates in commands.py.
- Published IDs: the existing Homie wire-key conversion removes hyphens. Every
  extracted target was checked against reader-declared properties across the
  API-only, SEMP-only and dual-source ownership variants. This is a mapping check,
  not an assertion that every declared property was published by a running bridge.

The current API parameter names and SEMP custom channel names match their respective
reference sets. The API live endpoint offers Measurement.* and Setpoint.* entries;
these are counted together, without calling setpoints physical measurements.
Numeric zero counts as present. Time acceptance is evaluated using the existing
current_measurement rules and the configured stale threshold, not by changing
freshness semantics during this audit.

The [official SMA SEMP description](https://manuals.sma.de/EVCxx20/en-US/15906683019.html)
and [official openHAB Homie binding documentation](https://www.openhab.org/addons/bindings/homie/)
were consulted. A missing matching Modbus list is not proof that the eCharger has
no Modbus capability; this audit intentionally covers the existing API/SEMP readers.

## Channel coverage

| Source inventory | Offered | Directly mapped for current ownership | Implemented fallback mapping | Only another transport has the mapping | Identity-only use | Intentionally excluded | Unmapped |
| --- | --: | --: | --: | --: | --: | --: | --: |
| API parameters | 85 | 12 | 1 | 1 | 2 | 7 | 62 |
| API live measurement/setpoint entries | 44 | 7 | 4 | 7 | 0 | 0 | 26 |
| SEMP custom Parameters entries | 25 | 16 | 8 | 0 | 0 | 1 | 0 |

The twelve directly mapped API parameters are the local settings. Firmware is a
baseline fallback read when SEMP is disabled. Phase assignment is already exposed
as a raw SEMP parameter, rather than through an API parameter mapping. Local model
string and serial are identity gates, not missing public identity topics. Six
password/access/SSID entries and the private location name are explicitly excluded.
The remaining 62 parameters are not automatically 62 useful new topics: they include
network configuration, identity duplicates, firmware/service actions and installer
settings, as well as potentially useful charging limits/preferences.

All 24 non-location SEMP custom channels have existing mappings. With both readers
enabled, API owns the settings; eight SEMP setting-only channels are consequently
fallback-owned and absent from the SEMP reader's own discovery. Charge mode and
charging release also have separately declared baseline/approval aliases. There is
no missing custom SEMP topic merely because an overlapping setting belongs to API.
The extra raw setpoint channels still have unresolved meaning and no setters.

Seven API live channels have mappings only in the SEMP adapter. They comprise four
raw diagnostic/state channels and three plant-control setpoints. They are covered
when SEMP is enabled, but those extra mappings are not reproduced by API-only mode.
Four baseline API measurements are implemented as fallbacks, while SEMP owns them
in dual-source mode. Device health has an API text fallback, but its additional
raw health-code alias also remains SEMP-only. The other-transport suffix column
retains these partial/alias differences instead of counting each as a new channel.
This source-specific distinction is explicit in the matrix.

## Actual API measurement gaps

Twelve of the 26 unmapped API live entries had a present numeric value and a
currently accepted timestamp in this single snapshot:

| Source channel family | Entries | Candidate use | Remaining review |
| --- | --: | --- | --- |
| Measurement.GridMs.W.phsA/B/C | 3 | Active charging-station power per phase | Confirm engineering units and sign meaning before new W topics. |
| Measurement.GridMs.TotVA and VA.phsA/B/C | 4 | Total and phase apparent power | Confirm VA units; select useful total/phase coverage rather than duplicates. |
| Measurement.GridMs.TotVAr and VAr.phsA/B/C | 4 | Total and phase reactive power | Confirm VAr units and sign convention; usefulness/group decision remains open. |
| Measurement.InOut.GI1 | 1 | Digital input observation | Value presence does not establish terminal/function/enum semantics. |

The API response does not include explicit engineering units for these live entries.
Channel names and readable numbers alone do not release a validated mapping or
command. All twelve are read candidates, not new implemented properties.

The other fourteen unmapped entries were not accepted as fresh by the current
runtime filter. Thirteen had a numeric/text value with an old or unaccepted
measurement timestamp; one Speedwire communication-status entry had no value.
They include digital output GO1, event description/number/user/installer counters,
active-power limitation source, update/web communication status, Wi-Fi states and
signal strength. They remain documented diagnostic candidates; do not mistake
timestamp-filtered state values for permanently unsupported channels.

The [existing timestamp investigation](VALIDATION.md#measurement-freshness-investigation-2026-10-11)
is still required: a state timestamp may describe a last change rather than a new
acquisition. This audit does not alter that behavior or infer a live charging mix.

## Configured but absent, and mapped but timestamp-filtered

- Measurement.GridMs.Hz was not offered by this API live response or the
  charging snapshots on 2026-10-15. Andreas requested removal on 2026-10-15;
  the Wallbox frequency mapping/discovery is now removed. Previously owned
  value/metadata topics retire through the normal manifest. Inverter frequency
  channels are unchanged; no permanent firmware-wide absence is inferred.
- Measurement.Metering.GridMs.TotWhIn is an absent configured alternative. The
  primary TotWhIn.ChaSta counter was present, so total-energy mapping is covered.
- Session energy, device health and several SEMP health/event/mode/authentication
  codes had source values but were rejected by the current timestamp filter.
  Vehicle state and charging power were accepted in this snapshot.
- The API reader returned non-None decoded results for 19 of its 20 keys. The
  SEMP reader returned non-None decoded results for 11 of 18 keys. These are reader
  outputs, not broker observations or a certificate of physical charging behavior.

## Potential charging parameter additions

The existing API setting mappings cover the requested operating controls, plan
fields and maximum charging power. Unmapped charging-related candidates include
Parameter.Chrg.AMinCha, Plan.DurTmm, UseEnergyMeter, Inverter.AcALim, Inverter.WMax,
Inverter.WMaxInRtg and PCC limits/fallback preferences. Availability of parameter
metadata is separate from useful presentation, confirmed units and control rights.
Do not confuse WMax with the existing maximum charging power setting WMaxIn.
Source metadata unit fields are incomplete; model/firmware-specific verified unit
fallbacks cover only the already documented allowlisted settings.

The API returned Confirmed state for all 85 parameter entries. This does not
certify every parameter as editable or safe to write. Only the existing nine direct
local command definitions can become property setters, behind runtime gates and
per-command metadata/identity/unit/bounds checks. Plan energy/end remain individual
read/staging values controlled through the explicit combined plan command. Stop
delay is read but is not in the direct command allowlist. This audit adds no setters.

## Standard SEMP XML coverage

Beyond Parameters, the current device XML has 19 distinct leaf paths. DeviceId and
DeviceSerial are used to validate identity. Device name/status association IDs stay
private; vendor/type fields are additional identity metadata without public topics.
The remaining 13 standard fields are not currently decoded into measurement topics:

- CurrentPower method, interruption support, optional-energy requests and timestamp
  capability flags.
- Minimum/maximum power consumption and minimum on/off times.
- DeviceStatus status and EMSignalsAccepted.
- PowerInfo AveragePower, AveragingInterval and Timestamp.

These may offer diagnostics, capability information or an alternative power
observation. AveragePower with an averaging interval is not automatically equivalent
to the custom instantaneous charging-power measurement. Capability flags are not
instructions to send SEMP control requests. The existing reader validates identity
and uses Parameters; inventorying these fields introduces no second controller.
The currently offered XML is a snapshot, not exhaustive coverage of every optional
SEMP request/response shape or every later charging state.

## Outcome and follow-up

The systematic coverage audit is complete for the available references and this
current response. Complete topic implementation is intentionally not claimed.
No API/SEMP adapter, timestamp policy, MQTT topic, command allowlist, device setting
or openHAB Item was changed.

Priorities for a joint selection are phase active power, then selected apparent/
reactive power; unit evidence must precede mapping. Separately review API-only
fallback coverage, digital I/O and diagnostics, charging-limit semantics, and the
13 standard SEMP fields. Keep the frequency absence, private/access exclusions,
source ownership and timestamp limitations visible. Agree basic/advanced/diagnostics
before adding new channel groups. Future observations across natural idle/charging
transitions need an explicitly scoped follow-up; no recurring audit was scheduled.

Validation: complete lint passed for 123 files and all 214 offline tests passed.
The matrix has 156 unique source/kind/channel rows and 154 currently offered
entries; twelve fresh unmapped API entries and nineteen standard SEMP paths were
checked. Private-value exclusions and declared mapping targets were verified.
`git diff --check` passed. These checks do not approve new units, setters or topics.

## Subsequent phase-power implementation, 2026-10-12

The user subsequently approved E01. The API reader now adds measurements/powerl1,
powerl2 and powerl3 from Measurement.GridMs.W.phsA/B/C. The CSV matrices above remain
the original audit snapshot; their pre-implementation coverage counts are not
rewritten. Three of the twelve fresh unmapped candidates are now implemented.
The remaining nine candidates and other E02–E07 questions stay open.

### Unit and numerical evidence

The retained official device WebUI 1.46.0 metadata lists each phase-power channel
as SCALAR with unit tag 18 and display precision 0. Its translation dictionary
maps tag 18 to W, and its scalar formatter passes Number(value) as the value with
W as the input unit. Formatting precision and optional display-unit conversion do
not introduce a source scaling factor. The API engineering value is therefore
published directly as float W, without division by 1000 or integer rounding.

| Retained device asset | SHA-256 |
| --- | --- |
| 3194.4c0f0d12e9cf8ed1.js / channel metadata | 3b4e549c4cfabab51d34866980f3411af85736de5b3ad9a5a27532480b7d1fa3 |
| 3462.63198e778e99e887.js / unit translations | 31cdf0ed35bb10e15aad1b8a1bd2ed310d7bbd74b4c627eafb8873930253a99d |
| main.741c4568facb569b.js / scalar formatting | 07d18e11ad759e06c5d153c0bad4b098846d2b66332459b53a8cbc14424bc0d9 |

Only derived technical facts and hashes are recorded; copyrighted assets are not
redistributed. Missing measurement units use this contract only for the verified
EVC22-3AC-20 / 2.6.37.R model/firmware. Explicit engineering units must consistently
be W at the channel and/or value-entry level; contradictory, empty or non-W units
make that phase unavailable. An unknown firmware without explicit watts cannot
use the fallback. Model identity still passes the normal API gate.

These read-only properties follow the existing API measurement basic default and
remain present when advanced/diagnostics are disabled. They are optional for
readiness and owned by API whether or not SEMP is enabled. The existing total
charging-power topic keeps its source/ownership; phase powers are not summed into
or substituted for it. No additional HTTP requests, settings or command definitions
are added. Signed values and valid zero remain unchanged; nonfinite, missing and
time-rejected observations remain unavailable under the existing policy.
The direction/physical charging interpretation of a signed observation is not
inferred from sign alone. No new phase control or SEMP controller is introduced.

## Subsequent plant-control semantic review, 2026-10-12

[Control observation review](ECHARGER_CONTROL_OBSERVATIONS.md) confirms that the
three control properties are Advanced and SEMP-owned. Rechecked API/SEMP timestamp
records show the active-count observation stays nonzero during waiting/zero-power
intervals, so it must not be used as an instantaneous local charging flag. SMA's
Multi-EVC description provides active-station/current-sharing context, with the
raw-channel association explicitly marked as inference. Limit units, reference
power, sign convention and control effectiveness remain unresolved. No mapping,
metadata, channel group, configuration, request or setter was changed.
