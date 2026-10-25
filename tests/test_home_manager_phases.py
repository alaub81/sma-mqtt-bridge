"""Deterministic phase decoding and independent Modbus/UDP ownership."""

import json
import struct
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from sma_mqtt_bridge.adapters.meter import MeterReader, parse_telegram
from sma_mqtt_bridge.config import HomeManager, load_config
from sma_mqtt_bridge.errors import ConfigError, ProtocolError
from sma_mqtt_bridge.homie import HomiePublisher
from sma_mqtt_bridge.model import SourceState
from sma_mqtt_bridge.plant import plant_plan
from sma_mqtt_bridge.runtime import sources


def telegram(records, serial=123, counter=1):
    header = bytearray(28)
    header[:4] = b"SMA\0"
    header[16:18] = b"\x60\x69"
    header[20:28] = struct.pack(">II", serial, counter)
    return bytes(header) + b"".join(struct.pack(">II", *r) for r in records) + bytes(4)


PHASE_RECORDS = [
    (0x00150400, 12345),
    (0x00160400, 0),
    (0x001F0400, 6123),
    (0x00200400, 230123),
    (0x00290400, 0),
    (0x002A0400, 23456),
    (0x00330400, 7123),
    (0x00340400, 231123),
    (0x003D0400, 34567),
    (0x003E0400, 0),
    (0x00470400, 8123),
    (0x00480400, 232123),
]


class PhaseProtocolTests(unittest.TestCase):
    def test_all_phases_units_scaling_and_separate_directions(self):
        _, values = parse_telegram(telegram(PHASE_RECORDS), "123")
        self.assertEqual(len(values), 12)
        for phase, expected in enumerate(("1234.5", "0", "3456.7"), 1):
            self.assertEqual(values[f"measurements/power-drawn-l{phase}"], Decimal(expected))
            self.assertEqual(
                values[f"measurements/current-l{phase}"], Decimal(phase + 5) + Decimal(".123")
            )
            self.assertEqual(
                values[f"measurements/voltage-l{phase}"], Decimal(phase + 229) + Decimal(".123")
            )
        self.assertEqual(values["measurements/power-grid-feed-in-l2"], Decimal("2345.6"))
        self.assertIsNone(parse_telegram(telegram(PHASE_RECORDS, serial=456), "123"))

    def test_documented_channel_one_and_mixed_duplicate_rejected(self):
        records = [(code | 0x01000000, raw) for code, raw in PHASE_RECORDS]
        self.assertEqual(
            parse_telegram(telegram(records), "123"),
            parse_telegram(telegram(PHASE_RECORDS), "123"),
        )
        with self.assertRaises(ProtocolError):
            parse_telegram(telegram(PHASE_RECORDS[:1] + records[:1]), "123")

    def test_missing_channels_not_invented_and_duplicates_rejected(self):
        _, values = parse_telegram(telegram(PHASE_RECORDS[:1]), "123")
        self.assertEqual(values, {"measurements/power-drawn-l1": Decimal("1234.5")})
        with self.assertRaises(ProtocolError):
            parse_telegram(telegram(PHASE_RECORDS[:1] * 2), "123")
        with self.assertRaises(ProtocolError):
            parse_telegram(telegram(PHASE_RECORDS)[:-5], "123")

    def test_phase_metadata_readonly_basic_and_main_readiness_unchanged(self):
        reader = MeterReader(HomeManager())
        state = SourceState("home-manager", "meter", reader.properties, 30)
        self.assertEqual(
            state.required_keys, ("measurements/power-import", "measurements/power-export")
        )
        for prop in MeterReader(HomeManager(), phases_only=True).properties:
            self.assertFalse(prop.settable)
            self.assertEqual(prop.channel_group, "basic")
            self.assertEqual(
                prop.unit,
                "A"
                if prop.id.startswith("current")
                else "V"
                if prop.id.startswith("voltage")
                else "W",
            )


