# Current validation and acceptance

Updated: **2026-10-12**. This is the current status reference. Historical checkpoints
and detailed investigation evidence remain in the [archive](archive/README.md).
A user-reported result is identified separately from a direct observation or an
automated test. Full production acceptance and openHAB migration remain open.

## Local verification

The documentation/widget cleanup preserved the bridge runtime and device configuration.
The subsequent API fix changes confirmation and unit checks; it does not activate
adapters or command gates.
The current offline suite contains **217 tests**. Repository lint covers all public
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
**203 offline tests** and Compose parity. The two formerly unhandled MQTT future
exceptions are resolved offline; unexpected event-loop errors now fail the suite.

The 2026-10-11 code review passed configured lint and all 174 offline tests. Its
MQTT disconnect tests also emitted unhandled future exceptions: the passing test
result alone did not close that defect; see the subsequent correction below.
Ruff now checks E4/E7/E9/F/I and formatting; Pylint checks error/fatal diagnostics.
Additional lint rules remain a separate planned improvement.

## Acceptance matrix

| Capability | Latest evidence and date | Remaining acceptance |
| --- | --- | --- |
| Configuration and ENV | Offline validation; 144 documented options/defaults checked, 2026-10-11 | Target-host permissions and operational thresholds |
| Homie node metadata | Required attributes, stable untranslated types, retained publication and dynamic retirement offline tested; new $type present at the broker reported by user, 2026-10-11; general openHAB display already accepted | Dynamic retirement on the target installation remains offline tested |
| Inverter baseline | Model-specific lists, local identities and MQTT publication for the original 41 channels, 2026-10-10; [register evidence](REGISTER_VALIDATION.md) | Aligned values/history/rules comparison; additional registers require separate verification |
| Inverter energy/labels | Storage kWh values, log times and labels accepted by user, 2026-10-11; inverter rename/link migration reported complete | Remaining quantity metadata/history continuity |
| Inverter sleep/wake | Evening behavior reported normal, 2026-10-11 | Morning autonomous wake-up; sleep versus outage |
| Home Manager Modbus | Direct read, 2026-10-10: all 16 core reads, three assignment entries; 3 of 48 delegated reads available, 45 unavailable | Target-host/openHAB value continuity; unavailable delegated fields remain unavailable |
| Home Manager startup | Init-to-ready behavior accepted by user, 2026-10-11 | Broader target-host outage/recovery acceptance |
| Home Manager UDP | Deterministic telegram tests; Mac attempt received no packets on a different network, 2026-10-10 | Actual Pi multicast/interface/VLAN and encryption applicability |
| SEMP/API/portal reads | Local identity/TLS and authenticated reads; selected live values reached MQTT, 2026-10-10 | Full per-channel freshness, unavailable channels and production comparison |
| Local setting units | Device WebUI metadata and MQTT kWh/min read publication, 2026-10-10 | Unknown models/firmware need their own unit evidence |
| Local enum/boolean controls | Offline identity/rights/bounds/readback/replay tests; status-light command reported accepted, 2026-10-10; individual API Confirmed-state regression and update-checklist setting readback reported accepted, 2026-10-11; updated value appeared after a noticeable delay | Tested setting and elapsed time not specified; Pending transition remains offline tested; every remaining command individually, if requested |
| Combined charging plan | Offline transaction/uncertainty tests; 10-kWh plan and target-mode activation reported accepted; repeat plan transmission/readback after confirmation/unit fix reported accepted, 2026-10-11 | Physical completion, cumulative/additional energy semantics and return mode |
| Portal minimum PV | Offline preserving write/readback tests; 90 → 70 → 90 and reopened widget value reported accepted, 2026-10-11 | Longer outage/uncertainty behavior; no extra portal setters accepted |
| Portal freshness | Two normal polling cycles accepted by user, 2026-10-11 | Longer target-host operation and source-failure behavior |
| Maximum charging power | Verified WMaxIn/W mapping and bounds; offline setter tests; canonical integer MQTT payload and openHAB display reported accepted, 2026-10-11 | Physical limit/phase effect; [details](ECHARGER_POWER_LIMIT.md) |
| eCharger total energy | Wh-to-kWh API conversion and unchanged Channel ID offline tested; openHAB unit, scaling and existing history reported accepted by user, 2026-10-11 | Accepted for the tested installation |
| Controlled stop/start | Retained values, reconnection, healthy container and no replay accepted by user, 2026-10-11 | Abrupt failures, Last Will, broker/host restart and manifest details |
| MQTT outage recovery | User-reported successful update check and supplied log, 2026-10-11: all five connections recovered autonomously in 11.0–28.5 seconds from their respective outage detection; errors/timeouts remained visible, no unhandled future exception in supplied excerpt | Longer outages, Last Will and broader production failure matrix |
| Source status/health | Independent operational status, watchdogs, heartbeat/state protection offline tested; Home Manager startup accepted by user; supplied target-host startup summary shows all seven sources ready and all five MQTT connections connected; widget source availability with optional diagnostics disabled reported accepted by user, 2026-10-11 | Multi-hour faults; individual external alarm scenarios remain unspecified |
| Garage widget | PV operation/staging and iOS layout accepted by user, 2026-10-11; canonical source/export parity checked locally | Existing acceptance remains; future behavior changes need a new check |
| openHAB migration | 100-row ledger, 34 linked inverter Items, four Home Manager Items and ten derived capabilities inventoried | Seven unidentified Item links; full rules/UI/units/offsets/persistence continuity |
| External monitoring and alarms | Setup reported complete by user, 2026-10-11 | Specific monitored signals and triggered alarm scenarios not supplied; host reboot/state restoration remain separate |
| Docker and publication | Existing GitHub CI including lint, tests, Compose checks, amd64/arm64 builds, container tests and scans reported repeatedly successful by user, 2026-10-11; target-host update checklist accepted | New release-to-CI dependency needs a hosted run; GHCR publication/pull acceptance remains separate |

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
this milestone; MQTT future errors were still open then. The user subsequently
reported activation on the target host on 2026-10-11. Recorded file contents and
sufficient quiet/charging/natural-transition observations have not yet been reviewed;
that review and the subsequent timestamp-policy decision remain pending.

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

