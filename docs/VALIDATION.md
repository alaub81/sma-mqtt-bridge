# Current validation and acceptance

Updated: **2026-10-11**. This is the current status reference. Historical checkpoints
and detailed investigation evidence remain in the [archive](archive/README.md).
A user-reported result is identified separately from a direct observation or an
automated test. Full production acceptance and openHAB migration remain open.

## Local verification

The documentation/widget cleanup preserved the bridge runtime and device configuration.
The subsequent API fix changes confirmation and unit checks; it does not activate
adapters or command gates.
The current offline suite contains **201 tests**. Repository lint covers all public
tracked and non-ignored files, including generated widget parity. Compose parity
checks both standalone files and deployment overrides. Final cleanup results are
recorded in [todo.md](../todo.md#2026-10-11--dokumente-und-widgetquellen-aufgeräumt).
The subsequent API confirmation/unit fix adds five regression tests, including
uncertain-command polling, retained observations and contradictory plan readback.
Results are recorded in [the new diary entry](../todo.md#2026-10-11--review-1-api-bestätigung-und-plan-einheiten).
The subsequent integer-payload fix adds two regressions for canonical formatting,
signed 64-bit bounds, invalid inputs and unchanged float handling.
The subsequent node-metadata fix adds a required-attribute regression across normal,
delegated and custom nodes. Existing translation and publisher tests also verify
stable types, publication before readiness, retirement and manifest ownership.
Latest checks on 2026-10-11 passed full repository lint over 107 public files, all
**201 offline tests** and Compose parity. The two formerly unhandled MQTT future
exceptions are resolved offline; unexpected event-loop errors now fail the suite.

The 2026-10-11 code review passed configured lint and all 174 offline tests. Its
MQTT disconnect tests also emitted unhandled future exceptions: the passing test
result alone did not close that defect; see the subsequent correction below.
Ruff currently checks E4/E7/E9/F and Pylint
error/fatal diagnostics; broader style checks are a separate planned improvement.

## Acceptance matrix

| Capability | Latest evidence and date | Remaining acceptance |
| --- | --- | --- |
| Configuration and ENV | Offline validation; 144 documented options/defaults checked, 2026-10-11 | Target-host permissions and operational thresholds |
| Homie node metadata | Required attributes, stable untranslated types, retained publication and dynamic retirement offline tested, 2026-10-11 | Deploy and verify actual broker/openHAB discovery |
| Inverter baseline | Model-specific lists, local identities and MQTT publication for the original 41 channels, 2026-10-10; [register evidence](REGISTER_VALIDATION.md) | Aligned values/history/rules comparison; additional registers require separate verification |
| Inverter energy/labels | Storage kWh values, log times and labels accepted by user, 2026-10-11; inverter rename/link migration reported complete | Remaining quantity metadata/history continuity |
| Inverter sleep/wake | Evening behavior reported normal, 2026-10-11 | Morning autonomous wake-up; sleep versus outage |
| Home Manager Modbus | Direct read, 2026-10-10: all 16 core reads, three assignment entries; 3 of 48 delegated reads available, 45 unavailable | Target-host/openHAB value continuity; unavailable delegated fields remain unavailable |
| Home Manager startup | Init-to-ready behavior accepted by user, 2026-10-11 | Broader target-host outage/recovery acceptance |
| Home Manager UDP | Deterministic telegram tests; Mac attempt received no packets on a different network, 2026-10-10 | Actual Pi multicast/interface/VLAN and encryption applicability |
| SEMP/API/portal reads | Local identity/TLS and authenticated reads; selected live values reached MQTT, 2026-10-10 | Full per-channel freshness, unavailable channels and production comparison |
| Local setting units | Device WebUI metadata and MQTT kWh/min read publication, 2026-10-10 | Unknown models/firmware need their own unit evidence |
| Local enum/boolean controls | Offline identity/rights/bounds/readback/replay tests; status-light command reported accepted, 2026-10-10; individual API Confirmed-state regression, 2026-10-11 | Every remaining command individually, if requested; deploy/accept the confirmation fix |
| Combined charging plan | Offline transaction/uncertainty tests; 10-kWh plan and target-mode activation reported accepted, 2026-10-11 | Physical completion, cumulative/additional energy semantics and return mode |
| Portal minimum PV | Offline preserving write/readback tests; 90 → 70 → 90 and reopened widget value reported accepted, 2026-10-11 | Longer outage/uncertainty behavior; no extra portal setters accepted |
| Portal freshness | Two normal polling cycles accepted by user, 2026-10-11 | Longer target-host operation and source-failure behavior |
| Maximum charging power | Verified WMaxIn/W mapping and bounds; offline setter tests and canonical integer readback, 2026-10-11 | Physical limit/phase effect and deployment acceptance; [details](ECHARGER_POWER_LIMIT.md) |
| eCharger total energy | Wh-to-kWh API conversion and unchanged Channel ID offline tested, 2026-10-11 | Image update, actual Item metadata and persistence/history acceptance |
| Controlled stop/start | Retained values, reconnection, healthy container and no replay accepted by user, 2026-10-11 | Abrupt failures, Last Will, broker/host restart and manifest details |
| Source status/health | Independent operational status, watchdogs, heartbeat/state protection offline tested; Home Manager startup accepted by user | Diagnostics-disabled deployment, startup-summary logs, multi-hour faults and external alarms |
| Garage widget | PV operation/staging and iOS layout accepted by user, 2026-10-11; canonical source/export parity checked locally | Existing acceptance remains; future behavior changes need a new check |
| openHAB migration | 100-row ledger, 34 linked inverter Items, four Home Manager Items and ten derived capabilities inventoried | Seven unidentified Item links; full rules/UI/units/offsets/persistence continuity |
| Docker and publication | Prior local builds/offline image checkpoints in archive; workflows prepared for amd64/arm64 | Current target-host image acceptance, hosted CI/security scans and separately authorized release |

Unavailable readings are not a successful measurement. Reported acceptance of one
command or UI action does not certify every control or completed physical charging.
No cleanup step connects to SMA devices, the portal or the installation broker.

## Open code-review findings

The API confirmation/unit, integer-payload, node-metadata, MQTT future and CLI
findings are resolved by offline regression evidence on 2026-10-11. Finding 4
remains pending timestamp observation and a subsequent policy decision.

| Finding | Required correction |
| --- | --- |
| API setting confirmation | Resolved offline: individually require Confirmed state, including manual-approval alias; preserve SEMP handling; validate plan-end units and command readback |
| Homie integers | Resolved offline: integral values serialize without decimals, signed 64-bit bounds enforced, no rounding of fractional values |
| Homie node metadata | Resolved offline: mandatory stable `$type` per node, untranslated and covered by topic ownership/retirement |
| Measurement freshness | Classify timestamp semantics first; carry remaining lifetime for verified acquisition timestamps; see the investigation below |
| MQTT disconnect cleanup | Resolved offline: retrieve completed/late disconnect errors, preserve primary failures, propagate standalone disconnect failures; strict event-loop test check |
| CLI status | Resolved offline: static code capabilities distinguish optional writes from default gates; check-config reports configured gates; module descriptions clarify local file I/O |

See the [archived review](archive/2026-10-11/todo.md#2026-10-11--repository--und-codereview)
for reproductions and original source references, and the
[implementation plan](IMPLEMENTATION_PLAN.md) for ordering. Later edits may move
source line numbers; use the named functions/tests when locating the findings.

## Unit and protocol evidence

The installed eCharger WebUI 1.46.0 metadata confirms `Parameter.Chrg.Plan.En`
unit tag 8 = kWh and `Parameter.Chrg.StpWhenFlTm` unit tag 34 = min; scalar
formatting adds no raw multiplier. The fallback is restricted to the verified
EVC22-3AC-20 / 2.6.37.R model and firmware. Full module/chunk provenance, read
results and limitations are preserved in
[the direct local verification](archive/2026-10-11/VALIDATION.md#direct-local-unit-and-channel-verification-on-2026-10-10).
Maximum-power metadata, limits and phase questions remain in
[ECHARGER_POWER_LIMIT.md](ECHARGER_POWER_LIMIT.md).

The existing verified epoch-second plan-command mapping for EVC22-3AC-20 / 2.6.37.R
is now shared with API plan-end reads. An explicit contradictory unit or unitless
unknown firmware is unavailable. SEMP retains its reference epoch-second contract
without synthesizing API Confirmed metadata. Offline readback tests also reject
matching plan numbers with contradictory units; no new live write acceptance is claimed.

API session/health samples can have old timestamps that may represent changes;
their complete timestamp semantics remain unverified. Two frequency channels
were absent from the inspected live inventory even though generic WebUI metadata
defines them. Do not infer freshness or channel presence from static metadata.
Retained values remain last-known observations; separate source readiness must be
used when deciding whether values are current.

Portal consumer-balance PV/battery/grid shares were observed through read-only
investigation on 2026-10-11. They describe period energy shares; the current
charging mix remains unverified. Detailed endpoint/identity notes are preserved in
[the earlier context](archive/2026-10-11/CONTEXT.md#charging-mix-investigation-2026-10-11).

## Measurement freshness investigation, 2026-10-11

This is an offline investigation of current code, original read-only references and
earlier installation evidence. Runtime behavior, device configuration and openHAB
were not changed. No new device, portal or installation-broker requests were sent.

### Evidence and scope

`current_measurement` accepts device ages from zero through the configured limit.
API and SEMP parsing subsequently discard timestamps. `SourceState.update` records
receipt time and `fresh_values` starts the complete lifetime again. With a 180-second
limit, a sample already 179 seconds old remains internally fresh two seconds after
receipt, although the adapter would reject it then. This was reproduced with fixed
UTC and monotonic times. The next successful poll rejects an over-age sample, so
the extension often ends at the next poll; it is not invariably another full lifetime.

The supplied SEMP parameter snapshot has different timestamps within one response:
power and vehicle status are less than one second apart, while session energy is
about three days older, health/event channels about 29 days older and some state
channels about 81 days older. Earlier API inspection also found old session/health
timestamps. These observations support mixed timestamp semantics but do not prove
which channels report acquisition versus change times. One snapshot cannot show
whether a timestamp advances while a value remains constant.

The original API JavaScript `measurements` function ignores measurement timestamps.
It is migration evidence, not proof that every returned sample is current. The
[official SMA on-site interface overview](https://developer.sma.de/on-site-integration)
and [eCharger SEMP description](https://manuals.sma.de/EVCxx20/en-US/15906683019.html)
do not establish a per-channel timestamp contract for these local responses.
Do not substitute cloud API or planning timestamps for local measurement semantics.

Candidate acquisition channels are charging power and API phase current/voltage;
frequency needs channel-presence evidence first. Session/total energy, vehicle and
health states, events and SEMP setpoints require independent classification.
Settings and nameplate observations must retain their separate confirmation/read
contract. Modbus, meter UDP and portal readers are outside this proposed eCharger
change; a shared model change still needs regressions for those sources.

### Availability and UI effects

Default SEMP readiness requires charging power; API requires phase L1 current and
voltage, plus power when API owns baseline measurements. Explicit readiness
overrides can change these requirements. Fresh settings must not hide missing
critical measurements. The aggregate Homie device is ready while any contributing
source is ready, so it cannot certify every property. Retained measurements remain
last-known observations; expiry must neither erase them nor fabricate zero.

The canonical garage widget checks API readiness for local control availability
and measurement readiness for vehicle-state presentation. Earlier expiry can
therefore disable controls or show unknown connection state even while another
source keeps aggregate Homie availability ready. Test those source-specific states.
The [official openHAB Homie mapping](https://www.openhab.org/addons/bindings/homie/)
maps device/node/property to Thing/channel group/channel; it does not supply our
per-property freshness policy. Existing installation rules and persistence are not
fully inventoried, so complete downstream acceptance remains open.

### Targeted verification before and after a change

Run the current deterministic baseline with:

```sh
PYTHONPATH=ressources .venv/bin/python -m unittest tests.test_measurement_freshness -v
```

These three tests cover device-age boundaries, zero, timezone offsets, invalid or
future timestamps and mixed-age SEMP replies with independent settings. They pass
before the change and do not close the timestamp-loss finding.
The full 185-test offline suite, lint over 104 public files and Compose parity
passed at this investigation checkpoint. The MQTT future finding was still open
then and is resolved by the subsequent correction below.

Before implementation, add failing regressions for the intended reader-to-state
behavior. Inject UTC and monotonic clocks; avoid real sleeps and device access.

| Case | Required result after the change |
| --- | --- |
| Sample age 179 s, limit 180 s, inspect 2 s later | Sample unavailable internally; critical source stale, retained observation preserved |
| Same cached timestamp received repeatedly before expiry | Original deadline stays fixed; receipt does not rejuvenate the sample |
| New acquisition timestamp with unchanged numeric value, including zero | Freshness advances; no false requirement that the value must change |
| Mixed ages, partial replies and aliases/fallback channels | Expiry follows the actual selected source sample, separately for each property |
| API parsing followed by delayed completion of the read cycle | Processing/lock delay consumes remaining lifetime too |
| Invalid, missing, future, conflicting or timezone-free timestamp | Existing rejection preserved; no replacement zero or borrowed timestamp |
| Old state/counter timestamp | Follow only an evidenced channel policy; until classified, preserve existing behavior |
| Fresh settings but expired required current/voltage/power | Source stale; settings do not restore measurement readiness |
| API stale with SEMP ready, and the reverse; custom readiness | Source diagnostics and aggregate availability follow their separate contracts |
| MQTT reconnect or process restart after expiry | Last retained observation survives; no expiry tombstone or startup write |
| Wall-clock jump after parsing | Local deadline uses monotonic time; no lifetime extension |
| Other adapters, units, commands and uncertainty journals | Existing behavior unchanged; no additional writes or retries |

For later read-only installation acceptance, observe API and SEMP independently
over at least two freshness windows in existing idle/waiting and charging periods.
Do not start charging or alter settings for the observation. Record per channel:
relative device age, receipt age, whether value and timestamp changed, source
status, and API/SEMP agreement. Keep identities, credentials and raw authenticated
responses private. A stationary timestamp with a stationary value is still
ambiguous; compare a naturally occurring value/state transition where possible.

Compare old and proposed decisions on the same observations before deployment.
Accept only explained differences, retained-value continuity and expected widget
gating; stop rollout on unexplained stale critical samples. Then run full lint,
offline tests and Compose parity, followed by the source/UI installation checks.
Return to the prior image/configuration if necessary while preserving the state
volume and command journals. No runtime correction or live acceptance is claimed
by this investigation.

## Recording new evidence

### Optional timestamp recording, 2026-10-11

The bridge now has default-disabled API/SEMP timestamp observation using existing
read responses. It records allowlisted numeric samples, including over-age ones,
in `echarger-timestamps.jsonl` in the existing state volume, with one rotated backup.
Unchanged samples are summarized; timestamp/value/quality changes are recorded
immediately. Storage failures cannot fail a read and are reported without response
contents. Freshness, command ownership and MQTT publication are unchanged.
See [activation and record semantics](CONFIGURATION.md#temporary-echarger-timestamp-observation).

Nine new tests verify numeric versus timestamp changes, unchanged summaries and
age-boundary transitions, redaction/allowlists, rotation/permissions/restart,
storage failures, symlink/FIFO rejection, configuration precedence and inactive
sources. API/SEMP integration fixtures compare output dictionaries and request counts
with observation disabled/enabled, including a failed diagnostic write.
All 194 offline tests, lint over 106 public files and Compose parity passed at
this milestone; MQTT future errors were still open then. Local Docker has no running service;
the feature has not been deployed or enabled on the installation. A new image and
explicit ENV activation are required. Natural-transition observation and the
subsequent timestamp-policy decision remain pending.

### MQTT disconnect future correction, 2026-10-11

The pinned aiomqtt 2.5.1 `__aexit__` returns immediately if its disconnect future
is already completed, without retrieving an error from that future. The bridge's
session teardown now retrieves completed errors. A disconnect failure is propagated
if there is no primary session failure; otherwise the existing failure is preserved.
A late disconnect error after failed bounded cleanup is retrieved by a completion
callback after the original failure has already propagated. No library upgrade,
retry policy, command replay or Last Will behavior was introduced.

The full pre-deployment runner now records unexpected event-loop exceptions, retains
their default diagnostic output, collects unreachable future cycles and exits with
failure even if individual unittest assertions passed. Before the runtime correction,
the 194-test suite reproducibly exited 1 for the two formerly unhandled MQTT errors.
After the correction, all 199 tests exit 0 without those messages.

Three new session tests cover standalone disconnect error propagation, preservation
of a publication timeout and a late future completion. Two runner self-tests prove
that an orphaned failed future makes an otherwise passing suite fail and that a
clean loop passes. Existing real aiomqtt/Paho loopback tests still verify reconnect,
retained discovery/measurements and graceful disconnect; they additionally assert
that the supervised failure count records the dropped connection.
Full lint over 107 public files and Compose parity passed. This is offline evidence,
not new installation fault/Last Will acceptance or deployment.

### CLI capability reporting, 2026-10-11

`--project-status` now reports `readOnly=false` for the implemented optional write
capabilities and `commandsEnabledByDefault=false` for the closed default gates.
It remains independent of installation configuration and does not claim complete
live acceptance. `--check-config` retains its effective configured `readOnly` flag;
no command gates, runtime commands or adapter activation changed. Module descriptions
now acknowledge optional writes and local configuration-file reads. Inverter profile
commands remain unsupported regardless of eCharger/portal capabilities.

The existing status regression failed before correction and now verifies the static
capabilities/default distinction. Two additional CLI tests prove that project status
ignores an absent configuration file and invalid installation ENV without exposing
credentials, and check all global/per-adapter gate combinations for local and portal
configuration. Invalid global-only gates remain rejected. All 201 offline tests,
full lint over 107 public files and Compose parity passed. No installation or device
configuration was changed.

Record date, tested image/version, source/transport, automated versus direct versus
user-reported result, and remaining limits. Keep authenticated responses, private
identities and secrets out of public fixtures. Update this matrix when acceptance
changes; preserve detailed German decisions in the active diary and its archive.
