"""File-driven Modbus profiles; descriptors never authorize device polling."""

from pathlib import Path
import re

from .config import ID, convert, read_json
from .errors import ConfigError, ProtocolError

BUNDLED = Path(__file__).resolve().parents[1] / "profiles"
TYPES = {"uint16": 1, "int16": 1, "uint32": 2, "int32": 2,
         "uint64": 4, "int64": 4, "float32": 2, "string": None}


def keys(obj, required, optional=()):
    if not isinstance(obj, dict) or set(required) - set(obj) or set(obj) - set(required) - set(optional):
        raise ConfigError("Invalid profile object/schema fields")


def integer(value, minimum, maximum):
    return type(value) is int and minimum <= value <= maximum


def load_profile(selector, host_dir, bundled_dir=None, require_validated=False):
    if not isinstance(selector, str):
        raise ConfigError("A profile selector must be a string")
    explicit = selector.startswith("file:")
    name = selector[5:] if explicit else selector + ".json"
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*\.json", name):
        raise ConfigError("Invalid profile selector/path")
    host_root = Path(host_dir).resolve()
    host = host_root / name
    if host.is_symlink() or not host.resolve().is_relative_to(host_root):
        raise ConfigError("Profile path escapes the host profile directory")
    # A dangling or unreadable override must fail, never fall back.
    path = host if explicit or host.exists() else Path(bundled_dir or BUNDLED) / name
    profile = validate_profile(read_json(path))
    if not explicit and profile["id"] != selector:
        raise ConfigError("Selected profile ID does not match the file")
    if require_validated and profile["validation"]["status"] != "validated":
        raise ConfigError("Selected profile is identity-only; verified mappings are required for polling")
    return profile


def validate_profile(raw):
    keys(raw, ("schemaVersion", "id", "device", "protocol", "validation", "pollers", "properties", "commands"), ("identity",))
    if type(raw["schemaVersion"]) is not int or raw["schemaVersion"] != 1 or not isinstance(raw["id"], str) or not ID.fullmatch(raw["id"]):
        raise ConfigError("Unsupported profile version/ID")
    device = raw["device"]
    keys(device, ("manufacturer", "models", "observedFirmware"), ("supportedFirmware",))
    if device["manufacturer"] != "SMA":
        raise ConfigError("Profile manufacturer must be SMA")
    for field in ("models", "observedFirmware", "supportedFirmware"):
        values = device.get(field, [])
        if not isinstance(values, list) or any(not isinstance(v, str) or not v for v in values) or len(values) != len(set(values)):
            raise ConfigError("Invalid profile identity list")
    if not device["models"]:
        raise ConfigError("Profile must name a model")
    protocol = raw["protocol"]
    keys(protocol, ("type", "defaults", "addressing"))
    if protocol["type"] != "modbus-tcp" or protocol["addressing"] != "zero-based":
        raise ConfigError("Unsupported profile protocol/addressing")
    keys(protocol["defaults"], ("port", "unitId"), ("pollIntervalSeconds", "timeoutSeconds", "staleSeconds"))
    defaults = protocol["defaults"]
    if not integer(defaults["port"], 1, 65535) or not integer(defaults["unitId"], 1, 247):
        raise ConfigError("Invalid profile port/unit ID")
    normalized = {"port": defaults["port"], "unit_id": defaults["unitId"]}
    for source, target in (("pollIntervalSeconds", "poll_interval_seconds"), ("timeoutSeconds", "timeout_seconds"), ("staleSeconds", "stale_seconds")):
        if source in defaults:
            value = convert(defaults[source], float, "profile duration")
            if value <= 0:
                raise ConfigError("Positive profile duration required")
            normalized[target] = value
    validation = raw["validation"]
    keys(validation, ("status", "reason"), ("evidence",))
    if validation["status"] not in ("identity-only", "validated") or not isinstance(validation["reason"], str) or not validation["reason"]:
        raise ConfigError("Invalid profile validation status/reason")
    if not all(isinstance(raw[k], list) for k in ("pollers", "properties", "commands")):
        raise ConfigError("Profile mappings must be arrays")
    if raw["commands"]:
        raise ConfigError("Read-only runtime does not accept profile commands")
    if validation["status"] == "identity-only":
        if raw["pollers"] or raw["properties"] or "identity" in raw:
            raise ConfigError("Identity-only descriptors cannot contain polling mappings")
    else:
        if not raw["pollers"] or not raw["properties"] or not device.get("supportedFirmware") or not isinstance(validation.get("evidence"), str) or not validation["evidence"]:
            raise ConfigError("Validated profiles need mappings, firmware compatibility and evidence")
    _, properties = validate_mappings(raw["pollers"], raw["properties"])
    if validation["status"] == "validated":
        keys(raw.get("identity"), ("model", "firmware", "serial"))
        for ref in raw["identity"].values():
            if not isinstance(ref, str) or ref not in properties:
                raise ConfigError("Identity needs explicit model, firmware and serial properties")
    return {**raw, "protocol": {**protocol, "defaults": normalized}}


