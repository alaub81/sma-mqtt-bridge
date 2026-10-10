"""Extract sanitized migration evidence from the supported Modbus Things subset.

This tooling never connects to devices or creates a validated polling profile.
Connection addresses and free-text labels are intentionally not exported.
"""

import argparse
import json
from pathlib import Path
import re


class InventoryError(ValueError):
    """A controlled diagnostic containing no source values or private addresses."""


def uncomment(text):
    result, quoted, escaped, comment = [], False, False, False
    i = 0
    while i < len(text):
        char = text[i]
        if comment:
            if char == "\n":
                comment = False
                result.append(char)
        elif escaped:
            result.append(char)
            escaped = False
        elif quoted and char == "\\":
            result.append(char)
            escaped = True
        elif char == '"':
            quoted = not quoted
            result.append(char)
        elif not quoted and text[i:i + 2] == "//":
            comment = True
            i += 1
        else:
            result.append(char)
        i += 1
    if quoted or escaped:
        raise InventoryError("Unterminated Things string")
    return "".join(result)


def fields(text):
    pattern = re.compile(r'\s*(\w+)\s*=\s*("(?:[^"\\]|\\.)*"|\d+)\s*(,|$)')
    values, position = {}, 0
    while position < len(text.rstrip()):
        match = pattern.match(text, position)
        if not match or match[1] in values:
            raise InventoryError("Unsupported or duplicate Things configuration field")
        values[match[1]] = json.loads(match[2])
        position = match.end()
    return values


def integer(value, minimum, maximum):
    return type(value) is int and minimum <= value <= maximum


def inventory(texts):
    devices = []
    declaration = re.compile(r'(Bridge modbus:tcp:|Bridge poller |Thing data )([\w-]+)\s+"(?:[^"\\]|\\.)*"\s*\[(.*?)\]\s*(\{?)')
    for text in texts:
        stack = []
        for line in uncomment(text).splitlines():
            line = line.strip()
            if not line:
                continue
            if line == "}":
                if not stack:
                    raise InventoryError("Unbalanced Things block")
                stack.pop()
                continue
            match = declaration.fullmatch(line)
            if not match:
                raise InventoryError("Unsupported Things syntax; review the export manually")
            kind, name, configuration, opening = match.groups()
            data = fields(configuration)
            if kind == "Bridge modbus:tcp:":
                if stack or opening != "{" or not re.fullmatch(r'inverter[1-9]\d*', name) or any(d["id"] == name for d in devices):
                    raise InventoryError("Invalid or duplicate inverter bridge")
                if set(data) - {"host", "port", "id", "connectMaxTries"} or not integer(data.get("port"), 1, 65535) or not integer(data.get("id"), 1, 247) or not integer(data.get("connectMaxTries"), 1, 100):
                    raise InventoryError("Unsupported inverter bridge configuration")
                device = {"id": name, "port": data["port"], "unitId": data["id"],
                          "connectMaxTries": data["connectMaxTries"], "pollers": []}
                devices.append(device)
                stack.append(device)
            elif kind == "Bridge poller ":
                if len(stack) != 1 or opening != "{" or any(p["id"] == name for p in stack[0]["pollers"]):
                    raise InventoryError("Invalid or duplicate poller block")
                if set(data) != {"start", "length", "refresh", "type"} or data["type"] != "input" or not integer(data["start"], 0, 65535) or not integer(data["length"], 1, 125) or data["start"] + data["length"] > 65536 or not integer(data["refresh"], 1, 86400000):
                    raise InventoryError("Unsupported Modbus poller configuration")
                poller = {"id": name, "function": 4, "start": data["start"], "count": data["length"],
                          "intervalSeconds": data["refresh"] / 1000, "channels": []}
                stack[0]["pollers"].append(poller)
                stack.append(poller)
            else:
                if len(stack) != 2 or opening or any(c["id"] == name for c in stack[1]["channels"]):
                    raise InventoryError("Invalid or duplicate data Thing")
                if set(data) - {"readStart", "readValueType", "readTransform"} or not isinstance(data.get("readStart"), str) or not data["readStart"].isdigit() or data.get("readValueType") not in ("int32", "uint32"):
                    raise InventoryError("Unsupported data Thing mapping; writes are not inventoried")
                start, poller = int(data["readStart"]), stack[1]
                if not poller["start"] <= start <= poller["start"] + poller["count"] - 2:
                    raise InventoryError("Data Thing exceeds its poller range")
                transform = data.get("readTransform", "")
                if transform and not re.fullmatch(r'JS\(smalimit(?:_undef|1000|100|10_undef)?\.js\)', transform):
                    raise InventoryError("Unknown transform requires manual migration review")
                poller["channels"].append({"id": name, "readStart": start, "offset": start - poller["start"],
                                           "type": data["readValueType"], "length": 2, "readTransform": transform})
        if stack:
            raise InventoryError("Unclosed Things block")
    if not devices or any(not d["pollers"] or any(not p["channels"] for p in d["pollers"]) for d in devices):
        raise InventoryError("Empty inverter inventory")
    return {"schemaVersion": 1, "status": "migration-evidence-only", "pollingAuthorized": False,
            "provenance": "Existing read-only openHAB Modbus Things; addresses and labels omitted",
            "unresolved": ["Local model, firmware and serial register definitions",
                           "Per-model register support, raw units and invalid sentinels",
                           "Byte/word order and status maps",
                           "Local endpoint identity and parallel-value acceptance"],
            "devices": sorted(devices, key=lambda d: int(d["id"][8:]))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = inventory([p.read_text(encoding="utf-8") for p in args.sources])
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    except (OSError, UnicodeError, ValueError):
        parser.exit(2, "Things inventory failed; no private source values were logged\n")


if __name__ == "__main__":
    main()
