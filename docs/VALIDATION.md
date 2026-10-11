# Current validation and acceptance

Updated: **2026-10-11**. This is the current status reference. Historical checkpoints
and detailed investigation evidence remain in the [archive](archive/README.md).
A user-reported result is identified separately from a direct observation or an
automated test. Full production acceptance and openHAB migration remain open.

## Local verification

The documentation/widget cleanup preserved the bridge runtime and device configuration.
The subsequent API fix changes confirmation and unit checks; it does not activate
adapters or command gates.
The current offline suite contains **182 tests**. Repository lint covers all public
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
Latest checks on 2026-10-11 passed full repository lint, all **182 offline tests**
and Compose parity. The two known MQTT future exceptions remain tracked separately.

The 2026-10-11 code review passed configured lint and all 174 offline tests. Its
MQTT disconnect tests also emitted unhandled future exceptions: the passing test
result does not close that defect. Ruff currently checks E4/E7/E9/F and Pylint
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

The API confirmation/unit, integer-payload and node-metadata findings are resolved by
offline regression evidence on 2026-10-11. Findings 4–5 and CLI capability reporting remain pending.
The documentation portion of the sixth finding is resolved by the cleanup.

| Finding | Required correction |
| --- | --- |
| API setting confirmation | Resolved offline: individually require Confirmed state, including manual-approval alias; preserve SEMP handling; validate plan-end units and command readback |
| Homie integers | Resolved offline: integral values serialize without decimals, signed 64-bit bounds enforced, no rounding of fractional values |
| Homie node metadata | Resolved offline: mandatory stable `$type` per node, untranslated and covered by topic ownership/retirement |
| Measurement freshness | Carry the device sample's remaining lifetime through source state |
| MQTT disconnect cleanup | Consume failed futures correctly; make unexpected loop exceptions fail tests |
| CLI status | Report optional write capabilities accurately; align module descriptions |

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

API session/health samples can have old change timestamps. Two frequency channels
were absent from the inspected live inventory even though generic WebUI metadata
defines them. Do not infer freshness or channel presence from static metadata.
Retained values remain last-known observations; separate source readiness must be
used when deciding whether values are current.

Portal consumer-balance PV/battery/grid shares were observed through read-only
investigation on 2026-10-11. They describe period energy shares; the current
charging mix remains unverified. Detailed endpoint/identity notes are preserved in
[the earlier context](archive/2026-10-11/CONTEXT.md#charging-mix-investigation-2026-10-11).

## Recording new evidence

Record date, tested image/version, source/transport, automated versus direct versus
user-reported result, and remaining limits. Keep authenticated responses, private
identities and secrets out of public fixtures. Update this matrix when acceptance
changes; preserve detailed German decisions in the active diary and its archive.