def validate_mappings(poller_list, property_list):
    """Validate reusable read mappings independently of device identity schema."""
    if not isinstance(poller_list, list) or not isinstance(property_list, list):
        raise ConfigError("Profile mappings must be arrays")
    pollers, properties = {}, {}
    for poller in poller_list:
        keys(poller, ("id", "function", "start", "count"), ("intervalSeconds",))
        if not isinstance(poller["id"], str) or not ID.fullmatch(poller["id"]) or poller["id"] in pollers:
            raise ConfigError("Invalid/duplicate poller ID")
        if type(poller["function"]) is not int or poller["function"] not in (3, 4) or not integer(poller["start"], 0, 65535) or not integer(poller["count"], 1, 125) or poller["start"] + poller["count"] > 65536:
            raise ConfigError("Invalid Modbus read range/function")
        if "intervalSeconds" in poller and convert(poller["intervalSeconds"], float, "poller interval") <= 0:
            raise ConfigError("Invalid poller interval")
        pollers[poller["id"]] = poller
    for prop in property_list:
        keys(prop, ("id", "node", "name", "poller", "offset", "type", "length", "byteOrder", "wordOrder", "scale", "unit", "invalid", "datatype"), ("valueMap", "minimum", "maximum", "format", "channelGroup", "requiredForReady"))
        if "requiredForReady" in prop and type(prop["requiredForReady"]) is not bool:
            raise ConfigError("Profile requiredForReady must be boolean")
        if not all(isinstance(prop[k], str) and ID.fullmatch(prop[k]) for k in ("id", "node")) or prop["id"] in properties:
            raise ConfigError("Invalid/duplicate profile property ID")
        if not isinstance(prop["name"], str) or not prop["name"] or not isinstance(prop["unit"], str):
            raise ConfigError("Invalid property name/unit")
        if not isinstance(prop["poller"], str) or not isinstance(prop["type"], str) or prop["poller"] not in pollers or prop["type"] not in TYPES:
            raise ConfigError("Property references unknown poller/type")
        if not integer(prop["offset"], 0, 124) or not integer(prop["length"], 1, 125) or prop["offset"] + prop["length"] > pollers[prop["poller"]]["count"]:
            raise ConfigError("Property outside poller range")
        if TYPES[prop["type"]] is not None and prop["length"] != TYPES[prop["type"]]:
            raise ConfigError("Property length does not match its type")
        if prop["byteOrder"] not in ("big", "little") or prop["wordOrder"] not in ("big", "little") or prop["datatype"] not in ("integer", "float", "string", "boolean", "enum"):
            raise ConfigError("Invalid property encoding/Homie datatype")
        convert(prop["scale"], float, "property scale")
        if "format" in prop and (prop["format"] != "sma-firmware" or prop["type"] != "uint32"
                                  or prop["datatype"] != "string" or prop["scale"] != 1 or "valueMap" in prop):
            raise ConfigError("Invalid firmware format/encoding")
        if not isinstance(prop["invalid"], list) or any(type(v) not in (int, str) for v in prop["invalid"]):
            raise ConfigError("Explicit raw sentinels required")
        if prop.get("channelGroup", "basic") not in ("basic", "advanced", "diagnostics"):
            raise ConfigError("Invalid property channelGroup")
        if "valueMap" in prop and (not isinstance(prop["valueMap"], dict) or not prop["valueMap"] or any(not isinstance(k, str) or not isinstance(v, str) or not v for k, v in prop["valueMap"].items())):
            raise ConfigError("Invalid property valueMap")
        if prop["datatype"] in ("enum", "boolean") and "valueMap" not in prop:
            raise ConfigError("Enum/boolean property requires an explicit valueMap")
        if prop["datatype"] == "boolean" and any(v not in ("true", "false") for v in prop["valueMap"].values()):
            raise ConfigError("Boolean valueMap must use true/false")
        if prop["datatype"] == "enum" and any("," in v for v in prop["valueMap"].values()):
            raise ConfigError("Enum values must not contain commas")
        for bound in ("minimum", "maximum"):
            if bound in prop:
                convert(prop[bound], float, "property bound")
        if "minimum" in prop and "maximum" in prop and prop["minimum"] > prop["maximum"]:
            raise ConfigError("Property minimum exceeds maximum")
        if any(ord(c) < 32 for c in prop["name"] + prop["unit"]):
            raise ConfigError("Property metadata contains control characters")
        properties[prop["id"]] = prop
    return pollers, properties


def verify_identity(profile, values, expected_serial=""):
    identity = profile["identity"]
    if any(values.get(ref) is None for ref in identity.values()):
        raise ProtocolError("Local inverter identity is incomplete")
    if values[identity["model"]] not in profile["device"]["models"]:
        raise ProtocolError("Local inverter model does not match its profile")
    if str(values[identity["firmware"]]) not in profile["device"]["supportedFirmware"]:
        raise ProtocolError("Local inverter firmware is not validated by its profile")
    if expected_serial and str(values[identity["serial"]]) != expected_serial:
        raise ProtocolError("Local inverter serial does not match the configured identity")
