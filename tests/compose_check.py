"""Render standalone Compose files with public settings and reject runtime drift."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ("compose.dev.yml", "compose.example.yml")


def render(filename, overrides):
    if re.search(r"^\s*extends:", (ROOT / filename).read_text(), re.MULTILINE):
        raise ValueError("Compose files must be standalone without extends")
    env = {key: value for key, value in os.environ.items() if not key.startswith("SMAB_")}
    env.update(SMAB_ENV_FILE=str(ROOT / "smab.example.env"), **overrides)
    result = subprocess.run(
        [
            "docker",
            "compose",
            "--env-file",
            str(ROOT / "smab.example.env"),
            "-f",
            filename,
            "config",
            "--format",
            "json",
        ],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )
    if result.returncode:
        raise ValueError("Compose rendering failed; configuration output withheld")
    config = json.loads(result.stdout)
    if set(config["services"]) != {"sma-mqtt-bridge"}:
        raise ValueError("Unexpected Compose service set")
    volumes = config.get("volumes", {})
    if (
        set(volumes) != {"data_smab_state"}
        or volumes["data_smab_state"]["name"] != config["name"] + "_data_smab_state"
    ):
        raise ValueError("State must use the project-scoped data_smab_state volume")
    return config["services"]["sma-mqtt-bridge"]


def check(overrides):
    dev, deployment = [render(filename, overrides) for filename in FILES]
    build = dev.pop("build")
    if (
        build["dockerfile"] != "Dockerfile-SMAB"
        or Path(build["context"]) != ROOT
        or build.get("pull") is not True
    ):
        raise ValueError("Development must use the root Dockerfile-SMAB and refresh base images")
    if "build" in deployment:
        raise ValueError("Deployment must use GHCR instead of a local build")
    if dev.pop("image") != "sma-mqtt-bridge:dev" or dev.pop("pull_policy") != "build":
        raise ValueError("Development must build its own local image")
    tag = overrides.get("SMAB_BRIDGE_VERSION", "latest")
    if deployment.pop("image") != f"ghcr.io/alaub81/sma-mqtt-bridge:{tag}":
        raise ValueError("Unexpected deployment image/tag")
    if "pull_policy" in deployment:
        raise ValueError("Deployment must use the normal Compose pull policy")
    if set(deployment.get("networks", {})) != {"app-nw"} or "network_mode" in deployment:
        raise ValueError("Default deployment must use only app-nw")
    host = render("compose.host.example.yml", overrides)
    if host.pop("network_mode") != "host" or "networks" in host:
        raise ValueError("Host variant must use only host networking")
    expected_host = dict(deployment)
    expected_host.pop("networks")
    expected_host["image"] = f"ghcr.io/alaub81/sma-mqtt-bridge:{tag}"
    if host != expected_host:
        raise ValueError("Host variant runtime options differ")
    if dev != deployment:
        raise ValueError("Compose runtime options differ")
    if dev["environment"].get("SMAB_MQTT_HOST") != "mqtt.example.invalid":
        raise ValueError("Compose check must use the public example, never private credentials")
    user = f"{overrides.get('SMAB_UID', '10001')}:{overrides.get('SMAB_GID', '10001')}"
    if dev["user"] != user:
        raise ValueError("Container user override was not applied")
    source = (ROOT / overrides.get("SMAB_DATA_DIR", "./data/sma-mqtt-bridge")).resolve()
    mounts = {mount["target"]: mount for mount in dev["volumes"]}
    if set(mounts) != {"/data/sma-mqtt-bridge/config", "/data/sma-mqtt-bridge/state"}:
        raise ValueError("Unexpected configuration/state mount paths")
    data_mount = mounts["/data/sma-mqtt-bridge/config"]
    if (
        data_mount["type"] != "bind"
        or Path(data_mount["source"]) != source
        or not data_mount.get("read_only", False)
    ):
        raise ValueError("Host data directory override was not applied")
    state_mount = mounts["/data/sma-mqtt-bridge/state"]
    if (
        state_mount["type"] != "volume"
        or state_mount["source"] != "data_smab_state"
        or state_mount.get("read_only", False)
    ):
        raise ValueError("State must use a writable named volume")


def main():
    for overrides in (
        {},
        {
            "SMAB_UID": "1234",
            "SMAB_GID": "2345",
            "SMAB_DATA_DIR": "./data/compose-fixture",
            "SMAB_BRIDGE_VERSION": "fixture",
        },
    ):
        check(overrides)
    print("Development and deployment match; host variant and overrides passed.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except OSError, ValueError, KeyError, subprocess.TimeoutExpired:
        print("Compose validation failed; no configuration values were logged.", file=sys.stderr)
        sys.exit(1)