### Python formatting and import ordering, 2026-10-11

The existing pinned Ruff now enforces formatting as a read-only repository check:
100-column target, double quotes and four-space indentation. Rule I enforces import
ordering/grouping, with `sma_mqtt_bridge` and `tests` classified as project packages.
EditorConfig and the README match these rules; no dependencies were upgraded.

The two changes were applied and validated sequentially. Formatting changed 44
public Python files; all 48 parsed syntax trees remained identical. Import ordering
then fixed 48 reported locations. A second comparison normalized only consecutive
import statements and aliases within their original scopes; all 48 syntax trees
matched beyond that ordering/grouping. Local runtime/test import changes were
reviewed; no import was moved into or out of a function or conditional.
The only intentional non-formatting code addition is the formatter check in the
lint runner. No protocol, configuration defaults, command gates or data changed.

All 201 offline tests passed after formatting and again after import ordering,
including the real loopback MQTT/HTTP cases and strict event-loop check. Final lint
over 107 public files, including formatter/import checks, and Compose parity passed.
This is offline validation; no image deployment or new installation acceptance
was performed. Private references and configuration were excluded from formatting.

### Named eCharger setting definitions, 2026-10-11

The six-position setting tuples are replaced by a small keyword-only frozen
`SettingDefinition` with named ID, channel, datatype, unit, mapping and format fields.
Boolean mappings are copied into read-only mapping proxies to prevent accidental
mutation through either the definition or the original dictionary. Read property
construction, API/SEMP decoding and the existing command allowlist use named fields;
commands reuse the same definition instead of creating another positional tuple.
No setting or writable capability was added.

