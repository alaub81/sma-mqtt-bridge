"""Offline acceptance of contribution roles, complete sums and durable energy balances."""

import asyncio
import copy
import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock, patch

from sma_mqtt_bridge.config import load_config
from sma_mqtt_bridge.errors import ConfigError, StateError
from sma_mqtt_bridge.homie import HomiePublisher, discovery
from sma_mqtt_bridge.model import SampleValues
from sma_mqtt_bridge.plant import PlantEngine, plant_plan
from sma_mqtt_bridge.profiles import BUNDLED, validate_profile
from sma_mqtt_bridge.runtime import run_locked, sources


class PlantFixture(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.env = {
            "SMAB_STATE_DIR": self.directory.name,
            "SMAB_PROFILE_DIR": self.directory.name,
            "SMAB_MQTT_HOST": "broker.invalid",
            "SMAB_MQTT_TLS": "false",
            "SMAB_PLANT_ENABLED": "true",
            "SMAB_PLANT_CHECKPOINT_INTERVAL_SECONDS": "1",
            "SMAB_HOME_MANAGER_ENABLED": "true",
            "SMAB_HOME_MANAGER_SERIAL": "424242",
        }
        for slot, role in ((1, "pv"), (2, "battery"), (3, "pv")):
            self.env.update(
                {
                    f"SMAB_INVERTER{slot}_ENABLED": "true",
                    f"SMAB_INVERTER{slot}_HOST": f"source{slot}.invalid",
                    f"SMAB_INVERTER{slot}_ROLE": role,
                }
            )
        self.wall = datetime(2026, 10, 14, 10, tzinfo=timezone.utc)

    def engine(self, *, ac=False, env=None):
        config = load_config(self.env | (env or {}))
        if ac:
            profiles = copy.deepcopy(config.profiles)
            for device in config.inverters:
                if device.enabled and device.role == "battery":
                    mapping = profiles[device.id]["plant"]["battery"]
                    mapping.update(energyBoundary="ac", energyEvidence="Synthetic AC fixture only")
            config = replace(config, profiles=profiles)
        states = [state for state, _, _ in sources(config)]
        for state in states:
            state.identity_fingerprint = hashlib.sha256(
                (state.id + "-fixture").encode()
            ).hexdigest()
        engine = PlantEngine(config, states)
        self.fill(engine, 100)
        return engine

    def fill(self, engine, now, overrides=None):
        values = {
            "inverter1": {"activepower": 2000, "dayyield": 5, "totalyield": 100},
            "inverter3": {"activepower": 3000, "dayyield": 7, "totalyield": 200},
            "inverter2": {
                "presbatcharge": 700,
                "presbattdischarge": 500,
                "batterychargeenergy": 40,
                "batterydischargeenergy": 30,
            },
            "inverter4": {
                "presbatcharge": 200,
                "presbattdischarge": 0,
                "batterychargeenergy": 50,
                "batterydischargeenergy": 20,
            },
            "home-manager": {
                "powerimport": 600,
                "powerexport": 800,
                "energyimport": 50,
                "energyexport": 60,
            },
        }
        for source, update in (overrides or {}).items():
            values[source].update(update)
        groups = [*engine.groups["pv"], *engine.groups["battery"], engine.grid]
        updates = {}
        for group in groups:
            for metric, ref in group.items():
                updates.setdefault(ref.source, {})[ref.key] = values[ref.source][metric]
        for source, update in updates.items():
            engine.sources[source].update(update, now=now)


class PlantConfigurationTests(PlantFixture):
    def test_disabled_plant_reads_no_energy_state_and_roles_do_not_enable_devices(self):
        config = load_config({"SMAB_STATE_DIR": "/not-present", "SMAB_INVERTER1_ROLE": "pv"})
        self.assertFalse(config.plant.enabled)
        self.assertFalse(config.has_sources)
        self.assertEqual(config.inverters[0].role, "pv")
        self.assertEqual(sources(config), [])

    def test_settings_types_bounds_roles_and_grid_activation(self):
        for update in (
            {"SMAB_PLANT_ENABLED": "1"},
            {"SMAB_PLANT_GRID_SOURCE": "missing"},
            {"SMAB_HOME_MANAGER_ENABLED": "false"},
            {"SMAB_INVERTER1_ROLE": "guess"},
            {"SMAB_PLANT_HOMIE_ID": "sma-inverter1"},
            {"SMAB_PLANT_BOUNDARY_TOLERANCE_SECONDS": "901"},
            {"SMAB_PLANT_MAX_SKEW_SECONDS": "3601"},
            {"SMAB_PLANT_CHECKPOINT_INTERVAL_SECONDS": "0"},
            {"SMAB_PLANT_INITIAL_CONSUMPTION_KWH": "-1"},
            {"SMAB_PLANT_INITIAL_CONSUMPTION_KWH": "NaN"},
        ):
            with self.subTest(update=update), self.assertRaises(ConfigError):
                load_config(self.env | update)

    def test_optional_json_then_explicit_env_precedence(self):
        path = Path(self.directory.name) / "config.json"
        path.write_text(
            json.dumps(
                {
                    "plant": {"enabled": True, "maxSkewSeconds": 20},
                    "inverters": [{"id": "inverter1", "role": "none"}],
                }
            )
        )
        config = load_config(self.env | {"SMAB_CONFIG_FILE": str(path)})
        self.assertEqual(config.plant.max_skew_seconds, 20)
        self.assertEqual(config.inverters[0].role, "pv")
        config = load_config(
            self.env | {"SMAB_CONFIG_FILE": str(path), "SMAB_PLANT_MAX_SKEW_SECONDS": "10"}
        )
        self.assertEqual(config.plant.max_skew_seconds, 10)

    def test_role_mapping_units_missing_and_hybrid_overlap_rejected(self):
        original = json.loads((BUNDLED / "sma-stp8-0-3av-40.json").read_text())
        validate_profile(original)
        for mutate in (
            lambda p: p["plant"]["pv"].update(activepower="measurements/absent"),
            lambda p: p["plant"]["pv"].update(dayyield="measurements/active-power"),
            lambda p: p["plant"].update(evidence=""),
            lambda p: p["plant"].update(hybridSeparated="true"),
            lambda p: p["plant"].update(hybridSeparated=True),
        ):
            profile = copy.deepcopy(original)
            mutate(profile)
            with self.subTest(profile=profile), self.assertRaises(ConfigError):
                validate_profile(profile)
        for role in ("battery", "hybrid"):
            with self.assertRaises(ConfigError):
                load_config(self.env | {"SMAB_INVERTER1_ROLE": role})

    def test_host_profiles_require_contribution_extension_explicitly(self):
        profile = json.loads((BUNDLED / "sma-stp8-0-3av-40.json").read_text())
        profile.pop("plant")
        Path(self.directory.name, "sma-stp8-0-3av-40.json").write_text(json.dumps(profile))
        with self.assertRaisesRegex(ConfigError, "contributions"):
            load_config(self.env)
        self.assertTrue(load_config(self.env | {"SMAB_INVERTER1_ROLE": "none"}).plant.enabled)

    def test_grid_profile_units_checked_before_connections_and_fingerprinted(self):
        config = load_config(
            self.env
            | {
                "SMAB_HOME_MANAGER_TRANSPORT": "modbus-tcp",
                "SMAB_HOME_MANAGER_HOST": "meter.invalid",
            }
        )
        signature = plant_plan(config)[3]
        profiles = copy.deepcopy(config.profiles)
        profile = profiles["home-manager"]
        prop = next(p for p in profile["properties"] if p["id"] == "energy-import")
        prop["unit"] = "Wh"
        with self.assertRaisesRegex(ConfigError, "units"):
            plant_plan(replace(config, profiles=profiles))
        prop["unit"] = "kWh"
        prop["name"] += " revised"
        self.assertNotEqual(signature, plant_plan(replace(config, profiles=profiles))[3])

    def test_generic_repeated_profile_and_single_device_suppression(self):
        engine = self.engine(env={"SMAB_INVERTER3_ENABLED": "false"})
        self.assertFalse(any(p.node == "pv" for p in engine.state.properties))
        self.assertFalse(any(p.node == "battery" for p in engine.state.properties))
        engine.refresh(100, self.wall)
        self.assertEqual(engine.state.fresh_values(100)["house/consumption"], "1600")
        engine = self.engine(
            env={
                "SMAB_INVERTER4_ENABLED": "true",
                "SMAB_INVERTER4_HOST": "four.invalid",
                "SMAB_INVERTER4_PROFILE": "sma-sbs3-7-10",
                "SMAB_INVERTER4_ROLE": "battery",
            }
        )
        engine.refresh(100, self.wall)
        values = engine.state.fresh_values(100)
        self.assertEqual(values["battery/totalpresbatcharge"], "900")
        self.assertEqual(Decimal(values["battery/totalbatterydischargeenergy"]), 50)

    def test_hybrid_requires_separated_channels_and_counts_each_flow_once(self):
        root = BUNDLED
        raw = json.loads((root / "sma-stp8-0-3av-40.json").read_text())
        battery = json.loads((root / "sma-sbs3-7-10.json").read_text())
        raw["plant"].update(battery=battery["plant"]["battery"], hybridSeparated=True)
        refs = set(raw["plant"]["battery"].values())
        additions = [p for p in battery["properties"] if p["node"] + "/" + p["id"] in refs]
        raw["properties"].extend(additions)
        wanted = {p["poller"] for p in additions}
        raw["pollers"].extend(p for p in battery["pollers"] if p["id"] in wanted)
        validate_profile(raw)
        Path(self.directory.name, "sma-stp8-0-3av-40.json").write_text(json.dumps(raw))
        config = load_config(
            self.env | {"SMAB_INVERTER1_ROLE": "hybrid", "SMAB_INVERTER2_ENABLED": "false"}
        )
        states = [s for s, _, _ in sources(config)]
        engine = PlantEngine(config, states)
        self.fill(
            engine,
            100,
            {
                "inverter1": {
                    "presbatcharge": 700,
                    "presbattdischarge": 500,
                    "batterychargeenergy": 40,
                    "batterydischargeenergy": 30,
                }
            },
        )
        engine.refresh(100, self.wall)
        self.assertEqual(engine.state.fresh_values(100)["house/consumption"], "4600")
        raw["plant"]["battery"]["presbatcharge"] = raw["plant"]["pv"]["activepower"]
        with self.assertRaisesRegex(ConfigError, "overlap"):
            validate_profile(raw)

    def test_filtered_contribution_and_mixed_battery_boundaries_rejected(self):
        root = BUNDLED
        raw = json.loads((root / "sma-stp8-0-3av-40.json").read_text())
        next(p for p in raw["properties"] if p["id"] == "active-power")["channelGroup"] = "advanced"
        Path(self.directory.name, "sma-stp8-0-3av-40.json").write_text(json.dumps(raw))
        with self.assertRaisesRegex(ConfigError, "filtered"):
            load_config(self.env | {"SMAB_INVERTER1_ADVANCED_CHANNELS_ENABLED": "false"})
        engine = self.engine(
            env={
                "SMAB_INVERTER4_ENABLED": "true",
                "SMAB_INVERTER4_HOST": "four.invalid",
                "SMAB_INVERTER4_PROFILE": "sma-sbs3-7-10",
                "SMAB_INVERTER4_ROLE": "battery",
            }
        )
        profiles = copy.deepcopy(engine.config.profiles)
        profiles["inverter4"]["plant"]["battery"].update(
            energyBoundary="ac", energyEvidence="Synthetic evidence"
        )
        with self.assertRaisesRegex(ConfigError, "boundaries"):
            PlantEngine(replace(engine.config, profiles=profiles), list(engine.sources.values()))


class PlantMeasurementTests(PlantFixture):
    def test_live_invalid_pv_power_is_named_and_retained_zero_is_not_reused(self):
        engine = self.engine()
        overrides = {
            "inverter1": {"activepower": 0},
            "inverter3": {"activepower": 0},
            "inverter2": {"presbatcharge": 0, "presbattdischarge": 234},
            "home-manager": {"powerimport": 400, "powerexport": 0},
        }
        self.fill(engine, 100, overrides)
        engine.refresh(100, self.wall)
        self.assertEqual(engine.state.fresh_values(100)["house/consumption"], "634")
        for slot in ("inverter1", "inverter3"):
            engine.sources[slot].update({"measurements/active-power": None}, now=101)
        engine.refresh(101, self.wall + timedelta(seconds=1))
        values = engine.state.fresh_values(101)
        self.assertNotIn("house/consumption", values)
        self.assertNotIn("pv/totalactivepower", values)
        self.assertIn("pv/totalyield", values)
        self.assertEqual(
            json.loads(values["diagnostics/power-input-status"]),
            {
                "inverter1/measurements/active-power": "missing-or-invalid",
                "inverter3/measurements/active-power": "missing-or-invalid",
            },
        )
        self.fill(engine, 102, overrides)
        engine.refresh(102, self.wall + timedelta(seconds=2))
        self.assertEqual(engine.state.fresh_values(102)["house/consumption"], "634")
        self.assertEqual(
            json.loads(engine.state.fresh_values(102)["diagnostics/power-input-status"]),
            {"status": "ready"},
        )

    def test_power_diagnostics_separate_age_skew_source_error_and_units(self):
        engine = self.engine(env={"SMAB_PLANT_MAX_SKEW_SECONDS": "1"})
        engine.sources["inverter1"].update({"measurements/active-power": 1000}, now=102)
        problems = engine.power_input_problems(102)
        self.assertEqual(problems["inverter3/measurements/active-power"], "sample-skew")
        problems = engine.power_input_problems(10000)
        self.assertEqual(problems["inverter1/measurements/active-power"], "stale")
        engine.sources["inverter1"].error = True
        self.assertEqual(
            engine.power_input_problems(102)["inverter1/measurements/active-power"],
            "source-error",
        )
        source = engine.sources["inverter3"]
        source.properties = tuple(
            replace(p, unit="kWh") if p.id == "active-power" else p for p in source.properties
        )
        self.assertEqual(
            engine.power_input_problems(102)["inverter3/measurements/active-power"],
            "unit-or-type-mismatch",
        )

    def test_negative_power_balance_has_distinct_diagnosis(self):
        engine = self.engine()
        self.fill(engine, 100, {"home-manager": {"powerexport": 10000}})
        engine.refresh(100, self.wall)
        values = engine.state.fresh_values(100)
        self.assertNotIn("house/consumption", values)
        self.assertEqual(
            json.loads(values["diagnostics/power-input-status"])["house/consumption"],
            "negative-balance",
        )

    def test_golden_power_yield_sums_topic_names_units_and_no_setters(self):
        engine = self.engine()
        engine.refresh(100, self.wall)
        values = engine.state.fresh_values(100)
        self.assertEqual(values["pv/totalactivepower"], "5000")
        self.assertEqual(values["pv/totaldayyield"], "12")
        self.assertEqual(values["pv/totalyield"], "300")
        self.assertEqual(values["house/consumption"], "4600")
        self.assertEqual(values["house/consumptionwithcharging"], "5300")
        self.assertNotIn("house/total-consumption", values)
        self.assertEqual(values["diagnostics/house-energy-status"], "unsupported-battery-boundary")
        self.assertEqual(values["diagnostics/import-day-status"], "partial")
        self.assertIn("pv/totalactivepower", values["diagnostics/valid-properties"].split(","))
        self.assertNotIn(
            "house/totalconsumption", values["diagnostics/valid-properties"].split(",")
        )
        topics = discovery("homie", "sma-plant", engine.state.properties)
        self.assertEqual(topics["homie/sma-plant/pv/totalactivepower/$unit"], "W")
        self.assertEqual(topics["homie/sma-plant/house/totalconsumption/$unit"], "kWh")
        self.assertTrue(all(not p.settable for p in engine.state.properties))

    def test_missing_invalid_error_and_zero_never_publish_partial_sum(self):
        engine = self.engine()
        engine.refresh(100, self.wall)
        source = engine.sources["inverter1"]
        source.update({"measurements/active-power": None}, now=101)
        self.assertNotIn("pv/totalactivepower", engine.state.fresh_values(101))
        engine.refresh(101, self.wall + timedelta(seconds=1))
        self.assertNotIn("house/consumption", engine.state.fresh_values(101))
        self.fill(engine, 102, {"inverter1": {"activepower": 0}, "inverter3": {"activepower": 0}})
        engine.refresh(102, self.wall + timedelta(seconds=2))
        self.assertEqual(engine.state.fresh_values(102)["pv/totalactivepower"], "0")
        source.error = True
        self.assertNotIn("pv/totalactivepower", engine.state.fresh_values(102))

    def test_input_age_is_not_renewed_and_shortest_deadline_wins(self):
        engine = self.engine()
        source = engine.sources["inverter1"]
        source.properties = tuple(
            replace(p, stale_seconds=2) if p.id == "active-power" else p for p in source.properties
        )
        source.update(
            SampleValues({"measurements/active-power": 2000}, {"measurements/active-power": 99}),
            now=100,
        )
        engine.refresh(100, self.wall)
        self.assertEqual(engine.state.values["pv/totalactivepower"][1], 99)
        engine.refresh(101, self.wall + timedelta(seconds=1))
        self.assertEqual(engine.state.values["pv/totalactivepower"][1], 99)
        self.assertNotIn("pv/totalactivepower", engine.state.fresh_values(101.01))

    def test_skew_negative_house_balance_and_retained_policy(self):
        engine = self.engine(env={"SMAB_PLANT_MAX_SKEW_SECONDS": "1"})
        engine.refresh(100, self.wall)
        engine.sources["inverter1"].update({"measurements/active-power": 1000}, now=102)
        self.assertNotIn("pv/totalactivepower", engine.state.fresh_values(102))
        self.fill(engine, 103, {"home-manager": {"powerexport": 10000}})
        engine.refresh(103, self.wall + timedelta(seconds=3))
        self.assertNotIn("house/consumption", engine.state.fresh_values(103))
        publisher = HomiePublisher(engine.config, [engine.state])
        published, status = publisher.snapshot([engine.state], 103)
        self.assertNotIn("house/consumption", published)
        self.assertIn("pv/totalactivepower", published)
        self.assertEqual(status, "alert")

    def test_supported_energy_equation_from_common_baseline_and_opening_value(self):
        engine = self.engine(ac=True, env={"SMAB_PLANT_INITIAL_CONSUMPTION_KWH": "1000"})
        engine.refresh(100, self.wall)
        self.assertEqual(Decimal(engine.state.fresh_values(100)["house/total-consumption"]), 1000)
        self.fill(
            engine,
            101,
            {
                "inverter1": {"totalyield": 112},
                "inverter3": {"totalyield": 208},
                "home-manager": {"energyimport": 56, "energyexport": 68},
                "inverter2": {"batterychargeenergy": 47, "batterydischargeenergy": 35},
            },
        )
        engine.refresh(101, self.wall + timedelta(seconds=1))
        self.assertEqual(Decimal(engine.state.fresh_values(101)["house/total-consumption"]), 1016)

    def test_actual_identity_change_blocks_energy_without_rebasing(self):
        engine = self.engine(ac=True)
        engine.refresh(100, self.wall)
        self.fill(engine, 101)
        engine.sources["inverter1"].identity_fingerprint = hashlib.sha256(
            b"replacement"
        ).hexdigest()
        engine.refresh(101, self.wall + timedelta(seconds=1))
        self.assertEqual(
            engine.state.fresh_values(101)["diagnostics/house-energy-status"],
            "configuration-changed",
        )
        self.assertNotIn("house/total-consumption", engine.state.fresh_values(101))
        self.assertIn("pv/totalactivepower", engine.state.fresh_values(101))

    def test_negative_directional_flows_are_unavailable_not_clamped(self):
        engine = self.engine()
        self.fill(engine, 101, {"inverter2": {"presbatcharge": -1}})
        engine.refresh(101, self.wall)
        self.assertNotIn("house/consumption", engine.state.fresh_values(101))
        self.assertNotIn("house/consumptionwithcharging", engine.state.fresh_values(101))
        self.assertEqual(engine.state.fresh_values(101)["pv/totalactivepower"], "5000")

    def test_changed_runtime_unit_cannot_reinterpret_an_existing_sample(self):
        engine = self.engine()
        engine.refresh(100, self.wall)
        source = engine.sources["inverter1"]
        source.properties = tuple(
            replace(p, unit="kW") if p.id == "active-power" else p for p in source.properties
        )
        self.assertNotIn("pv/totalactivepower", engine.state.fresh_values(100))
        engine.refresh(100, self.wall)
        self.assertNotIn("house/consumption", engine.state.fresh_values(100))
        self.assertNotIn(
            "pv/totalactivepower",
            engine.state.fresh_values(100)["diagnostics/valid-properties"].split(","),
        )

    def test_energy_publication_waits_for_checkpoint_and_keeps_snapshot_age(self):
        engine = self.engine(ac=True, env={"SMAB_PLANT_CHECKPOINT_INTERVAL_SECONDS": "300"})
        engine.refresh(100, self.wall)
        self.fill(engine, 101, {"home-manager": {"energyimport": 52}})
        engine.refresh(101, self.wall + timedelta(seconds=1))
        self.assertEqual(Decimal(engine.state.fresh_values(101)["house/total-consumption"]), 0)
        self.assertEqual(engine.state.values["house/total-consumption"][1], 100)
        self.fill(engine, 400, {"home-manager": {"energyimport": 52}})
        engine.refresh(400, self.wall + timedelta(seconds=300))
        self.assertEqual(Decimal(engine.state.fresh_values(400)["house/total-consumption"]), 2)
        restarted = PlantEngine(engine.config, list(engine.sources.values()))
        restarted.refresh(400, self.wall + timedelta(seconds=300))
        self.assertEqual(Decimal(restarted.state.fresh_values(400)["house/total-consumption"]), 2)

    def test_same_samples_do_not_advance_ledger_receipt_or_write_periodically(self):
        engine = self.engine(ac=True)
        engine.refresh(100, self.wall)
        previous = engine.ledger.path.read_bytes()
        for now in (101, 102, 103):
            engine.refresh(now, self.wall + timedelta(seconds=now - 100))
        self.assertEqual(previous, engine.ledger.path.read_bytes())
        self.assertEqual(
            engine.ledger.data["accounts"]["import"]["lastTime"], self.wall.isoformat()
        )

    def test_persistent_restart_configuration_change_and_disabled_retirement(self):
        engine = self.engine(ac=True)
        engine.refresh(100, self.wall)
        self.fill(engine, 101, {"home-manager": {"energyimport": 52}})
        engine.refresh(101, self.wall + timedelta(seconds=1))
        engine.ledger.persist(101, force=True)
        restarted = PlantEngine(engine.config, list(engine.sources.values()))
        restarted.refresh(101, self.wall + timedelta(seconds=1))
        self.assertEqual(restarted.state.fresh_values(101)["house/total-consumption"], "2.0")
        before = engine.ledger.path.read_bytes()
        changed = replace(
            engine.config,
            inverters=tuple(
                replace(i, role="none") if i.id == "inverter3" else i
                for i in engine.config.inverters
            ),
        )
        new = PlantEngine(changed, list(engine.sources.values()))
        new.refresh(101, self.wall + timedelta(seconds=1))
        self.assertFalse(any(p.node == "pv" for p in new.state.properties))
        self.assertEqual(
            new.state.fresh_values(101)["diagnostics/import-day-status"], "configuration-changed"
        )
        self.assertEqual(before, new.ledger.path.read_bytes())

    def test_corrupt_symlink_and_oversize_ledger_fail_closed(self):
        path = Path(self.directory.name, "energy-balances.json")
        for raw in (
            "{}",
            '{"schemaVersion":1,"accounts":{},"signature":"bad"}',
            '{"duplicate":1,"duplicate":2}',
        ):
            path.write_text(raw)
            with self.assertRaises(StateError):
                self.engine()
        path.unlink()
        path.symlink_to(Path(self.directory.name, "missing.json"))
        with self.assertRaises(StateError):
            self.engine()


class PlantRuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def test_supervised_plant_shutdown_and_no_adapter_io_with_fixtures(self):
        fixture = PlantFixture()
        fixture.setUp()
        try:
            engine = fixture.engine(ac=True)
            stop = asyncio.Event()
            publisher = AsyncMock()
            publisher.status = {}
            publisher.monitors = {}
            captured = []

            def factory(_config, states):
                captured.extend(states)
                return publisher

            async def source_fixture(state, *_args):
                state.update({k: v for k, (v, _) in engine.sources[state.id].values.items()})
                state.identity_fingerprint = engine.sources[state.id].identity_fingerprint
                await stop.wait()

            async def publish(_stop):
                for _ in range(100):
                    if next(s for s in captured if s.id == "plant").values:
                        stop.set()
                        return
                    await asyncio.sleep(0.001)
                self.fail("Plant calculation did not run")

            publisher.run.side_effect = publish
            with patch("sma_mqtt_bridge.runtime.supervise", side_effect=source_fixture):
                await run_locked(engine.config, stop=stop, publisher_factory=factory)
            self.assertTrue(stop.is_set())
            plant = next(s for s in captured if s.id == "plant")
            self.assertEqual(plant.fresh_values()["pv/totalactivepower"], "5000")
        finally:
            fixture.directory.cleanup()
