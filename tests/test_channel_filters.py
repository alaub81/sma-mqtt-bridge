"""Channel selection removes polling work while retaining internal safety checks."""

import asyncio
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from sma_mqtt_bridge.adapters.echarger import NS, SempReader, base_values, semp_values
from sma_mqtt_bridge.adapters.home_manager_modbus import HomeManagerModbusReader
from sma_mqtt_bridge.adapters.modbus import ModbusReader
from sma_mqtt_bridge.config import ECharger, HomeManager, Inverter, load_config
from sma_mqtt_bridge.errors import ConfigError, ProtocolError
from sma_mqtt_bridge.homie import HomiePublisher, discovery
from sma_mqtt_bridge.model import Property, SourceState
from tests.helpers import validated_profile, write_json
from tests.test_home_manager_modbus import profile, words
from tests.test_runtime import FakeClient


class ChannelTests(unittest.TestCase):
    def test_defaults_precedence_and_independent_flags(self):
        defaults = load_config({})
        self.assertTrue(defaults.home_manager.advanced_channels_enabled)
        self.assertTrue(defaults.echarger.diagnostics_enabled)
        with tempfile.TemporaryDirectory() as tmp:
            path = write_json(
                tmp, "config.json", {"homeManager": {"advancedChannelsEnabled": False}}
            )
            config = load_config(
                {"SMAB_CONFIG_FILE": path, "SMAB_INVERTER2_DIAGNOSTICS_ENABLED": "false"}
            )
            self.assertFalse(config.home_manager.advanced_channels_enabled)
            self.assertTrue(config.home_manager.diagnostics_enabled)
            self.assertFalse(config.inverters[1].diagnostics_enabled)
            self.assertTrue(config.inverters[0].diagnostics_enabled)
            override = load_config(
                {"SMAB_CONFIG_FILE": path, "SMAB_HOME_MANAGER_ADVANCED_CHANNELS_ENABLED": "true"}
            )
            self.assertTrue(override.home_manager.advanced_channels_enabled)
        with self.assertRaises(ConfigError):
            load_config({"SMAB_ECHARGER_ADVANCED_CHANNELS_ENABLED": "maybe"})

    def test_wallbox_raw_channels_disabled_settings_preserved(self):
        reader = SempReader(
            ECharger(advanced_channels_enabled=False, diagnostics_enabled=False), 4096
        )
        keys = {p.key for p in reader.properties}
        self.assertIn("settings/plan-energy", keys)
        self.assertIn("measurements/power", keys)
        self.assertNotIn("control/power-setpoint-min-percent", keys)
        self.assertNotIn("measurements/event-code", keys)
        self.assertIn("measurements/vehicle-status-code", keys)
        self.assertNotIn("parameters/nameplate-pkgrev", keys)
        prop = next(p for p in reader.properties if p.key == "measurements/vehicle-status-code")
        self.assertEqual(prop.datatype, "integer")
        self.assertFalse(prop.settable)
        self.assertFalse(prop.required_for_ready)
        values = base_values({"Measurement.Operation.EVeh.ChaStt": "200113"}, advanced=False)
        self.assertEqual(values["measurements/vehicle-status"], "Lädt")
        self.assertEqual(values["measurements/vehicle-status-code"], 200113)
        self.assertNotIn("parameters/nameplate-pkgrev", values)
        metadata = discovery("homie", "fixture", reader.properties)
        topic = "homie/fixture/measurements/vehiclestatuscode"
        self.assertEqual(metadata[topic + "/$datatype"], "integer")
        self.assertEqual(metadata[topic + "/$settable"], "false")
        self.assertEqual(metadata[topic + "/$retained"], "true")
        self.assertIn(
            "vehiclestatuscode", metadata["homie/fixture/measurements/$properties"].split(",")
        )
        state = SourceState("semp", "fixture", reader.properties, 180)
        state.update(values, now=10)
        self.assertEqual(state.fresh_values(10)["measurements/vehicle-status-code"], "200113")
        self.assertEqual(
            state.status(10), "stale"
        )  # Status code alone does not replace required power.
        xml = f'<Device2EM xmlns="{NS}"><Parameters><Parameter><channelId>Measurement.Operation.Evt.Msg</channelId><value>1</value></Parameter></Parameters></Device2EM>'
        values = semp_values(xml, 30, advanced=False, diagnostics=False)
        self.assertNotIn("measurements/event-code", values)
        self.assertNotIn("parameters/chrg-plan-en-raw", values)


class ChannelAsyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_home_manager_basic_only_identity_gate_and_no_inventory(self):
        settings = HomeManager(
            host="fixture.invalid",
            serial="123",
            advanced_channels_enabled=False,
            diagnostics_enabled=False,
            after_connection_delay_seconds=0,
        )
        reader = HomeManagerModbusReader(settings, profile())
        self.assertEqual(len(reader.properties), 6)
        self.assertTrue(all(p.node == "measurements" for p in reader.properties))
        self.assertTrue(all(p["unitId"] == 2 for p in reader.pollers))
        self.assertEqual(reader.inventory_pollers, [])
        identities = {
            "model": 9343,
            "device-class": 8128,
            "manufacturer": 461,
            "serial": 123,
            "serial-copy": 123,
        }
        reader.paced_read = AsyncMock(side_effect=lambda p: words(identities[p["id"]]))
        writer = MagicMock()
        with patch("asyncio.open_connection", new=AsyncMock(return_value=(MagicMock(), writer))):
            self.assertEqual(await reader.connect(), {})
        self.assertEqual(
            {c.args[0]["id"] for c in reader.paced_read.call_args_list}, set(identities)
        )
        reader.paced_read = AsyncMock(return_value=words(10))
        values = await reader.read()
        self.assertEqual(values, {"measurements/power-import": 10})
        self.assertEqual(reader.paced_read.call_args.args[0]["unitId"], 2)
        reader.writer = None
        identities["model"] = 1
        reader.paced_read = AsyncMock(side_effect=lambda p: words(identities[p["id"]]))
        with patch("asyncio.open_connection", new=AsyncMock(return_value=(MagicMock(), writer))):
            with self.assertRaises(ProtocolError):
                await reader.connect()

    async def test_inverter_skips_advanced_block_but_checks_identity(self):
        p = validated_profile()
        p["pollers"].append({"id": "extra", "function": 4, "start": 20, "count": 2})
        p["properties"].append(
            {**p["properties"][-1], "id": "extra", "poller": "extra", "channelGroup": "advanced"}
        )
        reader = ModbusReader(Inverter(advanced_channels_enabled=False), p)
        reader.read_block = AsyncMock(
            side_effect=lambda _, __, block: [1, 2, 123] if block["id"] == "identity" else [0, 100]
        )
        writer = MagicMock()
        writer.wait_closed = AsyncMock()
        with patch("asyncio.open_connection", new=AsyncMock(return_value=(MagicMock(), writer))):
            self.assertEqual(await reader.read(), {"measurements/power": 10})
        self.assertEqual(
            [call.args[2]["id"] for call in reader.read_block.call_args_list], ["identity", "power"]
        )

    async def test_widget_source_status_survives_disabled_diagnostics(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = load_config({"SMAB_STATE_DIR": tmp})
            for source_id in ("api", "semp", "portal"):
                with self.subTest(source=source_id):
                    state = SourceState(
                        source_id,
                        "test-device",
                        (Property("measurements", "power", "Power"),),
                        5,
                        diagnostics_enabled=False,
                    )
                    publisher = HomiePublisher(config, [state])
                    status_key, time_key = state.diagnostic_keys
                    props = {p.key: p for p in publisher.properties([state])}
                    self.assertIn(status_key, props)
                    self.assertFalse(props[status_key].settable)
                    self.assertNotIn(time_key, props)
                    self.assertEqual(publisher.snapshot([state], now=10)[0][status_key], "init")
                    state.update({"measurements/power": 12}, now=10)
                    self.assertEqual(publisher.snapshot([state], now=10)[0][status_key], "ready")
                    self.assertEqual(publisher.snapshot([state], now=16)[0][status_key], "stale")
                    state.error = True
                    self.assertEqual(publisher.snapshot([state], now=16)[0][status_key], "error")
            commands = SourceState(
                "commands",
                "test-device",
                (),
                5,
                diagnostics_enabled=False,
                contributes_availability=False,
            )
            self.assertEqual(publisher.properties([commands]), ())

    async def test_diagnostics_retirement_and_internal_availability(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = load_config({"SMAB_STATE_DIR": tmp})
            state = SourceState(
                "fixture",
                "test-device",
                (Property("measurements", "power", "Power"),),
                5,
                diagnostics_enabled=False,
            )
            state.update({"measurements/power": 12})
            stop = asyncio.Event()
            client = FakeClient()
            client.stop = stop
            publisher = HomiePublisher(config, [state], lambda *a, **k: client)
            old = {
                "homie/test-device/diagnostics/fixture-status",
                "homie/test-device/diagnostics/fixture-status/$datatype",
                "homie/test-device/device-1/cos-phi-setpoint",
            }
            publisher.owned = {"test-device": old | {"homie/test-device/diagnostics/fixturestatus"}}
            publisher.save_owned()
            publisher = HomiePublisher(config, [state], lambda *a, **k: client)
            self.assertEqual(
                {p.key for p in publisher.properties([state])},
                {"measurements/power", "diagnostics/fixture-status"},
            )
            self.assertEqual(publisher.snapshot([state])[1], "ready")
            await publisher.run(stop)
            messages = [(t, p) for t, p, _ in client.messages]
            for topic in old:
                self.assertIn((topic, b""), messages)
            self.assertIn(("homie/test-device/diagnostics/fixturestatus", "ready"), messages)
            self.assertNotIn(("homie/test-device/diagnostics/fixturestatus", b""), messages)
            self.assertFalse(any("lastsuccess" in t and p != b"" for t, p in messages))
            self.assertIn(("homie/test-device/$state", "ready"), messages)
            self.assertIn(("homie/test-device/measurements/power", "12"), messages)
            state.error = True
            self.assertEqual(publisher.snapshot([state])[1], "alert")
