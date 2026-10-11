"""Synthetic protocol fixtures; no installation-derived identities or secrets."""

import json
from pathlib import Path


def validated_profile():
    properties = []
    for id, offset, mapping in (
        ("model", 0, {"1": "TEST-INVERTER"}),
        ("firmware", 1, {"2": "test-1"}),
        ("serial", 2, None),
    ):
        p = {
            "id": id,
            "node": "identity",
            "name": id.title(),
            "poller": "identity",
            "offset": offset,
            "type": "uint16",
            "length": 1,
            "byteOrder": "big",
            "wordOrder": "big",
            "scale": 1,
            "unit": "",
            "invalid": [65535],
            "datatype": "string" if mapping else "integer",
        }
        if mapping:
            p["valueMap"] = mapping
        properties.append(p)
    properties.append(
        {
            "id": "power",
            "node": "measurements",
            "name": "Power",
            "poller": "power",
            "offset": 0,
            "type": "int32",
            "length": 2,
            "byteOrder": "big",
            "wordOrder": "big",
            "scale": 0.1,
            "unit": "W",
            "invalid": [-2147483648],
            "datatype": "float",
        }
    )
    return {
        "schemaVersion": 1,
        "id": "test-inverter",
        "device": {
            "manufacturer": "SMA",
            "models": ["TEST-INVERTER"],
            "observedFirmware": [],
            "supportedFirmware": ["test-1"],
        },
        "protocol": {
            "type": "modbus-tcp",
            "addressing": "zero-based",
            "defaults": {"port": 1502, "unitId": 4},
        },
        "validation": {
            "status": "validated",
            "reason": "Synthetic test fixture",
            "evidence": "Offline protocol test only",
        },
        "identity": {"model": "model", "firmware": "firmware", "serial": "serial"},
        "pollers": [
            {"id": "identity", "start": 0, "count": 3, "function": 4, "intervalSeconds": 60},
            {"id": "power", "start": 10, "count": 2, "function": 4, "intervalSeconds": 3},
        ],
        "properties": properties,
        "commands": [],
    }


def write_json(directory, name, value):
    path = Path(directory) / name
    path.write_text(json.dumps(value))
    return str(path)
