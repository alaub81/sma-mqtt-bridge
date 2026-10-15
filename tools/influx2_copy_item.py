"""Generate reviewable Flux for copying one default openHAB InfluxDB 2 measurement."""

import argparse
import json
from datetime import datetime, timezone


def literal(value):
    """Encode a Flux string without allowing interpolation or query injection."""
    if not value or "${" in value or any(ord(char) < 32 for char in value):
        raise ValueError("Names must be nonempty without control characters or Flux interpolation")
    return json.dumps(value, ensure_ascii=False)


def timestamp(value):
    """Require explicit UTC bounds; Flux range stop is exclusive."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError("Time bounds must include UTC (Z or +00:00)")
    return parsed.astimezone(timezone.utc)


def generate(*, bucket, org, old, new, start, stop, mode="preview"):
    """Keep original series untouched and refuse copying into a populated interval."""
    if old == new:
        raise ValueError("Source and target must differ")
    if timestamp(start) >= timestamp(stop):
        raise ValueError("Start must precede stop")
    if mode not in {"preview", "copy"}:
        raise ValueError("Unknown mode")
    bucket, org, old, new, start, stop = map(literal, (bucket, org, old, new, start, stop))
    header = f"""// Generated offline. Review the mapping and back up the bucket before copying.
// Assumes measurement = Item name and optional item tag = Item name.
read = (name) => from(bucket: {bucket})
    |> range(start: time(v: {start}), stop: time(v: {stop}))
    |> filter(fn: (r) => r._measurement == name)
source = read(name: {old})
target = read(name: {new})
"""
    if mode == "preview":
        return (
            header
            + """// Counts per original series and field; use before AND after copying.
source |> count(column: "_value") |> yield(name: "source_counts")
target |> count(column: "_value") |> yield(name: "target_counts")
source |> first() |> yield(name: "source_first")
source |> last() |> yield(name: "source_last")
target |> first() |> yield(name: "target_first")
target |> last() |> yield(name: "target_last")
"""
        )
    return (
        header
        + f"""// Count each series before combining differently typed fields.
points = (tables=<-) => tables
    |> count(column: "_value")
    |> keep(columns: ["_value"])
    |> group()
    |> sum(column: "_value")
    |> findRecord(fn: (key) => true, idx: 0)
existing = target |> points()
available = source |> points()
unexpected = source
    |> filter(fn: (r) => if exists r.item then r.item != {old} else false)
    |> points()
if exists existing._value and existing._value > 0 then
    die(msg: "Target interval is not empty; no automatic overwrite or merge")
else if exists unexpected._value and unexpected._value > 0 then
    die(msg: "Unexpected item tag; inspect custom persistence mapping first")
else if not exists available._value or available._value == 0 then
    die(msg: "Source interval is empty")
else
    union(tables: [
        source |> filter(fn: (r) => exists r.item) |> set(key: "item", value: {new}),
        source |> filter(fn: (r) => not exists r.item),
    ])
        |> set(key: "_measurement", value: {new})
        |> to(bucket: {bucket}, org: {org})
        |> count(column: "_value")
        |> yield(name: "copied_field_counts")
"""
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("bucket", "org", "old", "new", "start", "stop"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--mode", choices=("preview", "copy"), default="preview")
    args = parser.parse_args()
    try:
        print(generate(**vars(args)), end="")
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
