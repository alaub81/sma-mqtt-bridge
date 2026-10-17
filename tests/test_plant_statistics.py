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
    def test_export_counter_currency_and_invalid_input(self):
        engine = self.engine(
            env={
                "SMAB_PLANT_FEED_IN_TARIFF_PER_KWH": "0.12",
                "SMAB_INVERTER1_YIELD_TARIFF_PER_KWH": "99",
                "SMAB_INVERTER3_YIELD_TARIFF_PER_KWH": "99",
                "SMAB_PLANT_CURRENCY": "CHF",
            }
        )
        engine.refresh(100, self.wall)
        # Grid export is 60 kWh, PV production totals 300 kWh; never double count it.
        self.assertEqual(
            Decimal(engine.state.fresh_values(100)["pv/total-earnings"]), Decimal("7.2")
        )
        metadata = HomiePublisher(engine.config, [engine.state]).metadata(
            "sma-plant", HomiePublisher(engine.config, [engine.state]).properties([engine.state])
        )
        self.assertEqual(metadata["homie/sma-plant/grid/totalearnings/$unit"], "CHF")
        self.assertEqual(metadata["homie/sma-plant/grid/totalearnings/$settable"], "false")
        engine.sources["home-manager"].update({engine.grid["energyexport"].key: None}, now=101)
        engine.refresh(101, self.wall + timedelta(seconds=1))
        self.assertNotIn("pv/total-earnings", engine.state.fresh_values(101))

    def test_zero_tariff_rate_and_offset_changes_preserve_baselines(self):
        engine = self.engine(env={"SMAB_PLANT_FEED_IN_TARIFF_PER_KWH": "0"})
        engine.refresh(100, self.wall)
        before = engine.ledger.path.read_bytes()
        self.assertEqual(Decimal(engine.state.fresh_values(100)["pv/total-earnings"]), 0)
        changed = self.engine(
            env={
                "SMAB_PLANT_FEED_IN_TARIFF_PER_KWH": "0.5",
                "SMAB_HOME_MANAGER_ENERGY_EXPORT_OFFSET_KWH": "1000",
            }
        )
        self.assertFalse(changed.ledger.binding_changed)
        changed.refresh(100, self.wall)
        self.assertEqual(Decimal(changed.state.fresh_values(100)["pv/total-earnings"]), 530)
        self.assertEqual(changed.ledger.path.read_bytes(), before)
        self.assertEqual(
            changed.ledger.data["accounts"]["export"]["dailyBase"],
            {"home-manager/measurements/energy-export": "60"},
        )

    def test_omitted_common_tariff_and_legacy_tariffs_do_not_activate(self):
        for env in (
            {},
            {"SMAB_INVERTER1_YIELD_TARIFF_PER_KWH": "1"},
            {"SMAB_INVERTER3_YIELD_TARIFF_PER_KWH": "1"},
            {"SMAB_HOME_MANAGER_ENERGY_EXPORT_OFFSET_KWH": "100"},
        ):
            with self.subTest(env=env):
                engine = self.engine(env=env)
                engine.refresh(100, self.wall)
                self.assertNotIn("pv/total-earnings", engine.state.property_index())
                self.assertNotIn("pv/total-earnings", engine.state.fresh_values(100))

    def test_pv_measurements_do_not_gate_export_remuneration(self):
        engine = self.engine(env={"SMAB_PLANT_FEED_IN_TARIFF_PER_KWH": "0.12"})
        for members in engine.groups["pv"]:
            ref = members["totalyield"]
            engine.sources[ref.source].update({ref.key: None}, now=100)
            engine.sources[ref.source].error = True
        engine.refresh(100, self.wall)
        self.assertEqual(
            Decimal(engine.state.fresh_values(100)["pv/total-earnings"]), Decimal("7.2")
        )
        engine.sources["home-manager"].error = True
        engine.refresh(100, self.wall)
        self.assertNotIn("pv/total-earnings", engine.state.fresh_values(100))

    def test_json_tariff_offset_and_environment_zero_override(self):
        path = Path(self.directory.name) / "tariff-config.json"
        path.write_text(
            json.dumps(
                {
                    "plant": {"feedInTariffPerKwh": 0.25},
                    "homeManager": {"energyExportOffsetKwh": 100},
                }
            )
        )
        engine = self.engine(env={"SMAB_CONFIG_FILE": str(path)})
        engine.refresh(100, self.wall)
        self.assertEqual(Decimal(engine.state.fresh_values(100)["pv/total-earnings"]), 40)
        overridden = self.engine(
            env={
                "SMAB_CONFIG_FILE": str(path),
                "SMAB_PLANT_FEED_IN_TARIFF_PER_KWH": "0",
                "SMAB_HOME_MANAGER_ENERGY_EXPORT_OFFSET_KWH": "0",
            }
        )
        self.assertFalse(overridden.ledger.binding_changed)
        overridden.refresh(100, self.wall)
        self.assertEqual(Decimal(overridden.state.fresh_values(100)["pv/total-earnings"]), 0)

    def test_negative_stale_and_zero_export(self):
        engine = self.engine(env={"SMAB_PLANT_FEED_IN_TARIFF_PER_KWH": "0.1"})
        key = engine.grid["energyexport"].key
        for value, expected in ((0, "0"), (-1, None)):
            engine.sources["home-manager"].update({key: value}, now=100)
            engine.refresh(100, self.wall)
            actual = engine.state.fresh_values(100).get("pv/total-earnings")
            self.assertEqual(
                Decimal(actual) if actual is not None else None,
                Decimal(expected) if expected is not None else None,
            )
        self.fill(engine, 100)
        engine.refresh(100, self.wall)
        self.assertNotIn("pv/total-earnings", engine.state.fresh_values(1000))

    def test_remuneration_with_only_grid_source(self):
        engine = self.engine(
            env={
                "SMAB_INVERTER1_ENABLED": "false",
                "SMAB_INVERTER2_ENABLED": "false",
                "SMAB_INVERTER3_ENABLED": "false",
                "SMAB_PLANT_FEED_IN_TARIFF_PER_KWH": "0.1",
            }
        )
        engine.refresh(100, self.wall)
        self.assertEqual(Decimal(engine.state.fresh_values(100)["pv/total-earnings"]), 6)

    def test_invalid_configuration(self):
        for key in (
            "SMAB_PLANT_FEED_IN_TARIFF_PER_KWH",
            "SMAB_INVERTER1_YIELD_TARIFF_PER_KWH",
        ):
            for value in ("-1", "NaN", "Infinity"):
                with self.subTest(key=key, value=value), self.assertRaises(ConfigError):
                    load_config({key: value})
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
        self.assertEqual(packet["house/average-daily-consumption"], Decimal(91) / 7)
        self.assertEqual(packet["diagnostics/average-day-status"], "complete")
        restarted = self.engine(ac=True)
        restarted.update_averages(packet, end)
        self.assertEqual(packet["house/average-daily-consumption"], Decimal(91) / 7)
        history = restarted.ledger.committed["house"]["history"]
        self.assertEqual(len(history), 7)
        del history[(end.date() - timedelta(days=1)).isoformat()]
        restarted.update_averages(packet, end)
        self.assertEqual(packet["house/average-daily-consumption"], Decimal(75) / 6)
        self.assertEqual(packet["diagnostics/average-day-status"], "partial")
        restarted.update_averages(packet, end + timedelta(days=1))
        self.assertEqual(packet["house/average-daily-consumption"], Decimal(65) / 5)

    def test_gaps_are_skipped_and_failed_checkpoint_keeps_committed_average(self):
        engine = self.engine(ac=True)
        end = self.collect(engine, datetime(2026, 10, 14, 22, tzinfo=timezone.utc), gap=True)
        engine.ledger.persist(100, force=True)
        packet = {}
        engine.update_averages(packet, end)
        self.assertEqual(packet["house/average-daily-consumption"], Decimal("12.8"))
        self.assertEqual(packet["diagnostics/average-day-status"], "partial")
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
                self.assertEqual(packet["house/average-daily-consumption"], Decimal(91) / 7)
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

    def test_today_starts_immediately_and_updates_without_partial_daily_channel(self):
        engine = self.engine(ac=True)
        engine.refresh(100, self.wall)
        self.assertEqual(engine.state.fresh_values(100)["house/average-daily-consumption"], "0")
        self.assertNotIn("house/daily-consumption", engine.state.fresh_values(100))
        self.fill(engine, 102, {"inverter1": {"totalyield": 106}})
        engine.refresh(102, self.wall + timedelta(seconds=2))
        self.assertEqual(engine.state.fresh_values(102)["house/average-daily-consumption"], "6")
        today = self.wall.astimezone(engine.zone).date()
        record = engine.ledger.data["accounts"]["house"]
        record["history"] = {
            (today - timedelta(days=1)).isoformat(): "12",
            (today - timedelta(days=6)).isoformat(): "9",
            (today - timedelta(days=7)).isoformat(): "999",
        }
        engine.ledger.dirty = True
        engine.ledger.persist(104, force=True)
        packet = {}
        engine.update_averages(packet, self.wall)
        self.assertEqual(packet["house/average-daily-consumption"], 340)
        self.assertEqual(packet["diagnostics/average-day-status"], "partial")
        packet["diagnostics/house-energy-status"] = "unavailable"
        engine.update_averages(packet, self.wall)
        self.assertEqual(packet["house/average-daily-consumption"], Decimal(340))

    def test_startup_preview_then_completed_days_survive_restart_and_outage(self):
        for partial in ("true", "false"):
            with self.subTest(partial=partial):
                engine = self.engine(ac=True, env={"SMAB_PLANT_PUBLISH_PARTIAL_DAY": partial})
                engine.ledger.data["accounts"].clear()
                start = datetime(2026, 10, 20, 12, tzinfo=engine.zone)
                ref = engine.groups["pv"][0]["totalyield"].identity

                # Use the real recipe identities, with unchanged zero counters for other inputs.
                inputs = [(m["totalyield"], 1) for m in engine.groups["pv"]]
                inputs += [(engine.grid["energyimport"], 1), (engine.grid["energyexport"], -1)]
                for member in engine.groups["battery"]:
                    inputs += [
                        (member["batterydischargeenergy"], 1),
                        (member["batterychargeenergy"], -1),
                    ]
                signs = {r.identity: Decimal(sign) for r, sign in inputs}

                def step(wall, value, engine=engine, signs=signs, ref=ref):
                    counters = dict.fromkeys(signs, Decimal(0))
                    counters[ref] = Decimal(value)
                    engine.ledger.observe(
                        "house", counters, signs, "0" * 64, wall, wall, daily_only=True
                    )
                    engine.ledger.persist(100, force=True)
                    packet = {"diagnostics/house-energy-status": "unavailable"}
                    engine.update_averages(packet, wall)
                    return packet["house/average-daily-consumption"]

                self.assertEqual(step(start, 100), 0)
                midnight = start.replace(hour=0) + timedelta(days=1)
                self.assertEqual(step(midnight - timedelta(seconds=30), 114), 14)
                self.assertEqual(step(midnight, 114), 7)
                self.assertEqual(step(midnight + timedelta(hours=12), 120), 10)
                restarted = self.engine(ac=True, env={"SMAB_PLANT_PUBLISH_PARTIAL_DAY": partial})
                packet = {}
                restarted.update_averages(packet, midnight + timedelta(hours=12))
                self.assertEqual(packet["house/average-daily-consumption"], 10)
                step(midnight + timedelta(days=1, seconds=-30), 134)
                self.assertEqual(step(midnight + timedelta(days=1), 134), 20)
                self.assertEqual(step(midnight + timedelta(days=1, hours=12), 150), 20)
                step(midnight + timedelta(days=2, seconds=-30), 164)
                self.assertEqual(step(midnight + timedelta(days=2), 164), 25)
                # Without a current midnight sample, yesterday's completed history remains usable.
                packet = {"diagnostics/house-energy-status": "unavailable"}
                engine.update_averages(packet, midnight + timedelta(days=3))
                self.assertEqual(packet["house/average-daily-consumption"], 25)

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
        self.assertEqual(packet["house/average-daily-consumption"], Decimal("13.5"))
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
        self.assertEqual(packet["house/average-daily-consumption"], Decimal(70) / 7)
        self.assertEqual(packet["house/average-daily-consumption-without-wallbox"], Decimal(42) / 7)
        # The live day and temporary source outages do not change either average.
        for name in ("house", "housewithoutwallbox"):
            helper.observe_house(engine, end + timedelta(hours=1), 184, name=name, wallbox=34)
        engine.ledger.persist(200, force=True)
        engine.update_averages(packet, end + timedelta(hours=1))
        self.assertEqual(packet["house/average-daily-consumption"], Decimal(70) / 7)
        self.assertEqual(packet["house/average-daily-consumption-without-wallbox"], Decimal(42) / 7)
        self.assertFalse(any("average" in p.key for p in engine.wallbox_state.properties))
        self.assertEqual(
            engine.state.property_index()["house/average-daily-consumption"].unit, "kWh/d"
        )


class TariffRetirementTests(unittest.IsolatedAsyncioTestCase):
    async def test_removing_tariff_retires_old_retained_channel(self):
        fixture = RemunerationTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        before = fixture.engine(env={"SMAB_PLANT_FEED_IN_TARIFF_PER_KWH": "0.1"})
        before.refresh(100, fixture.wall)
        saved = before.ledger.path.read_bytes()
        engine = fixture.engine()
        old = {
            key
            for key in discovery("homie", "sma-plant", before.state.properties)
            if "/totalearnings/" in key
        }
        old.add("homie/sma-plant/pv/totalearnings")
        old.add("homie/sma-plant/grid/totalearnings")
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
