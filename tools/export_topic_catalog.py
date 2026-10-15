#!/usr/bin/env python3
"""Generate the public channel catalog from offline runtime metadata and bundled profiles."""

# Standalone tool bootstraps the image package before importing runtime metadata.
# ruff: noqa: E402

import argparse
import csv
import io
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ressources"))

from sma_mqtt_bridge.adapters.echarger import EChargerReader, SempReader
from sma_mqtt_bridge.adapters.home_manager_modbus import HomeManagerModbusReader
from sma_mqtt_bridge.adapters.meter import MeterReader
from sma_mqtt_bridge.adapters.modbus import ModbusReader
from sma_mqtt_bridge.adapters.portal import PortalReader
from sma_mqtt_bridge.config import ECharger, HomeManager, Inverter, load_config
from sma_mqtt_bridge.homie import HomiePublisher, wire_key
from sma_mqtt_bridge.model import SourceState
from sma_mqtt_bridge.plant import PlantEngine
from sma_mqtt_bridge.profiles import BUNDLED
from sma_mqtt_bridge.runtime import (
    LOCAL_COMMAND_PROPERTIES,
    PORTAL_COMMAND_PROPERTIES,
    PORTAL_REFRESH_PROPERTIES,
    sources,
)

OUTPUT = ROOT / "docs/topic-catalog.csv"


def inventories(directory):
    """Enumerate alternatives without loading private config, connecting or creating sessions."""
    config = load_config({"SMAB_STATE_DIR": directory, "SMAB_PROFILE_DIR": directory})
    publisher = HomiePublisher(config, [])

    def describe(source, properties, *, availability=True, diagnostics=True):
        state = SourceState(
            source,
            "catalog",
            properties,
            180,
            contributes_availability=availability,
            diagnostics_enabled=diagnostics,
        )
        state.monitor = object() if availability else None
        return publisher.properties([state])

    for path in sorted(BUNDLED.glob("*.json")):
        profile = json.loads(path.read_text())
        if profile.get("kind") == "home-manager-modbus-read":
            reader = HomeManagerModbusReader(HomeManager(), profile)
            reader.assignments = {0: (1, 1234, 3)}
            reader.rebuild_delegated()
            yield path.stem, "home-manager", describe("home-manager", reader.properties)
        elif profile.get("validation", {}).get("status") == "validated":
            reader = ModbusReader(Inverter(), profile)
            yield path.stem, "inverter<N>", describe("inverter<N>", reader.properties)
    yield (
        "home-manager-udp",
        "home-manager",
        describe("home-manager", MeterReader(HomeManager()).properties),
    )
    for source, reader in (
        ("api", EChargerReader(ECharger(), 4096)),
        ("semp", SempReader(ECharger(), 4096)),
    ):
        yield "echarger-" + source, source, describe(source, reader.properties)
    yield "portal", "portal", describe("portal", PortalReader.properties)
    for source, properties in (
        ("commands", LOCAL_COMMAND_PROPERTIES),
        ("portal-commands", PORTAL_COMMAND_PROPERTIES),
        ("portal-refresh", PORTAL_REFRESH_PROPERTIES),
    ):
        yield (
            "echarger-" + source,
            source,
            describe(
                source, properties, availability=False, diagnostics=source != "portal-refresh"
            ),
        )

    env = {
        "SMAB_STATE_DIR": directory,
        "SMAB_PROFILE_DIR": directory,
        "SMAB_MQTT_HOST": "broker.invalid",
        "SMAB_PLANT_ENABLED": "true",
        "SMAB_HOME_MANAGER_ENABLED": "true",
        "SMAB_HOME_MANAGER_SERIAL": "424242",
        "SMAB_ECHARGER_ENABLED": "true",
        "SMAB_ECHARGER_HOST": "charger.invalid",
        "SMAB_ECHARGER_EXPECTED_SERIAL": "424243",
        "SMAB_ECHARGER_USERNAME": "catalog",
        "SMAB_ECHARGER_PASSWORD": "synthetic-catalog-only",
        "SMAB_PLANT_FEED_IN_TARIFF_PER_KWH": "0",
        "SMAB_INVERTER4_ENABLED": "true",
        "SMAB_INVERTER4_HOST": "inverter4.invalid",
        "SMAB_INVERTER4_PROFILE": "sma-sbs3-7-10",
        "SMAB_INVERTER4_ROLE": "battery",
    }
    for slot, role in ((1, "pv"), (2, "battery"), (3, "pv")):
        env.update(
            {
                f"SMAB_INVERTER{slot}_ENABLED": "true",
                f"SMAB_INVERTER{slot}_HOST": f"inverter{slot}.invalid",
                f"SMAB_INVERTER{slot}_ROLE": role,
            }
        )
    config = load_config(env)
    plant = PlantEngine(config, [state for state, _, _ in sources(config)])
    for state in plant.output_states:
        yield "derived-" + state.id, state.id, publisher.properties([state])


def render():
    """Use wire IDs; repeated topics denote documented transport/ownership alternatives."""
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(("device_or_profile", "source", "topic_suffix", "meaning", "unit", "group"))
    with tempfile.TemporaryDirectory(prefix="smab-topic-catalog-") as directory:
        for device, source, properties in inventories(directory):
            for prop in sorted(properties, key=lambda p: wire_key(p.key)):
                suffix = wire_key(prop.key).replace("device1/", "device<N>/", 1)
                writer.writerow((device, source, suffix, prop.name, prop.unit, prop.channel_group))
    return output.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="Fail if the generated catalog is stale"
    )
    args = parser.parse_args()
    expected = render()
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text() != expected:
            print(
                "Topic catalog is stale; run .venv/bin/python tools/export_topic_catalog.py",
                file=sys.stderr,
            )
            return 1
        print("Topic catalog matches runtime metadata and bundled profiles.")
    else:
        OUTPUT.write_text(expected)
        print(f"Generated {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
