"""Tariff aggregation and durable seven-calendar-day averages without live I/O."""

import asyncio
import copy
import json
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock, patch

import test_wallbox_daily
from test_plant import PlantFixture
from test_runtime import FakeClient

from sma_mqtt_bridge.config import load_config
from sma_mqtt_bridge.energy_balances import EnergyBalances, validate_ledger
from sma_mqtt_bridge.errors import ConfigError, StateError
from sma_mqtt_bridge.homie import HomiePublisher, discovery


class RemunerationTests(PlantFixture):
    def test_weighted_total_yields_currency_and_invalid_member(self):
        engine = self.engine(
            env={
                "SMAB_INVERTER1_YIELD_TARIFF_PER_KWH": "0.12",
                "SMAB_INVERTER3_YIELD_TARIFF_PER_KWH": "0.08",
                "SMAB_INVERTER2_YIELD_TARIFF_PER_KWH": "99",
                "SMAB_PLANT_CURRENCY": "CHF",
            }
        )
        engine.refresh(100, self.wall)
        self.assertEqual(Decimal(engine.state.fresh_values(100)["pv/total-earnings"]), Decimal(28))
        metadata = discovery("homie", "sma-plant", engine.state.properties)
        self.assertEqual(metadata["homie/sma-plant/pv/totalearnings/$unit"], "CHF")
        self.assertEqual(metadata["homie/sma-plant/pv/totalearnings/$settable"], "false")
        ref = engine.groups["pv"][1]["totalyield"]
        engine.sources[ref.source].update({ref.key: None}, now=101)
        engine.refresh(101, self.wall + timedelta(seconds=1))
        self.assertNotIn("pv/total-earnings", engine.state.fresh_values(101))

    def test_default_zero_single_pv_and_tariffs_do_not_rebase(self):
        engine = self.engine(
            env={"SMAB_INVERTER3_ENABLED": "false", "SMAB_INVERTER1_YIELD_TARIFF_PER_KWH": "0"}
        )
        engine.refresh(100, self.wall)
        self.assertEqual(Decimal(engine.state.fresh_values(100)["pv/total-earnings"]), 0)
        changed = self.engine(
            env={
                "SMAB_INVERTER3_ENABLED": "false",
                "SMAB_INVERTER1_YIELD_TARIFF_PER_KWH": "0.5",
            }
        )
        self.assertFalse(changed.ledger.binding_changed)
        changed.refresh(100, self.wall)
        self.assertEqual(Decimal(changed.state.fresh_values(100)["pv/total-earnings"]), 50)

    def test_no_explicit_pv_tariff_has_no_metadata_or_values(self):
        for env in (
            {},
            {"SMAB_INVERTER2_YIELD_TARIFF_PER_KWH": "1"},
            {
                "SMAB_INVERTER3_ENABLED": "false",
                "SMAB_INVERTER3_YIELD_TARIFF_PER_KWH": "1",
            },
        ):
            with self.subTest(env=env):
                engine = self.engine(env=env)
                engine.refresh(100, self.wall)
                self.assertNotIn("pv/total-earnings", engine.state.property_index())
                self.assertNotIn("pv/total-earnings", engine.state.fresh_values(100))
                self.assertFalse(
                    any(
                        "totalearnings" in key
                        for key in discovery("homie", "sma-plant", engine.state.properties)
                    )
                )

    def test_unconfigured_pv_counter_does_not_block_configured_contributor(self):
        engine = self.engine(env={"SMAB_INVERTER1_YIELD_TARIFF_PER_KWH": "0.12"})
        ref = engine.groups["pv"][1]["totalyield"]
        engine.sources[ref.source].update({ref.key: None}, now=100)
        engine.refresh(100, self.wall)
        self.assertEqual(Decimal(engine.state.fresh_values(100)["pv/total-earnings"]), 12)
        configured_ref = engine.groups["pv"][0]["totalyield"]
        engine.sources[configured_ref.source].update({configured_ref.key: None}, now=101)
        engine.refresh(101, self.wall + timedelta(seconds=1))
        self.assertNotIn("pv/total-earnings", engine.state.fresh_values(101))

    def test_json_tariff_and_environment_zero_override(self):
        path = Path(self.directory.name) / "tariff-config.json"
        path.write_text(json.dumps({"inverters": [{"id": "inverter1", "yieldTariffPerKwh": 0.25}]}))
        engine = self.engine(env={"SMAB_CONFIG_FILE": str(path)})
        engine.refresh(100, self.wall)
        self.assertEqual(Decimal(engine.state.fresh_values(100)["pv/total-earnings"]), 25)
        overridden = self.engine(
            env={"SMAB_CONFIG_FILE": str(path), "SMAB_INVERTER1_YIELD_TARIFF_PER_KWH": "0"}
        )
        self.assertFalse(overridden.ledger.binding_changed)
        overridden.refresh(100, self.wall)
        self.assertEqual(Decimal(overridden.state.fresh_values(100)["pv/total-earnings"]), 0)

    def test_invalid_configuration(self):
        for value in ("-1", "NaN", "Infinity"):
            with self.subTest(value=value), self.assertRaises(ConfigError):
                load_config({"SMAB_INVERTER1_YIELD_TARIFF_PER_KWH": value})
        for value in ("", " ", "x" * 17, "€\n"):
            with self.subTest(value=value), self.assertRaises(ConfigError):
                load_config({"SMAB_PLANT_CURRENCY": value})
        self.assertEqual(load_config({}).plant.currency, "€")


