# Current validation and acceptance

Updated: **2026-10-13**. This is the current status reference. Historical checkpoints
and detailed investigation evidence remain in the [archive](archive/README.md).
A user-reported result is identified separately from a direct observation or an
automated test. Operational acceptance was closed by Andreas on 2026-10-13;
full openHAB migration, charging semantics and unresolved channel freshness remain
separate. See the user acceptance note below.

## v0.3.11 release publication, 2026-10-13

At Andreas' explicit request, `main` and annotated `v0.3.11` were pushed atomically
to commit `058738ecaef469b2047c7d2c971f9bb86c04ce47`. The recorder extension
follows the separately committed heartbeat, metadata-cache and payload hardening.
All 275 tests pass locally and in both local release images; each image reports
exactly `sma-mqtt-bridge 0.3.11`. Unrelated Compose comments and `.env.example`
were preserved outside the release.

Hosted [CI run 38454497216](https://github.com/alaub81/sma-mqtt-bridge/actions/runs/38454497216)
and [release run 38454496808](https://github.com/alaub81/sma-mqtt-bridge/actions/runs/38454496808)
completed successfully. Tests/lint, amd64/arm64 container tests and Trivy gates
all passed, followed by successful publication. GHCR index
`ghcr.io/alaub81/sma-mqtt-bridge:0.3.11` was directly inspected and contains
Linux amd64 and arm64 manifests, plus their provenance attestations:

- Index: `sha256:39512557b7da42d7f3bb0a6da251d746ec1620b42d3f521399637667d057aedc`
- amd64: `sha256:6eb84e43ccc6ba19e41cfc3a3c7474290bf7fecc14a5bbb3aa00b2299ffb2414`
- arm64: `sha256:afa7c41ab48e4435de3e5d6dea3bf79d2edeaea230470cd584156f59862cebb8`

Both published platform images were pulled by the index digest and run locally
with external networking disabled; each reports exactly
`sma-mqtt-bridge 0.3.11`.

The publicly downloadable recorder matches the tagged source exactly (SHA-256
`b4bfb6ec2d109c6a7a668ab6e5db5b422404606950d55a07308a55790959e95c`).
No target-host deployment, recorder launch or new CPU/I/O acceptance was performed;
Andreas owns those steps. The earlier resource/operational acceptance stays closed.

## Local verification

The external Linux resource recorder now includes schema-2 cgroup block I/O and
process logical/storage counters plus continuity-safe rates. Six new regressions
cover multiple devices, empty versus unavailable controllers, malformed/duplicate
counters, independent controller failures, process start time, partial snapshots,
membership/reset boundaries and exclusion of internal identities from output.
All **275 offline tests**, complete repository lint and Compose parity/overrides
pass. Python 3.9 syntax remains supported. A Linux ARM64 container additionally
verified actual `/proc/self/io` sampling without external networking. This does
not verify target-host procfs permissions or create a target-host I/O baseline.
Andreas requested v0.3.11 publication and will deploy/start the recorder himself.

Final container validation of runtime `e378535e` built
`0.3.10-dev.3+e378535e` for Linux ARM64 and AMD64. Each image passes all 269
offline tests with external networking disabled and public read-only fixtures.
ARM64 version/configuration/image-exclusion checks passed. Runtime dependencies,
base image and Compose runtime settings were not changed by this review.
The [complete performance review](PERFORMANCE_REVIEW_2026-10-13.md) records
measured gains, cache invalidation, hardening and remaining evidence limits.

Resource hardening additionally bounds observation payloads with the configurable
`SMAB_MAX_PAYLOAD_BYTES` / JSON `runtime.maxPayloadBytes` (4096 bytes by default).
The previous encoder expanded a nine-byte `1e1000000` value into 1,000,001 bytes;
the new length check rejects extreme positive/negative exponents before formatting.
Five regressions cover fixed-point boundaries, zero/signed zero, integer/enum/
boolean payloads, UTF-8 byte boundaries, invalid Unicode, invalid-sample readiness,
JSON/ENV precedence and propagation to source states. All **269 offline tests**,
full repository lint, Compose parity/overrides, Python compilation and local
documentation-link checks passed. The benchmark snapshot checksum stays unchanged;
the final local median was 0.255259 s for the same 2,000 cycles (about 42% below
the 0.436556 s original baseline). No live-device test or deployment was performed.

The subsequent metadata optimization passed **264 offline tests**, full lint
and Compose parity/overrides. Three new regressions cover inventory/type/TTL
replacement, runtime readiness/default-lifetime changes, per-sample device age,
invalid observations, dataclass copies and late monitor/diagnostic changes with
retained discovery retirement. An independent comparison against the previous
SourceState implementation matched all outputs across 168 phase/time cases.
The reproducible `tests/runtime_benchmark.py` fixture uses seven synthetic sources
and 150 bundled properties without device I/O. Five repetitions of 2,000 cycles
reduced median process CPU from 0.436556 s to 0.251237 s (approximately 42%)
for snapshot/status/missing-critical work on the local Python 3.14.8 environment.
Snapshots at five freshness boundaries retained the same SHA-256 digest:
`32d9f1c27f8a54fbc7a2523e88edf5f5142a0655ac87d5670cc91ce9b3d5be50`.
Twenty heartbeat writes changed from 40 explicit sync calls to zero. These are
local microbenchmark results, not new target-host CPU or HDD measurements.

On 2026-10-13, a fresh complete review baseline passed all 259 offline tests,
repository lint and Compose parity. The first resource optimization separates
atomic liveness heartbeat replacement from durable recovery-state storage.
Two regressions verify that running/stopped heartbeats avoid explicit disk sync,
recovery files still perform both file and directory sync, and a failed heartbeat
rename leaves the previous complete observation readable. All **261 offline tests**,
repository lint and Compose parity/overrides passed. At default intervals this
removes 17,280 explicit heartbeat sync calls per day, while atomic replacements
and health age/PID checks remain. This counts application calls, not measured
physical HDD operations. No target-host deployment or new resource recording.

On 2026-10-13, inverter and delegated Home Manager property metadata construction
was consolidated into `profile_property`. Sorted snapshots of all property fields,
Homie discovery, readiness keys, pollers and definitions remained byte-identical
across 240 cases: three bundled inverter profiles, synthetic mapped types,
Home Manager core/delegated properties, duplicate/invalid assignments, channel
flags, interval overrides and stale-time floors. Three additional regressions
preserve enum order, the distinct non-enum format policies, readiness and lifetimes.
All 30 focused tests passed before and after the extraction; the full suite passed
**259 offline tests**, and Compose parity/overrides passed. No device/broker I/O,
profile-file modification, command or deployment was performed.
Complete repository lint over 145 public files and diff hygiene also passed.

Final local image verification built `bf21423` as
`0.3.9-dev.3+bf214232` for Linux ARM64 and AMD64 using the unchanged pinned
Dockerfile. ARM64 ran natively on the local Docker host; AMD64 ran under emulation.
Both images passed all **259 offline tests**, exact version checks, disabled-source
`--check-config`, and image guards excluding private configuration, Git metadata,
pip and ensurepip. Containers used `--network none` and read-only public test
mounts. Local image names are `sma-mqtt-bridge:refactor-check-arm64` and
`sma-mqtt-bridge:refactor-check-amd64`. The final source comparison against
`v0.3.9` contains only the JSON and Modbus metadata extractions under `ressources/`;
bundled profiles, requirements, Dockerfile and Compose templates are unchanged.
No hosted CI/security result, release image publication or live device acceptance
is inferred from these local checks. The rollback tag remains on `e1c9a2d`.

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
The current working-tree offline suite contains **259 tests**; the local v0.3.8
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

## Read-only PV inventory and aggregation design, 2026-10-14

The [plant design and supplementary CSVs](PV_AGGREGATION_DESIGN.md) record live
Item metadata, channel-link identities, rule dependencies and four query methods.
The 129 scoped entries contain 51 old PV-tree entries including groups, four new
Homie device groups with 70 non-group Items, and four external dependencies.
All 109 listed rule code views were read; 29 relevant rules recorded, including
five additional presence/season/controller dependencies outside obvious PV names.
Literal-reference extraction does not prove dynamic-name/imported-code coverage.

All 70 new links and the 38 corresponding old links were inspected through UI.
The latter remain 34 Modbus and four SMA Energy Meter binding links. Comparison
manifest identities match observed new channels and current Item types; 38 pairs
are existing, eight aggregate destinations proposed, four old-only and 32 new-only.
This is source/mapping evidence, not persisted time-series agreement, an installed
Grafana dashboard, aggregate runtime acceptance or complete openHAB migration.

CSV column structure, unique Item identities, references, pair type/topic matches,
counts and enabled/disabled rule states passed consistency checks. Berlin calendar
examples for 2026-03-29 and 2026-10-25 confirmed 23/25-hour local days; no daily
runtime has been implemented. All 275 existing offline regressions passed with
local test-server permission. No device/broker/portal action or target-host change.
Private thresholds, tariffs, endpoints, credentials, states and raw scripts are
excluded from saved inventories; original private references remain unchanged.

## Post-update 24-hour resource recording, 2026-10-14

The supplied schema-2 recording contains 1,438 samples across a full 24 hours,
all running/healthy, zero restarts and one generation. Mean CPU is 4.300% of one
core versus 4.355% in the accepted baseline; complete two-process RSS median is
50.344 MiB versus 53.250 MiB. First/last-hour medians are 52.656/50.234 MiB.
No sustained memory growth or material CPU regression is evident.

The voluntary recording is complete; existing resource acceptance stays closed.
[Detailed analysis](RESOURCE_SOAK_ANALYSIS_2026-10-14.md) records partial process
I/O coverage, zero cgroup write accounting, missing cgroup memory and host-wide
network limits. No measured HDD saving or independent installed-version check
is claimed. Source/command/openHAB acceptance remains separate. Raw upload and
installation unchanged; no runtime modifications for this analysis.

## Optional plant calculations, 2026-10-14

The locally implemented feature adds explicit generic contributor roles,
profile-defined mappings, complete PV/storage sums, both legacy household power
balances and persistent grid/house counter accounting. It is disabled by default.
No polling registers, live device settings, openHAB Items/rules/links or histories
were changed. The published v0.3.11 does not contain this feature.

All 310 offline regressions passed on the host and independently inside ARM64
and AMD64 images, including 35 new plant/ledger tests. Container tests used
network isolation and synthetic fixtures. Coverage includes unit/profile/role
validation before connection, hybrid overlap rejection, fixed membership,
single-member suppression, valid zero, invalid/stale/skewed contributions,
oldest observation age, retained/current validity, both household power formulas,
UTC/local dates, Berlin 23/25-hour days, partial starts, midnight gaps, resets,
clock reversal, restart, configuration/hardware changes and durable checkpoint
publication. State corruption, symlinks, size limits and persistence failures are
checked; shutdown is tested with mocked sources and publisher.

Full lint, Compose parity including overrides and diff hygiene passed. Both local
images report 0.3.11-dev.1+plant; default configuration reports zero enabled sources.
Image exclusions for private configuration, Git metadata, pip and ensurepip were
verified. No base-image, dependency, publication or deployment change occurred.

The bundled battery energy boundary remains unverified. Household daily/lifetime
kWh is unavailable with unsupported-battery-boundary; verified synthetic AC
fixtures test the full software path without accepting real device semantics.
Whole-kWh PV counters limit precision. Live value comparison, midnight/restart
acceptance, finer counters and battery AC evidence remain pending. Existing
Influx power integrals and new counter deltas need a measured parallel comparison.

## Blocked plant power inputs, 2026-10-14

Read-only MQTT Explorer inspection and Andreas' startup log confirm the plant
is connected while its source status is stale; all seven physical adapters report
ready. PV daily/lifetime sums are available. Grid daily counters remain partial
on the initial day, and household energy reports unsupported-battery-boundary.
Those conditions are separate from missing household W.

A one-shot read-only probe used the locally configured enabled inverters with
identity validation and only the existing active/charge/discharge power mappings.
Both PV active-power results decoded as invalid while Storage power results were
valid. No Modbus write, MQTT connection/publication or source configuration change
was performed. No identities, addresses, credentials or raw measurements were
saved as acceptance evidence. Retained MQTT zero is not a fresh source sample;
source ready does not establish every optional property as currently valid.

The new always-available diagnostics/powerinputstatus JSON names blocked logical
source/property inputs and distinguishes missing/invalid data, expiry, source
errors, unit/type mismatches, negative directional values, sample skew and negative
household balances. Calculation eligibility and retained/current separation are
unchanged. A calendar-only nighttime zero substitution remains excluded; any
state-based fallback needs separate documented semantics and acceptance.

All 313 offline tests passed on the host and in isolated ARM64/AMD64 containers,
including three new power-diagnosis regressions. The invalid-PV case starts with
valid measured zeros, removes invalid observations, preserves other sums and
resumes only after valid power observations return. Full lint, Compose parity
including overrides and diff hygiene passed. Local images are
0.3.11-dev.2+plant. No publication/deployment or live acceptance of the added
MQTT diagnostic occurred; the live observation confirms the blocker only.

## Wallbox daily consumption and household exclusion, 2026-10-14

Locally implemented optional wallbox/dailyconsumption and
house/dailyconsumptionwithoutwallbox kWh properties use the existing local API
total-energy measurement. The household exclusion is one shared counter vector,
not subtraction of independently initialized day values. Wallbox-only daily
accounting works with the bundled unverified battery boundary; the household
exclusion retains that gate. No extra API calls, intervals, commands or source
activation were introduced. Measurement scope follows the existing Wallbox counter.

All 328 offline regressions passed on the host and independently in ARM64/AMD64
containers with network isolation. Fifteen new cases cover read-only discovery,
disabled local API, partial/covered days, session reset independence, common-vector
subtraction, negative balances, missing/stale/negative inputs, sample skew,
verified identity/endpoint changes, additive late enable with preserved grid/house
baselines, restart, committed publication, reset/gap recovery, kWh units and Berlin
23/25-hour days. Daily-only accounts avoid imposing an unrelated lifetime-balance
monotonicity requirement. Existing API fixtures additionally verify the fingerprint
binds validated serial and selected primary/fallback counter channel, including
missing/invalid counters, so source changes cannot silently jump daily consumption.

Full lint over 163 public files, Compose parity including overrides, comparison
manifest structure/counts and diff hygiene passed. The manifest has 84 rows with
38 existing pairs and ten implemented destinations awaiting live Items. Local
images use 0.3.11-dev.3+plant. The existing state schema accepts two additive account
names while preserving previous accounts; older-build rollback requires a matching
state backup. No private data, live measurement acceptance, deployment, publication
or openHAB/Influx/Shelly/history/control changes are included in this step.

## Wallbox day measurement on the charger identity, 2026-10-15

Andreas requested device ownership for daily Wallbox energy. The existing local
calculation now publishes measurements/dailyconsumption and the two Wallbox day
coverage/snapshot diagnostics through the configured eCharger Homie identity.
Household daily energy without Wallbox remains on the plant. Activation, units,
counter arithmetic, checkpoint cadence, AC gating and ledger schema/signatures
are unchanged. The same wallbox account/baseline is reused.

The runtime registers one derived output on the existing charger device and
keeps its partial-day availability independent of physical charger readiness.
No additional client/device identity, adapter I/O, polling, command or ENV setting
is introduced. Prior owned plant Wallbox topics/diagnostics retire through the
existing durable MQTT manifest; existing Item history requires relinking in place.
Official openHAB Homie discovery/channel documentation was consulted.

All 331 offline tests passed on the host and in isolated ARM64/AMD64 containers.
The 18 Wallbox tests retain prior arithmetic/freshness/reset/DST coverage and add
custom charger identity with partial-day readiness, actual runtime registration,
old-topic retained retirement and byte-preserved committed account reuse. Existing
house/grid/command behavior remains covered by the complete suite. Full lint over
163 public files, Compose parity with overrides, comparison-manifest ownership and
diff hygiene passed. Local images use 0.3.11-dev.4+plant. No deployment, live MQTT
retirement, openHAB Item/link/history change or new physical measurement acceptance
was performed in this correction.

## Provisional battery AC assumption, 2026-10-15

Andreas explicitly requested provisional household accounting before confirming
the battery counter measurement boundary. The boolean
SMAB_PLANT_ASSUME_AC_BATTERY_ENERGY defaults to false. When explicitly enabled,
unverified battery counters permit house daily/lifetime kWh and house daily kWh
without Wallbox; diagnostics report assumed-ac. Documented DC mappings remain
blocked. Profile evidence, existing grid/Wallbox baselines and all freshness,
counter/reset, consistency and midnight guards remain unchanged. New household
accounts start at activation; no previous partial-day consumption is invented.

All 333 offline tests and the complete linter passed. Added regression coverage
checks the provisional house/day-exclusion equations, grid-baseline continuity
and documented-DC rejection. Physical AC/DC confirmation and target-host deployment
remain pending; provisional historical energy is not automatically repaired.

## Plant calculation debug and PV raw-register evidence, 2026-10-15

An explicit plant debug flag plus DEBUG log level now enables periodic numeric
calculation evidence and selected numeric inverter register evidence from existing
verified reads. Default interval is 60 seconds; default activation is false.
Inputs include age/freshness and source-error flags; reports show signed recipes,
coverage, baselines, available derived values and separate committed checkpoints.
Identity/string registers, endpoints, serials, fingerprints and authenticated
payloads are excluded. No polling, publication or validity behavior is changed.

All 338 offline tests and full lint passed. Five new regression cases cover
missing versus zero, partial days, durable values, disabled/INFO/interval gates,
numeric register scope, invalid sentinel evidence and existing identity-gated
read calls without duplicate reads. Target-host debug deployment remains pending.

A one-shot read-only probe of the locally configured enabled inverters verified
identity before the selected measurement reads. Both PV sources returned
register 30775 words [32768, 0], int32 -2147483648 (0x80000000), which their profiles
declare invalid. Register 30201 returned valid status 307/OK; register 30217
returned invalid 16777213 for both PV sources. Storage reported valid charge 0 W
and discharge 240 W. This establishes actual invalid PV input at the probe time,
not measured zero, a transport failure or proof of permanent register absence.
No automatic nighttime-zero fallback follows from these observations. No MQTT
messages, device writes, openHAB changes or state-volume changes were performed
by the probe. Physical house-power acceptance and AC/DC confirmation remain open.

## Household lifetime topic removal, 2026-10-15

At Andreas' request, house/totalconsumption and its discovery are removed. The
inventory has no concrete existing legacy Item mapping for this added counter.
Daily household accounting, Wallbox exclusion, ledger format, configuration
fingerprint and existing internal legacy fields remain compatible. The existing
opening-value setting stays accepted for ledger compatibility, without publishing
a household lifetime property.

All 338 offline tests and full lint passed. Updated coverage verifies absence
from discovery/measurements, daily checkpoint publication with preserved snapshot
age and restart behavior, and manifest retirement of the old value/metadata while
preserving the ledger bytes. No target-host MQTT retirement or openHAB changes
have been performed; they must not be inferred from the offline fixture.

## Initial partial-day publication for tests, 2026-10-15

At Andreas' request, SMAB_PLANT_PUBLISH_PARTIAL_DAY (boolean, default false)
permits publication of initial partial-day deltas from the first valid saved
counter vector. It applies to grid import/export, house, Wallbox and house without
Wallbox day accounts. Status stays partial; the first valid vector gives zero
delta, with subsequent values measured since that vector. Existing partial
baselines and ledger fingerprints/schema remain unchanged. Restart and late
activation reuse them. A covered local midnight switches to normal complete-day
accounting; gaps/resets and invalid/negative/decreasing balances remain blocked.
Source PV day-yield sums retain their original device-day meaning.

All 345 offline tests and full lint passed. Seven new cases cover initial deltas,
restart, late activation/deactivation without rebasing, midnight transition,
gap/reset/identity/clock guards, negative/decreasing house balances, shared-vector
house/Wallbox exclusion with missing-input rejection, and durable-write/AC gates.
The private local ENV explicitly enables the test flag; target-host deployment,
real midnight acceptance and physical AC/DC confirmation remain pending.

## User-reported calculated power availability, 2026-10-15

Andreas reports numeric values for house/consumption and
house/consumptionwithcharging, and a correct zero for pv/totalactivepower.
This establishes user-reported availability for these properties at that time,
without an independent probe or complete physical balance comparison. Household/
Wallbox daily values remain reported unavailable. Current calculation diagnostics
are requested to distinguish the effective partial-day flag, input/account
statuses and committed values; no current failure cause is established yet.

Subsequent supplied calculation diagnostics show publishPartialDay=true, fresh
inputs, calculated partial-day household balances and pending checkpoint changes.
Committed household dailyValue fields were still null, with a 300-second
checkpoint interval, while Wallbox daily energy was already internally available.
Andreas then confirms that the values appeared. This is consistent with waiting
for durable checkpoint publication; no additional calculation fix was required.
This user-reported availability does not establish full-day accuracy, midnight
acceptance or the physical battery AC/DC boundary.

## Battery AC/DC history comparison, 2026-10-15

Read-only InfluxDB history now contains all five required power/current/voltage/
energy series. The [aligned analysis](BATTERY_ENERGY_BOUNDARY_2026-10-15.md)
strongly supports **AC-side charge and discharge counters for this installation**.
The discharge counter changes by 1.711 kWh versus 1.711919 kWh from original AC
samples and approximately 1.929356 kWh from reconstructed U×I. The charge counter
changes by 0.106 kWh versus 0.106640 kWh AC and approximately 0.092495 kWh DC.
Counter endpoints were used to align the windows; the original AC integral is an
independent cross-check of the resampled analysis. Sample gaps and DC reconstruction
limits are documented. This establishes boundary evidence, not round-trip
efficiency, calibration for all firmware, whole-day household accuracy or a new
runtime-profile declaration. Existing AC assumption/baselines remain unchanged.
No device/database/configuration writes or raw-series/credential capture occurred.

## Confirmed Storage AC profile and explicit baseline reset, 2026-10-15

The bundled Storage profile now declares ac with the aligned-history evidence.
Other unverified/DC mappings retain their existing guards. Andreas approves fresh
energy bases for this upgrade; the previous full-profile fingerprint deliberately
remains incompatible until an explicit reset. No automatic rebasing is introduced.

The offline --reset-energy-baselines action uses the normal exclusive state lock,
validates and uniquely archives only energy-balances.json, syncs its directory
and reports a non-secret backup basename. Missing state is a no-op; active locks,
invalid state and symlinks are rejected. Other state files are untouched. The
documented Compose sequence checks config, reset-command availability and the
effective AC profile before stopping the service and retiring the ledger.

All 350 tests pass on the host and in local ARM64/AMD64 containers with no network.
Five new tests cover the actual bundled profile upgrade, all five fresh day
accounts, archive-byte/unrelated-state preservation, exclusive locking, offline
CLI/no-op, invalid-state refusal and rename failure. Existing synthetic boundary
fixtures explicitly select unverified/ac instead of depending on the bundled
default. Full lint and diff hygiene pass. Public test/config/reference fixtures
are mounted read-only for container validation; private ENV/references are excluded.
Local images report build version 0.3.11-dev.5+ac; no image publication occurred.

Target-host reset/deployment is not performed or accepted: the SSH connection has
no previously verified host key and native Terminal access is unavailable through
the tool. No host-key protection was bypassed. Existing Pi ledgers and service
were not modified. Loading the new image, reconciling host overrides and executing
the explicit backup/reset procedure remain the concrete deployment steps.

## Item mapping documentation 2026-10-15

The [Item mapping](OPENHAB_ITEM_MAPPING.md) covers all recorded non-group Items
in the inverter/Home Manager PV scope: 46 pairs, two old calculations without
bridge counterparts and 33 observed new-only Items. All eight missing plant
Item names were resolved by live UI inspection on 2026-10-15, including labels,
units and Channel Links; the additional household daily Item without Wallbox
was also verified. [Sanitized evidence](plant-item-links-2026-10-15.csv) stores
no state or private broker identifiers. Other inventory entries retain their
2026-10-14 observation date; full live inventory/value acceptance is not implied.
Wallbox Items are excluded; Grafana is deferred. Prior full lint across 171 files
and all 350 offline tests passed for the mapping preparation. The name-only
follow-up changes documentation and CSV metadata, with no runtime or live
configuration changes; lint and scoped cross-file consistency are checked again.

## Grafana comparison dashboard created 2026-10-15

The separate **SMA · Alt und Neu im Vergleich** dashboard (UID
`sma-alt-neu-vergleich`) was imported and saved in the existing **TESTS** folder.
It contains all 46 mapped pairs: 39 numeric time-series panels and seven string
state timelines, grouped by plant/household, Home Manager and the three inverters.
Wallbox Items are excluded. The common top-level time picker was exercised for
the last hour and last 30 days; no panel has a separate time override.

Selected real old/new series loaded in each device group. Browser console
inspection returned no errors during the check. Full 92-series history coverage
and numerical equivalence were not accepted. An earlier schema check found no
field definition for the old inverter1Status series; missing history is not zero.
Numeric values use adaptive interval means with up to 10,000 points per panel;
short spikes may be smoothed over long ranges, so zooming remains necessary.
Old cumulative counter offsets and partial-day/reset boundaries remain visible
and are explained in the dashboard. Source histories, persistence and openHAB
configuration were not changed. Safari import stalled; the authenticated Codex
browser completed the import, and the saved result was opened in Safari.

## User-confirmed deployment and daily energy acceptance, 2026-10-15

Andreas explicitly marks target-host installation of the AC-profile build, host
profile reconciliation, backed-up energy-ledger reset and installed-version
verification complete. He also marks the full-day grid/house/Wallbox energy
comparison, including midnight, restart and data gaps, complete. This records
user acceptance; no new independent host probe was performed. Finer PV counters
remain a separate improvement.

## Plant yield remuneration and seven-day averages, 2026-10-15

Local implementation publishes plant-only lifetime PV yield remuneration using
per-inverter nonnegative currency/kWh tariffs and a configurable currency label
(default euro), plus house daily averages with and subtracting Wallbox energy.
The averages require all seven preceding complete local dates; charging days
remain included. Optional bounded history is stored in the existing energy ledger;
old baselines/signatures remain valid, but older binaries require a pre-upgrade
ledger backup for rollback once history fields are present.

All 359 offline tests pass, including nine new statistics cases: weighted tariffs,
battery exclusion, default zero/single PV, missing contributor, config rejection,
restart, missing/partial/reset days, seven-date coverage, Berlin spring/autumn DST,
corrupt history, signature mismatch, committed-only publication, failed state writes,
Wallbox subtraction and plant ownership. The full suite uses deterministic fixtures
and local fake servers only; localhost server checks require running outside the
socket sandbox. Full lint and standalone Compose parity including overrides pass.
No private tariffs were inserted, no image was built/published/deployed and no
openHAB Item/rule/history was modified. New channel live acceptance remains pending;
previous user-accepted deployment and day-energy checks remain closed.

## Explicit tariff activation, 2026-10-15

The plant remuneration channel is absent from discovery and values until at least
one enabled PV contribution has an explicit ENV/JSON tariff. Explicit zero remains
valid; omitted tariffs exclude their counters from both the sum and its freshness
guards. Disabled and battery-only sources cannot activate remuneration. Removing
all applicable tariffs retires retained value/metadata through the existing manifest
without modifying energy baselines or their configuration signature.

All 363 offline tests pass, including four additional regression cases covering
absence/disabled/battery tariffs, exclusion of an unavailable unconfigured counter,
JSON tariffs and explicit ENV-zero precedence, and retained retirement with
byte-preserved energy state. Existing zero-tariff/single-PV and weighted-sum tests
remain covered. Full lint, Compose parity including overrides and diff hygiene pass.
No build, deployment, publication, device I/O or private tariff changes occurred.

## Optional plant diagnostic visibility, 2026-10-15

SMAB_PLANT_DIAGNOSTICS_ENABLED=false now removes all optional plant diagnostics
from Homie discovery and published values, including coverage, energy timestamps,
input problems and seven-day status. The operational plantstatus remains, just as
other enabled measurement-source status does. Derived Wallbox day coverage/time
follows SMAB_ECHARGER_DIAGNOSTICS_ENABLED independently. Debug does not reenable
MQTT diagnostics. Profile classification is unchanged; Basic derating remains
visible and existing Advanced flags still control Advanced groups.

A publication inventory distinct from internal observations preserves calculation,
freshness, readiness and ledger behavior. All 368 offline tests pass, including
five new tests for plant metadata/value suppression with byte-identical ledger,
source-error status, debug independence, all four plant/Wallbox flag combinations,
Basic derating preservation and actual retained retirement on both logical outputs.
Existing source-status, Advanced filtering, widget and publication-cache regressions
remain covered. Full lint over 174 public files, Compose parity including overrides
and diff hygiene pass. Local fake-server tests run outside the socket sandbox.
No image build/deployment, device/broker access or openHAB change occurred; target
MQTT Explorer acceptance remains pending. Preserve the existing state volume so
the ownership manifest can retire the previous optional topics.

## Explicit topic groups and Basic quality status, 2026-10-15

This approved refinement supersedes the preceding coverage-visibility decision:
six plant day/average coverage properties and Wallbox day coverage are Basic.
They remain in metadata and values when optional Diagnostics is disabled.
Detailed timestamps/date, input lists and battery boundary remain Diagnostics.
Home Manager data-change counter and unlocked-device count follow Diagnostics
independently of Advanced. All topic IDs, labels and units are preserved.

All 372 offline tests pass. Four new tests enforce explicit maintained declarations,
all four reader group combinations, independent Home Manager protocol diagnostics
and reproducibility of the generated catalog. Updated plant tests cover Basic
metadata/values, all plant/Wallbox flag combinations, debug independence, source
error status and actual retirement of optional topics while preserving Basic
topics and byte-identical energy state. All four bundled profiles were compared
against the previous revision: only channel-group declarations changed.

The generated [catalog](topic-catalog.csv) contains 299 property rows, including
transport alternatives, conditional commands and multiple-contributor plant
outputs. It reads public bundled metadata and synthetic offline configuration,
never installation secrets or device responses. The CI container test command
mounts the exporter/catalog read-only; they remain outside image inputs.
Full repository lint, Compose parity including overrides and diff hygiene pass.
Four existing loopback-server protocol tests required execution outside the socket
sandbox; no real device/broker connections occurred. No image build, hosted CI,
publication, deployment or live openHAB changes were performed. Reconcile used
host profiles and verify target visibility separately; preserve state and links.

## eCharger active charging observation, 2026-10-15

Read-only MQTT Explorer and two local API/SEMP reads confirm current charging
status, both source statuses ready, single-phase L3 active power around 3.0–3.3 kW
and phase/total agreement within 0.01 W in the direct samples. Recent MQTT session
and total-energy increments differ by only 0.025 Wh over approximately three
minutes with about two seconds of endpoint offset. This is sampled consistency,
not calibrated/full-cycle acceptance. Current power/phase/total-energy source
timestamps advanced; unresolved health/event/mode/authorization timestamps stayed
weeks old and remain filtered. Frequency was absent from the API snapshots.

[Detailed evidence and limits](ECHARGER_LIVE_CHECK_2026-10-15.md) distinguish source
and receipt timestamps, earlier unexplained MQTT history gaps and remaining
session-reset/idle/target-completion questions. No commands, MQTT publication,
configuration/openHAB/history changes or recorder activation were performed.
Existing configured certificate trust and device identity checks were preserved.

## Wallbox frequency removal, 2026-10-15

At Andreas' request the unused Wallbox frequency mapping is removed. Discovery,
values and the regenerated public catalog no longer expose it; inverter frequency
channels remain unchanged. The 100-row migration ledger retains the historical
reference with explicit removed-by-user status, rather than silently dropping it.
All 374 offline tests pass, including two new cases for ignoring even a valid
source frequency and actual retained value/metadata retirement. Full lint and
diff hygiene pass; the generated catalog now contains 298 property rows.
No deployment, device request, MQTT publication or openHAB/history deletion was
performed for this change. On upgrade the existing manifest performs retirement;
keep the state volume and energy baselines.

## Grid-export comparison and remuneration correction, 2026-10-15

Andreas replaces total PV production remuneration with actual grid export and
explicitly confirms a common tariff. The [bounded source comparison](GRID_EXPORT_COMPARISON_2026-10-15.md)
found identical inverter1/inverter3 grid-export counters including a common one-unit
increment; the final raw/1000 values matched Home Manager kWh. The W readings were
small, time-skewed grid measurements, distinct from roughly 1.4/1.3 kW production.
This supports using one plant export counter, not summing inverter grid duplicates.
No inverter candidate was added to runtime profiles. Initial Home Manager single-
poller results and the final targeted identity-checked counter read are distinguished.

The unchanged plant earnings topic now uses only selected grid energy export
(default Home Manager), optional historical energy offset once, and one explicit
common tariff. Legacy inverter tariff settings are accepted but ignored. Missing
common tariff hides the channel; zero remains valid. Invalid/stale/errored export
blocks remuneration; PV availability does not. No automatic source failover occurs.

All 376 offline tests, full lint, generated catalog reproducibility, Compose parity
including overrides and diff hygiene pass. Revised regressions distinguish 60 kWh
grid export from 300 kWh PV production, ensure old rates cannot contribute/activate,
check JSON/ENV zero overrides, offset application, fresh zero versus invalid/stale
export, source errors, grid-only operation, retained retirement and byte-preserved
ledger continuity. Only documentation/configuration/source metadata and arithmetic
changed; day calculations and stored averages are unchanged. The live probes were
read-only; no MQTT publication, configuration/offset/rate migration, deployment,
openHAB change or old monetary-history rewrite was performed.

## Consistent Home Manager grid-power MQTT names, 2026-10-15

Home Manager Modbus and UDP now publish measurements/powerdrawn and
measurements/powergridfeedin, with the same labels, read-only Basic class and W
units as the inverters. The rename is scoped to publication of the two core
Home Manager properties. Original internal observations/readiness keys, profile
files, pollers, register/OBIS decoding and energy signatures remain unchanged.
No energy-baseline reset or host-profile rewrite is required for this rename.

All 380 offline tests pass. Four new cases cover both transports' metadata/values,
labels/units/readiness/error state, unchanged unrelated/delegated sources, actual
manifest retirement of old values/metadata, publication of the new values, correct
house power/export remuneration and byte-preserved ledger state across restart.
Full lint over 181 public files, generated catalog reproducibility, Compose parity
including overrides and diff hygiene pass. Both maintained migration CSV files
preserve row counts and all fields except the two target-topic/annotation pairs.
Recorded dated inventories remain unchanged; updated targets are not live relinks.
Existing openHAB Items need their links changed in place after deployment, preserving
Item names, units, rules and histories. The official Homie binding documentation
was consulted. No deployment, device/MQTT request or live openHAB change occurred.

## Home Manager energy offsets and canonical channel names, 2026-10-15

This supersedes the earlier intermediate plant-offset and unchanged-earnings-topic
wording above. Home Manager is the required remuneration source. Its signed,
finite import/export offsets default to zero and correct published cumulative
energy totals. Optional diagnostic properties retain the raw totals. Earnings
use corrected export once, multiplied by the explicitly configured common tariff,
and publish under grid/totalearnings. Nonzero legacy plant offsets are rejected
before device connection. Missing, stale, invalid-unit or negative corrected totals
do not manufacture a value. Raw observations, ledger signatures, daily deltas and
seven-day histories remain unchanged.

The [rename map](topic-renames-2026-10-15.csv) records 20 source-scoped mappings,
including batteryenergyreturnratio. Publication metadata, snapshots and plant
valid-properties diagnostics use the canonical names. Existing manifest cleanup
retires old properties. Profile mappings remain unchanged. The regenerated catalog
contains 302 rows; the migration inventory preserves its 100 rows and Item identities.
Existing openHAB Items require relinking after installation, and earlier openHAB
energy corrections must be removed to avoid applying the offsets twice.

All 389 offline tests, full lint, Compose parity, generated-catalog verification
and diff hygiene pass. Regression coverage includes both Home Manager transports,
signed offsets, freshness and units, negative corrected totals even with a zero
tariff, single application to remuneration, raw diagnostics, retained retirement,
canonical metadata and preserved energy-ledger state. No private offset values,
deployment, live MQTT publication or openHAB changes were performed.

## Immediate averages including today, 2026-10-15

The user supersedes the seven-completed-days requirement. Both plant house
averages now use available dates from today through six days ago, dividing by
the number available. Today contributes measured consumption without extrapolation,
including startup-day consumption since the baseline even when partial daily
channels are hidden. Historical gaps and invalid current values are omitted;
measured zero counts. Coverage is complete for seven dates, partial for one to
six, and insufficient-history for none. Existing channel IDs, units, energy
baselines, persisted history and checkpoint policy are preserved.

All 390 offline tests pass, including startup-day publication, live consumption,
both Wallbox variants, six-date history cutoff, missing-day denominator, midnight,
DST, restart, stale-current omission and committed-only publication. Complete lint
and Compose parity pass. This is offline evidence; no deployment, live MQTT or
openHAB change was performed.

## InfluxDB 2 history-copy preparation, 2026-10-15

The user supplied screenshots of 17 distinct orphaned Item links and confirmed
InfluxDB 2.x. A worksheet preserves all 17 Item names with no inferred targets;
15 are copy candidates, while unsupported frequency and semantically different
production-based earnings stay separate. Target names and persistence metadata
are pending. No connection, database write or Item removal occurred.

The offline Flux generator defaults to read-only counts and first/last previews.
Explicit copy mode changes measurement and an existing matching item tag, preserving
other tags, fields and timestamps. It guards empty sources, unexpected item tags
and populated target intervals. It has no deletion or automatic overwrite path.
Checks are not transactional; concurrent writes in the target interval must be
prevented. Partial failures require review, not blind retry. The workflow documents
backup, fixed UTC bounds, per-pair review and later validation before Item removal.

All 394 offline tests and full lint pass. Four new tests cover the mapping inventory,
read-only defaults, generated copy guards, identity/time validation and Flux literal
escaping. These tests validate generated text, not Flux execution against a live
InfluxDB server. Live schema review, execution and copied-history acceptance remain
open. Official openHAB and Flux documentation was consulted.

## Refreshed Item inventory and Grafana comparisons, 2026-10-15

Read-only live metadata captured through the existing Safari session supplies
159 scoped Items, with 18 targeted Item-detail checks covering channel links,
units and effective persistence. The original 2026-10-14 inventory remains
unchanged. Public CSVs exclude states, credentials and private broker identifiers.
Nine retained Items have confirmed canonical links; retained PV total daily yield
is currently unlinked. Two Home Manager power Items and three Carport voltage
Items have actual new names and correct links, but openHAB reports them as not
persisted. The old production-remuneration Item is unlinked. Both new average
Items are linked, use kWh/d metadata and have everyChange/restoreOnStartup policies.
These facts establish configuration, not successful stored measurements.

The existing Grafana dashboard was backed up and updated in TESTS with its UID
preserved. The generated model matches all 47 current Item pairs and 95 measurement
queries, adding the without-Wallbox average methods comparison and a standalone
inclusive average. Existing solid lines, no point markers and global time selection
are preserved. The updated intro and both new panels were visible after import.
The average panels showed no data in the selected last-hour window; complete
history coverage and numerical equivalence remain unaccepted. No live Item,
persistence-policy or InfluxDB changes occurred. No old Bridge history is silently
joined to a replacement Item, and no production earnings become feed-in earnings.

An automatic review rejected discarding unsaved Grafana editor state. It was not
discarded: the editor tab remains open and the import used a separate tab, preserving
the draft. The saved dashboard was separately backed up before updating. Direct
openHAB API certificate verification was not bypassed; the already open Safari
session supplied the metadata export instead. Official openHAB and Grafana
configuration/export documentation was consulted.

All 394 offline tests and full lint pass. The worksheet regression distinguishes
ten relinks, five replacement candidates and two archive-only entries. CSV and
model consistency checks pass; live Flux migration remains unexecuted.

## Inventory follow-up and corrected PV links, 2026-10-15

Live Item details confirm persistence on the five Home Manager/Carport replacement
Items and the new feed-in earnings Item (EUR, grid#totalearnings). Inventory now
contains 160 scoped Items, 20 targeted channel checks and 48 comparison pairs.
After Andreas corrected the links, independent reads confirm lifetime yield only
on totalyield and daily yield only on totaldailyyield, both with
everyChange/restoreOnStartup. Earlier mixed-history points were not changed.
The 56-panel, 97-query Grafana follow-up model is prepared but not saved: the
import folder selection remains unresponsive. Prior saved dashboard is preserved.
All 394 offline tests and the linter passed. No InfluxDB copy or deletion ran;
full history/value comparison remains separate.

### Grafana follow-up saved after restart, 2026-10-15

After Andreas restarted Grafana, the follow-up was imported directly from TESTS,
preserving the existing dashboard UID and folder. The saved dashboard visibly
shows 48 comparison pairs, confirmed persistence, corrected PV link notes and
the new feed-in earnings comparison panel. This resolves the earlier unsaved
import status. Query/value and history acceptance remain separate. No database
history was copied or repaired.

## Live history copy execution, 2026-10-15

The three populated replacement histories returned 205,552 copied points in total.
Carport L1/L2 have no source data. Backup availability was user-confirmed only.
See [the execution record](INFLUX2_ITEM_MIGRATION.md#live-execution-2026-10-15).
Independent post-copy acceptance remains pending after the verification queries
encountered a full query queue. No Item or original measurement was deleted.
All 394 tests and the linter passed after fixing Flux generation.

## PV nighttime power sentinel, 2026-10-15

All 396 offline tests and the full linter pass. Bundled STP8/SB4 active power now
normalizes the explicit raw SMA int32 sentinel to 0 W on successful reads via
validated profile opt-in. Tests cover normal/negative values, disabled opt-in,
invalid profile settings, nighttime PV/house readiness and invalidation on source
error or expired power. Existing identity and truncated-response tests still pass.
This reproduces the supplied openHAB transformation for the sentinel, not a
verified standby classifier. No live deployment or nighttime acceptance is claimed.
Host overrides need reconciliation; energy-state resets are outside this change.

## Invalid-value audit and ledger continuity, 2026-10-15

Static review found further legacy-zeroing differences on DC measurements and
inverter grid powers, but no additional confirmed live failure. These channels
remain unchanged pending evidence. Battery and energy-counter invalid values are
not safe zero substitutes. The complete audit is in
[INVALID_VALUE_AUDIT.md](INVALID_VALUE_AUDIT.md).

A regression correction excludes the power-only invalidAsZero option from ledger
identity; existing signatures and persisted accounts survive this option change.
All 397 tests and the full linter pass, including existing freshness, missing-input
and reset cases.
Live deployment and pre-existing configuration-changed diagnosis remain pending.

## Evening closure and private production ENV, 2026-10-15

Andreas accepts the release/CI step. Supplied logs show PV sentinel normalization
on both PV devices and a subsequent plant-ready startup. Following the explicitly
requested backed-up ledger reset, live MQTT at approximately 21:25 local time
shows plant ready, fresh house power, partial day/average coverage and numeric
averages matching the available startup-day deltas. This closes the observed
configuration-changed blockage after reset, not a signature-preserving repair.
The next midnight/following day and the earlier saved house-without-Wallbox
discrepancy remain separate acceptance items.

The private production ENV was reduced from 136 to 64 assignments using typed
loader/profile/Compose defaults; copied descriptions are from smab.example.env.
Andreas confirms no optional JSON or host profile overrides. Retained assignment
text/quoting is unchanged. Offline resolved Config, Compose values, explicit
interval selection and tariff-presence semantics match. Trust-file loading was
stubbed only for this offline comparison; no runtime TLS policy was changed or
validated. Production files were not replaced. Both private ENV files use mode
600 and are excluded from Git/Docker; no private constants enter this report.
The user must apply and validate the candidate on the target host separately.

[Wallbox idle samples](ECHARGER_LIVE_CHECK_2026-10-15.md#plugged-in-idle-follow-up-evening)
confirm fresh zero power/constant total energy and frozen stale session energy.
Reset boundaries and old state-channel semantics remain unaccepted.

### Session reset observed

Andreas unplugged the vehicle. MQTT and a direct API/SEMP sample confirm fresh
session energy zero with the unplug-time timestamp, vehicle not connected, zero
power and unchanged cumulative energy. This closes the observed unplug-reset
question only; replug/new charging and old state/event timestamps remain separate.
No Bridge command was sent.

### Replugged idle session observation

After Andreas confirmed reconnecting the vehicle, API/SEMP both reported fresh
locked vehicle status (5169), zero power and raw session zero. Total energy stayed
fresh and constant. The session timestamp remained at the unplug event and was
older than 180 seconds, so both readers correctly omitted fresh session output.
No charging permission was changed. Next charging-start behavior remains open.

## Additional legacy invalid-value channels, 2026-10-15

Read-only identity-verified Modbus sampling at 21:39 CEST covered all 15 remaining
legacy negative-to-zero channels: four grid powers returned valid 0/1 W values,
nine DC measurements returned S32 NaN, and Carport L1 power/voltage returned
S32/U32 NaN respectively. Earlier phase inventory identifies Carport L3 as active.
The [per-channel assessment](INVALID_VALUE_AUDIT.md) retains unavailable handling
for all 15. No runtime/profile change or MQTT write was made. This does not verify
the next daytime recovery or make retained optional measurements fresh.

## Conditional DC zero compatibility, 2026-10-15

Andreas subsequently approved zero compatibility for six DC current/power
channels. At 21:58 CEST, the updated local reader verified both PV identities and
read all 15 channels again: six selected DC sentinels became zero with fresh
AC-zero/OK guards; three DC voltages and both inactive Carport L1 channels remained
unavailable. No production deployment or MQTT publication was performed. The
official 40029 operating-status probe returned enum NaN on both devices; the
implemented guard is explicitly inferred no-production, not confirmed standby.
Deterministic tests cover positive production, fault/warning/invalid guards,
guard-read failure, signed values, policy validation, independent input-B polling
and preserved energy-ledger binding.

Validation after this change: `./tests/test-check.sh` passed all 401 tests;
`./tests/linter-check.sh` passed all checks. Loopback fixture tests required local
socket permission outside the restricted shell sandbox; no device network access
was used by the automated test suite.
