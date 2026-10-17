"""Regression coverage for display dictionaries and stable compact MQTT IDs."""

import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from sma_mqtt_bridge.config import load_config
from sma_mqtt_bridge.errors import ConfigError
from sma_mqtt_bridge.homie import HomiePublisher, discovery, publication_property
from sma_mqtt_bridge.model import Property, SourceState
from sma_mqtt_bridge.translation import BUNDLED, load_translation


class TranslationTests(unittest.TestCase):
    def test_bundled_languages_cover_the_same_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            en, de = (load_translation(lang, tmp) for lang in ("en", "de"))
        self.assertEqual(en.keys(), de.keys())
        self.assertEqual(de["Internal temperature"], "Interne Temperatur")
        self.assertEqual(de["Device {number}"], "Gerät {number}")
        self.assertGreater(len(en), 100)
        self.assertTrue((BUNDLED / "en.json").is_file())

    def test_bundled_profiles_have_concrete_translated_labels(self):
        labels = load_translation("de", "/nonexistent-smab-translation-fixture")
        for path in (BUNDLED.parent / "profiles").glob("*.json"):
            data = json.loads(path.read_text())
            for prop in data["properties"] + data.get("delegated", {}).get("properties", []):
                self.assertNotEqual(prop["name"], "-", (path.name, prop["id"]))
                self.assertIn(prop["name"], labels, (path.name, prop["id"]))
        self.assertEqual(labels["Battery state of charge"], "Batterieladezustand")

    def test_inverter_display_names_preserve_topics_and_storage_power(self):
        power = Property("measurements", "active-power", "Power", unit="W")
        day = Property("measurements", "day-yield", "Daily yield", unit="kWh")
        soc = Property("measurements", "current-bat-stat-charge", "Battery state of charge")
        pv = SourceState("inverter1", "pv", (power, day), 180)
        storage = SourceState("inverter2", "battery", (power, day, soc), 180)
        self.assertEqual(publication_property(pv, power).name, "PV production")
        self.assertEqual(publication_property(storage, power), power)
        for state, expected in ((pv, "Daily yield"), (storage, "Daily discharge")):
            published = publication_property(state, day)
            self.assertEqual(published.name, expected)
            self.assertEqual(published.key, "measurements/daily-yield")
            self.assertEqual(published.unit, "kWh")
        self.assertEqual(power.name, "Power")
        self.assertEqual(day.key, "measurements/day-yield")

    def test_custom_language_partial_override_and_config_precedence(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "fr.json").write_text(
                json.dumps({"schemaVersion": 1, "labels": {"Measurements": "Mesures"}})
            )
            labels = load_translation("fr", tmp)
            self.assertEqual(labels["Measurements"], "Mesures")
            self.assertEqual(labels["Internal temperature"], "Internal temperature")
            Path(tmp, "de.json").write_text(
                json.dumps(
                    {"schemaVersion": 1, "labels": {"Internal temperature": "Temperatur innen"}}
                )
            )
            self.assertEqual(
                load_translation("de", tmp)["Internal temperature"], "Temperatur innen"
            )
            config_file = Path(tmp, "config.json")
            config_file.write_text(json.dumps({"runtime": {"language": "fr", "translateDir": tmp}}))
            config = load_config({"SMAB_CONFIG_FILE": str(config_file), "SMAB_LANGUAGE": "de"})
            self.assertEqual(config.runtime.language, "de")
            self.assertEqual(config.runtime.translate_dir, tmp)

    def test_invalid_language_and_files_fail_before_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            for language in ("../de", "DE", "", "missing"):
                with self.assertRaises(ConfigError):
                    load_config({"SMAB_LANGUAGE": language, "SMAB_TRANSLATE_DIR": tmp})
            for contents in (
                "null",
                '{"schemaVersion":1,"labels":{"Power":"A","Power":"B"}}',
                '{"schemaVersion":true,"labels":{}}',
                '{"schemaVersion":1,"labels":{"Power":""}}',
                '{"schemaVersion":1,"labels":{"Device {number}":"Gerät"}}',
                '{"schemaVersion":1,"labels":{"Power":12}}',
            ):
                Path(tmp, "de.json").write_text(contents)
                with self.assertRaises(ConfigError):
                    load_config({"SMAB_LANGUAGE": "de", "SMAB_TRANSLATE_DIR": tmp})
            Path(tmp, "de.json").unlink()
            Path(tmp, "de.json").symlink_to(BUNDLED / "de.json")
            with self.assertRaises(ConfigError):
                load_translation("de", tmp)
            Path(tmp, "de.json").unlink()
            Path(tmp, "de.json").write_text(" " * 1048577)
            with self.assertRaises(ConfigError):
                load_translation("de", tmp)

    def test_discovery_translates_names_only_and_compacts_nodes(self):
        with tempfile.TemporaryDirectory() as tmp:
            labels = load_translation("de", tmp)
        props = (
            Property("measurements", "internal-temperature", "Internal temperature", unit="°C"),
            Property(
                "device-1",
                "charge-mode",
                "Charging mode",
                "enum",
                format="4718,4719",
                settable=True,
            ),
        )
        en = discovery("homie", "sma-wr1", props)
        de = discovery("homie", "sma-wr1", props, labels, "Inverter")
        self.assertEqual(en.keys(), de.keys())
        self.assertEqual(de["homie/sma-wr1/$name"], "Wechselrichter")
        self.assertEqual(de["homie/sma-wr1/device1/$name"], "Gerät 1")
        self.assertEqual(de["homie/sma-wr1/device1/$type"], "device")
        self.assertEqual(de["homie/sma-wr1/measurements/$type"], "measurements")
        self.assertEqual(
            de["homie/sma-wr1/measurements/internaltemperature/$name"], "Interne Temperatur"
        )
        self.assertEqual(de["homie/sma-wr1/device1/$properties"], "chargemode")
        self.assertEqual(de["homie/sma-wr1/$nodes"], "device1,measurements")
        for key in en:
            if not key.endswith("/$name"):
                self.assertEqual(en[key], de[key])

    def test_compact_collisions_fail_closed(self):
        for props in (
            (Property("measurements", "a-b", "First"), Property("measurements", "ab", "Second")),
            (Property("device-1", "x", "First"), Property("device1", "y", "Second")),
        ):
            with self.assertRaises(ConfigError):
                discovery("homie", "fixture", props)