class SupplementalRuntimeTests(unittest.TestCase):
    def config(self, directory, **overrides):
        return load_config(
            {
                "SMAB_STATE_DIR": directory,
                "SMAB_MQTT_HOST": "broker.invalid",
                "SMAB_HOME_MANAGER_ENABLED": "true",
                "SMAB_HOME_MANAGER_HOST": "meter.invalid",
                "SMAB_HOME_MANAGER_SERIAL": "123",
                "SMAB_HOME_MANAGER_UDP_PHASES_ENABLED": "true",
            }
            | overrides
        )

    def test_explicit_activation_no_duplicate_owners_and_independent_expiry(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.config(directory)
            entries = sources(config)
            self.assertEqual([s.id for s, _, _ in entries], ["home-manager", "home-manager-phases"])
            main, extra = entries[0][0], entries[1][0]
            self.assertFalse(extra.contributes_availability)
            self.assertFalse({p.key for p in main.properties} & {p.key for p in extra.properties})
            self.assertEqual(entries[1][1].settings.host, "")
            main.update({"measurements/power-import": 100, "measurements/power-export": 0}, now=100)
            _, values = parse_telegram(telegram(PHASE_RECORDS), "123")
            extra.update(values, now=100)
            main.update({"measurements/power-import": 200, "measurements/power-export": 0}, now=129)
            self.assertEqual(extra.fresh_values(now=131), {})
            self.assertEqual(main.fresh_values(now=131)["measurements/power-import"], "200")
            extra.error = True
            publisher = HomiePublisher(config, [main, extra])
            self.assertEqual(publisher.snapshot([main, extra], now=131)[1], "ready")
            main.error = True
            self.assertEqual(publisher.snapshot([main, extra], now=131)[1], "alert")
            main.error = False
            props = publisher.properties([main, extra])
            metadata = publisher.metadata(main.device, props)
            root = "homie/sma-home-manager/measurements/"
            self.assertEqual(metadata[root + "powerdrawnl1/$unit"], "W")
            self.assertEqual(metadata[root + "currentl3/$unit"], "A")
            self.assertNotIn(root + "powerdrawnl1/set", metadata)
            self.assertEqual(
                len(sources(self.config(directory, SMAB_HOME_MANAGER_UDP_PHASES_ENABLED="false"))),
                1,
            )
            self.assertEqual(sources(self.config(directory, SMAB_HOME_MANAGER_ENABLED="false")), [])
            self.assertEqual(
                len(
                    sources(
                        self.config(
                            directory,
                            SMAB_HOME_MANAGER_TRANSPORT="udp",
                            SMAB_HOME_MANAGER_HOST="192.0.2.1",
                        )
                    )
                ),
                1,
            )

    def test_json_env_precedence_and_energy_binding_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(
                json.dumps({"homeManager": {"udpPhasesEnabled": True, "udpHost": "192.0.2.5"}})
            )
            config = load_config({"SMAB_CONFIG_FILE": str(path)})
            self.assertTrue(config.home_manager.udp_phases_enabled)
            self.assertFalse(config.home_manager.enabled)
            override = load_config(
                {"SMAB_CONFIG_FILE": str(path), "SMAB_HOME_MANAGER_UDP_PHASES_ENABLED": "false"}
            )
            self.assertFalse(override.home_manager.udp_phases_enabled)
            enabled = self.config(directory)
            disabled = self.config(directory, SMAB_HOME_MANAGER_UDP_PHASES_ENABLED="false")
            self.assertEqual(plant_plan(enabled), plant_plan(disabled))

    def test_udp_sender_filter_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.config(directory, SMAB_HOME_MANAGER_UDP_HOST="192.0.2.10")
            self.assertEqual(sources(config)[1][1].settings.host, "192.0.2.10")
            with self.assertRaises(ConfigError):
                self.config(directory, SMAB_HOME_MANAGER_UDP_HOST="invalid.example")
            with self.assertRaises(ConfigError):
                self.config(directory, SMAB_HOME_MANAGER_UDP_PHASES_ENABLED="yes-please")


class SupplementalReceiveTests(unittest.IsolatedAsyncioTestCase):
    async def test_filter_serial_counter_and_exclude_total_values(self):
        reader = MeterReader(HomeManager(serial="123", host="192.0.2.1"), phases_only=True)
        reader.socket = object()
        frame = telegram([(0x00010400, 999)] + PHASE_RECORDS)
        receive = AsyncMock(
            side_effect=[
                (frame, ("192.0.2.2", 9522)),
                (telegram(PHASE_RECORDS, serial=456), ("192.0.2.1", 9522)),
                (frame, ("192.0.2.1", 9522)),
                (frame, ("192.0.2.1", 9522)),
                (telegram(PHASE_RECORDS[:1], counter=2), ("192.0.2.1", 9522)),
            ]
        )
        with patch(
            "sma_mqtt_bridge.adapters.meter.asyncio.get_running_loop",
            return_value=SimpleNamespace(sock_recvfrom=receive),
        ):
            values = await reader.read()
            self.assertEqual(len(values), 12)
            self.assertNotIn("measurements/power-import", values)
            second = await reader.read()
            self.assertEqual(len(second), 1)
        self.assertEqual(receive.await_count, 5)
