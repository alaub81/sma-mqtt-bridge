# InfluxDB 2 item-history migration

The 17 orphan links shown on 2026-10-15 are recorded in
[the mapping worksheet](influx2-item-migration-2026-10-15.csv). A later live inventory
and Andreas' relinking updates clarify that **ten existing Item names are retained**:
these need no history copy. All ten canonical links are confirmed, including
PV total daily yield after Andreas corrected it. Five actual new Item names are confirmed: two Home Manager power
Items and three Carport voltages. These are copy candidates. Their previously missing persistence is now enabled
and verified in the live Item details. Targets may already contain new data, so
select a historical interval that does not overlap it. Three histories were copied on 2026-10-15; see the execution record below.

Keep the removed Wallbox frequency history separately: there is no replacement
channel. Keep old PV-production remuneration separately too: its values are not
equivalent to new grid-feed-in remuneration. Do not copy it into the new earnings
history. Channel suffixes are linking evidence; Item names are verified separately.

## Preconditions and scope

The [generator](../tools/influx2_copy_item.py) creates Flux text locally and never
connects to InfluxDB. Preview is the default. Only running generated copy Flux on
InfluxDB writes data; there is no delete operation or openHAB Item modification.

This workflow assumes one measurement per Item and, if present, an `item` tag
matching that Item name, as documented by the
[official openHAB persistence documentation](https://www.openhab.org/addons/persistence/influxdb/).
Inspect actual Item persistence metadata and stored schema first. Custom shared
measurements, aliases or other Item tags need a separate mapping and query. Other
tags, fields, field types and timestamps are preserved; the existing `item` tag
is changed to the target name. An unexpected source `item` value aborts copying.
No unit conversion, offset or arithmetic is applied.

Before copying, back up the bucket, fill and review the actual new Item names,
and choose a fixed UTC cutover. Stop writes from old Items; new Items may write
only from the cutover onward. Use the same bounds for all preview/copy/verification
runs. `start` is inclusive and `stop` is exclusive. Select a start earlier than the
first stored point and ensure bucket retention covers the intended history.
The target interval must be empty: copy Flux refuses automatic overwrites/merges.
The check and write are not transactional, so prevent concurrent target writes in
that interval. Run one pair at a time; failures can leave a partial target copy.
Do not retry blindly or remove source data after a failure.

## Generate and inspect the queries

These placeholder names are examples, not the missing target mapping. The script
uses Python 3.10+ and no external dependencies. The Influx CLI uses your existing
local authentication; do not put tokens into generated queries or Git.

```bash
python3 tools/influx2_copy_item.py \
  --bucket YOUR_BUCKET --org YOUR_ORG \
  --old OLD_ITEM --new NEW_ITEM \
  --start 2000-01-01T00:00:00Z --stop 2026-10-15T18:00:00Z \
  > preview.flux
```

Review the file, then execute it using the InfluxDB 2 CLI:

```bash
influx query --file preview.flux
```

The preview returns counts and first/last points per series and field for both
names. Confirm source data, tags, units and an empty target interval. Generate the
copy query with the same arguments and explicit `--mode copy`:

```bash
python3 tools/influx2_copy_item.py \
  --bucket YOUR_BUCKET --org YOUR_ORG \
  --old OLD_ITEM --new NEW_ITEM \
  --start 2000-01-01T00:00:00Z --stop 2026-10-15T18:00:00Z \
  --mode copy > copy.flux
```

After review, execute the copy and repeat the original preview:

```bash
influx query --file copy.flux
influx query --file preview.flux
```

Compare per-series/field counts, first/last timestamps and values after normalizing
measurement and `item` names. Also compare representative points and openHAB charts.
These checks are evidence, not a complete point-for-point proof; the generator does
not automatically certify a migration. A repeated copy is intentionally refused
once the target interval contains data. Preserve source measurements and the backup
until the migration has been accepted. Deleting old openHAB Items is a separate,
later step after links, rules, charts and persistence have been reviewed.

The implementation follows the official Flux
[`to()`](https://docs.influxdata.com/flux/v0/stdlib/universe/to/) and
[`findRecord()`](https://docs.influxdata.com/flux/v0/stdlib/universe/findrecord/)
documentation. Local generator tests do not establish live Flux server acceptance.

## Live execution, 2026-10-15

Andreas confirmed that a current backup exists; its location and restore were not
independently verified. The server reports InfluxDB 2.9.1, unlimited bucket retention,
and the default Item measurement with matching `item` tag and double `value` field.
The exclusive cutover was `2026-10-15T16:00:00Z` (18:00 Europe/Berlin), with start
`1970-01-01T00:00:00Z`. All target intervals were empty before execution; existing
new-Item points start after the cutover. Each copy returned these field counts:

| Target Item | Copied points |
| --- | --: |
| `smahomemanager_Bezogene_Leistung` | 85,724 |
| `smahomemanager_Netzeinspeiseleistung` | 106,641 |
| `smainv3carport_Spannung_Phase_L3` | 13,187 |

Total: 205,552 points. Neither old nor new Carport L1/L2 measurements contained
points, so those pairs were skipped without synthetic data. Original measurements,
openHAB Items and data after cutover were not modified. Existing gaps remain gaps.

Two rejected attempts preceded the successful copies: an optional-tag record type
error and an empty scalar count caused by constant projection. The generator now
uses separate tagged/untagged streams and counts each series before summing counts.
The successful queries retained the target-empty and unexpected-tag guards.

The subsequent full-value checks were cancelled because they were too expensive;
a later read reported `queue length exceeded`. Copy responses are confirmed, but
independent post-copy counts and value acceptance remain pending. Do not rerun
copy queries or remove old Items while this verification is outstanding.
