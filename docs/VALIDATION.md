# Current validation and acceptance

Updated: **2026-10-13**. This is the current status reference. Historical checkpoints
and detailed investigation evidence remain in the [archive](archive/README.md).
A user-reported result is identified separately from a direct observation or an
automated test. Operational acceptance was closed by Andreas on 2026-10-13;
full openHAB migration, charging semantics and unresolved channel freshness remain
separate. See the user acceptance note below.

## Local verification

The local historical release tag `v0.3.9` points to `e1c9a2d`, before the first
JSON/widget refactoring. On 2026-10-13, an isolated source snapshot passed all
253 offline tests, complete lint over 140 public files and Compose parity with
overrides. This proves local source checks for the rollback point, not release
image publication, hosted CI or target-host acceptance. The first JSON refactoring
is already recorded in `73a60bd`; subsequent refactorings receive separate commits.

On 2026-10-13, the configuration and HTTP JSON duplicate-key/non-standard-constant
checks were moved into one pure decoder. Three new boundary regressions cover
valid values, nested/escaped duplicate keys, malformed input, NaN/Infinity,
invalid UTF-8 and unchanged redacted error types/messages across configuration,
HTTP and persistent-state readers. All 58 focused tests passed before and after
the extraction. The full working-tree suite passed **256 offline tests** and
Compose parity/overrides. The first sandbox run failed only at four localhost
server binds; the successful rerun allowed local test sockets. No installation
device, portal or broker was contacted, and no deployment was performed.
Complete repository lint over 144 public files and diff hygiene also passed.

On 2026-10-13, a reported container-suite failure exhausted the 15-second
wall-clock guard in the mixed-source twelve-hour simulation. The same test passed
locally in approximately 0.4 seconds. CI also runs ARM64 images under QEMU;
emulation overhead is the suspected cause, not yet confirmed by a hosted rerun.
Both twelve-hour virtual sequences now use a bounded 120-second fixture guard.
Virtual durations, assertions and production read/shutdown watchdogs are unchanged.
Local validation passed all 250 offline tests, repository lint and Compose parity;
this does not establish hosted ARM64 success or live outage acceptance.

