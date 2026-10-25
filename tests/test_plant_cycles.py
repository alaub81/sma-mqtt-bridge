"""Coordinated acquisitions preserve whole rounds, expiry and accounting identity."""

import asyncio
import copy
import json
import struct
import unittest
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from test_home_manager_modbus import adapter, words
from test_plant import PlantFixture

from sma_mqtt_bridge.adapters.modbus import ModbusException, ModbusReader
from sma_mqtt_bridge.config import Inverter, load_config
from sma_mqtt_bridge.errors import ConfigError, ProtocolError
from sma_mqtt_bridge.model import Property, SampleValues, SourceState
from sma_mqtt_bridge.plant import plant_plan
from sma_mqtt_bridge.plant_cycles import ReadSchedule
from sma_mqtt_bridge.runtime import sources, supervise
from tests.helpers import validated_profile


class CoordinatedPlantTests(PlantFixture):
    def coordinated(self, env=None):
        engine = self.engine(ac=True, env=env)
        readers = [(engine.sources[s.id], r, interval) for s, r, interval in sources(engine.config)]
        engine.configure_reads(readers, now=100)
        return engine, readers

    def submit(self, engine, source, now, values, cycle=0):
        packet = SampleValues(values, {key: now for key in values})
        if cycle is not None:
            packet.power_cycle = cycle
        state = engine.sources[source]
        state.update(packet, now=now)
        for group in set(engine.recipe_cycles.values()):
            group.observe(state, packet, now)
        engine.refresh(now, self.wall + timedelta(seconds=now - 100))

    def round(self, engine, start=100, cycle=0):
        for offset, source, values in (
            (0.1, "inverter1", {"measurements/active-power": 2364}),
            (0.2, "inverter3", {"measurements/active-power": 1725}),
            (
                0.3,
                "home-manager",
                {"measurements/power-import": 0, "measurements/power-export": 298},
            ),
            (
                0.4,
                "inverter2",
                {"measurements/pres-bat-charge": 3678, "measurements/pres-batt-discharge": 0},
            ),
        ):
            self.submit(engine, source, start + offset, values, cycle)

    def test_partial_round_never_publishes_mixed_battery_pv_peak(self):
        engine, _ = self.coordinated()
        # The previous 2329 W battery value would give a 1462 W intermediate peak.
        engine.sources["inverter2"].update({"measurements/pres-bat-charge": 2329}, now=100)
        self.submit(engine, "inverter1", 100.1, {"measurements/active-power": 2364})
        self.submit(engine, "inverter3", 100.2, {"measurements/active-power": 1725})
        self.submit(
            engine,
            "home-manager",
            100.3,
            {"measurements/power-import": 0, "measurements/power-export": 298},
        )
        self.assertNotIn("house/consumption", engine.state.fresh_values(100.3))
        self.submit(
            engine,
            "inverter2",
            100.4,
            {"measurements/pres-bat-charge": 3678, "measurements/pres-batt-discharge": 0},
        )
        self.assertEqual(engine.state.fresh_values(100.4)["house/consumption"], "113")

    def test_next_round_keeps_previous_sample_age_and_expires_without_complete_successor(self):
        engine, _ = self.coordinated()
        self.round(engine)
        old = engine.state.values["house/consumption"]
        self.submit(engine, "inverter1", 105.1, {"measurements/active-power": 4000}, 1)
        self.assertEqual(engine.state.values["house/consumption"], old)
        self.assertEqual(engine.state.fresh_values(109)["house/consumption"], "113")
        # Expiry must also hold if no calculation happens at the deadline.
        self.assertNotIn("house/consumption", engine.state.fresh_values(110.001))
        engine.refresh(110.001, self.wall + timedelta(seconds=10.001))
        self.assertNotIn("house/consumption", engine.state.fresh_values(110.001))

    def test_failed_source_and_unrelated_recovery_do_not_resurrect_old_cycle(self):
        engine, _ = self.coordinated()
        self.round(engine)
        state = engine.sources["inverter2"]
        state.error = True
        engine.power_cycles.observe(state, None, 105)
        state.update({"measurements/battery-charge-energy": 40}, now=105.1)
        self.assertFalse(state.error)
        self.assertNotIn("house/consumption", engine.state.fresh_values(105.1))
        self.round(engine, 105, 1)
        self.assertEqual(engine.state.fresh_values(105.4)["house/consumption"], "113")

    def test_invalid_snapshot_remains_unavailable_without_zero_or_previous_round_fallback(self):
        engine, _ = self.coordinated()
        self.round(engine)
        self.submit(engine, "inverter1", 105.1, {"measurements/active-power": None}, 1)
        self.submit(engine, "inverter3", 105.2, {"measurements/active-power": 1725}, 1)
        self.submit(
            engine,
            "home-manager",
            105.3,
            {"measurements/power-import": 0, "measurements/power-export": 298},
            1,
        )
        self.submit(
            engine,
            "inverter2",
            105.4,
            {"measurements/pres-bat-charge": 3678, "measurements/pres-batt-discharge": 0},
            1,
        )
        self.assertNotIn("house/consumption", engine.state.fresh_values(105.4))
        self.assertEqual(engine.power_cycles.completed, 1)

    def test_delayed_previous_round_cannot_complete_or_overwrite_current_round(self):
        engine, _ = self.coordinated()
        self.round(engine)
        self.submit(engine, "inverter1", 105.1, {"measurements/active-power": 9999}, 0)
        self.assertEqual(engine.state.fresh_values(105.1)["house/consumption"], "113")
        self.assertEqual(engine.power_cycles.completed, 0)
        self.round(engine, 105, 1)
        self.assertEqual(engine.state.fresh_values(105.4)["house/consumption"], "113")

    def test_udp_receipts_choose_cycle_and_do_not_recompute_completed_round(self):
        engine, _ = self.coordinated()
        self.round(engine)
        frozen = copy.deepcopy(engine.power_cycles.snapshot)
        self.submit(
            engine,
            "home-manager",
            101,
            {"measurements/power-import": 999, "measurements/power-export": 0},
            None,
        )
        self.assertEqual(engine.power_cycles.snapshot, frozen)
        self.assertEqual(engine.state.fresh_values(101)["house/consumption"], "113")

    def test_configuration_preserves_profiles_baselines_and_energy_intervals(self):
        engine, readers = self.coordinated()
        before = copy.deepcopy(engine.config.profiles)
        signature = plant_plan(engine.config)[3]
        for state, reader, _ in readers:
            if isinstance(reader, ModbusReader) and reader.schedule:
                for poller in reader.pollers:
                    if poller["id"] in reader.schedule.power_pollers:
                        self.assertEqual(reader.interval(poller), 5)
                    elif poller["id"] in reader.schedule.energy_pollers:
                        self.assertEqual(
                            reader.interval(poller),
                            poller.get("intervalSeconds", reader.settings.poll_interval_seconds),
                        )
        disabled = replace(
            engine.config,
            plant=replace(
                engine.config.plant, coordinated_reads_enabled=False, power_cycle_seconds=10
            ),
        )
        self.assertEqual(plant_plan(disabled)[3], signature)
        self.assertEqual(engine.config.profiles, before)
        self.assertFalse(engine.ledger.binding_changed)
        engine, readers = self.coordinated({"SMAB_PLANT_COORDINATED_READS_ENABLED": "false"})
        self.assertIsNone(engine.power_cycles)
        self.assertTrue(
            all(r.schedule is None for _, r, _ in readers if isinstance(r, ModbusReader))
        )

    def test_recorder_reconciles_frozen_inputs_and_exposes_raw_intermediates(self):
        engine, _ = self.coordinated({"SMAB_PLANT_RECORDER_ENABLED": "true"})
        self.round(engine)
        self.submit(engine, "inverter1", 105.1, {"measurements/active-power": 4000}, 1)
        row = json.loads(engine.recorder.path.read_text().splitlines()[-1])
        self.assertEqual(row["schemaVersion"], 2)
        self.assertEqual(row["inputs"]["inverter1/measurements/active-power"]["value"], "4000")
        self.assertEqual(row["powerInputs"]["inverter1/measurements/active-power"]["value"], "2364")
        terms = row["powerRecipes"]["house/consumption"]
        value = sum(Decimal(row["powerInputs"][t["input"]]["value"]) * t["sign"] for t in terms)
        self.assertEqual(str(value), row["outputs"]["house/consumption"]["candidate"])
        self.assertNotEqual(row["latestPowerBalances"]["house/consumption"], str(value))
        self.assertTrue(row["powerCycle"]["waitingFor"])
        self.assertIn("lastVectorDayKwh", row["accounts"]["house"])
        self.assertNotIn("hardware", engine.recorder.path.read_text())

    def test_cycle_bounds_and_nonparticipating_sources(self):
        for value in ("0", "-1", "60.001", "NaN"):
            with self.subTest(value=value), self.assertRaises(ConfigError):
                load_config({"SMAB_PLANT_POWER_CYCLE_SECONDS": value})
        engine, readers = self.coordinated(
            {
                "SMAB_INVERTER4_ENABLED": "true",
                "SMAB_INVERTER4_HOST": "unused.invalid",
                "SMAB_INVERTER4_PROFILE": "sma-sbs3-7-10",
                "SMAB_INVERTER4_ROLE": "none",
            }
        )
        self.assertIsNone(next(r for state, r, _ in readers if state.id == "inverter4").schedule)
        self.assertEqual(engine.power_cycles.seconds, 5)

    def test_unit_mismatch_and_device_replacement_invalidate_frozen_frame(self):
        engine, _ = self.coordinated()
        self.round(engine)
        state = engine.sources["inverter1"]
        original = state.properties
        state.properties = tuple(
            replace(p, unit="kW") if p.key == "measurements/active-power" else p for p in original
        )
        self.assertNotIn("house/consumption", engine.state.fresh_values(100.5))
        state.properties = original
        state.identity_fingerprint = "b" * 64
        state.update({"measurements/total-yield": 100}, now=105.1)
        engine.power_cycles.observe(state, {"measurements/total-yield": 100}, 105.1)
        self.assertNotIn("house/consumption", engine.state.fresh_values(105.1))
        self.round(engine, 105, 1)
        self.assertIn("house/consumption", engine.state.fresh_values(105.4))

    def test_json_and_environment_precedence_for_coordinated_options(self):
        from tests.helpers import write_json

        path = write_json(
            self.directory.name,
            "cycle-config.json",
            {
                "schemaVersion": 1,
                "plant": {"coordinatedReadsEnabled": False, "powerCycleSeconds": 12},
            },
        )
        config = load_config({"SMAB_CONFIG_FILE": path})
        self.assertFalse(config.plant.coordinated_reads_enabled)
        self.assertEqual(config.plant.power_cycle_seconds, 12)
        config = load_config(
            {
                "SMAB_CONFIG_FILE": path,
                "SMAB_PLANT_COORDINATED_READS_ENABLED": "true",
                "SMAB_PLANT_POWER_CYCLE_SECONDS": "7.5",
            }
        )
        self.assertTrue(config.plant.coordinated_reads_enabled)
        self.assertEqual(config.plant.power_cycle_seconds, 7.5)

    def test_pv_sum_remains_independent_of_failed_battery_and_recorder_names_its_vector(self):
        engine, _ = self.coordinated({"SMAB_PLANT_RECORDER_ENABLED": "true"})
        self.round(engine)
        battery = engine.sources["inverter2"]
        battery.error = True
        for group in set(engine.recipe_cycles.values()):
            group.observe(battery, None, 105)
        self.submit(engine, "inverter1", 105.1, {"measurements/active-power": 3000}, 1)
        self.submit(engine, "inverter3", 105.2, {"measurements/active-power": 2000}, 1)
        fresh = engine.state.fresh_values(105.2)
        self.assertEqual(fresh["pv/totalactivepower"], "5000")
        self.assertNotIn("house/consumption", fresh)
        row = json.loads(engine.recorder.path.read_text().splitlines()[-1])
        recipe = row["powerRecipes"]["pv/totalactivepower"]
        inputs = row["powerFrames"]["pv/totalactivepower"]["inputs"]
        self.assertEqual(
            sum(Decimal(inputs[t["input"]]["value"]) * t["sign"] for t in recipe), Decimal(5000)
        )


