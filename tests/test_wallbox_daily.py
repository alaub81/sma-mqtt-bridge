"""Wallbox calendar energy and household exclusion share durable counter baselines."""

import asyncio
import copy
import hashlib
import json
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from test_plant import PlantFixture
from test_runtime import FakeClient

from sma_mqtt_bridge.energy_balances import EnergyBalances
from sma_mqtt_bridge.errors import ConfigError
from sma_mqtt_bridge.homie import HomiePublisher, discovery
from sma_mqtt_bridge.model import SampleValues
from sma_mqtt_bridge.plant import PlantEngine
from sma_mqtt_bridge.runtime import run_locked


class WallboxDailyTests(PlantFixture):
    def setUp(self):
        super().setUp()
        self.env.update(
            SMAB_ECHARGER_ENABLED="true",
            SMAB_ECHARGER_HOST="wallbox.invalid",
            SMAB_ECHARGER_USERNAME="fixture",
            SMAB_ECHARGER_PASSWORD="fixture",
            SMAB_ECHARGER_EXPECTED_SERIAL="987654321",
            SMAB_ECHARGER_TLS_VERIFY="false",
        )
        self.wall = datetime(2026, 10, 14, 21, 59, tzinfo=timezone.utc)

    def fill(self, engine, now, overrides=None, *, energy=1000):
        super().fill(engine, now, overrides)
        if engine.wallbox is not None:
            engine.sources["api"].update({"measurements/total-energy": energy}, now=now)

    def output_values(self, engine, now):
        """Merge derived outputs only for arithmetic assertions; ownership is checked separately."""
        values = engine.state.fresh_values(now)
        if engine.wallbox_state is not None:
            values.update(engine.wallbox_state.fresh_values(now))
        return values

    def covered_day(self, *, ac=False):
        engine = self.engine(ac=ac)
        engine.refresh(100, self.wall)
        self.fill(engine, 220)
        engine.refresh(220, self.wall + timedelta(minutes=2))
        return engine

    def test_older_fresh_api_counter_cannot_poison_restart(self):
        engine = self.engine(ac=True)
        engine.refresh(100, self.wall)
        original = copy.deepcopy(engine.ledger.data["accounts"]["wallbox"])
        self.fill(engine, 130)
        engine.sources["api"].update(
            SampleValues({"measurements/total-energy": 1000}, {"measurements/total-energy": 99}),
            now=130,
        )
        engine.refresh(130, self.wall + timedelta(seconds=30))
        self.assertEqual(engine.ledger.data["accounts"]["wallbox"], original)
        restarted = EnergyBalances(engine.config, engine.ledger.data["signature"], engine.zone)
        self.assertEqual(restarted.data["accounts"]["wallbox"], original)
        self.fill(engine, 160, energy=1002)
        engine.refresh(160, self.wall + timedelta(seconds=60))
        self.assertEqual(
            engine.ledger.data["accounts"]["wallbox"]["lastTime"],
            (self.wall + timedelta(seconds=60)).isoformat(),
        )

    def advance_balances(self, engine, *, energy=1004, pv1=112):
        self.fill(
            engine,
            3820,
            {
                "inverter1": {"totalyield": pv1},
                "inverter3": {"totalyield": 208},
                "home-manager": {"energyimport": 56, "energyexport": 68},
                "inverter2": {"batterychargeenergy": 47, "batterydischargeenergy": 35},
            },
            energy=energy,
        )
        engine.refresh(3820, self.wall + timedelta(minutes=62))

    def test_topics_are_read_only_and_absent_without_local_api(self):
        engine = self.engine()
        topics = discovery("homie", "sma-plant", engine.state.properties)
        charger = discovery(
            "homie", engine.config.echarger.homie_id, engine.wallbox_state.properties
        )
        self.assertEqual(
            topics["homie/sma-plant/house/dailyconsumptionwithoutwallbox/$unit"], "kWh"
        )
        self.assertEqual(
            topics["homie/sma-plant/house/dailyconsumptionwithoutwallbox/$settable"], "false"
        )
        prefix = "homie/" + engine.config.echarger.homie_id + "/measurements/dailyconsumption"
        self.assertEqual(charger[prefix + "/$unit"], "kWh")
        self.assertEqual(charger[prefix + "/$settable"], "false")
        self.assertFalse(any("/wallbox/" in topic for topic in topics))
        self.assertNotIn("measurements/daily-consumption", engine.state.property_index())
        self.assertNotIn("diagnostics/wallbox-day-status", engine.state.property_index())
        disabled = self.engine(env={"SMAB_ECHARGER_ENABLED": "false"})
        self.assertIsNone(disabled.wallbox)
        self.assertIsNone(disabled.wallbox_state)
        self.assertNotIn("measurements/daily-consumption", disabled.state.property_index())
        self.assertNotIn("house/daily-consumption-without-wallbox", disabled.state.property_index())

    def test_wallbox_day_is_independent_of_unverified_battery_and_session_energy(self):
        engine = self.covered_day()
        self.assertEqual(self.output_values(engine, 220)["measurements/daily-consumption"], "0")
        self.advance_balances(engine)
        values = self.output_values(engine, 3820)
        self.assertEqual(Decimal(values["measurements/daily-consumption"]), 4)
        self.assertEqual(values["diagnostics/wallbox-day-status"], "complete")
        self.assertNotIn("house/daily-consumption-without-wallbox", values)
        self.assertEqual(
            values["diagnostics/house-without-wallbox-day-status"],
            "unsupported-battery-boundary",
        )
        engine.sources["api"].update({"measurements/session-energy": 0}, now=3820)
        engine.refresh(3820, self.wall + timedelta(minutes=62))
        self.assertEqual(
            Decimal(self.output_values(engine, 3820)["measurements/daily-consumption"]), 4
        )

    def test_partial_day_opt_in_publishes_common_vector_from_first_valid_snapshot(self):
        self.wall = datetime(2026, 10, 14, 10, tzinfo=timezone.utc)
        engine = self.engine(
            env={
                "SMAB_PLANT_PUBLISH_PARTIAL_DAY": "true",
                "SMAB_PLANT_ASSUME_AC_BATTERY_ENERGY": "true",
            }
        )
        engine.refresh(100, self.wall)
        values = self.output_values(engine, 100)
        for key in (
            "house/daily-consumption",
            "house/daily-consumption-without-wallbox",
            "measurements/daily-consumption",
            "grid/daily-energy-import",
            "grid/daily-energy-export",
        ):
            self.assertEqual(Decimal(values[key]), 0)
        self.advance_balances(engine)
        values = self.output_values(engine, 3820)
        self.assertEqual(Decimal(values["house/daily-consumption"]), 16)
        self.assertEqual(Decimal(values["house/daily-consumption-without-wallbox"]), 12)
        self.assertEqual(Decimal(values["measurements/daily-consumption"]), 4)
        for key in (
            "diagnostics/house-energy-status",
            "diagnostics/house-without-wallbox-day-status",
            "diagnostics/wallbox-day-status",
        ):
            self.assertEqual(values[key], "partial")
        restarted = PlantEngine(engine.config, list(engine.sources.values()))
        restarted.refresh(3820, self.wall + timedelta(minutes=62))
        self.assertEqual(self.output_values(restarted, 3820)["house/daily-consumption"], "16")
        # The test mode must not turn invalid source samples into usable deltas.
        engine.sources["api"].update({"measurements/total-energy": None}, now=3821)
        engine.refresh(3821, self.wall + timedelta(minutes=62, seconds=1))
        values = self.output_values(engine, 3821)
        self.assertNotIn("measurements/daily-consumption", values)
        self.assertNotIn("house/daily-consumption-without-wallbox", values)

    def test_partial_day_opt_in_still_requires_battery_boundary_and_durable_write(self):
        engine = self.engine(env={"SMAB_PLANT_PUBLISH_PARTIAL_DAY": "true"})
        with patch("sma_mqtt_bridge.energy_balances.write_state", side_effect=OSError("fixture")):
            with self.assertRaises(OSError):
                engine.refresh(100, self.wall)
        self.assertNotIn("measurements/daily-consumption", self.output_values(engine, 100))
        engine.refresh(100, self.wall)
        values = self.output_values(engine, 100)
        self.assertEqual(values["measurements/daily-consumption"], "0")
        self.assertNotIn("house/daily-consumption", values)
        self.assertEqual(values["diagnostics/house-energy-status"], "unsupported-battery-boundary")

    def test_explicit_ac_assumption_unlocks_house_balances_and_preserves_grid_baselines(self):
        blocked = self.covered_day()
        signature = blocked.ledger.data["signature"]
        grid = json.loads(json.dumps(blocked.ledger.data["accounts"]["import"]))
        engine = self.engine(env={"SMAB_PLANT_ASSUME_AC_BATTERY_ENERGY": "true"})
        self.assertEqual(engine.ledger.data["signature"], signature)
        self.assertEqual(engine.ledger.data["accounts"]["import"], grid)
        self.fill(engine, 220)
        engine.refresh(220, self.wall + timedelta(minutes=2))
        self.assertEqual(
            engine.state.fresh_values(220)["diagnostics/battery-energy-boundary"], "assumed-ac"
        )
        self.assertEqual(
            engine.state.fresh_values(220)["diagnostics/house-energy-status"], "partial"
        )
        self.assertNotIn("house/daily-consumption", engine.state.fresh_values(220))
        # Start a covered next day without inventing the previously blocked day's baseline.
        next_day = self.wall + timedelta(days=1)
        self.fill(engine, 86500)
        engine.refresh(86500, next_day)
        self.fill(engine, 86620)
        engine.refresh(86620, next_day + timedelta(minutes=2))
        self.fill(
            engine,
            86700,
            {
                "inverter1": {"totalyield": 112},
                "inverter3": {"totalyield": 208},
                "home-manager": {"energyimport": 56, "energyexport": 68},
                "inverter2": {"batterychargeenergy": 47, "batterydischargeenergy": 35},
            },
            energy=1004,
        )
        engine.refresh(86700, next_day + timedelta(seconds=200))
        values = self.output_values(engine, 86700)
        self.assertEqual(Decimal(values["house/daily-consumption"]), 16)
        self.assertEqual(Decimal(values["house/daily-consumption-without-wallbox"]), 12)

    def test_ac_assumption_does_not_override_documented_dc_boundary(self):
        engine = self.engine(env={"SMAB_PLANT_ASSUME_AC_BATTERY_ENERGY": "true"})
        profiles = copy.deepcopy(engine.config.profiles)
        profiles["inverter2"]["plant"]["battery"].update(
            energyBoundary="dc", energyEvidence="Synthetic DC fixture only"
        )
        engine = PlantEngine(
            replace(engine.config, profiles=profiles), list(engine.sources.values())
        )
        engine.refresh(100, self.wall)
        self.assertEqual(
            engine.state.fresh_values(100)["diagnostics/battery-energy-boundary"], "dc"
        )
        self.assertEqual(
            engine.state.fresh_values(100)["diagnostics/house-energy-status"],
            "unsupported-battery-boundary",
        )

    def test_charger_readiness_and_custom_identity_survive_partial_day(self):
        engine = self.engine(env={"SMAB_ECHARGER_HOMIE_ID": "garage-charger"})
        api = engine.sources["api"]
        api.update(
            {"measurements/power": 0, "measurements/current-l1": 0, "measurements/voltage-l1": 230},
            now=100,
        )
        engine.refresh(100, self.wall)
        self.assertEqual(engine.wallbox_state.device, "garage-charger")
        self.assertFalse(engine.wallbox_state.contributes_availability)
        self.assertEqual(
            engine.wallbox_state.fresh_values(100)["diagnostics/wallbox-day-status"], "partial"
        )
        publisher = HomiePublisher(engine.config, [api, *engine.output_states])
        states = [s for s in publisher.states if s.device == "garage-charger"]
        self.assertEqual(len(states), 2)
        metadata = publisher.metadata("garage-charger", publisher.properties(states))
        self.assertIn("homie/garage-charger/measurements/dailyconsumption/$unit", metadata)
        values, status = publisher.snapshot(states, 100)
        self.assertEqual(status, "ready")
        self.assertNotIn("measurements/daily-consumption", values)

    def test_common_counter_vector_subtracts_wallbox_once(self):
        engine = self.covered_day(ac=True)
        self.advance_balances(engine)
        values = self.output_values(engine, 3820)
        self.assertEqual(Decimal(values["house/daily-consumption"]), 16)
        self.assertEqual(Decimal(values["measurements/daily-consumption"]), 4)
        self.assertEqual(Decimal(values["house/daily-consumption-without-wallbox"]), 12)
        self.assertEqual(values["diagnostics/house-without-wallbox-day-status"], "complete")
        data = json.loads(engine.ledger.path.read_text())
        self.assertIn(
            "api/measurements/total-energy", data["accounts"]["housewithoutwallbox"]["dailyBase"]
        )
        self.assertEqual(data["schemaVersion"], 2)

    def test_missing_stale_or_negative_wallbox_does_not_block_existing_house(self):
        engine = self.covered_day(ac=True)
        self.advance_balances(engine)
        for energy in (None, -1):
            with self.subTest(energy=energy):
                engine.sources["api"].update({"measurements/total-energy": energy}, now=3820)
                engine.refresh(3820, self.wall + timedelta(minutes=62))
                values = self.output_values(engine, 3820)
                self.assertNotIn("measurements/daily-consumption", values)
                self.assertNotIn("house/daily-consumption-without-wallbox", values)
                self.assertEqual(Decimal(values["house/daily-consumption"]), 16)
        engine.sources["api"].update({"measurements/total-energy": 1004}, now=3820)
        source = engine.sources["api"]
        source.properties = tuple(
            replace(p, stale_seconds=1) if p.id == "total-energy" else p for p in source.properties
        )
        self.assertNotIn("measurements/daily-consumption", self.output_values(engine, 3822))
        self.assertIn("house/daily-consumption", self.output_values(engine, 3822))
        source.error = True
        self.assertNotIn("measurements/daily-consumption", self.output_values(engine, 3820))

    def test_negative_excluded_balance_is_unavailable_not_zero(self):
        engine = self.covered_day(ac=True)
        self.fill(engine, 3820, {"inverter1": {"totalyield": 102}}, energy=1003)
        engine.refresh(3820, self.wall + timedelta(minutes=62))
        values = self.output_values(engine, 3820)
        self.assertEqual(Decimal(values["house/daily-consumption"]), 2)
        self.assertEqual(Decimal(values["measurements/daily-consumption"]), 3)
        self.assertNotIn("house/daily-consumption-without-wallbox", values)
        self.assertEqual(values["diagnostics/house-without-wallbox-day-status"], "inconsistent")

    def test_identity_and_endpoint_changes_only_block_wallbox_accounts(self):
        engine = self.covered_day(ac=True)
        engine.sources["api"].identity_fingerprint = hashlib.sha256(b"replacement").hexdigest()
        self.fill(engine, 221)
        engine.refresh(221, self.wall + timedelta(minutes=2, seconds=1))
        values = self.output_values(engine, 221)
        self.assertEqual(values["diagnostics/wallbox-day-status"], "configuration-changed")
        self.assertEqual(
            values["diagnostics/house-without-wallbox-day-status"], "configuration-changed"
        )
        self.assertEqual(values["diagnostics/house-energy-status"], "complete")
        replacement = self.engine(ac=True, env={"SMAB_ECHARGER_HOST": "replacement.invalid"})
        self.fill(replacement, 222)
        replacement.refresh(222, self.wall + timedelta(minutes=2, seconds=2))
        self.assertEqual(
            self.output_values(replacement, 222)["diagnostics/wallbox-day-status"],
            "configuration-changed",
        )
        self.assertEqual(
            self.output_values(replacement, 222)["diagnostics/house-energy-status"], "complete"
        )

    def test_existing_ledger_survives_late_wallbox_enable_with_partial_new_accounts(self):
        engine = self.engine(ac=True, env={"SMAB_ECHARGER_ENABLED": "false"})
        engine.refresh(100, self.wall)
        self.fill(engine, 220)
        engine.refresh(220, self.wall + timedelta(minutes=2))
        enabled = self.engine(ac=True)
        self.fill(enabled, 230)
        enabled.refresh(230, self.wall + timedelta(minutes=2, seconds=10))
        values = self.output_values(enabled, 230)
        self.assertEqual(values["diagnostics/house-energy-status"], "complete")
        self.assertEqual(values["diagnostics/wallbox-day-status"], "partial")
        self.assertEqual(values["diagnostics/house-without-wallbox-day-status"], "partial")
        self.assertNotIn("house/daily-consumption-without-wallbox", values)

    def test_restart_keeps_committed_wallbox_day_and_common_baseline(self):
        engine = self.covered_day(ac=True)
        self.advance_balances(engine)
        restarted = self.engine(ac=True)
        self.advance_balances(restarted, energy=1005, pv1=114)
        values = self.output_values(restarted, 3820)
        self.assertEqual(Decimal(values["measurements/daily-consumption"]), 5)
        self.assertEqual(Decimal(values["house/daily-consumption-without-wallbox"]), 13)

    def test_both_daily_values_wait_for_durable_checkpoint(self):
        engine = self.engine(ac=True, env={"SMAB_PLANT_CHECKPOINT_INTERVAL_SECONDS": "300"})
        engine.refresh(100, self.wall)
        self.fill(engine, 220)
        engine.refresh(220, self.wall + timedelta(minutes=2))
        self.fill(engine, 221, {"inverter1": {"totalyield": 102}}, energy=1001)
        engine.refresh(221, self.wall + timedelta(minutes=2, seconds=1))
        values = self.output_values(engine, 221)
        self.assertEqual(values["measurements/daily-consumption"], "0")
        self.assertEqual(values["house/daily-consumption-without-wallbox"], "0")
        self.fill(engine, 520, {"inverter1": {"totalyield": 102}}, energy=1001)
        engine.refresh(520, self.wall + timedelta(minutes=7))
        values = self.output_values(engine, 520)
        self.assertEqual(values["measurements/daily-consumption"], "1")
        self.assertEqual(values["house/daily-consumption-without-wallbox"], "1")

    def test_wallbox_age_skew_blocks_only_the_combined_day(self):
        engine = self.engine(ac=True, env={"SMAB_PLANT_MAX_SKEW_SECONDS": "1"})
        engine.refresh(100, self.wall)
        self.fill(engine, 220)
        engine.refresh(220, self.wall + timedelta(minutes=2))
        self.fill(engine, 230)
        engine.sources["api"].values["measurements/total-energy"] = ("1000", 220)
        engine.refresh(230, self.wall + timedelta(minutes=2, seconds=10))
        values = self.output_values(engine, 230)
        self.assertIn("measurements/daily-consumption", values)
        self.assertIn("house/daily-consumption", values)
        self.assertNotIn("house/daily-consumption-without-wallbox", values)
        self.assertEqual(values["diagnostics/house-without-wallbox-day-status"], "unavailable")

    def test_local_api_energy_units_are_checked(self):
        engine = self.engine()
        source = engine.sources["api"]
        source.properties = tuple(
            replace(p, unit="Wh") if p.id == "total-energy" else p for p in source.properties
        )
        with self.assertRaisesRegex(ConfigError, "kWh"):
            PlantEngine(engine.config, list(engine.sources.values()))

    def test_wallbox_reset_and_midnight_gap_do_not_become_zero_consumption(self):
        engine = self.covered_day(ac=True)
        self.fill(engine, 280, energy=1)
        engine.refresh(280, self.wall + timedelta(minutes=3))
        values = self.output_values(engine, 280)
        self.assertEqual(values["diagnostics/wallbox-day-status"], "reset")
        self.assertNotIn("measurements/daily-consumption", values)
        self.assertEqual(values["diagnostics/house-energy-status"], "complete")
        self.fill(engine, 86620, energy=2)
        engine.refresh(86620, self.wall + timedelta(days=1, minutes=2))
        values = self.output_values(engine, 86620)
        self.assertEqual(values["diagnostics/wallbox-day-status"], "gap")
        self.assertNotIn("measurements/daily-consumption", values)
        self.fill(engine, 172900, energy=3)
        engine.refresh(172900, self.wall + timedelta(days=2))
        self.fill(engine, 173020, energy=4)
        engine.refresh(173020, self.wall + timedelta(days=2, minutes=2))
        values = self.output_values(engine, 173020)
        self.assertEqual(values["diagnostics/wallbox-day-status"], "complete")
        self.assertEqual(values["measurements/daily-consumption"], "0")

    def assert_dst_wallbox_day(self, before, hours):
        self.wall = before
        engine = self.covered_day()
        now = 100 + hours * 3600
        self.fill(engine, now, energy=1004)
        engine.refresh(now, self.wall + timedelta(hours=hours))
        self.assertEqual(self.output_values(engine, now)["measurements/daily-consumption"], "4")
        self.fill(engine, now + 120, energy=1005)
        engine.refresh(now + 120, self.wall + timedelta(hours=hours, minutes=2))
        self.assertEqual(
            self.output_values(engine, now + 120)["measurements/daily-consumption"], "0"
        )
        self.assertEqual(
            self.output_values(engine, now + 120)["diagnostics/wallbox-day-status"], "complete"
        )

    def test_wallbox_23_hour_day(self):
        self.assert_dst_wallbox_day(datetime(2026, 3, 28, 22, 59, tzinfo=timezone.utc), 23)

    def test_wallbox_25_hour_day(self):
        self.assert_dst_wallbox_day(datetime(2026, 10, 24, 21, 59, tzinfo=timezone.utc), 25)

    def test_daily_only_account_does_not_require_monotone_lifetime_balance(self):
        engine = self.engine(ac=True)
        ledger = engine.ledger
        signs = {"pv": Decimal(1), "wallbox": Decimal(-1)}
        hardware = hashlib.sha256(b"synthetic-pair").hexdigest()

        def observe(wall, pv, wallbox):
            return ledger.observe(
                "housewithoutwallbox",
                {"pv": Decimal(pv), "wallbox": Decimal(wallbox)},
                signs,
                hardware,
                wall,
                wall,
                daily_only=True,
            )

        observe(self.wall - timedelta(hours=2), 100, 50)
        observe(self.wall - timedelta(hours=1), 120, 50)
        self.assertEqual(observe(self.wall, 120, 65), (None, None, "partial"))
        self.assertEqual(
            observe(self.wall + timedelta(minutes=2), 120, 65), (Decimal(0), None, "complete")
        )
        self.assertEqual(
            observe(self.wall + timedelta(minutes=3), 121, 65), (Decimal(1), None, "complete")
        )
        ledger.persist(300)
        restored = EnergyBalances(engine.config, ledger.data["signature"], engine.zone)
        self.assertIn("housewithoutwallbox", restored.data["accounts"])


class WallboxPlacementRuntimeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.fixture = WallboxDailyTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    async def test_runtime_registers_derived_output_on_existing_charger(self):
        engine = self.fixture.engine()
        stop, captured = asyncio.Event(), []
        publisher = AsyncMock()
        publisher.status, publisher.monitors = {}, {}

        def factory(_config, states):
            captured.extend(states)
            return publisher

        async def source_fixture(state, *_args):
            state.update({k: v for k, (v, _) in engine.sources[state.id].values.items()})
            state.identity_fingerprint = engine.sources[state.id].identity_fingerprint
            await stop.wait()

        async def publish(_stop):
            for _ in range(100):
                daily = next(s for s in captured if s.id == "wallbox-day")
                if daily.values:
                    stop.set()
                    return
                await asyncio.sleep(0.001)
            self.fail("Derived charger output did not run")

        publisher.run.side_effect = publish
        with patch("sma_mqtt_bridge.runtime.supervise", side_effect=source_fixture):
            await run_locked(engine.config, stop=stop, publisher_factory=factory)
        daily = next(s for s in captured if s.id == "wallbox-day")
        api = next(s for s in captured if s.id == "api")
        self.assertEqual(daily.device, api.device)
        self.assertEqual(daily.fresh_values()["diagnostics/wallbox-day-status"], "partial")
        self.assertFalse(daily.contributes_availability)
        self.assertEqual(sum(s.id == "wallbox-day" for s in captured), 1)

    async def test_manifest_retires_old_plant_topics_and_preserves_energy_account(self):
        engine = self.fixture.covered_day(ac=True)
        self.fixture.advance_balances(engine)
        before = engine.ledger.path.read_bytes()
        restored = self.fixture.engine(ac=True)
        self.assertEqual(restored.ledger.path.read_bytes(), before)
        self.fixture.advance_balances(restored)
        self.assertEqual(
            restored.wallbox_state.fresh_values(3820)["measurements/daily-consumption"], "4"
        )
        clients = []

        def factory(*args, **kwargs):
            client = FakeClient(*args, **kwargs)
            clients.append(client)
            return client

        publisher = HomiePublisher(
            restored.config, [*restored.sources.values(), *restored.output_states], factory
        )
        old = {
            "homie/sma-plant/wallbox/dailyconsumption",
            "homie/sma-plant/wallbox/dailyconsumption/$unit",
            "homie/sma-plant/diagnostics/wallboxdaystatus",
            "homie/sma-plant/house/totalconsumption",
            "homie/sma-plant/house/totalconsumption/$unit",
            "homie/sma-plant/house/totalconsumption/$name",
            "homie/sma-plant/house/totalconsumption/$datatype",
            "homie/sma-plant/house/totalconsumption/$settable",
        }
        publisher.owned = {"sma-plant": old}
        publisher.publish_values = AsyncMock()
        await publisher.serve_device("sma-plant", [restored.state], asyncio.Event())
        messages = {(topic, value) for topic, value, _ in clients[0].messages}
        for topic in old:
            self.assertIn((topic, b""), messages)
            self.assertNotIn(topic, publisher.owned["sma-plant"])
        self.assertEqual(restored.ledger.path.read_bytes(), before)
        self.assertNotIn("wallbox/daily-consumption", restored.state.property_index())
