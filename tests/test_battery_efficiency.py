"""Counter-based energy ratio uses one existing poll response without cached mixing."""

import copy
import unittest
from dataclasses import replace
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

from sma_mqtt_bridge.adapters.modbus import ModbusReader, energy_return_ratio
from sma_mqtt_bridge.config import load_config
from sma_mqtt_bridge.profiles import load_profile


class BatteryEfficiencyTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.profile = load_profile(
            "sma-sbs3-7-10", "/tmp/no-smab-profiles", require_validated=True
        )
        self.settings = load_config({}).inverters[1]

    def test_counter_ratio_and_undefined_inputs(self):
        self.assertEqual(energy_return_ratio(Decimal(8507), Decimal(6699)), Decimal("78.75"))
        self.assertEqual(energy_return_ratio(Decimal(1), Decimal(0)), Decimal("0.00"))
        self.assertEqual(energy_return_ratio(Decimal(10), Decimal(11)), Decimal("110.00"))
        for charged, discharged in [(None, 1), (1, None), (0, 0), (-1, 1), (1, -1)]:
            self.assertIsNone(energy_return_ratio(charged, discharged))

    def test_metadata_only_for_matching_same_poll_kwh_counters(self):
        reader = ModbusReader(
            replace(self.settings, advanced_channels_enabled=False, diagnostics_enabled=False),
            self.profile,
        )
        prop = next(p for p in reader.properties if p.id == "battery-efficiency")
        self.assertEqual(prop.unit, "%")
        self.assertEqual(prop.datatype, "float")
        self.assertFalse(prop.settable)
        self.assertFalse(prop.required_for_ready)
        for change in ("missing", "unit", "poller"):
            profile = copy.deepcopy(self.profile)
            discharge = next(
                p for p in profile["properties"] if p["id"] == "battery-discharge-energy"
            )
            if change == "missing":
                profile["properties"].remove(discharge)
            elif change == "unit":
                discharge["unit"] = "Wh"
            else:
                discharge["poller"] = "identity"
            self.assertFalse(ModbusReader(self.settings, profile).energy_ratio)

    async def test_read_uses_same_block_and_does_not_recompute_between_energy_polls(self):
        reader = ModbusReader(self.settings, self.profile)
        writer = AsyncMock()
        writer.close = Mock()
        energy_poller = next(p for p in reader.pollers if p["id"] == "battery-energy")
        invalid = False

        async def read_block(stream, connection, poller):
            if poller["id"] == "battery-energy":
                raw = ((2**64 - 1) if invalid else 8507000).to_bytes(8, "big")
                raw += (6699000).to_bytes(8, "big")
                return [int.from_bytes(raw[i : i + 2], "big") for i in range(0, 16, 2)]
            return [0] * poller["count"]

        reader.read_block = AsyncMock(side_effect=read_block)
        with (
            patch(
                "sma_mqtt_bridge.adapters.modbus.asyncio.open_connection",
                AsyncMock(return_value=(Mock(), writer)),
            ),
            patch("sma_mqtt_bridge.adapters.modbus.verify_identity"),
        ):
            result = await reader.read()
            self.assertEqual(result["measurements/battery-efficiency"], Decimal("78.75"))
            self.assertEqual(
                sum(c.args[2] == energy_poller for c in reader.read_block.await_args_list), 1
            )
            self.assertNotIn("measurements/battery-efficiency", await reader.read())
            reader.next_due["battery-energy"] = 0
            invalid = True
            self.assertIsNone((await reader.read())["measurements/battery-efficiency"])