An independent before/after snapshot from the preceding commit compared all twelve
definitions, the eleven SEMP definitions, nine command keys, eight confirmed/pending
and unit-validation read variants, all properties/discovery topics of four API/SEMP
ownership combinations, and 156 accepted/rejected command-target cases. The complete
serialized snapshots match byte for byte. Plan and stop-delay fields remain excluded
from individual setters; units, enum order, boolean mapping and metadata are unchanged.

Two new tests enforce keyword-only construction and protect against mapping/field
mutation. All 66 targeted read/command tests and all 203 offline tests passed, along
with full lint over 107 public files and Compose parity. The final countercheck also
confirms no remaining positional unpacking/index access for these setting definitions.
No live commands, device queries or deployment were performed.

Record date, tested image/version, source/transport, automated versus direct versus
user-reported result, and remaining limits. Keep authenticated responses, private
identities and secrets out of public fixtures. Update this matrix when acceptance
changes; preserve detailed German decisions in the active diary and its archive.

### Full CI required before release, 2026-10-11

The release workflow calls the existing CI through workflow_call for the tagged
revision and requires its successful completion before the publishing job. This
includes lint, regressions, Compose parity and both amd64/arm64 build, container
test and Trivy matrix jobs. Package write permission is limited to publication.
The user reports repeated successful hosted runs of the existing full CI. A hosted
run of the newly added release-to-CI dependency remains pending; no run URLs or
commit identifiers were supplied.

### Security gate and public-data inspection, 2026-10-11

CI image scans for both architectures and the release scan now fail on fixable
HIGH or CRITICAL vulnerabilities; ignore-unfixed remains enabled. Results under
this stricter policy require the next hosted run.

Checksum-verified Gitleaks 8.30.1 found no secrets in the 107 current tracked
files or reachable Git history (46 commits, 570 unique blobs). Historical paths
contained no private ENV/data/reference files except the public private/README.md.
An additional comparison against selected current private ENV values produced
only harmless substring matches in historical library names. Reports were
redacted and stored outside the repository. This does not certify all personal
data or unreachable Git objects. Full lint and all 203 offline tests passed.

### Automatic application/build versions, 2026-10-11

Native calls derive clean release or development versions from local Git; immutable
image metadata takes precedence. Builds without Git-derived arguments or embedded
metadata report 0.0.0+unknown. CI checks CLI equality on both architectures; the
release checks its pre-publication image against the stable tag. Full lint and
205 offline tests passed, including Git failure and Git-free image cases. Local arm64/amd64 Docker builds and CLI version propagation subsequently passed;
hosted execution of this new version chain remains pending.

### Removal of vulnerable build-only installers, 2026-10-11

The supplied failed amd64 Trivy report identified four HIGH findings in pip
26.2.1 vendored msgpack, setuptools and urllib3. Local image metadata confirmed
those copies are installer internals rather than bridge runtime dependencies.
The image now runs pip check after installation, then removes pip and the stdlib
ensurepip bootstrap wheel/package. Runtime requirements remain unchanged. Both
CI architecture jobs assert installer absence.

Local arm64 and amd64 builds, CLI/version/config smoke checks and all 205 offline
tests in each container passed (amd64 emulated). Checksum-verified Trivy 0.75.0
scanned both images with HIGH,CRITICAL and ignore-unfixed: zero filtered findings
and zero secrets, exit 0. Lower severities and unfixed vulnerabilities are outside
this gate. Host lint and all 205 host tests passed. No production deployment or
publication was performed; the hosted/released image still needs its own scan.

### Operational limits and focused outage simulation, 2026-10-11

The read-only `python -m sma_mqtt_bridge.operational_limits` module resolves the
normal configuration and enabled-reader profile timing without network requests.
Only allowlisted operational fields are printed; private addresses, credentials,
serial numbers and configured MQTT identities are excluded. Target-host effective
settings and external alarm rules remain to be supplied. See
[the operational procedure](OPERATIONAL_ACCEPTANCE.md).