class StatisticsTests(PlantFixture):
    def observe_house(self, engine, wall, value, *, name="house", wallbox=0):
        values = {"house": Decimal(value)}
        signs = {"house": Decimal(1)}
        if name == "housewithoutwallbox":
            values["wallbox"] = Decimal(wallbox)
            signs["wallbox"] = Decimal(-1)
        return engine.ledger.observe(name, values, signs, "0" * 64, wall, wall, daily_only=True)

    def collect(self, engine, start, *, gap=False, name="house"):
        # Pre-boundary and boundary snapshots avoid inventing midnight interpolation.
        value = 100
        self.observe_house(engine, start - timedelta(seconds=30), value, name=name)
        self.observe_house(engine, start, value, name=name)
        for day in range(7):
            value += 10 + day
            end = start + timedelta(days=day + 1)
            if not (gap and day == 3):
                self.observe_house(engine, end - timedelta(seconds=30), value, name=name)
            self.observe_house(engine, end, value, name=name)
        return start + timedelta(days=7)

    def test_seven_days_restart_and_missing_day(self):
        engine = self.engine(ac=True)
        start = datetime(2026, 10, 20, tzinfo=engine.zone)
        end = self.collect(engine, start)
        engine.ledger.persist(100, force=True)
        packet = {}
        engine.update_averages(packet, end)
        self.assertEqual(packet["house/average-daily-consumption"], 13)
        self.assertEqual(packet["diagnostics/average-day-status"], "complete")
        restarted = self.engine(ac=True)
        restarted.update_averages(packet, end)
        self.assertEqual(packet["house/average-daily-consumption"], 13)
        history = restarted.ledger.committed["house"]["history"]
        self.assertEqual(len(history), 7)
        del history[next(iter(history))]
        restarted.update_averages(packet, end)
        self.assertIsNone(packet["house/average-daily-consumption"])
        restarted.update_averages(packet, end + timedelta(days=1))
        self.assertIsNone(packet["house/average-daily-consumption"])

    def test_gap_partial_and_failed_checkpoint_do_not_make_average(self):
        engine = self.engine(ac=True)
        end = self.collect(engine, datetime(2026, 10, 14, 22, tzinfo=timezone.utc), gap=True)
        engine.ledger.persist(100, force=True)
        packet = {}
        engine.update_averages(packet, end)
        self.assertIsNone(packet["house/average-daily-consumption"])
        self.assertEqual(len(engine.ledger.committed["house"]["history"]), 5)
        engine.ledger.committed.clear()
        engine.ledger.dirty = True
        with patch("sma_mqtt_bridge.energy_balances.write_state", side_effect=OSError("fixture")):
            with self.assertRaises(OSError):
                engine.ledger.persist(200, force=True)
        engine.update_averages(packet, end)
        self.assertIsNone(packet["house/average-daily-consumption"])

    def test_dst_full_calendar_days_and_history_validation(self):
        for start in (datetime(2026, 10, 23), datetime(2026, 3, 27)):
            with self.subTest(start=start):
                engine = self.engine(ac=True)
                engine.ledger.data["accounts"].clear()
                start = start.replace(tzinfo=engine.zone)
                end = self.collect(engine, start)
                engine.ledger.persist(100, force=True)
                packet = {}
                engine.update_averages(packet, end)
                self.assertEqual(packet["house/average-daily-consumption"], 13)
                data = copy.deepcopy(engine.ledger.data)
                data["accounts"]["house"]["history"][end.date().isoformat()] = "NaN"
                with self.assertRaises(StateError):
                    validate_ledger(data)

    def test_runtime_publishes_committed_history_only(self):
        engine = self.engine(ac=True)
        engine.refresh(100, self.wall)
        today = self.wall.astimezone(engine.zone).date()
        history = {(today - timedelta(days=i)).isoformat(): str(i) for i in range(1, 8)}
        engine.ledger.data["accounts"]["house"]["history"] = history
        engine.ledger.dirty = True
        self.fill(engine, 102)
        engine.refresh(102, self.wall + timedelta(seconds=2))
        self.assertEqual(engine.state.fresh_values(102)["house/average-daily-consumption"], "4")
        self.assertIn(
            "house/averagedailyconsumption",
            engine.state.fresh_values(102)["diagnostics/valid-properties"],
        )
        history[next(iter(history))] = "70"
        engine.ledger.dirty = True
        engine.ledger.last_save = 102
        self.fill(engine, 102.5)
        engine.refresh(102.5, self.wall + timedelta(seconds=2.5))
        self.assertEqual(engine.state.fresh_values(102.5)["house/average-daily-consumption"], "4")

    def test_reset_and_configuration_mismatch(self):
        engine = self.engine(ac=True)
        end = self.collect(engine, datetime(2026, 10, 14, 22, tzinfo=timezone.utc))
        engine.ledger.persist(100, force=True)
        engine.ledger.binding_changed = True
        packet = {}
        engine.update_averages(packet, end)
        self.assertIsNone(packet["house/average-daily-consumption"])
        engine.ledger.binding_changed = False
        self.observe_house(engine, end + timedelta(hours=1), 1)
        next_day = end + timedelta(days=1)
        self.observe_house(engine, next_day - timedelta(seconds=30), 2)
        self.observe_house(engine, next_day, 2)
        engine.ledger.persist(200, force=True)
        engine.update_averages(packet, next_day)
        self.assertIsNone(packet["house/average-daily-consumption"])
        # Old ledgers without history remain readable and keep their baselines.
        engine.ledger.data["accounts"]["house"].pop("history")
        validate_ledger(engine.ledger.data)
        self.assertFalse(
            EnergyBalances(
                engine.config, engine.ledger.data["signature"], engine.zone
            ).binding_changed
        )


