# Architecture and project decisions

This document records the architecture and scope decisions. The
[current acceptance matrix](VALIDATION.md) owns status and evidence; the
[implementation plan](IMPLEMENTATION_PLAN.md) contains future milestones.
Earlier protocol investigations and decisions remain in the
[working-document archive](archive/README.md).

## Scope and ownership

One Python Docker service integrates three SMA inverters, Sunny Home Manager 2.0
and SMA eCharger with Homie 4 MQTT. Raspberry Pi 5 with a 64-bit system is the
primary target. Home Manager remains the charging controller. The bridge supplies
measurements and explicitly requested, allowlisted preferences and controls.

Prefer local measurements and local eCharger settings. Use the existing ennexOS
web-portal API only where needed, initially for minimum PV percentage. A paid SMA
Developer API and replacing the charging controller with evcc are outside scope.
Local wallbox and portal authentication are separate sessions.

The installed eCharger model/firmware evidence is EVC22-3AC-20 / 2.6.37.R.
Model-dependent units or writable choices require matching metadata or a narrowly
verified fallback. Do not extend one device's protocol assumptions to other SMA
models. Private installation identities and original exports stay in ignored,
read-only reference files.

## Configuration and deployment

The binding contract is [CONFIGURATION.md](CONFIGURATION.md). Every operational
setting has a typed default and an explicit `SMAB_` environment override. Precedence
is built-in/profile defaults < optional JSON configuration < explicit environment.
Validate configuration before network connections. Credentials and addresses have
empty defaults and are required only for enabled sources that need them.

Each inverter, Home Manager transport, local API, SEMP reader and portal adapter
has its own configuration and activation flag. Credentials or an address never
implicitly enable a source. Disabled adapters perform no device I/O.

Root `smab.env` is private; `smab.example.env` documents all supported variables.
Optional JSON, reusable profiles, certificates and password files live under
`data/sma-mqtt-bridge/`, mounted at `/data/sma-mqtt-bridge`. Persistent state uses
`data_smab_state` at `/data/sma-mqtt-bridge/state`. Preserve the topic manifest,
command uncertainty journals and process-lock protection during storage changes.
Resolved environment secrets must never be written into generated configuration.

Both standalone Compose files share runtime settings. Development builds
`Dockerfile-SMAB`; the example selects a published GHCR image.
`ressources/` contains image inputs only: the Python package, bundled profiles and
runtime dependencies, copied into `/app`. Documentation and tooling stay outside it.
Use a verified stable official Python image; recheck published tags before updates.

TLS verification defaults to enabled. Only explicit local-wallbox or MQTT
`TLS_VERIFY=false` overrides are supported. Portal verification is mandatory;
certificate download alone does not establish trust.

## Read adapters and units

Inverter models use [file-based profiles](PROFILES.md), with bundled defaults and
host overrides. New models must be addable without model-specific adapter code.
Identity-only descriptors remain blocked for polling. Register types, sentinels,
units, signed values and independent poller intervals require model-specific evidence.
The original 41-channel baseline is documented in
[register validation](REGISTER_VALIDATION.md).

Home Manager offers separate UDP meter and Modbus TCP read transports; selecting
one does not imply that every setting is available through it. Unit tables, access
restrictions and delegated reads are documented in
[HOME_MANAGER_MODBUS.md](HOME_MANAGER_MODBUS.md). Linux multicast/interface/VLAN
acceptance is distinct from Modbus acceptance.

