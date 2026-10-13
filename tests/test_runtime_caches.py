"""Metadata reuse must preserve live expiry, readiness and inventory retirement."""

import asyncio
import tempfile
import unittest
from dataclasses import replace
from unittest.mock import AsyncMock, patch

from sma_mqtt_bridge.availability import Availability
from sma_mqtt_bridge.config import load_config
from sma_mqtt_bridge.errors import ProtocolError
from sma_mqtt_bridge.homie import HomiePublisher
from sma_mqtt_bridge.model import Property, SampleValues, SourceState


class PropertyIndexTests(unittest.TestCase):
    def test_replaced_inventory_uses_new_types_expiry_and_readiness(self):
        state = SourceState("fixture", "fixture", (Property("measurements", "a", "A"),), 10)
        state.update({"measurements/a": 1}, now=100)
        self.assertEqual(state.status(105), "ready")
        state.properties = (
            Property("measurements", "a", "A", "boolean", stale_seconds=2),
            Property("measurements", "b", "B", required_for_ready=True),
        )
        self.assertEqual(state.fresh_values(105), {})
        self.assertEqual(state.required_keys, ("measurements/b",))
        state.update({"measurements/a": True, "measurements/b": 0}, now=105)
        self.assertEqual(state.fresh_values(107), {"measurements/a": "true", "measurements/b": "0"})
        self.assertEqual(state.fresh_values(108), {"measurements/b": "0"})
        self.assertEqual(state.status(108), "ready")
        state.ready_properties = ("measurements/a",)
        self.assertEqual(state.status(108), "stale")
        state.ready_properties = ()
        self.assertEqual(state.status(108), "ready")
        with self.assertRaises(ProtocolError):
            state.update({"measurements/retired": 1}, now=108)

    def test_cached_descriptions_never_cache_samples_or_default_lifetime(self):
        prop = Property("measurements", "power", "Power")
        state = SourceState("fixture", "fixture", (prop,), 10)
        state.update(SampleValues({prop.key: 0}, {prop.key: 95}), now=100)
        self.assertEqual(state.status(105), "ready")
        self.assertEqual(state.status(105.01), "stale")
        state.stale_seconds = 20
        self.assertEqual(state.status(110), "ready")
        state.update({prop.key: None}, now=110)
        self.assertEqual(state.status(110), "stale")
        state.update({prop.key: -1}, now=111)
        self.assertEqual(state.fresh_values(111), {prop.key: "-1"})
        self.assertEqual(state.fresh_values(110), {})
        state.error = True
        self.assertEqual(state.status(111), "error")
        copied = replace(state, properties=(replace(prop, stale_seconds=1),))
        self.assertEqual(copied.fresh_values(113), {})
        self.assertEqual(state.fresh_values(113), {prop.key: "-1"})


class PublisherInventoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_reuse_and_invalidation_preserve_dynamic_discovery(self):
        with tempfile.TemporaryDirectory() as directory:
            config = load_config({"SMAB_STATE_DIR": directory})
            state = SourceState(
                "fixture", "fixture", (Property("measurements", "power", "Power"),), 60
            )
            state.update({"measurements/power": 0})
            publisher = HomiePublisher(config, [state])
            client, stop = AsyncMock(), asyncio.Event()
            cycle = 0

            async def advance(_stop, _seconds):
                nonlocal cycle
                cycle += 1
                if cycle == 2:
                    state.monitor = Availability("Fixture", 300)
                elif cycle == 3:
                    state.diagnostics_enabled = False
                elif cycle == 4:
                    state.properties = (Property("measurements", "energy", "Energy"),)
                    state.values.clear()
                    state.update({"measurements/energy": 1})
                elif cycle == 6:
                    stop.set()

            with (
                patch("sma_mqtt_bridge.homie.wait_stop", side_effect=advance),
                patch.object(publisher, "properties", wraps=publisher.properties) as descriptions,
            ):
                await publisher.publish_values(client, "homie/fixture", [state], stop, {}, 0, None)
            self.assertEqual(descriptions.call_count, 5)
            messages = [(call.args[0], call.args[1]) for call in client.publish.await_args_list]
            self.assertIn(
                ("homie/fixture/diagnostics/fixturefailures/$datatype", "integer"), messages
            )
            self.assertIn(("homie/fixture/diagnostics/fixturefailures/$datatype", b""), messages)
            self.assertIn(("homie/fixture/measurements/power", b""), messages)
            self.assertIn(("homie/fixture/measurements/energy", "1"), messages)
            self.assertIn(("homie/fixture/diagnostics/fixturestatus", "ready"), messages)
