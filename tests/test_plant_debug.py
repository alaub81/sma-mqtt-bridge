"""Scoped numeric diagnostics preserve read behavior, validity and rate limits."""

import json
import logging
import unittest
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

from test_plant import PlantFixture

from sma_mqtt_bridge.config import load_config
from sma_mqtt_bridge.errors import ConfigError
from sma_mqtt_bridge.plant_debug import LOG
from sma_mqtt_bridge.runtime import sources


class PlantDebugTests(PlantFixture):
    def test_missing_zero_partial_and_durable_values_are_distinct(self):
        engine = self.engine(
            env={"SMAB_PLANT_DEBUG_ENABLED": "true", "SMAB_PLANT_ASSUME_AC_BATTERY_ENERGY": "true"}
        )
        self.fill(
            engine, 100, {"inverter1": {"activepower": None}, "inverter3": {"activepower": 0}}
        )
        with self.assertLogs(LOG, level=logging.DEBUG) as logs:
            engine.refresh(100, self.wall)
        report = json.loads(logs.records[0].getMessage().split(" debug ", 1)[1])
        self.assertIsNone(report["inputs"]["inverter1/measurements/active-power"]["value"])
        self.assertEqual(report["inputs"]["inverter3/measurements/active-power"]["value"], "0")
        self.assertEqual(report["inputs"]["inverter3/measurements/active-power"]["ageSeconds"], 0)
        self.assertEqual(
            report["powerProblems"], {"inverter1/measurements/active-power": "missing-or-invalid"}
        )
        self.assertNotIn("sma-plant/house/consumption", report["availableValues"])
        self.assertEqual(report["status"]["diagnostics/houseenergystatus"], "partial")
        self.assertEqual(report["batteryBoundary"], "assumed-ac")
        self.assertIsNone(report["accounts"]["house"]["dailyValue"])
        self.assertEqual(Decimal(report["committedAccounts"]["house"]["totalValue"]), 0)
        self.assertEqual(
            report["energyRecipes"]["house"]["inverter2/measurements/battery-charge-energy"], -1
        )
        text = logs.records[0].getMessage()
        for secret in ("hardware", "signature", "expectedSerial", "source1.invalid", "424242"):
            self.assertNotIn(secret, text)

    def test_off_info_and_interval_do_not_emit_or_change_accounting(self):
        engine = self.engine()
        with self.assertNoLogs(LOG, level=logging.DEBUG):
            engine.refresh(100, self.wall)
        engine = self.engine(env={"SMAB_PLANT_DEBUG_ENABLED": "true"})
        with self.assertNoLogs(LOG, level=logging.INFO):
            engine.refresh(100, self.wall)
        with self.assertLogs(LOG, level=logging.DEBUG) as logs:
            engine.debug.report(engine, 100, self.wall)
            engine.debug.report(engine, 159, self.wall)
            engine.debug.report(engine, 160, self.wall)
        self.assertEqual(len(logs.records), 2)

    def test_runtime_gates_register_debug_on_enabled_plant_and_contributors(self):
        for env, expected in (
            ({}, 0),
            ({"SMAB_PLANT_DEBUG_ENABLED": "true"}, 60),
            ({"SMAB_PLANT_DEBUG_ENABLED": "true", "SMAB_PLANT_ENABLED": "false"}, 0),
            ({"SMAB_PLANT_DEBUG_ENABLED": "true", "SMAB_INVERTER1_ROLE": "none"}, 0),
        ):
            config = load_config(self.env | env)
            reader = next(reader for state, reader, _ in sources(config) if state.id == "inverter1")
            self.assertEqual(reader.debug.interval, expected)
        for value in ("0", "-1", "nan"):
            with self.assertRaises(ConfigError):
                load_config(self.env | {"SMAB_PLANT_DEBUG_INTERVAL_SECONDS": value})

    def test_raw_register_scope_sentinel_and_throttle(self):
        config = load_config(self.env | {"SMAB_PLANT_DEBUG_ENABLED": "true"})
        reader = next(r for s, r, _ in sources(config) if s.id == "inverter1")
        prop = next(p for p in reader.definitions if p["id"] == "active-power")
        block = [0] * next(p["count"] for p in reader.pollers if p["id"] == prop["poller"])
        block[prop["offset"] : prop["offset"] + 2] = [32768, 0]
        blocks = {prop["poller"]: block}
        result = {"measurements/active-power": None}
        selected = {prop["poller"]}
        with self.assertLogs(LOG, level=logging.DEBUG) as logs:
            reader.debug.modbus(reader, blocks, selected, 100, result)
            reader.debug.modbus(reader, blocks, selected, 101, result)
        rows = [json.loads(r.getMessage().split(" debug ", 1)[1]) for r in logs.records]
        power = next(r for r in rows if r["property"] == "measurements/active-power")
        self.assertEqual(power["register"], 30775)
        self.assertEqual(power["words"], [32768, 0])
        self.assertFalse(power["valid"])
        self.assertIsNone(power["numericValue"])
        self.assertTrue(all(r["property"].startswith("measurements/") for r in rows))
        self.assertEqual(sum(r["property"] == "measurements/active-power" for r in rows), 1)
        self.assertEqual(result, {"measurements/active-power": None})


class PlantRegisterReadTests(unittest.IsolatedAsyncioTestCase):
    async def test_raw_debug_uses_existing_reads_after_identity_verification(self):
        fixture = PlantFixture()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        config = load_config(fixture.env | {"SMAB_PLANT_DEBUG_ENABLED": "true"})
        reader = next(r for s, r, _ in sources(config) if s.id == "inverter1")
        writer = Mock(drain=AsyncMock(), wait_closed=AsyncMock())
        reader.read_block = AsyncMock(side_effect=lambda _r, _w, p: [0] * p["count"])
        reader.debug.modbus = Mock()
        with (
            patch(
                "sma_mqtt_bridge.adapters.modbus.asyncio.open_connection",
                AsyncMock(return_value=(Mock(), writer)),
            ),
            patch("sma_mqtt_bridge.adapters.modbus.verify_identity") as verify,
        ):
            await reader.read()
            verify.assert_called_once()
            reader.debug.modbus.assert_called_once()
            pollers = [call.args[2]["id"] for call in reader.read_block.await_args_list]
            self.assertEqual(len(pollers), len(set(pollers)))
        reader.debug.modbus.reset_mock()
        with (
            patch(
                "sma_mqtt_bridge.adapters.modbus.asyncio.open_connection",
                AsyncMock(return_value=(Mock(), writer)),
            ),
            patch(
                "sma_mqtt_bridge.adapters.modbus.verify_identity",
                side_effect=ConfigError("Mismatch"),
            ),
            self.assertRaises(ConfigError),
        ):
            await reader.read()
        reader.debug.modbus.assert_not_called()
