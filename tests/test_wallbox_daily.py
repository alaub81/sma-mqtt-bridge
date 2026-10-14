"""Wallbox calendar energy and household exclusion share durable counter baselines."""

import hashlib
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from test_plant import PlantFixture

from sma_mqtt_bridge.energy_balances import EnergyBalances
from sma_mqtt_bridge.errors import ConfigError
from sma_mqtt_bridge.homie import discovery
from sma_mqtt_bridge.plant import PlantEngine


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

    def covered_day(self, *, ac=False):
        engine = self.engine(ac=ac)
        engine.refresh(100, self.wall)
        self.fill(engine, 220)
        engine.refresh(220, self.wall + timedelta(minutes=2))
        return engine

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
        for key in ("wallbox/dailyconsumption", "house/dailyconsumptionwithoutwallbox"):
            self.assertEqual(topics["homie/sma-plant/" + key + "/$unit"], "kWh")
            self.assertEqual(topics["homie/sma-plant/" + key + "/$settable"], "false")
        disabled = self.engine(env={"SMAB_ECHARGER_ENABLED": "false"})
        self.assertIsNone(disabled.wallbox)
        self.assertNotIn("wallbox/daily-consumption", disabled.state.property_index())
        self.assertNotIn("house/daily-consumption-without-wallbox", disabled.state.property_index())

    def test_wallbox_day_is_independent_of_unverified_battery_and_session_energy(self):
        engine = self.covered_day()
        self.assertEqual(engine.state.fresh_values(220)["wallbox/daily-consumption"], "0")
        self.advance_balances(engine)
        values = engine.state.fresh_values(3820)
        self.assertEqual(Decimal(values["wallbox/daily-consumption"]), 4)
        self.assertEqual(values["diagnostics/wallbox-day-status"], "complete")
        self.assertNotIn("house/daily-consumption-without-wallbox", values)
        self.assertEqual(
            values["diagnostics/house-without-wallbox-day-status"],
            "unsupported-battery-boundary",
        )
        engine.sources["api"].update({"measurements/session-energy": 0}, now=3820)
        engine.refresh(3820, self.wall + timedelta(minutes=62))
        self.assertEqual(Decimal(engine.state.fresh_values(3820)["wallbox/daily-consumption"]), 4)

    def test_common_counter_vector_subtracts_wallbox_once(self):
        engine = self.covered_day(ac=True)
        self.advance_balances(engine)
        values = engine.state.fresh_values(3820)
        self.assertEqual(Decimal(values["house/daily-consumption"]), 16)
        self.assertEqual(Decimal(values["wallbox/daily-consumption"]), 4)
        self.assertEqual(Decimal(values["house/daily-consumption-without-wallbox"]), 12)
        self.assertEqual(values["diagnostics/house-without-wallbox-day-status"], "complete")
        data = json.loads(engine.ledger.path.read_text())
        self.assertIn(
            "api/measurements/total-energy", data["accounts"]["housewithoutwallbox"]["dailyBase"]
        )
        self.assertEqual(data["schemaVersion"], 1)

    def test_missing_stale_or_negative_wallbox_does_not_block_existing_house(self):
        engine = self.covered_day(ac=True)
        self.advance_balances(engine)
        for energy in (None, -1):
            with self.subTest(energy=energy):
                engine.sources["api"].update({"measurements/total-energy": energy}, now=3820)
                engine.refresh(3820, self.wall + timedelta(minutes=62))
                values = engine.state.fresh_values(3820)
                self.assertNotIn("wallbox/daily-consumption", values)
                self.assertNotIn("house/daily-consumption-without-wallbox", values)
                self.assertEqual(Decimal(values["house/daily-consumption"]), 16)
        engine.sources["api"].update({"measurements/total-energy": 1004}, now=3820)
        source = engine.sources["api"]
        source.properties = tuple(
            replace(p, stale_seconds=1) if p.id == "total-energy" else p for p in source.properties
        )
        self.assertNotIn("wallbox/daily-consumption", engine.state.fresh_values(3822))
        self.assertIn("house/daily-consumption", engine.state.fresh_values(3822))
        source.error = True
        self.assertNotIn("wallbox/daily-consumption", engine.state.fresh_values(3820))

    def test_negative_excluded_balance_is_unavailable_not_zero(self):
        engine = self.covered_day(ac=True)
        self.fill(engine, 3820, {"inverter1": {"totalyield": 102}}, energy=1003)
        engine.refresh(3820, self.wall + timedelta(minutes=62))
        values = engine.state.fresh_values(3820)
        self.assertEqual(Decimal(values["house/daily-consumption"]), 2)
        self.assertEqual(Decimal(values["wallbox/daily-consumption"]), 3)
        self.assertNotIn("house/daily-consumption-without-wallbox", values)
        self.assertEqual(values["diagnostics/house-without-wallbox-day-status"], "inconsistent")

    def test_identity_and_endpoint_changes_only_block_wallbox_accounts(self):
        engine = self.covered_day(ac=True)
        engine.sources["api"].identity_fingerprint = hashlib.sha256(b"replacement").hexdigest()
        self.fill(engine, 221)
        engine.refresh(221, self.wall + timedelta(minutes=2, seconds=1))
        values = engine.state.fresh_values(221)
        self.assertEqual(values["diagnostics/wallbox-day-status"], "configuration-changed")
        self.assertEqual(
            values["diagnostics/house-without-wallbox-day-status"], "configuration-changed"
        )
        self.assertEqual(values["diagnostics/house-energy-status"], "complete")
        replacement = self.engine(ac=True, env={"SMAB_ECHARGER_HOST": "replacement.invalid"})
        self.fill(replacement, 222)
        replacement.refresh(222, self.wall + timedelta(minutes=2, seconds=2))
        self.assertEqual(
            replacement.state.fresh_values(222)["diagnostics/wallbox-day-status"],
            "configuration-changed",
        )
        self.assertEqual(
            replacement.state.fresh_values(222)["diagnostics/house-energy-status"], "complete"
        )

    def test_existing_ledger_survives_late_wallbox_enable_with_partial_new_accounts(self):
        engine = self.engine(ac=True, env={"SMAB_ECHARGER_ENABLED": "false"})
        engine.refresh(100, self.wall)
        self.fill(engine, 220)
        engine.refresh(220, self.wall + timedelta(minutes=2))
        enabled = self.engine(ac=True)
        self.fill(enabled, 230)
        enabled.refresh(230, self.wall + timedelta(minutes=2, seconds=10))
        values = enabled.state.fresh_values(230)
        self.assertEqual(values["diagnostics/house-energy-status"], "complete")
        self.assertEqual(values["diagnostics/wallbox-day-status"], "partial")
        self.assertEqual(values["diagnostics/house-without-wallbox-day-status"], "partial")
        self.assertNotIn("house/daily-consumption-without-wallbox", values)

    def test_restart_keeps_committed_wallbox_day_and_common_baseline(self):
        engine = self.covered_day(ac=True)
        self.advance_balances(engine)
        restarted = self.engine(ac=True)
        self.advance_balances(restarted, energy=1005, pv1=114)
        values = restarted.state.fresh_values(3820)
        self.assertEqual(Decimal(values["wallbox/daily-consumption"]), 5)
        self.assertEqual(Decimal(values["house/daily-consumption-without-wallbox"]), 13)

    def test_both_daily_values_wait_for_durable_checkpoint(self):
        engine = self.engine(ac=True, env={"SMAB_PLANT_CHECKPOINT_INTERVAL_SECONDS": "300"})
        engine.refresh(100, self.wall)
        self.fill(engine, 220)
        engine.refresh(220, self.wall + timedelta(minutes=2))
        self.fill(engine, 221, {"inverter1": {"totalyield": 102}}, energy=1001)
        engine.refresh(221, self.wall + timedelta(minutes=2, seconds=1))
        values = engine.state.fresh_values(221)
        self.assertEqual(values["wallbox/daily-consumption"], "0")
        self.assertEqual(values["house/daily-consumption-without-wallbox"], "0")
        self.fill(engine, 520, {"inverter1": {"totalyield": 102}}, energy=1001)
        engine.refresh(520, self.wall + timedelta(minutes=7))
        values = engine.state.fresh_values(520)
        self.assertEqual(values["wallbox/daily-consumption"], "1")
        self.assertEqual(values["house/daily-consumption-without-wallbox"], "1")

    def test_wallbox_age_skew_blocks_only_the_combined_day(self):
        engine = self.engine(ac=True, env={"SMAB_PLANT_MAX_SKEW_SECONDS": "1"})
        engine.refresh(100, self.wall)
        self.fill(engine, 220)
        engine.refresh(220, self.wall + timedelta(minutes=2))
        self.fill(engine, 230)
        engine.sources["api"].values["measurements/total-energy"] = ("1000", 220)
        engine.refresh(230, self.wall + timedelta(minutes=2, seconds=10))
        values = engine.state.fresh_values(230)
        self.assertIn("wallbox/daily-consumption", values)
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
        values = engine.state.fresh_values(280)
        self.assertEqual(values["diagnostics/wallbox-day-status"], "reset")
        self.assertNotIn("wallbox/daily-consumption", values)
        self.assertEqual(values["diagnostics/house-energy-status"], "complete")
        self.fill(engine, 86620, energy=2)
        engine.refresh(86620, self.wall + timedelta(days=1, minutes=2))
        values = engine.state.fresh_values(86620)
        self.assertEqual(values["diagnostics/wallbox-day-status"], "gap")
        self.assertNotIn("wallbox/daily-consumption", values)
        self.fill(engine, 172900, energy=3)
        engine.refresh(172900, self.wall + timedelta(days=2))
        self.fill(engine, 173020, energy=4)
        engine.refresh(173020, self.wall + timedelta(days=2, minutes=2))
        values = engine.state.fresh_values(173020)
        self.assertEqual(values["diagnostics/wallbox-day-status"], "complete")
        self.assertEqual(values["wallbox/daily-consumption"], "0")

    def assert_dst_wallbox_day(self, before, hours):
        self.wall = before
        engine = self.covered_day()
        now = 100 + hours * 3600
        self.fill(engine, now, energy=1004)
        engine.refresh(now, self.wall + timedelta(hours=hours))
        self.assertEqual(engine.state.fresh_values(now)["wallbox/daily-consumption"], "4")
        self.fill(engine, now + 120, energy=1005)
        engine.refresh(now + 120, self.wall + timedelta(hours=hours, minutes=2))
        self.assertEqual(engine.state.fresh_values(now + 120)["wallbox/daily-consumption"], "0")
        self.assertEqual(
            engine.state.fresh_values(now + 120)["diagnostics/wallbox-day-status"], "complete"
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
