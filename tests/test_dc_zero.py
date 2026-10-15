"""Conditional DC compatibility must not turn faults or missing reads into zero."""

import copy
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from sma_mqtt_bridge.adapters.modbus import ModbusReader
from sma_mqtt_bridge.config import Inverter
from sma_mqtt_bridge.errors import ConfigError, ProtocolError
from sma_mqtt_bridge.profiles import load_profile, validate_profile


class DCZeroTests(unittest.IsolatedAsyncioTestCase):
    def profile(self, name="sma-stp8-0-3av-40"):
        with tempfile.TemporaryDirectory() as directory:
            return load_profile(name, directory, require_validated=True)

    async def sample(self, *, ac=0, status=307, current=None, fail=False):
        profile = self.profile()
        adapter = ModbusReader(Inverter(host="fixture.invalid"), profile)
        wanted = {"current-b-input", "power-b-input", "voltage-b-input"}
        adapter.definitions = [p for p in profile["properties"] if p["id"] in wanted]
        adapter.pollers = [p for p in profile["pollers"] if p["id"] == "power-b"]
        calls = []

        async def block(_reader, _writer, poller):
            calls.append(poller["id"])
            if fail and poller["id"] == "sma-status":
                raise ProtocolError("Synthetic guard read failure")
            words = [0] * poller["count"]
            for prop in profile["properties"]:
                if prop["poller"] != poller["id"] or prop["length"] != 2:
                    continue
                raw = {"active-power": ac, "status": status}.get(prop["id"], -2147483648)
                if prop["id"] == "current-b-input" and current is not None:
                    raw = current
                raw &= 0xFFFFFFFF
                words[prop["offset"] : prop["offset"] + 2] = [raw >> 16, raw & 65535]
            return words

        writer = MagicMock()
        writer.wait_closed = AsyncMock()
        with (
            patch("asyncio.open_connection", AsyncMock(return_value=(object(), writer))),
            patch("sma_mqtt_bridge.adapters.modbus.verify_identity"),
            patch.object(adapter, "read_block", side_effect=block),
        ):
            result = await adapter.read()
        return result, calls

    async def test_fresh_guards_required_even_when_their_pollers_are_not_due(self):
        for ac in (0, -2147483648):
            values, calls = await self.sample(ac=ac)
            self.assertEqual(values["measurements/current-b-input"], 0)
            self.assertEqual(values["measurements/power-b-input"], 0)
            self.assertIsNone(values["measurements/voltage-b-input"])
            self.assertIn("sma-status", calls)
            self.assertIn("power-a", calls)

    async def test_production_fault_and_unavailable_guards_do_not_zero_dc(self):
        for ac, status in ((20, 307), (0, 35), (0, 455), (0, 16777213)):
            values, _ = await self.sample(ac=ac, status=status)
            self.assertIsNone(values["measurements/current-b-input"])
            self.assertIsNone(values["measurements/power-b-input"])
        with self.assertRaises(ProtocolError):
            await self.sample(fail=True)

    async def test_valid_signed_current_is_preserved(self):
        values, _ = await self.sample(current=-1000)
        self.assertEqual(values["measurements/current-b-input"], -1)

    def test_only_six_confirmed_dc_channels_are_enabled(self):
        expected = {
            "sma-stp8-0-3av-40": {
                "current-a-input",
                "power-a-input",
                "current-b-input",
                "power-b-input",
            },
            "sma-sb4-0-1av-41": {"current-a-input", "power-a-input"},
        }
        for name, channels in expected.items():
            profile = self.profile(name)
            self.assertEqual(
                {p["id"] for p in profile["properties"] if "invalidAsZeroWhen" in p}, channels
            )
            for change in (
                {"unit": "V"},
                {"unit": "kWh"},
                {"invalid": [0]},
                {"invalidAsZeroWhen": {}},
                {"invalidAsZeroWhen": {"missing": [0]}},
                {"invalidAsZeroWhen": {"current-a-input": [0]}},
                {"invalidAsZeroWhen": {"status": [None]}},
            ):
                modified = copy.deepcopy(profile)
                prop = next(p for p in modified["properties"] if p["id"] == "current-a-input")
                prop.update(change)
                with self.subTest(change=change), self.assertRaises(ConfigError):
                    validate_profile(modified)