class TranslationPublisherTests(unittest.IsolatedAsyncioTestCase):
    async def test_upgrade_retires_old_topics_publishes_compact_values_and_subscribes(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = load_config({"SMAB_STATE_DIR": tmp, "SMAB_LANGUAGE": "de"})
            state = SourceState(
                "api",
                "sma-echarger",
                (
                    Property(
                        "settings",
                        "charge-mode",
                        "Charging mode",
                        "enum",
                        format="4718,4719",
                        settable=True,
                    ),
                ),
                60,
                diagnostics_enabled=False,
            )
            state.update({"settings/charge-mode": "4719"})
            stop = asyncio.Event()
            messages, subscriptions = [], []

            class Client:
                def __init__(self, *args, **kwargs):
                    self.messages = self.incoming()

                async def incoming(self):
                    await asyncio.Event().wait()
                    yield None

                async def __aenter__(self):
                    return self

                async def __aexit__(self, *args):
                    return None

                async def publish(self, topic, payload, **kwargs):
                    messages.append((topic, payload))
                    if topic.endswith("/settings/chargemode") and payload == "4719":
                        stop.set()

                async def subscribe(self, topic, **kwargs):
                    subscriptions.append(topic)

            publisher = HomiePublisher(config, [state], Client)
            old = {
                "homie/sma-echarger/settings/charge-mode",
                "homie/sma-echarger/settings/charge-mode/$name",
            }
            publisher.owned = {"sma-echarger": old}
            publisher.command_controller = object()
            await asyncio.wait_for(publisher.serve_device(state.device, [state], stop), 3)
            for topic in old:
                self.assertIn((topic, b""), messages)
            self.assertIn(("homie/sma-echarger/settings/chargemode", "4719"), messages)
            self.assertIn(("homie/sma-echarger/settings/chargemode/$name", "Lademodus"), messages)
            self.assertEqual(subscriptions, ["homie/sma-echarger/settings/chargemode/set"])
            self.assertFalse(old & publisher.owned[state.device])
