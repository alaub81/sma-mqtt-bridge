"""Render standalone Compose files with public settings and reject runtime drift."""

import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
FILES = ("docker-compose.dev.yml", "docker-compose.example.yml")


def render(filename, overrides):
    if re.search(r"^\s*extends:", (ROOT / filename).read_text(), re.MULTILINE):
        raise ValueError("Compose files must be standalone without extends")
    env = {key: value for key, value in os.environ.items() if not key.startswith("SMAB_")}
    env.update(SMAB_ENV_FILE=str(ROOT / "smab.example.env"), **overrides)
    result = subprocess.run(
        ["docker", "compose", "--env-file", str(ROOT / "smab.example.env"),
         "-f", filename, "config", "--format", "json"],
        cwd=ROOT, env=env, text=True, capture_output=True, timeout=30,
    )
    if result.returncode:
        raise ValueError("Compose rendering failed; configuration output withheld")
    config = json.loads(result.stdout)
    if set(config["services"]) != {"sma-mqtt-bridge"}:
        raise ValueError("Unexpected Compose service set")
    return config["services"]["sma-mqtt-bridge"]


def check(overrides):
    dev, deployment = [render(filename, overrides) for filename in FILES]
    build = dev.pop("build")
    if build["dockerfile"] != "Dockerfile-SMAB" or Path(build["context"]) != ROOT:
        raise ValueError("Development build must use the root Dockerfile-SMAB")
    if "build" in deployment:
        raise ValueError("Deployment must use GHCR instead of a local build")
    if dev.pop("image") != "sma-mqtt-bridge:dev" or dev.pop("pull_policy") != "build":
        raise ValueError("Development must build its own local image")
    tag = overrides.get("SMAB_BRIDGE_VERSION", "latest")
    if deployment.pop("image") != f"ghcr.io/alaub81/sma-mqtt-bridge:{tag}":
        raise ValueError("Unexpected deployment image/tag")
    if deployment.pop("pull_policy") != "always":
        raise ValueError("Deployment must pull its GHCR image")
    if dev != deployment:
        raise ValueError("Compose runtime options differ")
    if dev["environment"].get("SMAB_MQTT_HOST") != "mqtt.example.invalid":
        raise ValueError("Compose check must use the public example, never private credentials")
    user = f"{overrides.get('SMAB_UID', '10001')}:{overrides.get('SMAB_GID', '10001')}"
    if dev["user"] != user:
        raise ValueError("Container user override was not applied")
    source = (ROOT / overrides.get("SMAB_DATA_DIR", "./data/sma-mqtt-bridge")).resolve()
    if Path(dev["volumes"][0]["source"]) != source:
        raise ValueError("Host data directory override was not applied")


def main():
    for overrides in ({}, {"SMAB_UID": "1234", "SMAB_GID": "2345",
                           "SMAB_DATA_DIR": "./data/compose-fixture", "SMAB_BRIDGE_VERSION": "fixture"}):
        check(overrides)
    print("Both standalone Compose files render with identical runtime options; overrides passed.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired):
        print("Compose validation failed; no configuration values were logged.", file=sys.stderr)
        sys.exit(1)
