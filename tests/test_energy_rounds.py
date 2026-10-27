"""Counter confirmation waits for every contributor, never an interim high-water mark."""

from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from test_plant import PlantFixture

from sma_mqtt_bridge.errors import ConfigError
from sma_mqtt_bridge.model import SampleValues
from sma_mqtt_bridge.plant_cycles import CounterReadCadence
from sma_mqtt_bridge.runtime import sources


class EnergyRoundTests(PlantFixture):
    def prepared(self, extra=None):
        engine = self.engine(
            ac=True, env={"SMAB_PLANT_PUBLISH_PARTIAL_DAY": "true"} | (extra or {})
        )
        readers = [(engine.sources[s.id], r, interval) for s, r, interval in sources(engine.config)]
        engine.configure_reads(readers, now=100)
        inputs = [(m["totalyield"], 1) for m in engine.groups["pv"]]
        inputs += [(engine.grid["energyimport"], 1), (engine.grid["energyexport"], -1)]
        for m in engine.groups["battery"]:
            inputs += [(m["batterydischargeenergy"], 1), (m["batterychargeenergy"], -1)]
        if engine.wallbox is not None:
            engine.sources["api"].update({"measurements/total-energy": 1000}, now=100)
        engine.account("house", inputs, 100, self.wall)
        return engine, inputs

    def update(self, engine, source, now, values):
        packet = SampleValues(values, {key: now for key in values})
        state = engine.sources[source]
        state.update(packet, now=now)
        with patch("sma_mqtt_bridge.plant.time.monotonic", return_value=now):
            engine.observe_source(state, packet)

    def counters(self, engine, now, roof=100.020, charge=0.014, skip=()):
        for source in engine.sources.values():
            if source.id in skip:
                continue
            values = {
                ref.key: source.values[ref.key][0]
                for ref, unit in engine.expected_units.items()
                if ref.source == source.id and unit == "kWh"
            }
            if source.id == "inverter1":
                values[engine.groups["pv"][0]["totalyield"].key] = Decimal(str(roof))
            if source.id == "inverter2":
                key = engine.groups["battery"][0]["batterychargeenergy"].key
                values[key] = Decimal(source.values[key][0]) + Decimal(str(charge))
            if values:
                self.update(engine, source.id, now, values)

    def test_pv_answer_cannot_confirm_before_battery_answer(self):
        engine, inputs = self.prepared()
        before = engine.ledger.data["accounts"]["house"]["dailyValue"]
        ref = engine.groups["pv"][0]["totalyield"]
        self.update(engine, ref.source, 280.1, {ref.key: Decimal("100.020")})
        result = engine.account("house", inputs, 280.1, self.wall + timedelta(seconds=180.1))
        self.assertIn(result[2], ("unavailable", "synchronizing", "partial"))
        self.assertEqual(engine.ledger.data["accounts"]["house"]["dailyValue"], before)
        self.counters(engine, 280.2)
        daily, _, status, _ = engine.account(
            "house", inputs, 280.2, self.wall + timedelta(seconds=180.2)
        )
        self.assertEqual(daily, Decimal("0.006"))
        self.assertEqual(status, "partial")

    def test_real_counter_reset_is_not_hidden_by_pending_round(self):
        engine, inputs = self.prepared()
        ref = engine.groups["pv"][0]["totalyield"]
        self.update(engine, ref.source, 101, {ref.key: 1})
        self.assertEqual(
            engine.account("house", inputs, 101, self.wall + timedelta(seconds=1))[2],
            "reset",
        )

    def test_source_failure_blocks_saved_round_and_recovery_needs_complete_round(self):
        engine, inputs = self.prepared()
        engine.sources["inverter1"].error = "offline"
        self.assertEqual(engine.account("house", inputs, 101, self.wall)[2], "unavailable")
        self.assertEqual(engine.ledger.data["accounts"]["house"]["dailyValue"], "0")
        engine.energy_cycles["house"].observe(engine.sources["inverter1"], None, 101)
        engine.sources["inverter1"].error = False
        self.counters(engine, 280.2)
        self.assertEqual(
            engine.account("house", inputs, 280.2, self.wall + timedelta(seconds=180.2))[0],
            Decimal("0.006"),
        )

    def test_previous_day_snapshot_cannot_start_new_day(self):
        engine, inputs = self.prepared()
        next_day = self.wall.replace(hour=0) + timedelta(days=1)
        self.assertEqual(engine.account("house", inputs, 101, next_day)[2], "synchronizing")
        self.assertEqual(
            engine.ledger.data["accounts"]["house"]["date"], self.wall.date().isoformat()
        )

    def test_wallbox_reply_is_part_of_house_without_wallbox_round(self):
        engine, inputs = self.prepared(
            {
                "SMAB_ECHARGER_ENABLED": "true",
                "SMAB_ECHARGER_HOST": "wallbox.invalid",
                "SMAB_ECHARGER_USERNAME": "fixture",
                "SMAB_ECHARGER_PASSWORD": "fixture",
                "SMAB_ECHARGER_EXPECTED_SERIAL": "987654321",
            }
        )
        inputs = [*inputs, (engine.wallbox, -1)]
        engine.account("housewithoutwallbox", inputs, 100, self.wall)
        self.counters(engine, 280.1, charge=0, skip=("api",))
        engine.account("housewithoutwallbox", inputs, 280.1, self.wall + timedelta(seconds=180.1))
        self.assertEqual(engine.ledger.data["accounts"]["housewithoutwallbox"]["dailyValue"], "0")
        self.update(engine, "api", 280.3, {"measurements/total-energy": Decimal("1000.015625")})
        daily, _, _, _ = engine.account(
            "housewithoutwallbox", inputs, 280.3, self.wall + timedelta(seconds=180.3)
        )
        self.assertEqual(daily, Decimal("0.004375"))

    def test_snapshot_does_not_renew_its_sample_time(self):
        engine, inputs = self.prepared()
        initial = engine.ledger.data["accounts"]["house"]["lastTime"]
        for now in (101, 102, 103):
            engine.account("house", inputs, now, self.wall + timedelta(seconds=now - 100))
            self.assertEqual(engine.ledger.data["accounts"]["house"]["lastTime"], initial)

    def test_expired_snapshot_cannot_be_published_as_a_current_value(self):
        engine, inputs = self.prepared()
        result = engine.account("house", inputs, 500, self.wall + timedelta(seconds=400))
        self.assertIsNone(result[0])
        self.assertIn(result[2], ("unavailable", "synchronizing"))

    def test_existing_high_water_mark_is_not_lowered_to_new_round(self):
        engine, inputs = self.prepared()
        record = engine.ledger.data["accounts"]["house"]
        record["dailyValue"] = "0.020"
        self.counters(engine, 280.2)
        engine.account("house", inputs, 280.2, self.wall + timedelta(seconds=180.2))
        self.assertEqual(record["dailyValue"], "0.020")

    def test_energy_round_rejects_large_receipt_spread(self):
        engine, inputs = self.prepared()
        self.counters(engine, 280.1, skip=("inverter1",))
        ref = engine.groups["pv"][0]["totalyield"]
        self.update(engine, ref.source, 300, {ref.key: Decimal("100.020")})
        result = engine.account("house", inputs, 300, self.wall + timedelta(seconds=200))
        self.assertEqual(result[2], "unavailable")
        self.assertEqual(engine.ledger.data["accounts"]["house"]["dailyValue"], "0")

    def test_independent_counter_cadence_skips_missed_slots_without_drift(self):
        cadence = CounterReadCadence(100, 60, 10)
        self.assertEqual(cadence.delay(100), 5)
        self.assertEqual(cadence.delay(107), 58)
        self.assertEqual(cadence.delay(166), 59)
        self.assertEqual(cadence.delay(230), 55)

    def test_counter_collection_limit_is_validated(self):
        for value in ("0", "-1", "61"):
            with self.subTest(value=value), self.assertRaises(ConfigError):
                self.prepared({"SMAB_PLANT_ENERGY_MAX_SKEW_SECONDS": value})

    def test_modbus_home_manager_uses_profile_counter_intervals(self):
        engine, _ = self.prepared(
            {
                "SMAB_HOME_MANAGER_TRANSPORT": "modbus-tcp",
                "SMAB_HOME_MANAGER_HOST": "manager.invalid",
            }
        )
        self.assertEqual(engine.energy_intervals[engine.grid["energyimport"]], 60)
        self.assertEqual(engine.energy_intervals[engine.grid["energyexport"]], 60)

    def test_confirmed_counter_bridges_member_expiry_without_retiming(self):
        engine, inputs = self.prepared()
        record = engine.ledger.data["accounts"]["house"]
        original = record.copy()
        # Current sources keep reporting; the accepted round itself stays at t=100.
        self.fill(engine, 220)
        daily, _, status, age = engine.account(
            "house", inputs, 230, self.wall + timedelta(seconds=130)
        )
        self.assertEqual(daily, Decimal("0"))
        self.assertEqual(status, "partial")
        self.assertEqual(age[0], 100)
        self.assertEqual(age[1], 250)
        self.assertEqual(record, original)

    def test_confirmed_counter_hold_ends_at_next_round_collection_deadline(self):
        engine, inputs = self.prepared()
        self.fill(engine, 280)
        self.assertIsNotNone(
            engine.account("house", inputs, 289, self.wall + timedelta(seconds=189))[0]
        )
        self.assertEqual(
            engine.account("house", inputs, 290, self.wall + timedelta(seconds=190))[2],
            "unavailable",
        )

    def test_current_stale_input_still_blocks_confirmed_counter(self):
        engine, inputs = self.prepared()
        self.assertEqual(
            engine.account("house", inputs, 230, self.wall + timedelta(seconds=130))[2],
            "unavailable",
        )

    def test_publication_keeps_original_confirmed_time_across_member_expiry(self):
        engine, _ = self.prepared()
        self.fill(engine, 220)
        engine.refresh(230, self.wall + timedelta(seconds=130))
        key = "house/daily-consumption"
        self.assertEqual(engine.state.fresh_values(230)[key], "0")
        self.assertEqual(engine.state.values[key][1], 100)
        self.assertEqual(engine.state.deadlines[key], 250)