The documentation/widget cleanup preserved the bridge runtime and device configuration.
The subsequent API fix changes confirmation and unit checks; it does not activate
adapters or command gates.
The current working-tree offline suite contains **256 tests**; the local v0.3.8
tag has 253. Repository lint covers all public
tracked and non-ignored files, including generated widget parity. Compose parity
checks both standalone files and deployment overrides. Final cleanup results are
recorded in [todo.md](archive/2026-10-13/todo.md#2026-10-11--dokumente-und-widgetquellen-aufgeräumt).
The subsequent API confirmation/unit fix adds five regression tests, including
uncertain-command polling, retained observations and contradictory plan readback.
Results are recorded in [the new diary entry](archive/2026-10-13/todo.md#2026-10-11--review-1-api-bestätigung-und-plan-einheiten).
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
| Inverter sleep/wake | Evening behavior reported normal, 2026-10-11; autonomous morning wake-up with ready status and new measurements confirmed by user for 2026-10-12 | Deliberate sleep-versus-outage distinction and longer observations remain separate |
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
| Controlled stop/start | Previous acceptance on 2026-10-11; v0.3.6 healthy before restart and all seven sources/five MQTT connections ready after Compose restart in supplied logs, 2026-10-12 | New-run openHAB updates/settings continuity; broker/host restart and manifest details |
| Abrupt process failure / Last Will | User reports `$state=lost` on all five devices after SIGKILL; supplied log at 19:16:28 Europe/Berlin shows seven sources ready and five MQTT connections connected after explicit Compose up, 2026-10-12 | Post-start Docker health confirmed by user; autonomous crash restart, openHAB updates, settings/command replay and persistent-state contents not separately confirmed |
| MQTT outage recovery | User-reported successful update check and supplied log, 2026-10-11: all five connections recovered autonomously in 11.0–28.5 seconds from their respective outage detection; errors/timeouts remained visible, no unhandled future exception in supplied excerpt | Longer outages, Last Will and broader production failure matrix |
| Source status/health | Independent operational status, watchdogs, heartbeat/state protection offline tested; Home Manager startup accepted by user; supplied target-host startup summary shows all seven sources ready and all five MQTT connections connected; widget source availability with optional diagnostics disabled reported accepted by user, 2026-10-11 | Multi-hour faults; individual external alarm scenarios remain unspecified |
| Garage widget | PV operation/staging and iOS layout accepted by user, 2026-10-11; canonical source/export parity checked locally | Existing acceptance remains; future behavior changes need a new check |
| openHAB migration | 100-row ledger, 34 linked inverter Items, four Home Manager Items and ten derived capabilities inventoried | Seven unidentified Item links; full rules/UI/units/offsets/persistence continuity |
| External monitoring and alarms | Setup reported complete by user, 2026-10-11 | Specific monitored signals and triggered alarm scenarios not supplied; host reboot/state restoration remain separate |
| Docker and publication | Existing GitHub CI including both architecture builds/scans repeatedly successful according to user, 2026-10-11; v0.3.6 GHCR pull/version and healthy startup reported by user, 2026-10-12 | Future releases need their own hosted results and deployment checks |

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

## Garage connection indicator labels, 2026-10-12

With a ready measurement source, the connection row now displays Gesperrt for
that vehicle state and Ladefehler for Fehler am Ladepunkt. Both retain the orange
indicator without asserting cable attachment. Unknown states or non-ready sources
display Status unbekannt. Connected/disconnected labels and source gating remain
unchanged. Canonical source and generated MainUI import match. Full lint and all
217 offline tests passed; local MQTT test servers required execution outside the
sandbox. Installation and iPhone rendering acceptance remain pending.

## Sunny Boy DC input B implementation, 2026-10-12

The user requested both documented MPP inputs. Input B is now mapped as three basic read-only properties; the earlier production scan found valid zeros. Existing expansion regressions cover register addresses, FC04 intervals, scales, zero, S32 NaN and read-only discovery with advanced channels disabled. Live MQTT/openHAB acceptance remains pending; v0.3.3 predates this addition.

Validation after the addition: all 217 offline tests, full repository lint over 126 files, Compose parity and `git diff --check` passed.

## MQTT Explorer verification of v0.3.4 additions, 2026-10-12

Andreas reported v0.3.4 deployed and healthy. Direct read-only inspection of the
connected MQTT Explorer around 16:51–16:55 Europe/Berlin checked the 28 additions
(T01–T28) against advertised Homie properties and expanded metadata. All three
inverters and the eCharger advertised ready. No message was published, deleted or
changed; no configuration or device setting was modified.

| Group | New basic properties checked | Observation |
| --- | --: | --- |
| Tripower | 4 | Frequency and all three phase currents have numeric payloads and expected Hz/A metadata. |
| Storage | 5 | Frequency, L1 current, AC active power, battery current and voltage have numeric payloads; signed values preserved. |
| Sunny Boy | 10 | L3 power/voltage/current, frequency and DC input B have numeric payloads; the three L2 properties have correct metadata without measurement payloads. DC input B is valid zero. |
| eCharger | 3 | All three phase powers have float/W metadata and numeric payloads, with message history. Idle small negative readings are preserved. |

All 22 basic properties have expected datatype/unit metadata, `$retained=true`
and `$settable=false`. Nineteen have numeric payloads; the remaining three are
expected unavailable Sunny Boy L2 channels. No literal NaN was visible among these
properties. The six advanced inverter1/2 type/power-limit properties are absent
from advertised property lists. Andreas confirmed both deployed advanced flags
are disabled, so this absence is expected. Publication with the advanced group
enabled remains unverified.

Variable inverter readings changed during observation; retained values alone do
not prove source freshness or restart behavior. Wallbox total power was zero and
vehicle status waiting, so phase scaling under actual charging remains unaccepted.
No aligned independent SMA or openHAB measurement comparison was performed.
DC input A/B display names are identical despite distinct topic IDs; clarifying
those labels is a separate follow-up. Public evidence omits private device IDs,
addresses, raw telemetry and command history.

## DC input display labels clarified, 2026-10-12

Sunny Boy and Tripower now distinguish DC current/voltage/power input A and B
in profile names and English/German display dictionaries. All other profile
fields compare identically with the pre-change definitions; topic IDs, units,
registers, sentinels and polling remain unchanged. Generic translation keys remain
for custom profiles. Deployment and live `$name` refresh are pending; custom host
profile/translation overrides may need equivalent label changes.

Validation: all 217 offline tests, full lint over 126 files and `git diff --check` passed. Before/after discovery comparisons for both models in English and German changed only the six DC `$name` payloads per device, with an identical topic set.

## Selected inverter counters and derating implementation, 2026-10-12

Eleven optional read-only properties are implemented from the model lists and
existing production scan. Units and model-specific enums are documented in
[register evidence](REGISTER_VALIDATION.md#selected-counters-and-derating-extension-2026-10-12).
Four regression tests cover U64 word order/precision above 2^53, seconds, Wh-to-kWh
scaling without the legacy yield override, zero and sentinels, unknown/model-scoped
enum values, channel filtering, read-only discovery and optional readiness.
Existing profile properties and pollers compare unchanged from the pre-extension
working state. These additions are not deployed; direct device-GUI counter
comparison, MQTT publication and openHAB acceptance remain pending.

Final checks passed: all 221 offline tests, complete repository lint over 127 files, standalone Compose parity and `git diff --check`. No live device or broker action was performed for this extension.

Andreas confirmed the channel groups: battery energy Basic, operating/feed-in times Advanced, and derating Diagnostics. The implementation already matches the approved selection.

## Local/CI Markdown lint parity, 2026-10-12

The two reported MD060 failures were reproduced from unchanged HEAD documents
with the pinned pymarkdownlnt 0.9.40. The local environment had 0.9.39. Compact
right-aligned table delimiters now use `--:`. The lint runner rejects Python
linter package versions that differ from `tests/requirements-lint.txt`; a
simulated 0.9.39 mismatch returned exit code 1 with an update instruction.
Full repository lint (127 files) and all 221 offline tests passed after updating
the local environment. Tests used local loopback servers outside the sandbox.
Hosted CI verification remains pending.

## Full DEV MQTT acceptance, 2026-10-12

Direct read-only MQTT Explorer inspection covered all 268 advertised properties
of the five user-selected DEV adapters, with Advanced and Diagnostics available.
All had required metadata; datatype/enum/unit checks passed, with 205 payloads
and 63 explained or tracked absences. All five devices and all read sources were
ready; read failure/timeout/outage/missing-critical counters and Home Manager
rejected-block count were zero. All 39 recently added channels were present:
36 with values, three Sunny Boy L2 additions with metadata only.
The new type/limits, time counters, Storage energy, derating and DC A/B labels
therefore have direct DEV publication evidence. A fresh Explorer reconnect
confirmed sampled legacy paths absent and operating counters progressed.

[Complete scope, counts and limitations](MQTT_DEV_VALIDATION_2026-10-12.md) distinguish
expected phase/delegated NaN, wallbox availability filtering and unused command
results. Commands were not sent. Production/openHAB continuity, independent SMA
counter comparison, charging under load and outage/reboot acceptance remain open.

## Retained eCharger timestamp analysis, 2026-10-12

[Analysis and classification matrix](ECHARGER_TIMESTAMP_ANALYSIS_2026-10-12.md)
cover 4,597 supplied records over approximately 3 h 20 min, including idle and
two positive-power periods. Power, current, total energy, vehicle status and
plant-control observations refresh timestamps with unchanged numeric values.
Session energy freezes while idle and crosses the existing 180-second filter
despite fresh surrounding measurements. Fixed old health/event/mode/authorization
timestamps remain unresolved. Phase voltage is fresh but lacks constant-value
pairs. Review 4 remains open; no runtime, installation or freshness policy changed.

Analysis validation: all 29 matrix keys are unique; counts reconcile to all 4,597
records. Full lint over 130 files, all 221 offline tests and `git diff --check`
passed. The initial sandbox test run blocked four loopback socket binds; the
approved rerun passed. Raw input files remain unchanged.

## Scoped eCharger remaining-lifetime correction, 2026-10-12

Selected channels now propagate monotonic observation times from reader parsing
through SourceState: charging power, API phase currents, the API primary total
charging-energy counter, vehicle-status text/code, and the three SEMP plant-control
observations. The observation anchor subtracts accepted device age; subsequent
processing time consumes remaining lifetime. Repeated cached timestamps preserve
the deadline, while unchanged numbers with a new timestamp refresh it. Settings,
unknown state semantics, session energy, voltage/phase power and alternate energy
channels keep their existing behavior. No added HTTP request, environment option,
write path or topic is introduced. Plain-dict Modbus/UDP/portal reads remain
receipt-based. Per-property configured limits still apply.

Four intended end-to-end regressions failed before the fix. Eleven added tests
cover exact/near-limit age, zero, processing delay, partial updates, repeated
cached stamps, equal values with a new stamp, aliases, control ages, invalid
monotonic metadata, shorter property limits, scaled primary energy and conservative
alternate fallback, SEMP filtering without settings, API/SEMP independence in both
directions, and no retained measurement replay/deletion on expiry or restart.
Existing malformed/future/conflicting timestamp, settings confirmation, command
and uncertainty tests remain part of the full suite.

No installation, broker or device action was performed. Deployment and openHAB
source gating under actual expiry remain unaccepted. Review 4 is partly addressed,
not closed: unresolved channel policies and installation acceptance remain open.

Final validation passed: all 232 offline tests, complete lint over 130 project
files, standalone Compose parity including overrides and `git diff --check`.
Tests used synthetic loopback servers outside the sandbox; no installation
endpoint was contacted.

## Target-host restart and SIGKILL acceptance, 2026-10-12

Andreas supplied CLI output identifying v0.3.6, with the target-host container
healthy before the controlled Compose restart. Startup summaries at 19:14:09 and
19:14:43 Europe/Berlin show all seven configured read sources ready and all five
MQTT connections connected. Following the requested SIGKILL procedure, Andreas
reported `$state=lost` visible for every Homie device. After explicit
`docker compose up -d sma-mqtt-bridge`, the supplied 19:16:28 startup summary again
shows all seven sources ready and all five connections connected.

This is user-reported broker observation and supplied-log evidence, not direct
Codex access. It accepts Last Will delivery for this abrupt termination and
recovery after explicit start. It does not prove autonomous restart after crash,
post-start Docker health, command non-replay, preserved state-file contents,
openHAB/history continuity or host/broker restart. No private host/device/topic
identifiers or raw telemetry are included. Codex performed no live action.

## Target-host health and boot startup confirmation, 2026-10-12

Andreas confirmed that the container is healthy after the tested restart and that
a host reboot starts the bridge automatically. This accepts reported container
health and boot startup for the installation. No post-reboot source/MQTT log or
state-file comparison was supplied; complete source recovery, openHAB/history,
settings continuity and manifest/uncertainty-journal restoration remain separate.
Boot startup does not establish autonomous recovery from an arbitrary process crash.

## User-reported Mosquitto stop/start recovery, 2026-10-12

Andreas confirms an already completed Compose-service interruption of Mosquitto:
the broker service was shut down, bridge behavior was observed, and after broker
startup the bridge reconnected. This accepts user-reported reconnect following
that service outage; no repeated test is required for this same scenario. The
exact test date, duration, individual connection timings and alarm observations
were not supplied. Longer outages, in-flight publish failures and state/history
continuity remain separate; no complete failure matrix is inferred. Codex did not
operate the broker or other installation services.

## User-reported InfluxDB/Grafana restart continuity, 2026-10-12

Following the targeted Grafana checklist for approximately 19:05–19:30
Europe/Berlin, Andreas confirmed that all four checks passed: Home Manager
import/export energy counters had no reset or unexplained jump; eCharger total
energy retained its kWh scale and older history; Home Manager power received
new samples after the 19:16 restart; derived daily values showed no abnormal
restart-related jump. The installation uses InfluxDB/Grafana.

This is user-reported acceptance for those selected series across the tested
bridge restart window. No raw persistence samples or queries were supplied to
Codex. It does not certify all migration rows, midnight/DST behavior, an openHAB
restart, or Wallbox setting continuity, which remains separately unconfirmed.

## User-reported Wallbox setting continuity, 2026-10-12

Andreas confirmed the follow-up read-only widget comparison: charging mode,
charging release and maximum charging power match their pre-restart settings;
plan energy/end time were included conditionally if a plan existed. Plan presence
was not separately stated, so no unconditional plan-continuity claim is made.
Together with the preceding Grafana checks, this completes the selected
openHAB/history/settings continuity checklist for the tested bridge restart.
This is user-reported display/readback evidence, not command-traffic capture or
a complete audit of every setting, rule, persistence series or migration row.

## User-reported inverter morning wake-up, 2026-10-12

Andreas confirmed that the proposed morning check worked on 2026-10-12:
the inverters woke autonomously, returned ready and supplied new measurements
after the night. This complements the previously reported normal evening
behavior. Exact times, per-device logs and aligned readings were not supplied;
this is user-reported acceptance of the observed overnight cycle, not a controlled
network-outage test or evidence for every future weather/operating condition.
The morning observation predates the evening v0.3.6 tests and does not establish
a v0.3.6-specific overnight run.

## Extended deterministic long-outage verification, 2026-10-12

Three additional tests exercise actual supervisor/publisher loops with synthetic
readers/clients and virtual time. The twelve-hour mixed-source sequence verifies
partial/slow/time-out/disconnected reads, critical expiry and independent ready
zero values from another supervisor, serialized reads, cleanup and recovery.
Twenty-four real watchdog cancellations consume twelve simulated hours and leave
no overlapping read. The broker sequence simulates ten hours of connection
failures plus lost publication acknowledgements until twelve hours, then restores
publication; connected clients close, no background task remains, retries/logs
are bounded, and topic manifest/retirement and an unchanged journal are checked.
See [scope and limits](OPERATIONAL_ACCEPTANCE.md#extended-deterministic-fault-sequences-2026-10-12).

No runtime behavior or configuration changed. No installation endpoint was
contacted. These tests do not certify actual memory/CPU/network soak, TLS,
external alarm delivery or the complete production failure matrix.

Final checks passed: all 235 offline tests in approximately 7.3 seconds, complete
lint over 131 files, standalone Compose parity including overrides, and
`git diff --check`. Loopback transport fixtures required the permitted execution
outside the sandbox; the three new fault tests use no sockets.

## User-supplied resource baseline and effective limits, 2026-10-12

Andreas supplied one Docker stats snapshot: CPU 0.73%, three tasks, and zero
reported memory usage/limit and network I/O. The zeros are unavailable/unverified
accounting, not evidence of zero resource consumption; no optimization is justified
by this single sample. Memory-controller availability and actual network mode
need read-only host checks before selecting a collection method.

The allowlisted operational report shows all seven sources: inverter minimum
poll intervals 3/5/3 s, Home Manager 3 s, API 60 s, SEMP 30 s, portal 900 s.
Portal freshness is 1,800 s; API/SEMP 180 s, inverters 60 s and Home Manager 30 s
with individual property overrides. Read-cycle limit 120 s, retry 1–60 s,
health heartbeat 10 s / expiry 60 s and MQTT timeout/keepalive 10/60 s.
This confirms reported effective configuration, not measured request rates or
manufacturer approval for those intervals. No runtime or host setting changed.

## Linux host resource probe and recorder preparation, 2026-10-12

Andreas supplied cgroup v2 with systemd and host networking. The Python process
reported RSS/HWM 53,776 KiB (52.5 MiB), two threads; docker-init reported 592 KiB
and one thread. This is one resident-memory observation with identical high-water
mark, not evidence of a stable long-term baseline. The supplied `/proc/cgroups`
listing is not authoritative for controller availability on cgroup v2; inspect
actual sysfs memory metrics. Docker's zero memory remains unexplained.

A bounded external [host recorder](OPERATIONAL_ACCEPTANCE.md#bounded-linux-host-resource-recording)
is prepared with cgroup CPU, optional memory, process RSS and contextual host
network counters, reset-aware sampling and exclusive output creation. Five
synthetic tests cover CPU counter discontinuities, missing/partial process reads,
missing/root-cgroup accounting, bounded collection with restart gaps and identity
redaction, exclusive output, and Python 3.9-compatible host syntax. The bridge
image/runtime and existing polling configuration are unchanged. Recorder deployment
and the actual two-minute/24-hour host recording remain pending.

Recorder preparation validation passed: all 240 offline tests, full lint over
133 public files, standalone Compose parity with overrides and `git diff --check`.
This is local fixture evidence only; no target-host recording was started.

## User-supplied two-minute host recorder check, 2026-10-12

Three supplied samples span 20:56:16–20:58:16 Europe/Berlin. Container cgroup
CPU deltas are 4.328% and 3.686% of one core; the initial CPU rate is null as
expected. Summed process RSS/peak RSS is unchanged at 55,672,832 bytes
(53.1 MiB), with both expected processes read, three total threads, healthy
status, restartCount zero and one continuity segment. Cgroup memory is null,
so process RSS is the available memory trend; controller availability is not
otherwise established. Two physical host-interface counters are recorded,
without attributing that traffic to the bridge. The recorder short check is
accepted for these metrics; a 24-hour resource soak remains pending.

## Basic eCharger vehicle-status code, 2026-10-12

`measurements/vehicle-status-code` (wire ID `vehiclestatuscode`) now belongs to
the basic group. API baseline ownership and SEMP supply the same integer property
with Advanced/Diagnostics disabled. Firmware remains Advanced, other channel
filters and command gates are unchanged. No new request, unit conversion,
readiness requirement or timestamp rule was introduced. The text and code aliases
retain the selected observation's remaining lifetime.

Existing filter/discovery/state tests now check basic availability, integer
non-settable retained metadata, unchanged wire ID, payload and readiness behavior.
API freshness/ownership cases run with optional groups disabled and verify the
code expires with the text alias and is omitted when SEMP owns baseline values.
The change is local only; deployment and production discovery remain pending
until the resource baseline recording is complete.

Validation passed: all 240 offline tests, full lint over 133 files, standalone
Compose parity including overrides and `git diff --check`. No installation
endpoint was contacted.

## Publication documentation reconciliation, 2026-10-12

README and [release notes](RELEASES.md) now describe the existing GHCR image
and separate published v0.3.6 behavior from local unreleased additions. Installation
uses explicit Compose interpolation via root smab.env and supports exact image
version pinning. Upgrade/rollback preserve the Compose project, state volume,
manifest and uncertainty journals. Obsolete future-publication statements were
removed from configuration/context/plan and Compose/workflow comments. Runtime
options and workflow behavior are unchanged. No new tag, push or deployment
was performed.

Validation passed: all 240 offline tests, complete lint over 134 files, standalone
Compose parity with overrides and `git diff --check`. Compose and release workflow
diffs contain comment changes only. Installation commands were reviewed locally,
not executed against the production host.

## Home Manager plant-time openHAB display and DateTime, 2026-10-12

Direct MainUI inspection found the existing plant-time Item as Number:Time with
unit s, its original Homie link and numeric InfluxDB persistence group. Its State
Description now converts accepted whole Unix seconds through Java Instant and
Europe/Berlin for display, preserving its original state/type/link and history.
The live display showed a local date/time with CEST after saving.

A distinct DateTime companion was created with autoupdate disabled and readOnly
metadata, in the same equipment group without copying the numeric persistence
group. Its link to the existing channel uses SCRIPT ECMAScript to return an ISO
offset timestamp from the supplied Unix seconds. Command/state return scripts
remain blank. After page reload, the stored link profile was inspected and
successive date/time displays advanced in thirty-second steps. The companion is
not separately persisted and no existing rule was changed.

[Setup and exact transformations](../openHAB/openHAB.md#home-manager-plant-time-display-and-rules)
follow official Item/transformations/JavaScript documentation. No device write,
bridge restart/deployment or protocol/profile/interval change occurred. No private
installation identifiers or raw telemetry are included here. ZoneId handles DST;
actual time-change/startup behavior and future rule use need their own acceptance.

Repository validation: all 240 offline tests and `git diff --check` passed;
complete lint over 134 public files passed after correcting section spacing.
The local machine has no Java runtime for an additional offline JVM execution;
JavaScript/Java conversion and recurring DateTime updates were verified directly
in the installation's openHAB runtime. No synthetic future date was injected into
the live Item for DST testing.

## Standard PV slider metadata documentation, 2026-10-12

The MainUI guide now includes default-list `oh-slider-item` metadata for the
existing PV Dimmer: 0–100, step 1, raw state through `ignoreDisplayState`,
release-only sending and handle labels. Official component documentation supports
those properties; `type`, `sendButton` and `useDisplayState` were removed from the
slider example. The guide distinguishes release sending from the comfort widget's
staged Apply workflow and preserves autoupdate=false/plain integer commands.
This is documentation/configuration review only; no portal command or live widget
change was performed. Installation behavior remains to be accepted separately.

PV slider documentation refinement, 2026-10-12: the user reported loss of the
percent display in raw-state mode. Current list/card examples retain display
state (`ignoreDisplayState: false`) for the integer-percent Dimmer; raw mode
is only an option when formatting causes misinterpretation. The supplied
standalone card's scale/label/release-only options were checked against official
component documentation. No live command or widget configuration was changed.

## eCharger Advanced plant-control review, 2026-10-12

[Findings and source limits](ECHARGER_CONTROL_OBSERVATIONS.md) reconcile runtime
group/ownership with supplied timestamp recordings and official SMA Multi-EVC
context. All three topics require SEMP plus Advanced; Diagnostics is independent.
Active count remains nonzero during observed waiting/zero-power periods. The
normalized limits are constant across the captured charging transitions, and
matching API/SEMP metadata supplies no unit/reference-power contract. Exact
semantics remain partly open; no runtime, group, configuration or live-I/O change
was performed. This review does not authorize a setter or a new controller.

Validation passed: all 240 offline tests, full lint over 135 public files and
`git diff --check`. A separate non-I/O check of all four Advanced/Diagnostics
combinations confirms that all three control properties depend on Advanced only.

## Manual portal refresh, 2026-10-12

Implemented locally: enabled portal adapters expose a settable string
`portal/refresh`, accepting only non-retained `refresh` requests. The existing
supervisor performs validated reads and updates existing preference topics;
write gates need not be enabled. A separate non-availability feedback state
reports progress and rejection. No new portal write method, session or ENV flag.

Seven deterministic offline tests cover zero-interval idle startup, invalid and
retained payloads, runtime discovery/routing with write gates off, disabled
portal exclusion, periodic-wait wakeup, coalescing during a read, authentication
blocking, preserved last values and retry backoff on transient failure, and real
asyncio deadline cancellation/session reset. Existing MQTT transport and command
tests cover shared consumer rejection and cleanup.

MainUI String Item/standard link/autoupdate=false and command-button setup is
documented against official Homie binding and button documentation. No live
portal, broker or openHAB changes; deployment/discovery/button acceptance remains
pending after the user-run resource baseline.

Validation: all 247 offline tests passed, complete lint over 137 public files,
standalone Compose parity including overrides, and diff hygiene passed. Existing
loopback test servers required the approved run outside the filesystem sandbox;
no installation endpoints were contacted.

## Selected additional topics visible, 2026-10-13

Andreas confirms that all topics in the supplied acceptance list are present:
inverter frequency, operating/feed-in duration and derating reason; Tripower
phase currents; Storage AC power/current, battery current/voltage and charge/
discharge energy counters; Sunny Boy L2/L3 and DC input B; inverter1/2 device
type and power limits; and eCharger phase active power.

This is user-reported topic visibility, not a direct broker inspection. The
confirmation does not separately establish numeric payload availability for
every operating state, openHAB links/units or an independent device-value
comparison. Those acceptance steps remain open. No installation changes.

## Target-host resource recording, 2026-10-13

The user supplied 1,324 samples covering 22 h 06 min, plus the three-sample
recorder check. All long-run samples report running/healthy, restart count 0 and
one generation. CPU average 4.355% of one core, sampled maximum 5.708%; two-process
RSS median 53.250 MiB and first/last-hour medians 53.094/53.188 MiB. Temporary
third-process snapshots explain the distinct summed-memory population, without
identifying that process. Two process snapshots are partial; cgroup memory is
unavailable and networking counters are host-wide.

See [the analysis](RESOURCE_SOAK_ANALYSIS_2026-10-13.md) for methodology and limits.
**Resource acceptance closed by Andreas on 2026-10-13**: the measured 22 h 06 min
is explicitly sufficient; no additional recording is required. No optimization
is indicated. This does not assert a complete 24-hour recording. Accounting
limits remain. Andreas confirms target-host recorder/file cleanup; repository
tooling remains available. No direct cleanup inspection, live source-level
acceptance or release/deployment.

## v0.3.7 release and target-host deployment, 2026-10-13

Release commit `6a143dfb327e8170149b315d0337bbe8cfec5942` and annotated tag
`v0.3.7` were atomically pushed on Andreas' explicit request. Both
[release workflow](https://github.com/alaub81/sma-mqtt-bridge/actions/runs/38437253361)
and [main CI](https://github.com/alaub81/sma-mqtt-bridge/actions/runs/38437254996)
succeeded: lint, offline tests/Compose parity, amd64/arm64 image tests and security
gates, followed by multi-architecture GHCR publication.

The target host pulled `ghcr.io/alaub81/sma-mqtt-bridge:0.3.7`, digest
`sha256:57a508291a9569817f9a767df9a6b0a0ae87b117c5b70e29d6d35fd5298d62b1`.
An isolated network-disabled version check passed before replacement. Compose
image interpolation was pinned to 0.3.7 in the host's `.env`; previous `.env`
(if present) and image ID were saved in a host-private rollback directory.
The existing Compose project and state-volume mount were preserved; no volume
removal, polling adjustment or device preference command was performed.

Compose replacement completed healthy and the installed CLI reports 0.3.7.
At 19:23:40 Europe/Berlin, startup reports all seven data sources ready and all
five MQTT connections connected. A subsequent heartbeat independently confirms
those source/connection states. Auxiliary write-result states remain init until
a command occurs and do not contribute availability.

The deployment is accepted for version/health/startup recovery. New MainUI refresh
Item/button setup, live command feedback and full openHAB/history continuity
remain separate checks; no preference writes or comprehensive migration acceptance.

## MainUI portal refresh acceptance, 2026-10-13

Andreas supplied the configured String Item with autoupdate=false, the
portal#refresh link and command actions in both default list and standalone
widget metadata. After the proposed app-change/refresh check, Andreas reports
that the values arrive after approximately 3–5 seconds. Manual refresh is
user-accepted for this observed test; no independent MQTT trace or exhaustive
failure/rate-limit acceptance is implied. The setup guide now includes both
Item metadata widget configurations and distinguishes them from page buttons.

## Battery energy return ratio, 2026-10-13

Andreas reports both Storage counters visible and plausible in openHAB and
confirms a common counter start. Independent SMA-GUI comparison, reset behavior
and measurement boundary are not separately confirmed. The requested cumulative
ratio is implemented locally as measurements/batteryefficiency (%), basic,
read-only, using the existing same-poll kWh counter pair. Three new offline tests
cover arithmetic, zero/invalid inputs, unclamped ratios above 100%, compatible
profile selection, metadata, same-response computation and no refresh between
counter polls. Deployment and live derived-topic acceptance remain pending.

Validation: all 250 offline tests and Compose parity including overrides passed;
complete lint over 139 public files and diff hygiene checked. No installation
changes or release/deployment for this addition.

## Operating/feed-in duration comparison, 2026-10-13

Andreas confirms that the discussed openHAB operating/feed-in duration values
match the SMA display after the Advanced-channel and unit setup discussion.
The user-reported display comparison for M07 is accepted. No concrete readings,
timestamps or device-by-device list were supplied; no independent live inspection
or separate 15-minute progression/operating-state transition test is claimed.
No Item, device or polling changes were made.

## Storage electrical measurement comparison, 2026-10-13

Following the targeted Storage comparison question, Andreas confirms that the
values are present and match: signed AC active power, battery current and battery
voltage. The user-reported comparison for these Storage additions is accepted.
No concrete readings/timestamps or independent live inspection were supplied.
Tripower/Sunny Boy comparisons and the remaining M02–M04 properties are separate;
this does not establish acceptance for every new inverter channel. No changes
to device settings, Item configuration or polling.

## Tripower electrical measurement comparison, 2026-10-13

Andreas confirms that grid frequency and phase currents L1/L2/L3 match between
openHAB and SMA. The user-reported comparison for these four basic additions is
accepted. No concrete readings/timestamps or independent live inspection were
supplied. Other channel comparisons remain separate; no device, Item or polling
changes were made.

## Sunny Boy additional measurement comparison, 2026-10-13

Andreas confirms matching openHAB/SMA readings for the discussed L3 active power,
voltage and current, grid frequency and DC input B measurements. This
user-reported value comparison is accepted. No concrete readings/timestamps,
independent live inspection or separate evidence of actual input-B wiring were
supplied. Valid L2 payloads, host-profile reconciliation and other new channels
are not established by this confirmation. No device, Item or polling changes.

## Tripower/Storage type and power-limit comparison, 2026-10-13

Andreas confirms the discussed comparison of measurements/type, maxpower and
setmaxpower for Tripower and Storage. These advanced properties remain read-only;
both power limits use W. The user-reported value comparison is accepted. No
concrete readings/timestamps or independent live inspection were supplied.
Host-profile reconciliation and other acceptance criteria remain separate;
no device, Item or polling changes were made.

## Basic derating reason, 2026-10-13

On Andreas' request, the three bundled profiles classify derating-reason as Basic.
The existing diagnostics/deratingreason topic, model-scoped enums, invalid-value
handling, register blocks and read-only/readiness semantics are preserved.
Existing tests now verify presence with Advanced/Diagnostics disabled, unchanged
Homie metadata and valid no-derating state without replacing required status.
Andreas reports the current no-derating display; other event states are not live
accepted. Host-profile reconciliation and deployment remain pending.

Validation: all 250 offline tests, complete lint over 139 public files, Compose
parity with overrides and diff hygiene passed.

## Home Manager ISO plant time, 2026-10-13

Locally implemented Basic measurements/planttimeiso and Advanced raw
measurements/planttime via two profile mappings of one existing register read.
Three tests cover U32 boundaries/invalid sentinel, UTC/DST instants, incompatible
format configuration, optional-group discovery, one-call raw/ISO consistency,
invalid responses and no cached re-publication between polls. Existing basic-only
Home Manager filtering checks verify raw exclusion and ISO inclusion.

No live deployment or DateTime-link acceptance. Homie 4 uses string metadata;
MainUI instructions use the SCRIPT profile to parse ISO into the DateTime Item.
Existing raw numeric history requires Advanced and remains untouched. Host
profile overrides require reconciliation; UDP source is unaffected.

Validation: all 253 offline tests, complete lint over 140 public files, Compose
parity with overrides and diff hygiene passed.

## Remaining operational acceptance closed by user, 2026-10-13

Andreas reports conducting additional tests and explicitly requests closing the
remaining operational acceptance. Remaining outage/recovery and host-state
restoration tasks are therefore accepted by the user. Existing individually
documented restart, broker recovery, healthy startup and 22-hour resource
observations remain the concrete evidence.

No additional scenario list, durations, logs or tested version was supplied.
This acceptance is not a new independent observation of TLS alarms, journals,
process-lock behavior or topic retirement, nor acceptance of the not-yet-deployed
local v0.3.8 changes. Earlier procedural/evidence gaps remain methodological
limits rather than a request to repeat the accepted operating tests.

Unresolved measurement timestamp semantics, full openHAB/history migration,
physical charging checks, planned infrastructure changes and future release
validation remain separate tasks. No live action was performed for this closure.

## Widget expression simplification, 2026-10-13

The canonical garage widget and generated MainUI import replace 29 repeated
expressions with three functions in the existing `oh-context`: local write gate,
portal write gate and charging mode. No new scope or variable defaults were added.
Parsed YAML equality against the pre-change widget, after expanding every function
call and removing only the new function definitions, confirms unchanged expressions,
layout, props, command payloads and per-control validation. Functions retain dynamic
Item/prop/variable evaluation; see the official
[oh-context contract](https://www.openhab.org/docs/ui/components/oh-context.html).

All 253 offline tests passed with local test-server sockets permitted. The initial
sandboxed run could not bind four localhost transport fixtures. Complete lint and
generated export parity passed. MainUI rendering and reactive dependency tracking
remain pending installation acceptance; offline YAML equivalence does not certify
the UI renderer. The [widget guide](../openHAB/echarger-comfort.md#shared-expressions-and-update-check)
documents visual/gating checks and restoring the saved installed YAML. No live
openHAB change or device command was performed.

## Focused correctness lint rules, 2026-10-13

Ruff's pinned version and existing E4/E7/E9/F/I selection are retained. Ten
additional explicit rules are enabled: B006, B008, B012, B018, B020, B023, B025,
B032, RUF006 and RUF100. They cover shared/evaluated defaults, suppressed
exceptions, discarded expressions, loop bindings, duplicate handlers, accidental
annotations, unreferenced asyncio tasks and stale noqa directives. No broad style
family, global ignore or version upgrade was introduced.

Eight loop-variable diagnostics across three existing test files were resolved
by binding fixture values at callback definition time. Existing test assertions
and production watchdogs were preserved. An additional binding in the separately
added JSON parsing test was fixed in the shared workspace and remains with that
pending JSON change. Concurrent JSON/widget edits are not part of the lint commit.

Each enabled rule rejected a synthetic erroneous snippet using the actual project
configuration. Complete lint over 144 public files, all 256 working-tree offline
tests, Compose parity with overrides and diff hygiene passed. This lint change
has no production runtime edit, publication or deployment.