The eCharger local API uses `/api/v1/token`, `/parameters/search`,
`/measurements/live` and the allowlisted parameter-write endpoint. SEMP is a
separate public XML reader. Preserve source units and timestamps; static metadata
alone does not prove a live channel exists. Unit evidence and its acceptance limits
are linked from [VALIDATION.md](VALIDATION.md#unit-and-protocol-evidence).

For locally observed periodically refreshed eCharger channels, carry device age
into a monotonic observation time so parsing/processing cannot restart a complete
freshness window. Session energy and other unresolved timestamp families keep
separate existing policies until evidence establishes their semantics. Source
readiness and retained last-known MQTT values remain distinct; see
[the channel evidence](ECHARGER_TIMESTAMP_ANALYSIS_2026-10-12.md) and
[the configured lifetime contract](CONFIGURATION.md#echarger-measurement-lifetime).

Portal minimum PV is a preference. Its complementary allowed grid share is
`100 - minPvPercentage`; neither is a measurement of current charging mix. Observed
consumer-balance PV/battery/grid percentages describe period energy shares. A live
charging-mix feature needs a verified endpoint, timestamp and consumer association.

## Commands and uncertainty

An enabled portal adapter additionally accepts the read-only Homie action
`portal/refresh/set` with payload `refresh`, independently of preference-write
gates. It wakes the existing supervisor rather than creating a second reader.
Requests coalesce; authentication blocking, read deadlines, retry backoff and
the shared portal-session lock remain authoritative. The feedback property does
not contribute availability. No retained replay or refresh on MQTT reconnect.

Only confirmed writable parameters belong on Homie `/set`; measurements remain
non-settable. Independent global, local and portal gates default to disabled.
Validate identity, permissions, metadata choices, units and bounds before a write.
Read back the device setting before publishing confirmation. HTTP success alone
cannot establish completion.

Local enum/boolean controls, combined energy/end-time plans and portal PV updates
have distinct contracts in [CONFIGURATION.md](CONFIGURATION.md). Confirm both plan
targets before activating target mode. Preserve unrelated portal options. Maximum
power and possible future phase controls have additional
[mapping and acceptance requirements](ECHARGER_POWER_LIMIT.md).

Reject retained-command replay and writes on startup or reconnection. An ambiguous
response records uncertainty and blocks duplicate retries; recovery must preserve
that journal. openHAB command Items use device readback rather than optimistic
state updates. Device setting confirmation does not prove completed physical charging.

## Availability and MQTT

Supervise sources and MQTT independently with bounded backoff and read watchdogs.
Docker health checks main-loop progress; source and broker availability have their
own diagnostics. A single device outage must not force a restart loop.

Retained measurements represent the last valid observation. Invalid, stale or missing
samples must not become fabricated zeros; readiness describes freshness separately.
Keep receipt timestamps distinct from device measurement timestamps. The remaining
freshness gap and offline MQTT cleanup evidence are tracked in the acceptance matrix.

Owned topic names are persisted for retirement after source/ID/prefix changes.
Command journals and topic ownership remain durable through file and directory
sync. Liveness heartbeats are atomically replaced without forcing disk sync;
their current process and monotonic age must still pass the health probe.
SourceState caches only immutable property descriptions/readiness defaults and
invalidates them when its inventory tuple is replaced. The MQTT publication loop
reuses descriptions until source IDs, property tuples, diagnostics/availability
flags or monitor presence change. Samples, expiry, status and command rights are
always evaluated from current observations.
Preserve the state volume to clean up old discovery. Moving brokers also requires
retirement on the old broker. One client and Last Will per Homie device maintain
independent availability. Commands are never replayed during recovery.

## openHAB continuity and repository maintenance

The [2026-10-14 plant aggregation design](PV_AGGREGATION_DESIGN.md) implements an optional
separate logical Homie plant device for PV/storage sums, current household power
and daily energy. The additional house/totalconsumption topic was removed at
Andreas' request; existing ledger fields/fingerprints remain compatible and owned
retained topics retire through the manifest. Explicit configured roles and file-based contribution
mappings must prevent grid duplicates and hybrid PV/storage double-counting.
The existing validated SMAB_TIMEZONE controls local calendar boundaries; freshness
remains monotonic. Atomic energy-balances.json checkpoints in the existing state
volume preserve counter baselines; only durable snapshots are published.
Missing inputs never become zero or partial sums. Initial partial-day counter publication can be explicitly
enabled for tests using SMAB_PLANT_PUBLISH_PARTIAL_DAY. It reuses the first valid
saved baseline, retains partial status, preserves all other guards and changes
to normal calendar accounting at a covered midnight. It never resets existing
accounts or relaxes gaps/resets. Single-member groups retain
only their device topics. The bundled Storage energy boundary is now ac. The installation's
[2026-10-15 aligned history comparison](BATTERY_ENERGY_BOUNDARY_2026-10-15.md)
strongly supports AC boundaries for both battery counters and is linked as profile
evidence. Other unverified mappings still require the explicit provisional AC
override; documented DC mappings remain blocked. Andreas accepts fresh daily
baselines for this upgrade. The offline --reset-energy-baselines command archives
only the validated ledger under the normal exclusive state lock, preserving the
topic manifest and command journals. Never silently rebase a mismatched ledger.
Optional plant debug logging requires both an explicit plant flag and DEBUG log
level. Rate-limited calculation reports contain numeric inputs/ages, signed recipes,
coverage/baselines and durable snapshot evidence. Selected numeric inverter
register words are logged only from existing identity-verified polling responses;
identity/string registers and authenticated payloads remain excluded. The mode
does not add reads or change invalid-value, freshness or counter semantics.
The optional local eCharger API contributes its existing total-energy counter to
Wallbox daily kWh and a shared-vector household day balance without Wallbox.
The Wallbox day measurement and its diagnostics belong to the existing eCharger
Homie identity; household exclusion remains on the plant. Derived Wallbox daily
coverage does not contribute to physical charger availability. These accounts
preserve previous baselines; Wallbox alone is independent of the battery boundary. Session counters and independently initialized daily subtraction
are excluded. Implementation is offline tested; live acceptance remains pending.
The current Item/rule/query inventory and old/new comparison manifest supplement
the historical migration ledger without changing current openHAB ownership.

Keep existing Items, maps, offsets, rules, units, UI dependencies and persistence
until each [migration-ledger](migration-coverage.csv) row is accepted.
[MIGRATION.md](MIGRATION.md) records the existing calculations, InfluxDB day boundaries,
Shelly dependencies and remaining inventory gaps. They initially stay in openHAB.

The maintained [MainUI guide](../openHAB/openHAB.md) and
[garage widget guide](../openHAB/echarger-comfort.md) use existing Items. Example Item
files and sitemaps were removed from scope at the user's request.
The garage widget has one canonical YAML source and a generated manual-import file;
its exporter and lint check prevent divergent copies. Consult
[official openHAB documentation](https://www.openhab.org/docs/) for integration work.

Keep active German tasks and decisions in [todo.md](../todo.md). Archive earlier
working documents without deleting entries or unresolved questions. Configuration,
profile, migration and technical evidence documents remain maintained contracts.
Configuration files and HTTP responses share the pure JSON decoder in `json_codec.py`
for duplicate-key and non-standard numeric-constant rejection. Callers retain
their own file/network handling, schema checks and redacted error boundaries;
sharing decoding does not merge local API and portal sessions or command policies.
Inverter and delegated Home Manager metadata use the same `profile_property`
constructor. Callers explicitly retain their format and readiness policies;
polling, decoding, identity checks and lifetime calculations stay in the readers.
GitHub/GHCR publication is operational. New commits/tags are published only as
explicitly requested release work; local preparation does not automatically
authorize a push or deployment.

## Complete register coverage decision, 2026-10-12

The [2026-10-16 parity review](INVERTER_TOPIC_PARITY_2026-10-16.md) closes
documented, availability-backed phase/grid telemetry gaps while retaining
device-specific unsupported/inactive quantities. Exact normalized bundled-profile
hashes permit only these telemetry additions to retain the released energy
fingerprint layout. Runtime polling uses the full new profiles. Unrecognized
profile changes still fail the existing accounting identity guard; no baseline
reset or automatic ledger rebase is introduced.

The goal includes all verified readable device values and readable configurable
parameters, beyond the original openHAB baseline. The
[Modbus completeness audit](MODBUS_TOPIC_AUDIT.md) inventories candidates without
preselecting basic/advanced/diagnostics; agree those groups with Andreas. Keep
documentary evidence, implemented mappings and observed live support distinct.
RW/WO inventory does not alter command allowlists or authorize device writes.

## Availability-first scope refinement, 2026-10-12

Andreas clarified that the full register inventory is evidence for selection, not
a target to publish every address. First run one read-only availability scan while
both PV inverters produce. Then choose useful Smart Home properties together.
Exclude missing values from the initial candidate set while preserving the tested
operating-state evidence; valid zero is available, and transport failure is not
proof of unsupported registers. Agree channel groups after this selection.

## New topic classification approved, 2026-10-12

Andreas approved the classification of the 25 newly added properties listed in
[todo.md](../todo.md): the six inverter1/inverter2 device-type and power-limit
properties remain advanced; the other 19 measurement properties remain basic.
The implementation already matches this selection. All 25 remain read-only;
classification approval is separate from live MQTT and openHAB acceptance.

## Sunny Boy DC completeness refinement, 2026-10-12

At Andreas’ request, expose both documented DC MPP inputs as basic measurements, even when an input is unused or temporarily has no valid sample. Input B had valid zeros in the production scan. Preserve zero versus invalid-sample semantics; the mapping does not imply that both inputs are wired. Existing input A identities and history remain unchanged.

## Plant remuneration and averages, 2026-10-15

Andreas selects total PV yield times independently configured inverter tariffs,
summed only on the plant, with configurable currency (default euro). This is
production remuneration, including self-consumption, rather than allocation of
shared grid export. Seven-day house averages use seven completed local calendar
days, once including and once subtracting Wallbox energy; charging days remain.
Bounded optional history fields extend the existing durable energy ledger without
rebasing or changing its configuration signature. No external history is inferred.

## Explicit tariff activation, 2026-10-15

The plant remuneration channel now requires an explicitly configured tariff on
at least one enabled PV contributor. Loader metadata tracks ENV/JSON presence
independently of the numeric zero default. Explicit zero activates contribution;
omission excludes it. Battery/disabled/unassigned sources never activate the
channel. Only configured PV counters gate remuneration freshness. Removing all
applicable tariffs uses normal manifest retirement; energy baselines are unchanged.

## Consistent optional diagnostic publication, 2026-10-15

Plant internal observations and its MQTT publication inventory are separate.
The plant diagnostics flag hides all optional coverage, input, timestamp and
average diagnostics from metadata and values while preserving internal calculations,
readiness, checkpoints and debug evidence. Derived Wallbox day diagnostics follow
the eCharger diagnostics flag independently. Operational measurement-source status
remains the explicit exception; source status and Homie device state stay usable
by the existing widget. Device profile channel groups remain authoritative:
Basic derating stays Basic even beneath the diagnostics topic path. Existing
Advanced/profile/SEMP filtering remains unchanged. Hidden owned topics retire
through the persistent MQTT manifest on reconnect without resetting energy state.

## Explicit topic groups and Basic data quality, 2026-10-15

Andreas approved the refinement in [TOPIC_GROUPS.md](TOPIC_GROUPS.md): six plant
day/average coverage statuses and Wallbox day status are Basic. This supersedes
the preceding decision to hide those seven statuses with optional Diagnostics.
Detailed inputs, accounting times/date and battery boundary remain Diagnostics.
Coverage and operational availability answer separate questions; neither retained
measurements nor retained coverage certify current connectivity.

Home Manager data-change counter and Grid Guard unlocked-device count now follow
Diagnostics independently of Advanced. Advanced still controls delegated discovery
and metadata; identity verification remains mandatory. Every bundled mapping and
runtime property explicitly declares its group. Legacy host-profile fallback is
preserved; host overrides must adopt changed declarations explicitly.
The [generated catalog](topic-catalog.csv) derives public property metadata from
offline constructors and bundled profiles, including conditional outputs and
transport alternatives. These classes do not change topic IDs, write allowlists,
readiness, calculation/energy state or activation. No new configuration flags.

## Wallbox frequency removal, 2026-10-15

Andreas removes the Wallbox frequency channel after repeated absent source readings.
Drop its local API mapping rather than retaining empty discovery. Normal topic
manifest retirement removes previously published metadata/value; inverter frequency
mappings remain unchanged. This is an explicit scope choice, not a claim of
permanent firmware-wide protocol absence.

## Actual grid-export remuneration replaces PV-yield valuation, 2026-10-15

Andreas corrects the requirement: only electricity exported to the grid is valued,
using one common tariff. The Home Manager is the preferred explicitly selected
grid source. Bounded identity-checked reads found the same grid-export counter
at both PV inverters and Home Manager; these are duplicate plant views, not
separately summable export allocations. Inverter grid power is W, not billable kWh.
The unchanged plant earnings topic now uses only the selected grid-energy counter,
with optional historical export offset applied once before multiplying the common
rate. No automatic source failover or production-based substitute is permitted.
Legacy inverter tariffs remain accepted but ignored. Ledger signatures/baselines,
raw counters and averages are unchanged; past production-based monetary history
is not automatically rewritten. See the configuration contract for new ENV fields.

## Shared grid-power publication terminology, 2026-10-15

Andreas requests Home Manager powerdrawn/powergridfeedin naming to match the
inverters. Apply aliases only at the Homie publication boundary for the two core
Home Manager properties, for both Modbus and UDP. Keep protocol/profile/internal
keys, readiness, formulas and energy signatures unchanged. This avoids a cosmetic
rename invalidating durable baselines or requiring edits of host overrides.
Use the same aliases for metadata, values and ownership retirement. Other sources
and delegated properties are untouched; grid energy and PV production stay distinct.
Existing openHAB Items need new links, with names/units/history preserved.

## Meter offsets and canonical channel names, 2026-10-15

Andreas selects Home Manager energyexport as the remuneration basis and requests
independent ENV corrections for cumulative import/export energy, plus the proposed
naming cleanup including batteryenergyreturnratio. Correct published Home Manager
totals only; retain raw observations, fingerprints, daily vectors and seven-day
history. Use the corrected export once for money; expose optional raw counters
under Diagnostics. Signed finite corrections are allowed; negative corrected totals
are suppressed. The old plant-specific correction must stay zero to avoid double
correction. Remuneration requires the Home Manager grid source, with no failover.

Apply concrete naming candidates as source-scoped publication aliases, including
the corresponding plant aggregate names, explicit house-power/rated-limit names
and the earnings move to grid/totalearnings. Keep profiles and protocol keys stable.
Existing manifest retirement removes old owned discovery/value topics. Preserve
Item identities/history when relinking; no live relink or state reset is implied.
The full map is topic-renames-2026-10-15.csv. Unverified battery-capacity semantics
and lower-priority diagnostic reorganization remain outside this implementation.

## Immediate seven-day house averages, 2026-10-15

Andreas supersedes the earlier seven-completed-days requirement: average available
consumption for today and the six preceding local calendar dates. Include today's
measured value without extrapolation, counting it as one day. Divide by available
days, not always seven. The startup partial day participates independently of
daily-channel visibility. Omit invalid/missing days; measured zero remains valid.
Keep both including/excluding-Wallbox channels under the plant. Preserve durable
counter baselines, history schema and checkpoint cadence. No external backfill.

## New Item history migration, 2026-10-15

Andreas chooses new openHAB Items after channel renaming and requires transferring
InfluxDB histories before removing old Items. InfluxDB version 2.x is confirmed;
actual target names remain unknown. Prepare explicit old/new mappings and
non-deleting copies preserving timestamps, fields and tags. Keep removed frequency
and old PV-production remuneration separate from current feed-in remuneration.
No automatic Item deletion or monetary-history reinterpretation is authorized.

## Partial Item reuse and Grafana refresh, 2026-10-15

The live inventory refines the blanket new-Item migration plan: ten listed Items
retain their identities, five have actual replacement names, and two histories
remain separate. Unchanged Item identities require no database copy. Current
Grafana comparisons follow confirmed Item/link evidence, while missing persistence
and absent links remain explicit. Average algorithms differ and must be labelled
as a methods comparison. Reuse the existing dashboard UID/folder and preserve its
solid-line style and global time selection. No history rewrite is inferred.

## Follow-up persistence and earnings inventory, 2026-10-15

Andreas enabled persistence on the five actual replacement Items; live Item details
confirm the policies. A new feed-in earnings Item is also linked and persisted,
separate from the old PV-production remuneration Item. Inventory now contains
160 scoped Items and 48 pairs. A discovered daily/lifetime PV link conflict is
explicitly pending correction; the user will perform it after the Safari link
editor failed to respond. No successful save is inferred from opening a dialog.

### PV link correction verified, 2026-10-15

Andreas corrected the links manually. Live Item details confirm that
`smaplant_PVGesamtertrag` has only `pv#totalyield` and
`smaplant_PVGesamttagesertrag` has only `pv#totaldailyyield`. Both retain
everyChange/restoreOnStartup persistence. The link conflict is resolved; review
any earlier mixed lifetime-history interval separately, without automatic repair.
The 48-pair Grafana follow-up was saved in the existing TESTS folder after
Grafana restarted. Opening import from that folder bypassed the unresponsive
folder picker. Updated introduction and earnings panel were verified in the UI.

## PV nighttime sentinel compatibility, 2026-10-15

Existing openHAB active-power channels use `smalimit.js`, which converts negative
raw values to zero. The user confirmed nighttime standby. The bundled PV profiles
now explicitly normalize the raw SMA int32 invalid-power sentinel to 0 W on a
successful read. This preserves nighttime house calculations without synthesizing
values during communication failures. It does not classify status 307 (OK) as
standby and does not clamp other negative readings. See [profiles](PROFILES.md).

## Power-only profile compatibility and ledger identity

The validated `invalidAsZero` power option is excluded from energy-ledger binding
identity. Adding it to otherwise identical profiles must preserve existing daily
bases and average history. All other signature inputs remain unchanged. See the
[invalid-value audit](INVALID_VALUE_AUDIT.md) for remaining compatibility differences.
