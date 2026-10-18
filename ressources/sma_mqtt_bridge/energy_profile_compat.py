"""Preserve released energy identities for exactly recognized telemetry-only additions."""

import hashlib
import json

# Hashes cover the complete profiles after power-sentinel options are removed by
# energy_binding_profile. Any other profile edit retains strict mismatch handling.
TELEMETRY_LAYOUTS = {
    "sma-stp8-0-3av-40": "206453ecb2d00e45b90f245249be5e2b14c2944b8b4567d446ea26295cc40eef",
    "sma-sbs3-7-10": "d6f94fe2ee5439d1f59fb8eadb901a308f76cda863eb3a5b781e062fe8a9f284",
    "sma-sb4-0-1av-41": "92c8542b81601be4c1a946e6b2306c36eccf78ea2d3781b04597228affd8a26b",
}


# Exact parallel-counter layouts; accounting mappings remain unchanged.
FINE_ENERGY_LAYOUTS = {
    "sma-stp8-0-3av-40": "563ea8e40ecf30ed484614afc2e6fc00d0fd322da74fbfe4b179b5a2c9aad81e",
    "sma-sbs3-7-10": "79106d18873e9cf2a8f7ccbe79e3daa72ac1282559060240b3bedf1743ad3609",
    "sma-sb4-0-1av-41": "460c8a82897ed7d22b059dd5edbe6ec6819be57a7cf22dd2c58d03510ed57c12",
}


# Only the complete validated Storage condition/temperature extension is normalized.
BATTERY_DIAGNOSTIC_LAYOUT = "8c00a833953b17b12a27cbfac3d2bb87649122c675a178b8060c010ae92ad728"


def without_battery_observations(profile):
    """Keep existing baselines for these optional, non-accounting observations."""
    digest = hashlib.sha256(json.dumps(profile, sort_keys=True).encode()).hexdigest()
    if profile.get("id") != "sma-sbs3-7-10" or digest != BATTERY_DIAGNOSTIC_LAYOUT:
        return profile
    profile = json.loads(json.dumps(profile))
    added = {"battery-condition", "battery-temperature-max", "battery-temperature-min"}
    profile["properties"] = [p for p in profile["properties"] if p["id"] not in added]
    profile["pollers"] = [p for p in profile["pollers"] if p["id"] not in added]
    return profile


def without_parallel_energy(profile):
    """Normalize only the verified complete bundled extension, never custom edits."""
    digest = hashlib.sha256(json.dumps(profile, sort_keys=True).encode()).hexdigest()
    if digest != FINE_ENERGY_LAYOUTS.get(profile.get("id")):
        return profile
    profile = json.loads(json.dumps(profile))
    profile["properties"] = [
        prop
        for prop in profile["properties"]
        if prop["id"] not in ("daily-yield-precise", "total-yield-precise")
    ]
    block = next(b for b in profile["pollers"] if b["id"] == "yield")
    block["start"] += 4
    block["count"] -= 4
    for prop in profile["properties"]:
        if prop["poller"] == "yield":
            prop["offset"] -= 4
    return profile


def released_energy_layout(profile):
    """Use pre-2026-10-16 layout for these exact additions, without changing polling."""
    profile = without_parallel_energy(without_battery_observations(profile))
    expected = TELEMETRY_LAYOUTS.get(profile.get("id"))
    if expected is None:
        return profile
    digest = hashlib.sha256(json.dumps(profile, sort_keys=True).encode()).hexdigest()
    if digest != expected:
        return profile
    profile = json.loads(json.dumps(profile))
    model = profile["id"]
    removed = set()
    if model == "sma-stp8-0-3av-40":
        removed = {f"{prefix}{phase}" for prefix in ("power-l", "volt-g") for phase in (1, 2, 3)}
    elif model == "sma-sbs3-7-10":
        removed = {"power-l1", "volt-g1", "power-drawn", "power-grid-feed-in"}
        profile["pollers"] = [
            block
            for block in profile["pollers"]
            if block["id"] not in ("phase-voltage", "grid-power")
        ]
        next(block for block in profile["pollers"] if block["id"] == "ac-power")["count"] = 2
    else:
        removed = {"current-l1"}
        block = next(block for block in profile["pollers"] if block["id"] == "phase-currents")
        block.update(start=30979, count=4)
        for prop in profile["properties"]:
            if prop["id"] in ("current-l2", "current-l3"):
                prop["offset"] -= 2
    profile["properties"] = [prop for prop in profile["properties"] if prop["id"] not in removed]
    return profile