class WallboxStatisticsTests(PlantFixture):
    def test_wallbox_subtraction_keeps_charging_days_and_plant_ownership(self):
        fixture = test_wallbox_daily.WallboxDailyTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        engine = fixture.engine(ac=True)
        start = datetime(2026, 10, 14, 22, tzinfo=timezone.utc)
        helper = StatisticsTests()
        for name in ("house", "housewithoutwallbox"):
            helper.observe_house(engine, start - timedelta(seconds=30), 100, name=name)
            helper.observe_house(engine, start, 100, name=name)
            for day in range(1, 8):
                end = start + timedelta(days=day)
                for wall in (end - timedelta(seconds=30), end):
                    helper.observe_house(engine, wall, 100 + day * 10, name=name, wallbox=day * 4)
        engine.ledger.persist(100, force=True)
        packet = {}
        engine.update_averages(packet, end)
        self.assertEqual(packet["house/average-daily-consumption"], 10)
        self.assertEqual(packet["house/average-daily-consumption-without-wallbox"], 6)
        self.assertFalse(any("average" in p.key for p in engine.wallbox_state.properties))
        self.assertEqual(
            engine.state.property_index()["house/average-daily-consumption"].unit, "kWh/d"
        )


class TariffRetirementTests(unittest.IsolatedAsyncioTestCase):
    async def test_removing_tariff_retires_old_retained_channel(self):
        fixture = RemunerationTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        before = fixture.engine(env={"SMAB_INVERTER1_YIELD_TARIFF_PER_KWH": "0.1"})
        before.refresh(100, fixture.wall)
        saved = before.ledger.path.read_bytes()
        engine = fixture.engine()
        old = {
            key
            for key in discovery("homie", "sma-plant", before.state.properties)
            if "/totalearnings/" in key
        }
        old.add("homie/sma-plant/pv/totalearnings")
        clients = []

        def factory(*args, **kwargs):
            client = FakeClient(*args, **kwargs)
            clients.append(client)
            return client

        publisher = HomiePublisher(
            engine.config, [*engine.sources.values(), *engine.output_states], factory
        )
        publisher.owned = {"sma-plant": old}
        publisher.publish_values = AsyncMock()
        await publisher.serve_device("sma-plant", [engine.state], asyncio.Event())
        messages = {(topic, value) for topic, value, _ in clients[0].messages}
        for topic in old:
            self.assertIn((topic, b""), messages)
            self.assertNotIn(topic, publisher.owned["sma-plant"])
        self.assertEqual(engine.ledger.path.read_bytes(), saved)


if __name__ == "__main__":
    unittest.main()