class ScheduleTests(unittest.TestCase):
    def test_counter_deadlines_preserve_interval_without_accumulating_late_receipts(self):
        schedule = ReadSchedule(100, 5, {"power"}, {"energy"})
        self.assertEqual(schedule.next_due({}, 60, 161.5), 220)
        self.assertEqual(schedule.next_due({}, 180, 281.5), 460)
        self.assertEqual(schedule.next_due({}, 60, 1000), 1060)

    def test_grouping_never_crosses_gaps_units_functions_or_request_limit(self):
        schedule = ReadSchedule(0, 5, {"a", "b", "c", "d", "e"}, set())
        a = {"id": "a", "unitId": 2, "function": 4, "start": 100, "count": 2}
        b = a | {"id": "b", "start": 102}
        self.assertEqual(len(schedule.groups([b, a])), 1)
        for other in (
            b | {"start": 103},
            b | {"unitId": 3},
            b | {"function": 3},
            b | {"count": 124},
        ):
            self.assertEqual(len(schedule.groups([a, other])), 2)


class CoordinatedProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_inverter_identity_first_preserves_per_block_receipts_and_shared_deadlines(self):
        reader = ModbusReader(Inverter(host="fixture.invalid"), validated_profile())
        reader.configure_schedule({"measurements/power"}, set(), 100, 5)
        clock = [100.0]
        requests = []
        writer = MagicMock()
        writer.wait_closed = AsyncMock()

        async def read(_stream, _writer, poller):
            requests.append(poller["id"])
            clock[0] += 0.1
            return [1, 2, 123] if poller["id"] == "identity" else [0, 100]

        with (
            patch("asyncio.open_connection", AsyncMock(return_value=(object(), writer))),
            patch.object(reader, "read_block", read),
            patch(
                "sma_mqtt_bridge.adapters.modbus.time", SimpleNamespace(monotonic=lambda: clock[0])
            ),
        ):
            result = await reader.read()
        self.assertEqual(requests, ["identity", "power"])
        self.assertEqual(result.power_cycle, 0)
        self.assertAlmostEqual(result.observed_at["measurements/power"], 100.2)
        self.assertEqual(reader.next_due["power"], 105)
        state = SourceState("fixture", "fixture", reader.properties, 60)
        result.legacy_counters = {"measurements/power": Decimal(10)}
        state.update(result, now=101)
        self.assertEqual(
            state.values["measurements/power"][1], state.legacy_counters["measurements/power"][1]
        )
        writer.close.assert_called_once()

    async def test_home_manager_reads_direction_pairs_once_and_keeps_counter_cadence(self):
        reader = adapter()
        reader.configure_schedule(
            {"measurements/power-import", "measurements/power-export"},
            {"measurements/energy-import", "measurements/energy-export"},
            100,
            5,
        )
        writer = MagicMock()
        writer.wait_closed = AsyncMock()
        requests = []
        identity = {
            "model": 9343,
            "serial": 123,
            "serial-copy": 123,
            "device-class": 8128,
            "manufacturer": 461,
        }

        async def read(_stream, _writer, poller):
            requests.append((poller.get("unitId"), poller["start"], poller["count"]))
            if poller["id"] in identity:
                return words(identity[poller["id"]])
            return words(20) + words(30) if poller["count"] == 4 else [0] * poller["count"]

        with (
            patch("asyncio.open_connection", AsyncMock(return_value=(object(), writer))),
            patch.object(reader, "read_block", read),
            patch(
                "sma_mqtt_bridge.adapters.home_manager_modbus.time",
                SimpleNamespace(monotonic=lambda: 100.5),
            ),
        ):
            power = await reader.read()
            energy = await reader.read()
        self.assertIn((2, 30865, 4), requests)
        self.assertIn((2, 30581, 4), requests)
        self.assertEqual(power["measurements/power-import"], 20)
        self.assertEqual(power["measurements/power-export"], 30)
        self.assertEqual(
            power.observed_at["measurements/power-import"],
            power.observed_at["measurements/power-export"],
        )
        self.assertEqual(energy["measurements/energy-import"], Decimal(".020"))
        self.assertEqual(energy["measurements/energy-export"], Decimal(".030"))
        self.assertEqual(reader.next_due["power-import"], 105)
        self.assertEqual(reader.next_due["energy-import"], 160)
        await reader.close()

    async def test_rejected_pair_invalidates_both_directions_without_fabricating_zero(self):
        reader = adapter()
        reader.writer = MagicMock()
        reader.writer.wait_closed = AsyncMock()
        reader.configure_schedule(
            {"measurements/power-import", "measurements/power-export"}, set(), 100, 5
        )
        with (
            patch.object(reader, "paced_read", AsyncMock(side_effect=ModbusException(2))),
            patch(
                "sma_mqtt_bridge.adapters.home_manager_modbus.time",
                SimpleNamespace(monotonic=lambda: 100),
            ),
        ):
            packet = await reader.read()
        self.assertIsNone(packet["measurements/power-import"])
        self.assertIsNone(packet["measurements/power-export"])
        self.assertEqual(reader.next_due["power-import"], 105)
        await reader.close()

    async def test_adjacent_pair_wire_request_is_four_read_only_registers(self):
        reader = adapter()
        group = [p for p in reader.pollers if p["id"] in ("power-import", "power-export")]
        stream = asyncio.StreamReader()
        stream.feed_data(
            struct.pack(">HHHB", 1, 0, 11, 2) + bytes([4, 8]) + struct.pack(">4H", 0, 20, 0, 30)
        )
        writer = MagicMock()
        writer.drain = AsyncMock()
        blocks = await reader.read_group(stream, writer, group)
        self.assertEqual(blocks, {"power-import": [0, 20], "power-export": [0, 30]})
        request = writer.write.call_args.args[0]
        self.assertEqual(request[6], 2)
        self.assertEqual(request[7:], struct.pack(">BHH", 4, 30865, 4))


