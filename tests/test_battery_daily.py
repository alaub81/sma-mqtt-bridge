"""Battery day accounts share durable accounting without changing existing baselines."""

import copy
import json
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from test_plant import PlantFixture

from sma_mqtt_bridge.energy_balances import validate_ledger
from sma_mqtt_bridge.errors import StateError
from sma_mqtt_bridge.homie import wire_key
from sma_mqtt_bridge.runtime import sources
from sma_mqtt_bridge.translation import load_translation

CHARGE = "battery/daily-charge-energy"
DISCHARGE = "battery/daily-discharge-energy"


class BatteryDailyTests(PlantFixture):
    def prepared(self, extra=None):
        engine = self.engine(env={"SMAB_PLANT_PUBLISH_PARTIAL_DAY": "true"} | (extra or {}))
        engine.refresh(100, self.wall)
        return engine

    def advance(self, engine, now=102, charge="42.125", discharge="31.25"):
        self.fill(
            engine,
            now,
            {
                "inverter2": {
                    "batterychargeenergy": Decimal(charge),
                    "batterydischargeenergy": Decimal(discharge),
                }
            },
        )
        engine.refresh(now, self.wall + timedelta(seconds=now - 100))
        return engine.state.fresh_values(now)

    def test_metadata_translations_and_single_battery_wire_names(self):
        engine = self.prepared()
        for key, name, german in (
            (CHARGE, "Daily battery charge energy", "Batterie-Tagesladung"),
            (DISCHARGE, "Daily battery discharge energy", "Batterie-Tagesentladung"),
        ):
            prop = engine.state.property_index()[key]
            self.assertEqual(wire_key(key), key.replace("-", ""))
            self.assertEqual(
                (prop.name, prop.unit, prop.settable, prop.channel_group),
                (name, "kWh", False, "basic"),
            )
            self.assertEqual(load_translation("de", self.directory.name)[name], german)
            self.assertEqual(load_translation("en", self.directory.name)[name], name)

    def test_independent_directions_and_restart(self):
        engine = self.prepared()
        values = self.advance(engine)
        self.assertEqual(Decimal(values[CHARGE]), Decimal("2.125"))
        self.assertEqual(Decimal(values[DISCHARGE]), Decimal("1.25"))
        self.assertEqual(values["diagnostics/batterycharge-day-status"], "partial")
        saved = copy.deepcopy(engine.ledger.data)
        restarted = self.engine(env={"SMAB_PLANT_PUBLISH_PARTIAL_DAY": "true"})
        self.assertFalse(restarted.ledger.binding_changed)
        self.assertEqual(restarted.ledger.data, saved)
        values = self.advance(restarted, 104, "43.5", "32")
        self.assertEqual(Decimal(values[CHARGE]), Decimal("3.5"))
        self.assertEqual(Decimal(values[DISCHARGE]), Decimal("2"))

    def test_old_accounts_preserved_when_new_accounts_are_added(self):
        engine = self.prepared()
        old = copy.deepcopy(engine.ledger.data)
        for name in engine.battery_accounts:
            old["accounts"].pop(name)
        engine.ledger.path.write_text(json.dumps(old))
        restarted = self.prepared()
        self.assertFalse(restarted.ledger.binding_changed)
        self.assertEqual(restarted.ledger.data["signature"], old["signature"])
        for name, record in old["accounts"].items():
            self.assertEqual(restarted.ledger.data["accounts"][name], record)
        self.assertEqual(validate_ledger(restarted.ledger.data), restarted.ledger.data)
        bad = copy.deepcopy(old)
        bad["accounts"]["unknown"] = next(iter(old["accounts"].values()))
        with self.assertRaises(StateError):
            validate_ledger(bad)

    def test_without_battery_no_daily_channels_or_accounts(self):
        engine = self.prepared({"SMAB_INVERTER2_ROLE": "none"})
        self.assertEqual(engine.battery_accounts, {})
        self.assertNotIn(CHARGE, engine.state.property_index())
        self.assertNotIn("batterycharge", engine.ledger.data["accounts"])

    def test_two_batteries_sum_without_shrinking_on_failure(self):
        engine = self.prepared(
            {
                "SMAB_INVERTER4_ENABLED": "true",
                "SMAB_INVERTER4_HOST": "four.invalid",
                "SMAB_INVERTER4_PROFILE": "sma-sbs3-7-10",
                "SMAB_INVERTER4_ROLE": "battery",
            }
        )
        self.fill(
            engine,
            102,
            {
                "inverter2": {"batterychargeenergy": 42, "batterydischargeenergy": 31},
                "inverter4": {"batterychargeenergy": 53, "batterydischargeenergy": 24},
            },
        )
        engine.refresh(102, self.wall + timedelta(seconds=2))
        values = engine.state.fresh_values(102)
        self.assertEqual(Decimal(values[CHARGE]), 5)
        self.assertEqual(Decimal(values[DISCHARGE]), 5)
        engine.sources["inverter4"].error = "offline"
        engine.refresh(103, self.wall + timedelta(seconds=3))
        self.assertNotIn(CHARGE, engine.state.fresh_values(103))
        self.assertNotIn(DISCHARGE, engine.state.fresh_values(103))
        self.assertEqual(
            engine.state.fresh_values(103)["diagnostics/batterycharge-day-status"], "unavailable"
        )

    def test_reset_blocks_only_affected_direction_and_pv_failure_does_not_block_battery(self):
        engine = self.prepared()
        self.advance(engine)
        engine.sources["inverter1"].error = "offline"
        values = self.advance(engine, 104, "1", "32")
        self.assertNotIn(CHARGE, values)
        self.assertEqual(values["diagnostics/batterycharge-day-status"], "reset")
        self.assertEqual(Decimal(values[DISCHARGE]), 2)

    def test_midnight_and_gap_use_existing_calendar_guards(self):
        self.wall = self.wall.replace(hour=21, minute=59, second=30)
        engine = self.prepared({"SMAB_PLANT_PUBLISH_PARTIAL_DAY": "false"})
        self.assertNotIn(CHARGE, engine.state.fresh_values(100))
        values = self.advance(engine, 160)
        self.assertEqual(Decimal(values[CHARGE]), 0)
        self.assertEqual(values["diagnostics/batterycharge-day-status"], "complete")
        values = self.advance(engine, 162, "43", "32")
        self.assertEqual(Decimal(values[CHARGE]), Decimal("0.875"))
        values = self.advance(engine, 100 + 86400 + 1200, "44", "33")
        self.assertNotIn(CHARGE, values)
        self.assertEqual(values["diagnostics/batterycharge-day-status"], "gap")

    def test_uncommitted_energy_is_not_published_and_stale_inputs_expire(self):
        engine = self.prepared({"SMAB_PLANT_CHECKPOINT_INTERVAL_SECONDS": "300"})
        values = self.advance(engine)
        self.assertEqual(Decimal(values[CHARGE]), 0)
        self.assertEqual(
            Decimal(engine.ledger.data["accounts"]["batterycharge"]["dailyValue"]), Decimal("2.125")
        )
        self.assertNotIn(CHARGE, engine.state.fresh_values(10000))

    def test_coordinated_battery_round_collects_all_members(self):
        engine = self.engine(
            env={
                "SMAB_PLANT_PUBLISH_PARTIAL_DAY": "true",
                "SMAB_INVERTER4_ENABLED": "true",
                "SMAB_INVERTER4_HOST": "four.invalid",
                "SMAB_INVERTER4_PROFILE": "sma-sbs3-7-10",
                "SMAB_INVERTER4_ROLE": "battery",
            }
        )
        readers = [(engine.sources[s.id], r, i) for s, r, i in sources(engine.config)]
        engine.configure_reads(readers, now=100)
        engine.refresh(100, self.wall)
        interval = engine.energy_cycles["batterycharge"].seconds
        now = 100 + interval + 0.1
        before = copy.deepcopy(engine.ledger.data["accounts"]["batterycharge"])
        for index, member in enumerate(engine.groups["battery"]):
            ref = member["batterychargeenergy"]
            source = engine.sources[ref.source]
            packet = {ref.key: Decimal(source.values[ref.key][0]) + 2}
            source.update(packet, now=now)
            with patch("sma_mqtt_bridge.plant.time.monotonic", return_value=now):
                engine.observe_source(source, packet)
            engine.refresh(now, self.wall + timedelta(seconds=now - 100))
            if index == 0:
                self.assertEqual(engine.ledger.data["accounts"]["batterycharge"], before)
        self.assertEqual(Decimal(engine.state.fresh_values(now)[CHARGE]), 4)
