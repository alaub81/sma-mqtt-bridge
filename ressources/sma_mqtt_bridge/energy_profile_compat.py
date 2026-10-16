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


def released_energy_layout(profile):
    """Use pre-2026-10-16 layout for these exact additions, without changing polling."""
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
