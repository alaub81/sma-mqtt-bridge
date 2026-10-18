"""Keep public grouping explicit, independently selectable and reproducibly cataloged."""

import ast
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import sma_mqtt_bridge
from sma_mqtt_bridge.adapters.echarger import EChargerReader, SempReader
from sma_mqtt_bridge.adapters.home_manager_modbus import HomeManagerModbusReader
from sma_mqtt_bridge.adapters.modbus import ModbusReader
from sma_mqtt_bridge.config import ECharger, HomeManager, Inverter
from sma_mqtt_bridge.errors import ConfigError
from sma_mqtt_bridge.home_manager_profile import load_home_manager_profile
from sma_mqtt_bridge.model import Property
from sma_mqtt_bridge.profiles import BUNDLED
from tools.export_topic_catalog import OUTPUT, render

PACKAGE = Path(sma_mqtt_bridge.__file__).resolve().parent


class TopicGroupTests(unittest.TestCase):
    def test_runtime_declarations_and_bundled_mappings_require_explicit_groups(self):
        for path in PACKAGE.rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text())):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "Property"
                ):
                    self.assertIn(
                        "channel_group",
                        {k.arg for k in node.keywords},
                        f"{path.name}:{node.lineno}",
                    )
        for path in BUNDLED.glob("*.json"):
            raw = json.loads(path.read_text())
            for prop in raw["properties"] + raw.get("delegated", {}).get("properties", []):
                self.assertIn(prop["channelGroup"], ("basic", "advanced", "diagnostics"))
        with self.assertRaises(ConfigError):
            Property("measurements", "power", "Power", channel_group="unknown")

    def test_every_reader_group_combination_keeps_basic_and_filters_optional_channels(self):
        with tempfile.TemporaryDirectory() as directory:
            hm_profile = load_home_manager_profile("sma-home-manager-2-modbus", directory)
        factories = [
            (
                ECharger(advanced_channels_enabled=True, diagnostics_enabled=True),
                lambda s: EChargerReader(s, 4096),
            ),
            (
                ECharger(advanced_channels_enabled=True, diagnostics_enabled=True),
                lambda s: SempReader(s, 4096),
            ),
            (
                HomeManager(advanced_channels_enabled=True, diagnostics_enabled=True),
                lambda s: HomeManagerModbusReader(s, hm_profile),
            ),
        ]
        for path in BUNDLED.glob("*.json"):
            raw = json.loads(path.read_text())
            if raw.get("validation", {}).get("status") == "validated":
                factories.append(
                    (
                        Inverter(advanced_channels_enabled=True, diagnostics_enabled=True),
                        lambda s, profile=raw: ModbusReader(s, profile),
                    )
                )
        for settings, factory in factories:
            full = factory(settings)
            for advanced, diagnostics in (
                (False, False),
                (False, True),
                (True, False),
                (True, True),
            ):
                reader = factory(
                    replace(
                        settings,
                        advanced_channels_enabled=advanced,
                        diagnostics_enabled=diagnostics,
                    )
                )
                expected = {
                    p.key
                    for p in full.properties
                    if p.channel_group == "basic"
                    or p.channel_group == "advanced"
                    and advanced
                    or p.channel_group == "diagnostics"
                    and diagnostics
                }
                with self.subTest(
                    reader=type(reader).__name__, advanced=advanced, diagnostics=diagnostics
                ):
                    self.assertEqual({p.key for p in reader.properties}, expected)
                    if isinstance(reader, HomeManagerModbusReader):
                        self.assertEqual(bool(reader.inventory_pollers), advanced)
                    if isinstance(reader, ModbusReader):
                        pollers = (
                            reader.core_pollers
                            if isinstance(reader, HomeManagerModbusReader)
                            else reader.pollers
                        )
                        definitions = (
                            reader.core_definitions
                            if isinstance(reader, HomeManagerModbusReader)
                            else reader.definitions
                        )
                        self.assertEqual(
                            {p["id"] for p in pollers},
                            {p["poller"] for p in definitions},
                        )

    def test_home_manager_protocol_diagnostics_are_independent_of_advanced(self):
        with tempfile.TemporaryDirectory() as directory:
            profile = load_home_manager_profile("sma-home-manager-2-modbus", directory)
        keys = {"parameters/data-change-counter", "parameters/grid-guard-unlocked-devices"}
        for advanced in (False, True):
            for diagnostics in (False, True):
                reader = HomeManagerModbusReader(
                    HomeManager(
                        advanced_channels_enabled=advanced, diagnostics_enabled=diagnostics
                    ),
                    profile,
                )
                props = {p.key: p for p in reader.properties}
                self.assertEqual(keys & props.keys(), keys if diagnostics else set())
                self.assertTrue(
                    all(
                        props[k].channel_group == "diagnostics" and not props[k].settable
                        for k in keys & props.keys()
                    )
                )

    def test_public_catalog_matches_conditional_runtime_metadata(self):
        expected = render()
        self.assertEqual(OUTPUT.read_text(), expected)
        self.assertIn("diagnostics/wallboxdaystatus,Wallbox day coverage,,basic", expected)
        self.assertIn("parameters/datachangecounter,Data Change Counter,,diagnostics", expected)
        self.assertIn("battery/totalchargepower,Total battery charging power,W,basic", expected)
        self.assertNotIn("diagnostics/portalrefresh", expected)


if __name__ == "__main__":
    unittest.main()