Three additional tests cover report redaction, twelve virtual hours of partial
samples with independent readiness and retained last-known measurements, and sixty
serial timeout/retry cycles followed by valid-zero recovery. Existing hung-read,
partial/invalid-response and MQTT protocol tests remain in the full suite.
All 206 offline tests passed with local synthetic loopback servers; no installation
connections or commands were made. Full lint passed hygiene, JSON, ENV, widget,
shell, Dockerfile, YAML, Actions, Pylint and Markdown checks, but failed Ruff import
ordering/formatting in pre-existing `version.py` and `test_bootstrap.py` worktree
changes. The new Python files pass Ruff and formatting. A real multi-hour resource
soak and target-host external alarm delivery are not covered by virtual-time tests.

## Documentary Modbus completeness audit, 2026-10-12

[Full audit and ledgers](MODBUS_TOPIC_AUDIT.md) reconcile all numeric SMA register
addresses in the three matching source archives with bundled profile properties.
All existing addresses, raw types, lengths and FIX/TEMP scales passed the comparison.
There are 491/410/360 unmapped readable device/register pairs; these include
alternatives and conditional channels, not guaranteed live support. No runtime,
profile, channel filter, device setting or openHAB integration changed. New mapping
semantics, channel-group decisions, command approval and live acceptance remain open.

Validation: complete lint passed for 116 files; all 208 offline tests passed,
including synthetic loopback servers. The first sandboxed run could not bind four
local test sockets; the permitted rerun passed. `git diff --check` passed.

## Production-gated availability probe, 2026-10-12

A user-authorized direct FC04 probe around 07:51 Europe/Berlin passed the configured
model, firmware and serial gates for inverter1 and inverter3. Both returned valid
0 W at register 30775, so the full availability scan did not start. Seven synthetic
raw/sentinel classification checks passed; no new profile or runtime support is
claimed. The private one-shot checker distinguishes numeric zero, SMA NaN, empty
strings, undecoded raw data, Modbus exceptions and transport failures. It skips
WO and access-control register 43090 and performs no MQTT I/O or device writes.

