"""Strict, file-selectable BYD HVS layout and firmware compatibility contract."""

import re
from pathlib import Path

from .config import read_json
from .errors import ConfigError

BUNDLED = Path(__file__).resolve().parent.parent / "byd-profiles"


def load_byd_profile(selector, directory):
    if not isinstance(selector, str):
        raise ConfigError("Invalid BYD profile selector")
    explicit = selector.startswith("file:")
    name = selector[5:] if explicit else selector + ".json"
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*\.json", name):
        raise ConfigError("Invalid BYD profile selector")
    host = Path(directory) / name
    path = host if explicit or host.exists() or host.is_symlink() else BUNDLED / name
    p = read_json(path)
    keys = {
        "schemaVersion",
        "id",
        "kind",
        "layout",
        "validation",
        "model",
        "modules",
        "cellsPerModule",
        "temperaturesPerModule",
        "moduleCapacityKwh",
        "supportedBmuFirmware",
        "supportedBmsFirmware",
        "supportedParameterTables",
    }
    if not isinstance(p, dict) or set(p) != keys:
        raise ConfigError("Invalid BYD profile schema")
    valid = p["validation"]
    if (
        type(p["schemaVersion"]) is not int
        or p["schemaVersion"] != 1
        or type(p["layout"]) is not int
        or p["layout"] != 1
        or p["kind"] != "byd-hvs-read"
        or p["model"] != "HVS"
        or p["id"] != name[:-5]
        or not isinstance(valid, dict)
        or set(valid) != {"status", "evidence"}
        or valid["status"] != "validated"
        or not isinstance(valid["evidence"], str)
        or not valid["evidence"].strip()
        or type(p["modules"]) is not int
        or not 2 <= p["modules"] <= 4
        or type(p["cellsPerModule"]) is not int
        or p["cellsPerModule"] != 32
        or type(p["temperaturesPerModule"]) is not int
        or p["temperaturesPerModule"] != 12
        or type(p["moduleCapacityKwh"]) not in (int, float)
        or p["moduleCapacityKwh"] != 2.56
    ):
        raise ConfigError("Unvalidated or unsupported BYD read profile")
    for key in ("supportedBmuFirmware", "supportedBmsFirmware", "supportedParameterTables"):
        values = p[key]
        if (
            not isinstance(values, list)
            or not values
            or any(
                not isinstance(v, str) or not re.fullmatch(r"[0-9]{1,3}\.[0-9]{1,3}", v)
                for v in values
            )
            or len(set(values)) != len(values)
        ):
            raise ConfigError("BYD profiles require explicit firmware/table versions")
    return p
