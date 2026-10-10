"""Configuration precedence, strictness, activation gates and redaction."""

from dataclasses import fields
from pathlib import Path
import ssl
import tempfile
import unittest
from unittest.mock import patch

from sma_mqtt_bridge.config import COMPOSE_KEYS, ECharger, echarger_ssl_context, load_config, ssl_context
from sma_mqtt_bridge.errors import ConfigError
from tests.helpers import validated_profile, write_json

ROOT = Path(__file__).resolve().parents[1]


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.env = {"SMAB_PROFILE_DIR": self.directory.name}

    def enabled(self):
        write_json(self.directory.name, "test-inverter.json", validated_profile())
        return dict(self.env, SMAB_MQTT_HOST="broker.example.invalid", SMAB_MQTT_TLS="false",
                    SMAB_INVERTER1_ENABLED="true", SMAB_INVERTER1_HOST="inverter.example.invalid",
                    SMAB_INVERTER1_PROFILE="test-inverter")

    def test_minimal_all_disabled(self):
        config = load_config({})
        self.assertFalse(config.has_sources)
        self.assertEqual([i.profile for i in config.inverters],
                         ["sma-stp8-0-3av-40", "sma-sbs3-7-10", "sma-sb4-0-1av-41"])

    def test_hosts_and_credentials_do_not_enable_sources(self):
        config = load_config({"SMAB_INVERTER1_HOST": "test.invalid", "SMAB_ECHARGER_PASSWORD": "fixture-password"})
        self.assertFalse(config.has_sources)
        self.assertNotIn("fixture-password", repr(config.echarger))

    def test_disabled_adapter_reads_no_installation_files(self):
        with patch("sma_mqtt_bridge.profiles.load_profile", side_effect=AssertionError), patch("sma_mqtt_bridge.config.ssl_context", side_effect=AssertionError):
            config = load_config({"SMAB_INVERTER1_PROFILE": "file:missing.json",
                                  "SMAB_ECHARGER_PASSWORD_FILE": "/not/present",
                                  "SMAB_MQTT_TLS_CA_FILE": "/not/present"})
        self.assertFalse(config.has_sources)

    def test_profile_defaults_json_env_precedence(self):
        env = self.enabled()
        file = write_json(self.directory.name, "config.json", {"inverters": [{"id": "inverter1", "port": 2502}]})
        env["SMAB_CONFIG_FILE"] = file
        config = load_config(env)
        self.assertEqual(config.inverters[0].port, 2502)
        self.assertEqual(config.inverters[0].unit_id, 4)
        env["SMAB_INVERTER1_PORT"] = "3502"
        config = load_config(env)
        self.assertEqual(config.inverters[0].port, 3502)
        self.assertFalse(config.interval_overrides)

    def test_interval_override_is_explicit_only(self):
        env = self.enabled()
        self.assertFalse(load_config(env).interval_overrides)
        env["SMAB_INVERTER1_POLL_INTERVAL_SECONDS"] = "5"
        self.assertEqual(load_config(env).interval_overrides, frozenset({"inverter1"}))

    def test_json_interval_override(self):
        env = self.enabled()
        env["SMAB_CONFIG_FILE"] = write_json(self.directory.name, "c.json", {
            "inverters": [{"id": "inverter1", "pollIntervalSeconds": 5}]})
        self.assertIn("inverter1", load_config(env).interval_overrides)

    def test_profile_is_reusable_across_arbitrary_slots(self):
        env = self.enabled()
        env.update(SMAB_INVERTER12_ENABLED="true", SMAB_INVERTER12_HOST="second.invalid",
                   SMAB_INVERTER12_PROFILE="test-inverter")
        config = load_config(env)
        self.assertEqual(config.inverters[-1].id, "inverter12")
        self.assertEqual(config.inverters[-1].profile, config.inverters[0].profile)

    def test_identity_only_cannot_enable_polling(self):
        env = self.enabled()
        profile = validated_profile()
        profile.pop("identity")
        profile.update(pollers=[], properties=[])
        profile["validation"]["status"] = "identity-only"
        write_json(self.directory.name, "test-inverter.json", profile)
        with self.assertRaisesRegex(ConfigError, "identity-only"):
            load_config(env)

    def test_local_unverified_tls_override_is_isolated(self):
        verified = echarger_ssl_context(ECharger())
        self.assertTrue(verified.check_hostname)
        self.assertEqual(verified.verify_mode, ssl.CERT_REQUIRED)
        unverified = echarger_ssl_context(ECharger(tls_verify=False, tls_ca_file="/not/present"))
        self.assertFalse(unverified.check_hostname)
        self.assertEqual(unverified.verify_mode, ssl.CERT_NONE)
        self.assertTrue(ssl_context().check_hostname)
        with self.assertRaises(ConfigError):
            echarger_ssl_context(ECharger(tls_ca_file="/not/present"))

    def test_mqtt_unverified_tls_is_explicit_and_keeps_defaults_verified(self):
        env = self.enabled() | {"SMAB_MQTT_TLS": "true", "SMAB_MQTT_TLS_VERIFY": "false",
                                "SMAB_MQTT_TLS_CA_FILE": "/not/present"}
        config = load_config(env)
        self.assertTrue(config.mqtt.tls)
        self.assertFalse(config.mqtt.tls_verify)
        context = ssl_context(config.mqtt.tls_ca_file, verify=config.mqtt.tls_verify)
        self.assertEqual(context.verify_mode, ssl.CERT_NONE)
        self.assertTrue(load_config({}).mqtt.tls_verify)
        self.assertTrue(ssl_context().check_hostname)

    def test_bool_numbers_unknown_options_and_bounds(self):
        cases = {"SMAB_HOME_MANAGER_ENABLED": "1", "SMAB_HOME_MANAGER_PORT": "0",
                 "SMAB_INVERTER1_PORT": "65536", "SMAB_INVERTER1_UNIT_ID": "248",
                 "SMAB_MQTT_TLS": "", "SMAB_MQTT_TLS_VERIFY": "sometimes",
                 "SMAB_HOME_MANAGER_TIMEOUT_SECONDS": "NaN", "SMAB_RECONNECT_MAX_SECONDS": "inf",
                 "SMAB_ECHARGER_API_POLL_INTERVAL_SECONDS": "0", "SMAB_HEALTH_INTERVAL_SECONDS": "",
                 "SMAB_HEALTH_STALE_SECONDS": "10", "SMAB_RECONNECT_MIN_SECONDS": "61",
                 "SMAB_COMMANDS_ENABLED": "true", "SMAB_MQTT_QOS": "0", "SMAB_INVERTER01_ENABLED": "false",
                 "SMAB_SECRET_UNKNOWN": "fixture-secret", "SMAB_MQTT_PORT": "2.5", "SMAB_LOG_LEVEL": "TRACE",
                 "SMAB_TIMEZONE": "../invalid", "SMAB_MQTT_HOMIE_PREFIX": "homie/#",
                 "SMAB_MQTT_TLS_CERT_FILE": "/missing", "SMAB_INVERTER1_HOMIE_ID": "Uppercase",
                 "SMAB_INVERTER3_HOMIE_ID": "sma-inverter1"}
        for key, value in cases.items():
            with self.subTest(key=key), self.assertRaises(ConfigError) as raised:
                load_config({key: value})
            self.assertNotIn("fixture-secret", str(raised.exception))

    def test_explicit_missing_json_is_error(self):
        with self.assertRaises(ConfigError):
            load_config({"SMAB_CONFIG_FILE": "/not/present"})

    def test_json_strict_types_sections_duplicates_and_secrets(self):
        for value in ({"mqtt": {"port": True}}, {"runtime": {"healthIntervalSeconds": "5"}},
                      {"inverters": [{"id": "inverter1"}, {"id": "inverter1"}]},
                      {"unknown": "fixture-secret"}, {"mqtt": {"password": "fixture-secret"}},
                      {"mqtt": {"port": 1e100}}, {"inverters": {"id": "inverter1"}}):
            with self.subTest(value=value), self.assertRaises(ConfigError):
                load_config({"SMAB_CONFIG_FILE": write_json(self.directory.name, "c.json", value)})
        for text in ('{"mqtt":{},"mqtt":{}}', '{"runtime":{"healthIntervalSeconds":NaN}}'):
            path = Path(self.directory.name) / "c.json"
            path.write_text(text)
            with self.assertRaises(ConfigError):
                load_config({"SMAB_CONFIG_FILE": str(path)})

    def test_empty_optional_string_clears_json(self):
        filename = write_json(self.directory.name, "c.json", {"mqtt": {"tlsCaFile": "/missing"}})
        config = load_config({"SMAB_CONFIG_FILE": filename, "SMAB_MQTT_TLS_CA_FILE": ""})
        self.assertEqual(config.mqtt.tls_ca_file, "")

    def test_compose_variables_are_recognized(self):
        self.assertFalse(load_config({"SMAB_DATA_DIR": "ignored", "SMAB_BRIDGE_VERSION": "dev", "SMAB_ENV_FILE": "ignored"}).has_sources)

    def test_public_json_and_complete_env_example(self):
        load_config({"SMAB_CONFIG_FILE": str(ROOT / "config.example.json")})
        env = {}
        lines = (ROOT / "smab.example.env").read_text().splitlines()
        for index, line in enumerate(lines):
            line = line.removeprefix("# ")
            if line.startswith("SMAB_") and "=" in line:
                key, value = line.split("=", 1)
                self.assertNotIn(key, env, "Duplicate documented ENV variable")
                self.assertTrue(lines[index - 1].startswith("# Type:"))
                self.assertTrue(lines[index - 2].startswith("# "))
                env[key] = value
        defaults = load_config({})
        expected = COMPOSE_KEYS | {"SMAB_CONFIG_FILE"}
        sections = [("SMAB_", defaults.runtime), ("SMAB_MQTT_", defaults.mqtt),
                    ("SMAB_HOME_MANAGER_", defaults.home_manager), ("SMAB_ECHARGER_", defaults.echarger),
                    ("SMAB_PORTAL_", defaults.portal), ("SMAB_COMMAND_", defaults.commands)]
        sections.extend((f"SMAB_INVERTER{n}_", device) for n, device in enumerate(defaults.inverters, 1))
        for prefix, section in sections:
            for field in fields(section):
                if field.name == "id":
                    continue
                key = prefix + field.name.upper()
                if key == "SMAB_COMMAND_ENABLED":
                    key = "SMAB_COMMANDS_ENABLED"
                expected.add(key)
                value = getattr(section, field.name)
                if key != "SMAB_MQTT_HOST":
                    if isinstance(value, bool):
                        self.assertEqual(env[key], str(value).lower())
                    elif isinstance(value, (int, float)):
                        self.assertEqual(float(env[key]), value)
                    else:
                        self.assertEqual(env[key], value)
        self.assertEqual(set(env), expected, "Example must cover every supported ENV option")
        self.assertEqual(env["SMAB_ENV_FILE"], "./smab.env")
        self.assertFalse(load_config({k: v for k, v in env.items() if k != "SMAB_CONFIG_FILE"}).has_sources)

    def test_separate_semp_gate_needs_no_api_credentials(self):
        config = load_config({"SMAB_ECHARGER_SEMP_ENABLED": "true", "SMAB_ECHARGER_HOST": "charger.invalid",
                              "SMAB_ECHARGER_SEMP_DEVICE_ID": "synthetic", "SMAB_MQTT_HOST": "broker.invalid",
                              "SMAB_MQTT_TLS": "false"})
        self.assertTrue(config.echarger.semp_enabled)
        self.assertFalse(config.echarger.enabled)

    def test_enabled_sources_require_installation_fields(self):
        for env in ({"SMAB_HOME_MANAGER_ENABLED": "true"}, {"SMAB_ECHARGER_ENABLED": "true"}, {"SMAB_PORTAL_ENABLED": "true"}):
            with self.subTest(env=env), self.assertRaises(ConfigError):
                load_config(dict(env, SMAB_MQTT_HOST="broker.invalid", SMAB_MQTT_TLS="false"))

    def test_password_file_precedence_conflict_and_no_persistence(self):
        path = Path(self.directory.name) / "password"
        path.write_text("fixture-password\n")
        env = self.enabled() | {"SMAB_MQTT_PASSWORD_FILE": str(path)}
        before = {p.name: p.read_bytes() for p in Path(self.directory.name).iterdir()}
        config = load_config(env)
        self.assertEqual(config.mqtt.password, "fixture-password")
        self.assertNotIn("fixture-password", repr(config.mqtt))
        self.assertEqual(before, {p.name: p.read_bytes() for p in Path(self.directory.name).iterdir()})
        env["SMAB_MQTT_PASSWORD"] = "other"
        with self.assertRaises(ConfigError):
            load_config(env)

    def test_boolean_case_insensitivity_and_zero_portal_interval(self):
        config = load_config({"SMAB_MQTT_TLS": "FaLsE", "SMAB_PORTAL_POLL_INTERVAL_SECONDS": "0"})
        self.assertFalse(config.mqtt.tls)
        self.assertEqual(config.portal.poll_interval_seconds, 0)
