"""Precision upgrades preserve old balances, downtime increments and durable origins."""

import copy
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from sma_mqtt_bridge.config import load_config
from sma_mqtt_bridge.energy_balances import EnergyBalances, validate_ledger
from sma_mqtt_bridge.errors import StateError
from sma_mqtt_bridge.model import Property, SampleValues, SourceState
from sma_mqtt_bridge.storage import write_state


class PrecisionTransitionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = load_config(
            {"SMAB_STATE_DIR": self.tmp.name, "SMAB_PLANT_PUBLISH_PARTIAL_DAY": "true"}
        )
        self.signature = hashlib.sha256(b"profile-fixture").hexdigest()
        self.hardware = hashlib.sha256(b"hardware-fixture").hexdigest()
        self.zone = ZoneInfo("Europe/Berlin")
        self.wall = datetime(2026, 10, 18, 12, tzinfo=timezone.utc)

    def ledger(self, precise=True, signature=None):
        return EnergyBalances(
            self.config,
            signature or self.signature,
            self.zone,
            precision_inputs={"pv"} if precise else (),
        )

    def observe(self, ledger, value, seconds=0):
        wall = self.wall + timedelta(seconds=seconds)
        return ledger.observe(
            "house", {"pv": Decimal(value)}, {"pv": Decimal(1)}, self.hardware, wall, wall
        )

    def legacy(self):
        old = self.ledger(False)
        self.observe(old, "100")
        self.observe(old, "105", 60)
        old.persist(60, force=True)
        return copy.deepcopy(old.data)

    def calibrated_reset(self):
        self.legacy()
        ledger = self.ledger()
        adjusted = ledger.precise_values({"pv": Decimal("106.123")}, {"pv": Decimal(106)})
        self.observe(ledger, str(adjusted["pv"]), 120)
        ledger.persist(120)
        self.assertEqual(self.observe(ledger, "-0.123", 121), (None, None, "reset"))
        return ledger

    def test_calibrated_reset_is_durable_once_and_idempotent_after_restart(self):
        ledger = self.calibrated_reset()
        with patch("sma_mqtt_bridge.energy_balances.write_state", wraps=write_state) as write:
            ledger.persist(121)
            self.assertEqual(write.call_count, 1)
            original = ledger.path.read_bytes()
            for seconds in (122, 123, 124):
                self.assertEqual(self.observe(ledger, "-0.123", seconds), (None, None, "reset"))
                ledger.persist(seconds)
                self.assertFalse(ledger.dirty)
                self.assertFalse(ledger.force_save)
            self.assertEqual(write.call_count, 1)
            self.assertEqual(ledger.path.read_bytes(), original)
            restarted = self.ledger()
            self.assertEqual(self.observe(restarted, "-0.123", 125), (None, None, "reset"))
            restarted.persist(125)
            self.assertFalse(restarted.dirty)
            self.assertEqual(write.call_count, 1)

    def test_repeated_calibrated_reset_keeps_failed_transition_pending(self):
        ledger = self.calibrated_reset()
        with patch(
            "sma_mqtt_bridge.energy_balances.write_state", side_effect=StateError("fixture")
        ):
            with self.assertRaises(StateError):
                ledger.persist(121)
        self.observe(ledger, "-0.123", 122)
        self.assertTrue(ledger.dirty)
        self.assertTrue(ledger.force_save)
        ledger.persist(122)
        self.assertEqual(self.ledger().data["accounts"]["house"]["totalStatus"], "reset")

    def test_transition_retains_baselines_history_and_downtime_then_counts_fine_growth(self):
        original = self.legacy()
        ledger = self.ledger()
        self.assertIsNone(ledger.data["precisionOffsets"]["pv"])
        self.assertEqual(ledger.data["accounts"], original["accounts"])
        # One kWh accumulated while the service was stopped; do not lose it.
        adjusted = ledger.precise_values({"pv": Decimal("106.123")}, {"pv": Decimal(106)})
        self.assertEqual(adjusted["pv"], 106)
        self.assertEqual(self.observe(ledger, str(adjusted["pv"]), 120)[0], 6)
        ledger.persist(120, force=True)
        backups = list(Path(self.tmp.name).glob("energy-balances.before-fine-*.json"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(json.loads(backups[0].read_text()), original)
        restarted = self.ledger()
        adjusted = restarted.precise_values({"pv": Decimal("106.128")}, {})
        self.assertEqual(self.observe(restarted, str(adjusted["pv"]), 180)[0], Decimal("6.005"))
        self.assertEqual(
            restarted.data["accounts"]["house"]["dailyBase"],
            original["accounts"]["house"]["dailyBase"],
        )
        self.assertEqual(restarted.data["precisionOffsets"], {"pv": "-0.123"})

    def test_missing_invalid_or_partial_pairs_do_not_calibrate(self):
        self.legacy()
        ledger = self.ledger()
        for pair in ({}, {"pv": Decimal(108)}):
            self.assertIsNone(ledger.precise_values({"pv": Decimal("106.123")}, pair))
            self.assertIsNone(ledger.data["precisionOffsets"]["pv"])
        ledger.persist(90, force=True)
        self.assertIsNone(self.ledger().data["precisionOffsets"]["pv"])
        self.assertTrue(self.ledger(False).binding_changed)
        self.assertTrue(
            self.ledger(signature=hashlib.sha256(b"changed").hexdigest()).binding_changed
        )

    def test_fresh_state_has_no_artificial_origin_and_failed_write_keeps_backup(self):
        fresh = self.ledger()
        self.assertEqual(
            fresh.precise_values({"pv": Decimal("100.123")}, {})["pv"], Decimal("100.123")
        )
        self.legacy()
        ledger = self.ledger()
        ledger.precise_values({"pv": Decimal("105.2")}, {"pv": Decimal(105)})
        with patch(
            "sma_mqtt_bridge.energy_balances.write_state", side_effect=StateError("fixture")
        ):
            with self.assertRaises(StateError):
                ledger.persist(90, force=True)
        self.assertIsNotNone(ledger.precision_backup)
        self.assertEqual(json.loads(ledger.path.read_text())["schemaVersion"], 1)

    def test_schema_rejects_nonfinite_or_unbounded_origin(self):
        data = self.ledger().data
        for value in ("NaN", "Infinity", "1.001", True, {}, "-2"):
            modified = copy.deepcopy(data)
            modified["precisionOffsets"]["pv"] = value
            with self.assertRaises(StateError):
                validate_ledger(modified)

    def test_pairs_remain_internal_same_sample_and_invalid_updates_clear_them(self):
        state = SourceState(
            "fixture",
            "fixture",
            (Property("measurements", "total-yield", "Yield", unit="kWh", channel_group="basic"),),
            60,
        )
        values = SampleValues({"measurements/total-yield": Decimal("100.2")}, {})
        values.legacy_counters = {"measurements/total-yield": Decimal(100)}
        state.update(values, now=10)
        self.assertEqual(state.legacy_counters["measurements/total-yield"], (Decimal(100), 10))
        state.update({}, now=11)
        self.assertEqual(len(state.legacy_counters), 1)
        state.update({"measurements/total-yield": None}, now=12)
        self.assertEqual(state.legacy_counters, {})

    def test_midnight_rollover_and_real_counter_reset_remain_visible(self):
        self.wall = datetime(2026, 10, 18, 21, 59, 30, tzinfo=timezone.utc)
        self.legacy()
        ledger = self.ledger()
        values = ledger.precise_values({"pv": Decimal("106.123")}, {"pv": Decimal(106)})
        self.observe(ledger, str(values["pv"]), 120)
        ledger.persist(120, force=True)
        restarted = self.ledger()
        values = restarted.precise_values({"pv": Decimal("106.623")}, {})
        result = self.observe(restarted, str(values["pv"]), 86460)
        self.assertEqual(result[2], "gap")
        values = restarted.precise_values({"pv": Decimal("10.123")}, {})
        self.assertEqual(self.observe(restarted, str(values["pv"]), 86520)[2], "reset")
        values = restarted.precise_values({"pv": Decimal(0)}, {})
        self.assertEqual(self.observe(restarted, str(values["pv"]), 86580)[2], "reset")
        validate_ledger(restarted.data)


class StandardPrecisionReaderTests(unittest.IsolatedAsyncioTestCase):
    async def test_legacy_pair_comes_from_same_identity_verified_block_without_discovery(self):
        from unittest.mock import AsyncMock, MagicMock

        from sma_mqtt_bridge.adapters.modbus import ModbusReader
        from sma_mqtt_bridge.config import Inverter
        from sma_mqtt_bridge.homie import discovery
        from sma_mqtt_bridge.profiles import load_profile

        with tempfile.TemporaryDirectory() as directory:
            profile = load_profile("sma-stp8-0-3av-40", directory, require_validated=True)
        reader = ModbusReader(Inverter(expected_serial="123"), profile)
        total = next(p for p in reader.definitions if p["id"] == "total-yield")
        reader.definitions = [total]
        reader.pollers = [p for p in profile["pollers"] if p["id"] == "yield"]
        block = [0] * 40
        block[:4] = [0, 0, 1, 34587]  # 100123 Wh.
        block[18:20] = [0, 100]
        identity = [0, 9347, 0, 0, 0, 123, 0x0410, 0x0A04]
        writer = MagicMock()
        writer.wait_closed = AsyncMock()
        with (
            patch("asyncio.open_connection", AsyncMock(return_value=(object(), writer))),
            patch.object(reader, "read_block", AsyncMock(side_effect=[identity, block])) as read,
        ):
            result = await reader.read()
        self.assertEqual(read.await_count, 2)
        self.assertEqual(result["measurements/total-yield"], Decimal("100.123"))
        self.assertEqual(result.legacy_counters, {"measurements/total-yield": Decimal(100)})
        topics = discovery("homie", "fixture", reader.properties)
        self.assertFalse(any("precise" in key for key in topics))
        self.assertEqual(topics["homie/fixture/measurements/totalyield/$datatype"], "float")
        self.assertTrue(reader.identity_fingerprint)


class PrecisionPlantUpgradeTests(unittest.TestCase):
    def test_deployed_parallel_ledger_upgrades_without_changing_house_balance(self):
        from dataclasses import replace

        from sma_mqtt_bridge.energy_profile_compat import without_standard_precision
        from sma_mqtt_bridge.plant import PlantEngine, plant_plan
        from sma_mqtt_bridge.runtime import sources
        from tests.test_plant import PlantFixture

        fixture = PlantFixture()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        config = load_config(fixture.env | {"SMAB_PLANT_PUBLISH_PARTIAL_DAY": "true"})
        profiles = copy.deepcopy(config.profiles)
        for key, profile in profiles.items():
            for prop in profile["properties"]:
                prop.pop("invalidAsZero", None)
                prop.pop("invalidAsZeroWhen", None)
            profiles[key] = without_standard_precision(profile)
        old_config = replace(config, profiles=profiles)
        self.assertEqual(plant_plan(old_config)[3], plant_plan(config)[3])

        def engine(settings):
            states = [state for state, _, _ in sources(settings)]
            for state in states:
                state.identity_fingerprint = hashlib.sha256(
                    (state.id + "-fixture").encode()
                ).hexdigest()
            result = PlantEngine(settings, states)
            fixture.fill(result, 100)
            return result

        old = engine(old_config)
        old.refresh(100, fixture.wall)
        fixture.fill(old, 110, {"inverter1": {"totalyield": 101}})
        old.refresh(110, fixture.wall + timedelta(seconds=10))
        old.ledger.persist(110, force=True)
        accounts = copy.deepcopy(old.ledger.data["accounts"])
        self.assertEqual(old.ledger.data["schemaVersion"], 1)
        upgraded = engine(config)
        fixture.fill(
            upgraded,
            120,
            {
                "inverter1": {"totalyield": Decimal("101.123")},
                "inverter3": {"totalyield": Decimal("200.4")},
            },
        )
        for source, coarse in (("inverter1", 101), ("inverter3", 200)):
            state = upgraded.sources[source]
            value = Decimal(state.values["measurements/total-yield"][0])
            sample = SampleValues({"measurements/total-yield": value}, {})
            sample.legacy_counters = {"measurements/total-yield": Decimal(coarse)}
            state.update(sample, now=120)
        upgraded.refresh(120, fixture.wall + timedelta(seconds=20))
        record = upgraded.ledger.data["accounts"]["house"]
        self.assertFalse(upgraded.ledger.binding_changed)
        self.assertEqual(Decimal(record["dailyValue"]), Decimal(accounts["house"]["dailyValue"]))
        self.assertEqual(record["dailyBase"], accounts["house"]["dailyBase"])
        self.assertEqual(
            upgraded.ledger.data["precisionOffsets"],
            {
                "inverter1/measurements/total-yield": "-0.123",
                "inverter3/measurements/total-yield": "-0.4",
            },
        )
        restarted = PlantEngine(config, list(upgraded.sources.values()))
        self.assertFalse(restarted.ledger.binding_changed)
        self.assertEqual(restarted.ledger.data["accounts"], upgraded.ledger.data["accounts"])
