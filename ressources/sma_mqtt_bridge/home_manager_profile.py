"""Strict file-defined Home Manager read profile, separate from inverter firmware gates."""

from pathlib import Path
import re

from .config import ID, read_json
from .errors import ConfigError
from .profiles import BUNDLED, integer, keys, validate_mappings


def mappings(pollers, properties, *, delegated=False):
    if not isinstance(pollers, list):
        raise ConfigError("Home Manager pollers must be an array")
    clean = []
    for poller in pollers:
        if not isinstance(poller, dict):
            raise ConfigError("Invalid Home Manager poller")
        unit = poller.get("unitId")
        if delegated:
            if unit is not None:
                raise ConfigError("Delegated pollers use the discovered assignment")
        elif not integer(unit, 1, 2):
            raise ConfigError("Home Manager core pollers require Unit 1 or 2")
        clean.append({k: v for k, v in poller.items() if k != "unitId"})
    _, props = validate_mappings(clean, properties)
    if not clean or not props:
        raise ConfigError("Home Manager mappings must not be empty")
    return props


def load_home_manager_profile(selector, host_dir, bundled_dir=None):
    if not isinstance(selector, str):
        raise ConfigError("Home Manager profile selector must be a string")
    explicit = selector.startswith("file:")
    name = selector[5:] if explicit else selector + ".json"
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*\.json", name):
        raise ConfigError("Invalid Home Manager profile selector")
    root = Path(host_dir).resolve()
    host = root / name
    if host.is_symlink() or not host.resolve().is_relative_to(root):
        raise ConfigError("Home Manager profile escapes the profile directory")
    path = host if explicit or host.exists() else Path(bundled_dir or BUNDLED) / name
    raw = read_json(path)
    keys(raw, ("schemaVersion", "id", "kind", "evidence", "identity", "pollers", "properties", "inventory", "delegated", "commands"))
    if (type(raw["schemaVersion"]) is not int or raw["schemaVersion"] != 1
            or not isinstance(raw["id"], str) or not ID.fullmatch(raw["id"])
            or raw["kind"] != "home-manager-modbus-read" or raw["commands"] != []
            or not isinstance(raw["evidence"], str) or not raw["evidence"]):
        raise ConfigError("Invalid Home Manager read profile")
    if not explicit and raw["id"] != selector:
        raise ConfigError("Home Manager profile ID mismatch")
    props = mappings(raw["pollers"], raw["properties"])
    keys(raw["identity"], ("model", "serial", "serialCopy", "deviceClass", "manufacturer"))
    if any(not isinstance(ref, str) for ref in raw["identity"].values()) or len(set(raw["identity"].values())) != 5:
        raise ConfigError("Home Manager identity references must be distinct")
    for ref in raw["identity"].values():
        if not isinstance(ref, str) or ref not in props:
            raise ConfigError("Home Manager identity property is missing")
        poller = next(p for p in raw["pollers"] if p["id"] == props[ref]["poller"])
        prop = props[ref]
        if (prop["type"] != "uint32" or prop["scale"] != 1 or prop["datatype"] != "integer"
                or "valueMap" in prop or "format" in prop):
            raise ConfigError("Home Manager identity must use unscaled U32 fields")
        if poller["unitId"] != 1:
            raise ConfigError("Home Manager identity must be read on Unit 1")
    inv = raw["inventory"]
    keys(inv, ("start", "slots", "intervalSeconds"))
    if (not integer(inv["start"], 0, 65535) or not integer(inv["slots"], 1, 245)
            or inv["start"] + inv["slots"] * 4 > 65536
            or type(inv["intervalSeconds"]) not in (int, float) or not 0 < inv["intervalSeconds"] < float('inf')):
        raise ConfigError("Invalid Home Manager inventory range/interval")
    keys(raw["delegated"], ("pollers", "properties"))
    mappings(raw["delegated"]["pollers"], raw["delegated"]["properties"], delegated=True)
    return raw
