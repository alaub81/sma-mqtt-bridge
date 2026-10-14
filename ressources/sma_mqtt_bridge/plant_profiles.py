"""File-based contribution references; no inverter model branches or inferred roles."""

from .errors import ConfigError

FIELDS = {
    "pv": {"activepower": "W", "dayyield": "kWh", "totalyield": "kWh"},
    "battery": {
        "presbatcharge": "W",
        "presbattdischarge": "W",
        "batterychargeenergy": "kWh",
        "batterydischargeenergy": "kWh",
    },
    "grid": {
        "powerimport": "W",
        "powerexport": "W",
        "energyimport": "kWh",
        "energyexport": "kWh",
    },
}


def validate_contributions(raw, properties):
    if not isinstance(raw, dict) or set(raw) - {*FIELDS, "hybridSeparated", "evidence"}:
        raise ConfigError("Invalid plant contribution schema")
    if not isinstance(raw.get("evidence"), str) or not raw["evidence"].strip():
        raise ConfigError("Plant contributions require mapping evidence")
    if "hybridSeparated" in raw and type(raw["hybridSeparated"]) is not bool:
        raise ConfigError("Hybrid separation must be boolean")
    if not set(raw) & FIELDS.keys():
        raise ConfigError("Plant profile requires contribution mappings")
    references = {p["node"] + "/" + p["id"]: p for p in properties.values()}
    for group, fields in FIELDS.items():
        if group not in raw:
            continue
        mapping = raw[group]
        extras = {"energyBoundary", "energyEvidence"} if group == "battery" else set()
        if (
            not isinstance(mapping, dict)
            or set(fields) - set(mapping)
            or set(mapping) - set(fields) - extras
        ):
            raise ConfigError("Incomplete or unknown plant contribution fields")
        refs = [mapping[k] for k in fields]
        if any(not isinstance(r, str) for r in refs) or len(set(refs)) != len(refs):
            raise ConfigError("Plant contribution references must be distinct property keys")
        for metric, unit in fields.items():
            prop = references.get(mapping[metric])
            if prop is None or prop["unit"] != unit or prop["datatype"] not in ("integer", "float"):
                raise ConfigError(
                    "Plant contribution requires a numeric property with matching unit"
                )
        if group == "battery":
            if "energyEvidence" in mapping and (
                not isinstance(mapping["energyEvidence"], str)
                or not mapping["energyEvidence"].strip()
            ):
                raise ConfigError("Battery energy evidence must be nonempty text")
            if mapping.get("energyBoundary") not in ("ac", "dc", "unverified"):
                raise ConfigError("Battery energy boundary must be ac, dc or unverified")
            if mapping["energyBoundary"] != "unverified" and (
                not isinstance(mapping.get("energyEvidence"), str)
                or not mapping["energyEvidence"].strip()
            ):
                raise ConfigError("A confirmed battery energy boundary requires evidence")
    if raw.get("hybridSeparated"):
        if not {"pv", "battery"} <= raw.keys():
            raise ConfigError("Hybrid contributions require both separated groups")
        if set(raw["pv"].values()) & {raw["battery"][k] for k in FIELDS["battery"]}:
            raise ConfigError("Hybrid PV and battery contributions overlap")