class CycleObserverTests(unittest.IsolatedAsyncioTestCase):
    async def test_supervisor_delivers_updated_samples_and_invalidates_on_failure(self):
        config = load_config({})
        stop = asyncio.Event()
        state = SourceState(
            "fixture", "fixture", (Property("measurements", "power", "Power", unit="W"),), 60
        )
        reader = SimpleNamespace(
            read=AsyncMock(
                side_effect=[
                    {"measurements/power": 10},
                    ProtocolError("fixture"),
                    {"measurements/power": 20},
                ]
            ),
            close=AsyncMock(),
        )
        events = []

        def observe(observed, values):
            events.append(
                (
                    observed.error,
                    dict(values) if values is not None else None,
                    dict(observed.values),
                )
            )
            if len(events) == 3:
                stop.set()

        with (
            patch("sma_mqtt_bridge.runtime.wait_stop", AsyncMock()),
            self.assertLogs("sma_mqtt_bridge.availability", "WARNING"),
        ):
            await supervise(state, reader, 1, config, stop, on_samples=observe)
        self.assertEqual(events[0][2]["measurements/power"][0], "10")
        self.assertEqual(events[1][:2], (True, None))
        self.assertEqual(events[2][2]["measurements/power"][0], "20")
        reader.close.assert_awaited_once()