Andreas authorized a thread automation to check every 30 minutes on this date and
perform exactly one scan when both PV inverters have positive power. The completed
scan, useful topic selection and channel-group decisions remain pending. Sunny Boy
[official specifications](https://manuals.sma.de/SBxx-1AV-41/de-DE/4177679243.html)
list two independent MPP inputs; actual second-input wiring remains unverified.

## Completed production availability scan, 2026-10-12

The authorized one-shot FC04 scan completed at 08:25–08:31 Europe/Berlin with
positive power on both PV inverters before and after. All three identity gates
passed. All 1,367 device/register ledger pairs were accounted for: 1,307 read
attempts, 57 WO exclusions and three exclusions of access-control register 43090.
There were 872 non-NaN numeric/string samples (including 105 numeric zeros),
433 SMA NaN readings and two undecodable Storage strings. No rejected requests,
transport errors or untested ledger entries occurred. The automation is paused;
no second scan, writes, MQTT I/O or profile/runtime/openHAB changes took place.

[Full report and candidates](MODBUS_AVAILABILITY_2026-10-12.md) and the
[public result matrix](modbus-availability-2026-10-12.csv) contain no private raw
values or installation identities. Matrix uniqueness, counts, NaN exclusion and
valid-zero retention were checked against private scan records. Units, enums,
state-dependent support, useful topic selection and channel groups remain pending.

Sunny Boy phase assignment 40183 returned code 329 (L3 in the matching official
V16 list), agreeing with valid L3 power/voltage/current and NaN on L1/L2. Input B
returned valid zero for all three DC readings; actual string wiring remains open.
These observations explain unavailable L1 mappings but do not authorize silently
changing their meaning or migrating existing Item links/history.

Complete lint passed for 118 files and all 208 offline tests passed after recording
these results; `git diff --check` passed. These checks do not approve new polling
profiles, setters, physical phase wiring or openHAB migration.

## Sunny Boy L2/L3 implementation, 2026-10-12

Six additive phase properties are implemented in the bundled Sunny Boy profile;
see the [register table](REGISTER_VALIDATION.md#sunny-boy-l2l3-profile-extension-2026-10-12).
Existing properties and pollers were compared against an independent pre-edit
snapshot and are unchanged. All six new addresses, types, lengths, scales and units
match the official inventory. L2/L3 power/voltage reuse the existing 3-second block;
L2/L3 current uses one four-register block every 5 seconds.

Targeted synthetic tests cover signed values, fractional V/A scaling, valid zero,
SMA NaN, phase-specific discovery/labels/units/non-settable metadata, optional
filters disabled, and ready status with L1/L2 unavailable while L3 returns values.
The existing migration-baseline test still checks original ranges/intervals and
original channel counts independently of the additive extension.
No device query, write, runtime deployment, MQTT publication or openHAB link change
was performed for this implementation; those installation checks remain pending.

Full validation passed: all 211 offline tests, the complete lint check over 119
files, and `git diff --check`. The separate `tests/compose_check.py` also passed.

## Selected inverter expansion and other-device coverage, 2026-10-12

Sixteen additional file-based properties implement the requested type/limits,
frequency, available phase currents and Storage AC/battery measurements. An
independent pre-edit snapshot confirms that all previous property definitions and
poller ranges/intervals remain unchanged. Every added register matches documentary
metadata and has a valid sample in the existing production availability matrix.
See the [register table](REGISTER_VALIDATION.md#small-inverter-measurement-extension-2026-10-12).
Targeted synthetic tests cover raw model codes, advanced-group limit filtering,
non-settable metadata, signed/fractional decoding, zero/NaN handling, basic reads
with optional filters disabled and unchanged status-based readiness.
No new device read/write, deployment, MQTT publication or openHAB migration was
performed for this implementation. Host profile overrides need explicit updates.

Home Manager coverage was rechecked against the existing profile and its complete
inventory regression: 16 fixed Unit 1/2 properties, all 245 assignment slots and
16 delegated parameter templates cover the known readable NSD document entries.
The recent inverter scan did not include Home Manager; full actual register and
assignment/delegated availability still needs a separate read-only installation
check. Basic readiness acceptance does not certify all advanced readings.

The eCharger reader uses local API/SEMP and separate portal observations. The
supplied documents contain no matching complete Modbus register table that could
support an equivalent address sweep. Local parameter/SEMP inventories and known
reads exist, but exhaustive metadata-to-topic coverage and availability in natural
charging states remain a separate task. Do not claim that absence of a supplied
register list proves absence of any hardware Modbus capability.

Validation passed: all 214 offline tests, complete lint over 120 files, separate
Compose parity including overrides, and `git diff --check`. No new device I/O was
used for this expansion or the Home Manager/eCharger coverage clarification.

## Markdown table lint correction, 2026-10-12

Four separator rows in the three Modbus evidence documents now use compact
three-character right-alignment delimiters (`--:`). Table contents and alignment
are unchanged. Complete lint passed over 120 files, including all 27 Markdown
files; all 214 offline tests passed. The initial sandbox run blocked four synthetic
loopback server binds; the approved rerun passed. `git diff --check` passed.

## eCharger API/SEMP completeness audit, 2026-10-12

The [systematic audit](ECHARGER_TOPIC_AUDIT.md), channel matrix and standard-field
matrix compare reference inventories with one current read cycle of each enabled
local reader. API and SEMP identity checks passed using the existing TLS policy.
The API offered 85 confirmed parameters and 44 measurement/setpoint entries; SEMP
25 custom channels and 19 standard XML leaf paths. All 24 non-location custom SEMP
channels have mappings; source ownership explains setting fallbacks. There are 26
unmapped API live entries, of which twelve have a value and a currently accepted
timestamp. Thirteen further entries have timestamp-filtered values and one has no value.
Frequency is configured but absent; primary total energy is present.

The matrices contain metadata/status categories only, without device values,
identities, credentials, tokens, addresses or authenticated responses. Unique
source/kind/channel keys and target-property declarations across ownership variants
were checked. No runtime/topic/timestamp/command/openHAB changes or device writes
were made. Unit validation, useful topic selection, API-only extra fallback coverage,
standard SEMP field semantics and natural charging-state acceptance remain open.

Audit validation: full lint over 123 files and all 214 offline tests passed. Matrix
row uniqueness, counts, twelve fresh unmapped channels, standard-field inventory
and value redaction passed direct consistency checks; `git diff --check` passed.

## eCharger phase active power implementation, 2026-10-12

The API reader now provides three read-only float-W measurements, powerl1/powerl2/
powerl3, from the corresponding GridMs.W.phsA/B/C channels. Unit tag 18 = W and
SCALAR/no raw multiplier are verified in retained official WebUI assets; hashes
and the model/firmware-scoped fallback are recorded in the
[phase-power evidence](ECHARGER_TOPIC_AUDIT.md#subsequent-phase-power-implementation-2026-10-12).
Explicit non-W/conflicting units reject that phase; missing units on unverified
firmware do not produce a value. Existing API identity gates remain unchanged.

Synthetic regressions cover phase-to-topic mapping, fractional/signed/zero values,
read-only float-W discovery and German labels, unchanged total-power ownership,
SEMP independence, optional filters disabled, readiness exclusion, missing/NaN/
Infinity/bool values, stale/future/malformed timestamps, conflicting unit levels
and explicit-W versus missing-W behavior on unknown firmware. Reads still use
only the existing search/live requests; no command endpoint or extra request was
introduced. The earlier live audit established channel availability, not publication
from the extended bridge. New MQTT/openHAB/physical acceptance remains pending.

Full validation passed: all 217 offline tests, complete lint over 124 project files,
separate Compose parity with overrides, and `git diff --check`. No live write,
broker publication or physical charging experiment was used for this change.

## Complete live Home Manager NSD read check, 2026-10-12

Following user-requested commit `1828a35`, the explicitly enabled local Home Manager
completed one identity-gated, paced FC04 session. All sixteen Unit 1/2 properties
were valid (including three zeros); all 245 assignment slots were read. Three
assigned units received all sixteen delegated reads each: register 30233 was valid
for each, and the other 45 observations were SMA NaN. No exceptions, transport
failures, missing enum mappings or untested in-scope properties occurred.

[Full evidence](HOME_MANAGER_AVAILABILITY_2026-10-12.md) and its public CSV omit
installation identities and raw values. No write, Grid Guard login, MQTT connection,
profile/group change or openHAB migration was performed. Full MQTT/history/outage
acceptance and the reason for delegated NaN remain separate outstanding work.

Validation: all 217 offline tests and the complete lint check over 126 project
files passed; `git diff --check` passed. The status matrix has 64 unique unit/register
observations and the topic-choice list has 25 unique device/topic entries.

## Pre-deployment build and verification, 2026-10-12

The local `sma-mqtt-bridge:dev` image built successfully using the existing pinned
Python base. All 217 offline tests passed both on the host and inside the local
container with networking disabled. Container default configuration validation
passed with zero enabled sources. UID 10001 and the absence of pip/ensurepip were
verified. Complete repository lint and standalone Compose parity passed.
The user clarified that deployment should use a GitHub tag-triggered release,
not this local image. Target-platform builds and scans remain the release workflow's
responsibility; these local checks do not prove target-host live publication.
The [deployment checklist](MAC_TEST.md#accept-the-2026-10-12-topic-extension)
records the remaining installation checks.
