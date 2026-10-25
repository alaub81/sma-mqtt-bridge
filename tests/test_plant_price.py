"""Local MQTT electricity price survives restarts without replay or device writes."""

import asyncio
import json
import unittest
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from test_plant import PlantFixture

from sma_mqtt_bridge.errors import ConfigError, StateError
from sma_mqtt_bridge.homie import HomiePublisher, discovery
from sma_mqtt_bridge.plant_price import (
    FEED_IN_PRICE,
    FEED_IN_RESULT,
    PRICE,
    PRICE_KEY,
    RESULT_KEY,
    PlantPrice,
)
from sma_mqtt_bridge.portal_commands import CommandRouter
from sma_mqtt_bridge.runtime import run_locked


class PlantPriceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.fixture = PlantFixture()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.engine = self.fixture.engine(
            env={
                "SMAB_PLANT_ELECTRICITY_PRICE_PER_KWH": "0.3",
                "SMAB_PLANT_PUBLISH_PARTIAL_DAY": "true",
            }
        )
        self.price = self.engine.price

    def result(self):
        return self.price.state.fresh_values().get(RESULT_KEY)

    async def test_save_readback_revalues_day_and_restart_overrides_env(self):
        wall = self.fixture.wall
        self.engine.refresh(100, wall)
        self.fixture.fill(self.engine, 102, {"home-manager": {"energyimport": 60}})
        self.engine.refresh(102, wall + timedelta(seconds=2))
        before = self.engine.ledger.path.read_bytes()
        await self.price.handle(PRICE.id, b"0.252")
        self.assertEqual(self.result(), "confirmed")
        self.assertTrue(self.engine.changed.is_set())
        self.engine.refresh(102, wall + timedelta(seconds=2))
        self.assertEqual(
            Decimal(self.engine.state.fresh_values(102)["grid/daily-costs"]), Decimal("2.52")
        )
        self.assertEqual(self.engine.ledger.path.read_bytes(), before)
        self.engine.sources["home-manager"].error = True
        self.assertNotIn("grid/daily-costs", self.engine.state.fresh_values(102))
        self.engine.sources["home-manager"].error = False
        restored = PlantPrice(
            replace(self.engine.config, electricity_price_configured=False), asyncio.Event()
        )
        self.assertEqual(restored.price, Decimal("0.252"))
        self.assertEqual(restored.state.fresh_values()[PRICE_KEY], "0.252")
        self.assertIsNone(restored.state.fresh_values().get(RESULT_KEY))
        self.assertEqual(json.loads(self.price.path.read_text())["price"], "0.252")
        configured = replace(
            self.engine.config,
            plant=replace(self.engine.config.plant, electricity_price_per_kwh=0.8),
        )
        self.assertEqual(PlantPrice(configured, asyncio.Event()).price, Decimal("0.252"))

    async def test_no_startup_write_and_value_never_expires(self):
        self.assertFalse(self.price.path.exists())
        self.assertEqual(self.price.price, Decimal("0.3"))
        stamp = self.price.state.values[PRICE_KEY][1]
        self.assertEqual(self.price.state.fresh_values(stamp + 1e9)[PRICE_KEY], "0.3")
        self.assertFalse(self.price.state.contributes_availability)
        metadata = discovery("homie", "sma-plant", self.price.state.properties)
        self.assertEqual(metadata["homie/sma-plant/settings/electricityprice/$settable"], "true")
        self.assertEqual(metadata["homie/sma-plant/settings/electricityprice/$datatype"], "float")
        self.assertEqual(metadata["homie/sma-plant/settings/electricityprice/$unit"], "€")

    async def test_missing_env_waits_for_first_mqtt_price_including_zero(self):
        config = replace(self.engine.config, electricity_price_configured=False)
        price = PlantPrice(config, asyncio.Event())
        self.assertIsNone(price.price)
        self.assertNotIn(PRICE_KEY, price.state.fresh_values())
        await price.handle(PRICE.id, b"0")
        self.assertEqual(price.price, 0)
        self.assertEqual(price.state.fresh_values()[RESULT_KEY], "confirmed")

    async def test_invalid_retained_and_oversized_never_change_price(self):
        for data in (
            b"",
            b"-1",
            b"NaN",
            b"Infinity",
            b"0,252",
            b"0.252 EUR",
            b"1e3",
            b" 0.2",
            b"true",
            b"\xff",
            b"9" * 400,
            "0.2",
            b"1" * 5000,
        ):
            with self.subTest(data=str(data)[:30]):
                await self.price.handle(PRICE.id, data)
                self.assertEqual(self.result(), "rejected")
        await self.price.handle(PRICE.id, b"0.1", retained=True)
        self.assertEqual(self.result(), "rejected-retained")
        await self.price.handle("unknown", b"0.1")
        self.assertEqual(self.price.price, Decimal("0.3"))
        self.assertFalse(self.price.path.exists())
        self.assertFalse(self.engine.changed.is_set())

    async def test_storage_failure_never_confirms_or_changes_active_value(self):
        with patch("sma_mqtt_bridge.plant_price.write_state", side_effect=OSError("fixture")):
            await self.price.handle(PRICE.id, b"0.252")
        self.assertEqual(self.result(), "storage-error")
        self.assertEqual(self.price.price, Decimal("0.3"))
        self.assertFalse(self.engine.changed.is_set())
        with patch("sma_mqtt_bridge.plant_price.read_state", return_value={}):
            await self.price.handle(PRICE.id, b"0.252")
        self.assertEqual(self.result(), "storage-error")
        self.assertEqual(self.price.price, Decimal("0.3"))

    async def test_corrupt_currency_or_identity_mismatch_fails_closed(self):
        await self.price.handle(PRICE.id, b"0.252")
        record = json.loads(self.price.path.read_text())
        for change in (
            {"schemaVersion": True},
            {"currency": "USD"},
            {"device": "other"},
            {"price": -1},
            {"price": "NaN"},
            {"price": "1e500"},
            {"extra": "unknown"},
        ):
            with self.subTest(change=change):
                self.price.path.write_text(json.dumps(record | change))
                with self.assertRaises(StateError):
                    PlantPrice(self.engine.config, asyncio.Event())
        self.price.path.write_text("{")
        with self.assertRaises(StateError):
            PlantPrice(self.engine.config, asyncio.Event())

    async def test_real_mqtt_consumer_rejects_retained_and_routes_live_price(self):
        base = "homie/sma-plant"
        router = CommandRouter(plant_price=self.price, feed_in_price=self.engine.feed_in_price)
        publisher = HomiePublisher(self.engine.config, list(self.engine.output_states))
        publisher.command_controller = router

        async def messages():
            yield SimpleNamespace(
                topic=base + "/settings/electricityprice/set", payload=b"0.1", retain=True
            )
            self.assertFalse(self.price.path.exists())
            self.assertEqual(self.result(), "rejected-retained")
            yield SimpleNamespace(
                topic=base + "/settings/electricityprice/set", payload=b"0.252", retain=False
            )
            await asyncio.sleep(0)

        await publisher.receive_commands(
            SimpleNamespace(messages=messages()), base, self.price.state.properties
        )
        self.assertEqual(self.result(), "confirmed")
        self.assertEqual(self.price.price, Decimal("0.252"))
        await router.close()

    async def test_runtime_registers_price_without_device_command_gates(self):
        test = self
        stop = asyncio.Event()
        config = replace(
            self.engine.config, commands=replace(self.engine.config.commands, enabled=False)
        )

        class Publisher:
            def __init__(self, cfg, states):
                self.command_controller = None
                self.status = {}
                props = [p for s in states for p in s.properties if p.settable]
                test.assertEqual([p.key for p in props], [PRICE_KEY, "settings/feed-in-price"])

            async def run(self, stopping):
                await self.command_controller.handle(PRICE.id, b"0.252")
                await self.command_controller.handle(FEED_IN_PRICE.id, b"0.08")
                stop.set()

        async def supervise(*args, **_kwargs):
            await args[4].wait()

        readers = [
            (state, SimpleNamespace(close=AsyncMock()), 1) for state in self.engine.sources.values()
        ]
        with (
            patch("sma_mqtt_bridge.runtime.sources", return_value=readers),
            patch("sma_mqtt_bridge.runtime.supervise", side_effect=supervise),
        ):
            await asyncio.wait_for(run_locked(config, stop=stop, publisher_factory=Publisher), 2)
        self.assertEqual(PlantPrice(config, asyncio.Event()).price, Decimal("0.252"))

    async def test_feed_in_price_activates_both_earnings_and_restores_independently(self):
        feed = self.engine.feed_in_price
        wall = self.fixture.wall
        inventory = self.engine.state.properties
        self.engine.refresh(100, wall)
        self.assertIs(self.engine.state.properties, inventory)
        self.assertNotIn("pv/total-earnings", self.engine.state.property_index())
        self.fixture.fill(self.engine, 102, {"home-manager": {"energyexport": 64}})
        self.engine.refresh(102, wall + timedelta(seconds=2))
        saved = self.engine.ledger.path.read_bytes()
        await feed.handle(FEED_IN_PRICE.id, b"0.08")
        self.engine.refresh(102, wall + timedelta(seconds=2))
        values = self.engine.state.fresh_values(102)
        self.assertEqual(Decimal(values["grid/daily-earnings"]), Decimal("0.32"))
        self.assertEqual(Decimal(values["pv/total-earnings"]), Decimal("5.12"))
        self.assertEqual(self.price.price, Decimal("0.3"))
        self.assertFalse(self.price.path.exists())
        inventory = self.engine.state.properties
        self.engine.refresh(102, wall + timedelta(seconds=2))
        self.assertIs(self.engine.state.properties, inventory)
        self.assertEqual(self.engine.ledger.path.read_bytes(), saved)
        restored = self.fixture.engine(env={"SMAB_PLANT_FEED_IN_TARIFF_PER_KWH": "0.99"})
        self.assertEqual(restored.feed_in_price.price, Decimal("0.08"))
        self.assertIn("grid/daily-earnings", restored.state.property_index())
        self.assertEqual(feed.state.fresh_values()[FEED_IN_RESULT.key], "confirmed")
        metadata = discovery("homie", "sma-plant", feed.state.properties)
        self.assertEqual(metadata["homie/sma-plant/settings/feedinprice/$unit"], "€")
        self.assertEqual(metadata["homie/sma-plant/settings/feedinprice/$settable"], "true")
        await feed.handle(FEED_IN_PRICE.id, b"0")
        self.engine.refresh(102, wall + timedelta(seconds=2))
        for key in ("grid/daily-earnings", "pv/total-earnings"):
            self.assertEqual(Decimal(self.engine.state.fresh_values(102)[key]), 0)

    async def test_feed_in_env_fallback_retained_rejection_and_storage_failure(self):
        config = replace(
            self.engine.config,
            feed_in_tariff_configured=True,
            plant=replace(self.engine.config.plant, feed_in_tariff_per_kwh=0.07),
        )
        feed = PlantPrice(config, asyncio.Event(), feed_in=True)
        self.assertEqual(feed.price, Decimal("0.07"))
        await feed.handle(FEED_IN_PRICE.id, b"0.1", retained=True)
        self.assertEqual(feed.state.fresh_values()[FEED_IN_RESULT.key], "rejected-retained")
        self.assertFalse(feed.path.exists())
        await feed.handle(FEED_IN_PRICE.id, b"-1")
        self.assertEqual(feed.state.fresh_values()[FEED_IN_RESULT.key], "rejected")
        with patch("sma_mqtt_bridge.plant_price.write_state", side_effect=OSError("fixture")):
            await feed.handle(FEED_IN_PRICE.id, b"0.08")
        self.assertEqual(feed.state.fresh_values()[FEED_IN_RESULT.key], "storage-error")
        self.assertEqual(feed.price, Decimal("0.07"))
        self.assertEqual(self.price.price, Decimal("0.3"))

    async def test_feed_in_cannot_bypass_home_manager_source_validation(self):
        config = replace(
            self.engine.config, plant=replace(self.engine.config.plant, grid_source="inverter1")
        )
        feed = PlantPrice(config, asyncio.Event(), feed_in=True)
        self.assertFalse(feed.property.settable)
        await feed.handle(FEED_IN_PRICE.id, b"0.08")
        self.assertIsNone(feed.price)
        self.assertFalse(feed.path.exists())
        config = replace(config, feed_in_tariff_configured=True)
        with self.assertRaises(ConfigError):
            PlantPrice(config, asyncio.Event(), feed_in=True)
