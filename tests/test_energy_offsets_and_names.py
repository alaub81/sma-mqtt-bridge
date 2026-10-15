"""Meter corrections and publication renames preserve raw accounting and topic ownership."""

import asyncio
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock

from test_plant import PlantFixture
from test_runtime import FakeClient

from sma_mqtt_bridge.adapters.echarger import EChargerReader, SempReader
from sma_mqtt_bridge.config import load_config
from sma_mqtt_bridge.errors import ConfigError
from sma_mqtt_bridge.homie import (
    CHARGER_ALIASES,
    HOME_MANAGER_ALIASES,
    INVERTER_ALIASES,
    PLANT_ALIASES,
    HomiePublisher,
    publication_key,
    publication_property,
)
from sma_mqtt_bridge.model import Property, SourceState


class OffsetTests(PlantFixture):
    def test_published_totals_and_earnings_correct_once_raw_ledger_survives_changes(self):
        baseline = self.engine(ac=True)
        baseline.refresh(100, self.wall)
        saved = baseline.ledger.path.read_bytes()
        engine = self.engine(
            ac=True,
            env={
                "SMAB_HOME_MANAGER_ENERGY_IMPORT_OFFSET_KWH": "1000.25",
                "SMAB_HOME_MANAGER_ENERGY_EXPORT_OFFSET_KWH": "2000.5",
                "SMAB_PLANT_FEED_IN_TARIFF_PER_KWH": "0.1",
            },
        )
        engine.refresh(100, self.wall)
        self.assertFalse(engine.ledger.binding_changed)
        state = engine.sources["home-manager"]
        publisher = HomiePublisher(engine.config, [state, engine.state])
        values, _ = publisher.snapshot([state, engine.state], now=100)
        self.assertEqual(Decimal(values["measurements/energy-import"]), Decimal("1050.25"))
        self.assertEqual(Decimal(values["measurements/energy-export"]), Decimal("2060.5"))
        self.assertEqual(Decimal(values["grid/total-earnings"]), Decimal("206.05"))
        self.assertEqual(Decimal(values["diagnostics/raw-energy-import"]), 50)
        self.assertEqual(Decimal(values["diagnostics/raw-energy-export"]), 60)
        self.assertEqual(state.fresh_values(100)["measurements/energy-export"], "60")
        self.assertEqual(engine.ledger.path.read_bytes(), saved)
        restart = self.engine(ac=True, env={"SMAB_HOME_MANAGER_ENERGY_EXPORT_OFFSET_KWH": "3000"})
        self.assertFalse(restart.ledger.binding_changed)
        self.assertEqual(restart.ledger.path.read_bytes(), saved)

    def test_signed_offsets_missing_stale_and_negative_corrected_values(self):
        engine = self.engine(
            env={
                "SMAB_HOME_MANAGER_ENERGY_IMPORT_OFFSET_KWH": "-50",
                "SMAB_HOME_MANAGER_ENERGY_EXPORT_OFFSET_KWH": "-61",
                "SMAB_PLANT_FEED_IN_TARIFF_PER_KWH": "0",
            }
        )
        engine.refresh(100, self.wall)
        state = engine.sources["home-manager"]
        publisher = HomiePublisher(engine.config, [state, engine.state])
        values, _ = publisher.snapshot([state, engine.state], now=100)
        self.assertEqual(Decimal(values["measurements/energy-import"]), 0)
        self.assertNotIn("measurements/energy-export", values)
        self.assertNotIn("grid/total-earnings", values)
        state.update({"measurements/energy-export": None}, now=100)
        self.assertNotIn("measurements/energy-export", publisher.snapshot([state], now=100)[0])
        self.assertNotIn("diagnostics/raw-energy-export", publisher.snapshot([state], now=100)[0])
        self.assertNotIn("measurements/energy-import", publisher.snapshot([state], now=10000)[0])

    def test_offsets_independent_of_optional_diagnostics_and_transport(self):
        for transport in ("udp", "modbus-tcp"):
            for enabled in ("true", "false"):
                engine = self.engine(
                    env={
                        "SMAB_HOME_MANAGER_TRANSPORT": transport,
                        "SMAB_HOME_MANAGER_HOST": "manager.invalid"
                        if transport == "modbus-tcp"
                        else "",
                        "SMAB_HOME_MANAGER_ENERGY_EXPORT_OFFSET_KWH": "10",
                        "SMAB_HOME_MANAGER_DIAGNOSTICS_ENABLED": enabled,
                    }
                )
                state = engine.sources["home-manager"]
                publisher = HomiePublisher(engine.config, [state])
                values, _ = publisher.snapshot([state], now=100)
                props = {p.key for p in publisher.properties([state])}
                self.assertEqual(Decimal(values["measurements/energy-export"]), 70)
                self.assertEqual("diagnostics/raw-energy-export" in values, enabled == "true")
                self.assertEqual("diagnostics/raw-energy-export" in props, enabled == "true")
                self.assertIn("diagnostics/home-manager-status", props)

    def test_invalid_counter_units_do_not_publish_corrected_or_raw_energy(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = load_config(
                {"SMAB_STATE_DIR": tmp, "SMAB_HOME_MANAGER_ENERGY_EXPORT_OFFSET_KWH": "100"}
            )
            state = SourceState(
                "home-manager",
                "fixture",
                (Property("measurements", "energy-export", "Wrong unit", unit="W"),),
                30,
            )
            state.update({"measurements/energy-export": 10}, now=100)
            publisher = HomiePublisher(config, [state])
            values, _ = publisher.snapshot([state], now=100)
            self.assertNotIn("measurements/energy-export", values)
            self.assertNotIn("diagnostics/raw-energy-export", values)

    def test_json_precedence_defaults_validation_and_legacy_offset_rejected(self):
        config = load_config({})
        self.assertEqual(config.home_manager.energy_export_offset_kwh, 0)
        self.assertFalse(config.home_manager.enabled)
        path = Path(self.directory.name) / "offsets.json"
        path.write_text(
            json.dumps({"homeManager": {"energyExportOffsetKwh": 12, "energyImportOffsetKwh": -4}})
        )
        config = load_config(
            {"SMAB_CONFIG_FILE": str(path), "SMAB_HOME_MANAGER_ENERGY_EXPORT_OFFSET_KWH": "0"}
        )
        self.assertEqual(config.home_manager.energy_export_offset_kwh, 0)
        self.assertEqual(config.home_manager.energy_import_offset_kwh, -4)
        for key in (
            "SMAB_HOME_MANAGER_ENERGY_EXPORT_OFFSET_KWH",
            "SMAB_HOME_MANAGER_ENERGY_IMPORT_OFFSET_KWH",
        ):
            for value in ("NaN", "Infinity", "invalid"):
                with self.assertRaises(ConfigError):
                    load_config({key: value})
        with self.assertRaisesRegex(ConfigError, "SMAB_HOME_MANAGER_ENERGY_EXPORT_OFFSET_KWH"):
            load_config({"SMAB_PLANT_FEED_IN_ENERGY_OFFSET_KWH": "1"})
        with self.assertRaisesRegex(ConfigError, "Home Manager"):
            load_config(
                self.env
                | {
                    "SMAB_PLANT_FEED_IN_TARIFF_PER_KWH": "0.1",
                    "SMAB_PLANT_GRID_SOURCE": "inverter1",
                }
            )


class NameTests(unittest.TestCase):
    def test_all_declared_aliases_preserve_types_units_groups_and_read_only_rights(self):
        cases = (
            ("home-manager", HOME_MANAGER_ALIASES),
            ("inverter3", INVERTER_ALIASES),
            ("plant", PLANT_ALIASES),
            ("api", CHARGER_ALIASES),
            ("semp", CHARGER_ALIASES),
        )
        for source, aliases in cases:
            for old, (new, label) in aliases.items():
                node, identifier = old.split("/")
                original = Property(
                    node, identifier, "Original", unit="W", channel_group="advanced"
                )
                state = SourceState(source, "fixture", (original,), 30)
                actual = publication_property(state, original)
                self.assertEqual(actual.key, new)
                self.assertEqual(publication_key(state, old), new)
                self.assertEqual(actual.name, label)
                self.assertEqual(actual.unit, original.unit)
                self.assertEqual(actual.datatype, original.datatype)
                self.assertEqual(actual.channel_group, original.channel_group)
                self.assertFalse(actual.settable)
                self.assertEqual(state.properties, (original,))

    def test_plant_valid_property_list_uses_the_published_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = load_config({"SMAB_STATE_DIR": tmp})
            state = SourceState(
                "plant",
                "fixture",
                (Property("diagnostics", "valid-properties", "Available", "string"),),
                30,
            )
            state.update(
                {
                    "diagnostics/valid-properties": "house/consumption,pv/totalearnings,pv/totalyield"
                },
                now=100,
            )
            actual = HomiePublisher(config, [state]).snapshot([state], now=100)[0][
                "diagnostics/valid-properties"
            ]
            self.assertEqual(actual, "grid/totalearnings,house/consumptionpower,pv/totalyield")

    def test_charger_firmware_both_transports_and_no_delegated_rename(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = load_config({"SMAB_STATE_DIR": tmp})
            for source, reader in (
                ("api", EChargerReader(config.echarger, 4096)),
                ("semp", SempReader(config.echarger, 4096)),
            ):
                state = SourceState(source, "charger", reader.properties, 30)
                state.update({"parameters/nameplate-pkgrev": "2.6.37.R"}, now=100)
                publisher = HomiePublisher(config, [state])
                props = publisher.properties([state])
                self.assertIn("identity/firmware", {p.key for p in props})
                self.assertNotIn("parameters/nameplate-pkgrev", {p.key for p in props})
                self.assertEqual(
                    publisher.snapshot([state], now=100)[0]["identity/firmware"], "2.6.37.R"
                )
            state = SourceState(
                "home-manager", "meter", (Property("device-1", "day-yield", "Delegated"),), 30
            )
            self.assertEqual(
                publication_property(state, state.properties[0]).key, "device-1/day-yield"
            )


class RenameRetirementTests(unittest.IsolatedAsyncioTestCase):
    async def test_all_old_alias_topics_retire_without_losing_new_measurements(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = load_config({"SMAB_STATE_DIR": tmp})
            for source, aliases in (
                ("inverter3", INVERTER_ALIASES),
                ("plant", PLANT_ALIASES),
                ("api", CHARGER_ALIASES),
            ):
                properties = tuple(Property(*key.split("/"), "Original") for key in aliases)
                state = SourceState(
                    source, "fixture", properties, 30, contributes_availability=False
                )
                state.update({p.key: 1 for p in properties})
                client = FakeClient()
                publisher = HomiePublisher(
                    config, [state], lambda *a, active_client=client, **k: active_client
                )
                old = {
                    "homie/fixture/" + key.replace("-", "") + suffix
                    for key in aliases
                    for suffix in ("", "/$name", "/$datatype", "/$unit", "/$retained", "/$settable")
                }
                publisher.owned = {"fixture": old}
                publisher.publish_values = AsyncMock()
                await publisher.serve_device("fixture", [state], asyncio.Event())
                messages = {(topic, value) for topic, value, _ in client.messages}
                for topic in old:
                    self.assertIn((topic, b""), messages)
                    self.assertNotIn(topic, publisher.owned["fixture"])
                values, _ = publisher.snapshot([state])
                self.assertTrue(all(new in values for new, _ in aliases.values()))
                self.assertFalse(set(aliases) & values.keys())


if __name__ == "__main__":
    unittest.main()
