"""Strict defaults < profile < JSON < ENV precedence and local file reads, without network I/O."""

import ipaddress
import json
import math
import os
import re
import ssl
from dataclasses import dataclass, fields, replace
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .errors import ConfigError

DATA = "/data/sma-mqtt-bridge"
ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
SLOT = re.compile(r"inverter([1-9][0-9]*)\Z")
COMPOSE_KEYS = {"SMAB_BRIDGE_VERSION", "SMAB_DATA_DIR", "SMAB_ENV_FILE", "SMAB_UID", "SMAB_GID"}
DEFAULT_PROFILES = ("sma-stp8-0-3av-40", "sma-sbs3-7-10", "sma-sb4-0-1av-41")


class SafeRepr:
    def __repr__(self):
        return f"<{type(self).__name__}: values withheld>"


@dataclass(frozen=True, repr=False)
class Runtime(SafeRepr):
    language: str = "en"
    translate_dir: str = DATA + "/translate"
    profile_dir: str = DATA + "/profiles"
    state_dir: str = DATA + "/state"
    timezone: str = "Europe/Berlin"
    log_level: str = "INFO"
    health_interval_seconds: float = 10.0
    health_stale_seconds: float = 60.0
    shutdown_timeout_seconds: float = 10.0
    reconnect_min_seconds: float = 1.0
    reconnect_max_seconds: float = 60.0
    max_response_bytes: int = 1048576
    max_state_bytes: int = 1048576
    read_cycle_timeout_seconds: float = 120.0
    failure_log_interval_seconds: float = 300.0


@dataclass(frozen=True, repr=False)
class MQTT(SafeRepr):
    host: str = ""
    port: int = 8883
    username: str = ""
    password: str = ""
    password_file: str = ""
    client_id: str = "sma-mqtt-bridge"
    homie_prefix: str = "homie"
    tls: bool = True
    tls_verify: bool = True
    tls_ca_file: str = ""
    tls_cert_file: str = ""
    tls_key_file: str = ""
    keepalive_seconds: int = 60
    connect_timeout_seconds: float = 10.0
    qos: int = 1
    max_queue_messages: int = 1000


@dataclass(frozen=True, repr=False)
class Inverter(SafeRepr):
    ready_properties: str = ""
    advanced_channels_enabled: bool = True
    diagnostics_enabled: bool = True
    id: str = ""
    enabled: bool = False
    host: str = ""
    port: int = 502
    unit_id: int = 3
    profile: str = ""
    expected_serial: str = ""
    homie_id: str = ""
    poll_interval_seconds: float = 10.0
    timeout_seconds: float = 5.0
    stale_seconds: float = 60.0
    commands_enabled: bool = False


@dataclass(frozen=True, repr=False)
class HomeManager(SafeRepr):
    ready_properties: str = ""
    advanced_channels_enabled: bool = True
    diagnostics_enabled: bool = True
    transport: str = "udp"
    profile: str = "sma-home-manager-2-modbus"
    modbus_port: int = 502
    poll_interval_seconds: float = 3.0
    connect_timeout_seconds: float = 5.0
    transaction_delay_seconds: float = 0.2
    after_connection_delay_seconds: float = 3.0
    reconnect_delay_seconds: float = 5.0
    enabled: bool = False
    host: str = ""
    serial: str = ""
    interface_address: str = "0.0.0.0"
    bind_address: str = "0.0.0.0"
    port: int = 9522
    multicast_enabled: bool = True
    multicast_group: str = "239.12.255.254"
    timeout_seconds: float = 5.0
    stale_seconds: float = 30.0
    homie_id: str = "sma-home-manager"


@dataclass(frozen=True, repr=False)
class ECharger(SafeRepr):
    api_ready_properties: str = ""
    semp_ready_properties: str = ""
    advanced_channels_enabled: bool = True
    diagnostics_enabled: bool = True
    timestamp_diagnostics_enabled: bool = False
    timestamp_diagnostics_max_bytes: int = 1048576
    timestamp_diagnostics_summary_interval_seconds: float = 300.0
    enabled: bool = False
    host: str = ""
    port: int = 443
    username: str = ""
    password: str = ""
    password_file: str = ""
    tls_ca_file: str = ""
    tls_verify: bool = True
    expected_serial: str = ""
    tls_server_name: str = ""
    api_poll_interval_seconds: float = 60.0
    semp_enabled: bool = False
    semp_port: int = 80
    semp_path: str = "/SEMP/"
    semp_poll_interval_seconds: float = 30.0
    semp_device_id: str = ""
    timeout_seconds: float = 10.0
    stale_seconds: float = 180.0
    homie_id: str = "sma-echarger"
    commands_enabled: bool = False


@dataclass(frozen=True, repr=False)
class Portal(SafeRepr):
    ready_properties: str = ""
    diagnostics_enabled: bool = True
    enabled: bool = False
    base_url: str = "https://ennexos.sunnyportal.com"
    api_base_url: str = "https://uiapi.sunnyportal.com/api/v1"
    auth_base_url: str = "https://login.sma.energy/auth/realms/SMA"
    client_id: str = "SPpbeOS"
    username: str = ""
    password: str = ""
    password_file: str = ""
    plant_id: str = ""
    device_id: str = ""
    timeout_seconds: float = 15.0
    poll_interval_seconds: float = 0.0
    stale_seconds: float = 180.0
    commands_enabled: bool = False


@dataclass(frozen=True, repr=False)
class Commands(SafeRepr):
    enabled: bool = False
    readback_timeout_seconds: float = 30.0
    readback_interval_seconds: float = 1.0


@dataclass(frozen=True, repr=False)
class Config(SafeRepr):
    runtime: Runtime
    mqtt: MQTT
    inverters: tuple
    home_manager: HomeManager
    echarger: ECharger
    portal: Portal
    commands: Commands
    profiles: dict
    interval_overrides: frozenset

    @property
    def has_sources(self):
        return (
            any(i.enabled for i in self.inverters)
            or self.home_manager.enabled
            or self.echarger.enabled
            or self.echarger.semp_enabled
            or self.portal.enabled
        )


def camel(name):
    first, *rest = name.split("_")
    return first + "".join(part.title() for part in rest)


def read_json(path):
    """Reject ambiguous keys and non-standard numbers without echoing file data."""

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError
            result[key] = value
        return result

    def constant(_):
        raise ValueError

    try:
        with Path(path).open(encoding="utf-8") as stream:
            return json.load(stream, object_pairs_hook=pairs, parse_constant=constant)
    except OSError, ValueError, UnicodeError:
        raise ConfigError("Cannot read a valid JSON configuration/profile file") from None


def convert(value, kind, key, env=False):
    try:
        if env:
            if kind is bool:
                if value.lower() not in ("true", "false"):
                    raise ValueError
                return value.lower() == "true"
            if kind is int:
                if not re.fullmatch(r"[+-]?[0-9]+", value):
                    raise ValueError
                return int(value)
            if kind is float:
                number = float(value)
                if not math.isfinite(number):
                    raise ValueError
                return number
        if kind is float and type(value) in (int, float):
            if not math.isfinite(value):
                raise ValueError
            return float(value)
        if type(value) is not kind:
            raise ValueError
        if kind is str and any(ord(c) < 32 for c in value):
            raise ValueError
        return value
    except ValueError, TypeError, AttributeError, OverflowError:
        raise ConfigError(f"Invalid type/value for {key}") from None


def section(defaults, data, env, prefix, recognized):
    if not isinstance(data, dict):
        raise ConfigError("Configuration section must be an object")
    definitions = {camel(f.name): f for f in fields(defaults)}
    if set(data) - set(definitions):
        raise ConfigError("Unknown JSON configuration option")
    if any(key in data for key in ("password", "username")):
        raise ConfigError("Supply account credentials through ENV or password files")
    values = {}
    for name, field in definitions.items():
        key = prefix + field.name.upper()
        if field.name == "id":
            if name in data and data[name] != defaults.id:
                raise ConfigError("Inverter slot identity mismatch")
            continue
        recognized.add(key)
        value = getattr(defaults, field.name)
        if name in data:
            value = convert(data[name], field.type, key)
        if key in env:
            value = convert(env[key], field.type, key, env=True)
        # Numeric ranges also apply to disabled sections.
        if field.type in (float, int):
            minimum, maximum = 0, None
            if field.name.endswith("port"):
                minimum, maximum = 1, 65535
            elif field.name == "unit_id":
                minimum, maximum = 1, 247
            elif field.name == "qos":
                minimum, maximum = 1, 2
            elif field.name in (
                "max_queue_messages",
                "max_response_bytes",
                "max_state_bytes",
                "keepalive_seconds",
            ):
                minimum = 1
            elif field.name == "timestamp_diagnostics_max_bytes":
                minimum, maximum = 4096, 16777216
            elif not (
                (isinstance(defaults, Portal) and field.name == "poll_interval_seconds")
                or (
                    isinstance(defaults, HomeManager)
                    and field.name
                    in (
                        "transaction_delay_seconds",
                        "after_connection_delay_seconds",
                        "reconnect_delay_seconds",
                    )
                )
            ):
                if value <= 0:
                    raise ConfigError(f"Positive number required for {key}")
            if value < minimum or (maximum is not None and value > maximum):
                raise ConfigError(f"Out of range: {key}")
        values[field.name] = value
        if field.name.endswith("ready_properties") and value:
            entries = value.split(",")
            if len(set(entries)) != len(entries) or any(
                len(k.split("/")) != 2 or not all(ID.fullmatch(p) for p in k.split("/"))
                for k in entries
            ):
                raise ConfigError("Readiness properties must be unique node/property keys")
    return replace(defaults, **values)


def valid_host(value):
    if not value or value.strip() != value or any(c in value for c in "/@?#% "):
        return False
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return bool(re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?", value))


def require_host(value, label):
    if not valid_host(value):
        raise ConfigError(f"A valid host is required for {label}")


def https_url(value):
    try:
        parsed = urlsplit(value)
        return (
            parsed.scheme == "https"
            and parsed.hostname
            and not parsed.username
            and not parsed.password
            and not parsed.query
            and not parsed.fragment
            and parsed.port in (None, 443)
        )
    except ValueError:
        return False


def ssl_context(ca="", cert="", key="", *, verify=True):
    try:
        context = ssl.create_default_context(cafile=(ca or None) if verify else None)
        if not verify:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        if cert:
            context.load_cert_chain(cert, key)
        return context
    except OSError, ValueError, ssl.SSLError:
        raise ConfigError("Cannot load configured TLS trust/client certificate") from None


def echarger_ssl_context(settings):
    """An explicit installation override applies only to the local wallbox."""
    return ssl_context(settings.tls_ca_file, verify=settings.tls_verify)


def password(settings, active):
    if settings.password and settings.password_file:
        raise ConfigError("Choose PASSWORD or PASSWORD_FILE, never both")
    if settings.password_file and active:
        try:
            value = Path(settings.password_file).read_text(encoding="utf-8").rstrip("\r\n")
            if not value or "\n" in value or "\r" in value:
                raise ValueError
        except OSError, ValueError, UnicodeError:
            raise ConfigError("Cannot read configured password file") from None
        settings = replace(settings, password=value)
    return settings


def load_config(environ=None, bundled_dir=None):
    """Load/validate before any network connection; never modify host files."""
    from .profiles import load_profile

    env = dict(os.environ if environ is None else environ)
    filename = env.get("SMAB_CONFIG_FILE", DATA + "/config.json")
    if not filename:
        raise ConfigError("SMAB_CONFIG_FILE must not be empty")
    explicit = "SMAB_CONFIG_FILE" in env
    data = read_json(filename) if explicit or Path(filename).exists() else {}
    if not isinstance(data, dict) or set(data) - {
        "schemaVersion",
        "runtime",
        "mqtt",
        "inverters",
        "homeManager",
        "echarger",
        "portal",
        "commands",
    }:
        raise ConfigError("Unknown JSON configuration section")
    if "schemaVersion" in data and (
        type(data["schemaVersion"]) is not int or data["schemaVersion"] != 1
    ):
        raise ConfigError("Unsupported configuration schemaVersion")
    recognized = COMPOSE_KEYS | {"SMAB_CONFIG_FILE"}
    runtime = section(Runtime(), data.get("runtime", {}), env, "SMAB_", recognized)
    from .translation import load_translation

    load_translation(runtime.language, runtime.translate_dir)
    mqtt = section(MQTT(), data.get("mqtt", {}), env, "SMAB_MQTT_", recognized)
    hm = section(HomeManager(), data.get("homeManager", {}), env, "SMAB_HOME_MANAGER_", recognized)
    ec = section(ECharger(), data.get("echarger", {}), env, "SMAB_ECHARGER_", recognized)
    portal = section(Portal(), data.get("portal", {}), env, "SMAB_PORTAL_", recognized)
    commands = section(Commands(), data.get("commands", {}), env, "SMAB_COMMAND_", recognized)
    # Global enable flag has the established plural name.
    recognized.add("SMAB_COMMANDS_ENABLED")
    if "SMAB_COMMAND_ENABLED" in env:
        raise ConfigError("Use SMAB_COMMANDS_ENABLED")
    if "SMAB_COMMANDS_ENABLED" in env:
        commands = replace(
            commands,
            enabled=convert(env["SMAB_COMMANDS_ENABLED"], bool, "SMAB_COMMANDS_ENABLED", True),
        )
    raw_inverters = data.get("inverters", [])
    if not isinstance(raw_inverters, list):
        raise ConfigError("inverters must be an array")
    indexed = {}
    for item in raw_inverters:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("id"), str)
            or not SLOT.fullmatch(item["id"])
        ):
            raise ConfigError("Each inverter needs a numbered id")
        if item["id"] in indexed:
            raise ConfigError("Duplicate inverter slot")
        indexed[item["id"]] = item
    slots = {1, 2, 3} | {int(SLOT.fullmatch(k)[1]) for k in indexed}
    for key in env:
        match = re.fullmatch(r"SMAB_INVERTER([1-9][0-9]*)_.+", key)
        if match:
            slots.add(int(match[1]))
    inverters, profiles, intervals = [], {}, set()
    for number in sorted(slots):
        slot = f"inverter{number}"
        prefix = f"SMAB_INVERTER{number}_"
        default = Inverter(
            id=slot,
            homie_id=f"sma-{slot}",
            profile=DEFAULT_PROFILES[number - 1] if number <= 3 else "",
        )
        device_data = indexed.get(slot, {})
        selector = env.get(prefix + "PROFILE", device_data.get("profile", default.profile))
        enabled = (
            convert(env[prefix + "ENABLED"], bool, prefix + "ENABLED", True)
            if prefix + "ENABLED" in env
            else device_data.get("enabled", False)
        )
        # Disabled devices do not read installation profile files.
        if enabled is True:
            profile = load_profile(
                selector, runtime.profile_dir, bundled_dir, require_validated=True
            )
            profiles[slot] = profile
            default = replace(default, **profile["protocol"]["defaults"])
        device = section(default, device_data, env, prefix, recognized)
        if "pollIntervalSeconds" in device_data or prefix + "POLL_INTERVAL_SECONDS" in env:
            intervals.add(slot)
        inverters.append(device)
    if any(key.startswith("SMAB_") and key not in recognized for key in env):
        raise ConfigError("Unknown SMAB_ environment option")
    if runtime.health_stale_seconds <= runtime.health_interval_seconds:
        raise ConfigError("Health stale threshold must exceed heartbeat interval")
    if runtime.reconnect_max_seconds < runtime.reconnect_min_seconds:
        raise ConfigError("Reconnect maximum must be at least the minimum")
    if runtime.log_level not in ("DEBUG", "INFO", "WARNING", "ERROR"):
        raise ConfigError("Invalid SMAB_LOG_LEVEL")
    try:
        ZoneInfo(runtime.timezone)
    except ValueError, ZoneInfoNotFoundError:
        raise ConfigError("Invalid SMAB_TIMEZONE") from None
    ids = [i.homie_id for i in inverters] + [hm.homie_id, ec.homie_id]
    if any(not ID.fullmatch(i) for i in ids) or len(ids) != len(set(ids)):
        raise ConfigError("Invalid or duplicate Homie device IDs")
    if not ID.fullmatch(mqtt.homie_prefix) or not mqtt.client_id:
        raise ConfigError("Invalid MQTT prefix/client ID")
    if bool(mqtt.tls_cert_file) != bool(mqtt.tls_key_file):
        raise ConfigError("MQTT client certificate and key must be configured together")
    config = Config(
        runtime, mqtt, tuple(inverters), hm, ec, portal, commands, profiles, frozenset(intervals)
    )
    mqtt_needed = config.has_sources or (Path(runtime.state_dir) / "mqtt-topics.json").exists()
    if mqtt_needed:
        require_host(mqtt.host, "MQTT")
        if mqtt.tls:
            ssl_context(
                mqtt.tls_ca_file, mqtt.tls_cert_file, mqtt.tls_key_file, verify=mqtt.tls_verify
            )
    mqtt = password(mqtt, mqtt_needed)
    for inverter in inverters:
        if inverter.enabled:
            require_host(inverter.host, inverter.id)
    for attr in ("interface_address", "bind_address", "multicast_group"):
        try:
            address = ipaddress.IPv4Address(getattr(hm, attr))
            if attr == "multicast_group" and not address.is_multicast:
                raise ValueError
        except ValueError:
            raise ConfigError("Invalid Home Manager network address") from None
    if hm.transport not in ("udp", "modbus-tcp"):
        raise ConfigError("Home Manager transport must be udp or modbus-tcp")
    if hm.enabled and hm.transport == "modbus-tcp":
        from .home_manager_profile import load_home_manager_profile

        require_host(hm.host, "Home Manager Modbus")
        profiles["home-manager"] = load_home_manager_profile(
            hm.profile, runtime.profile_dir, bundled_dir
        )
        if "SMAB_HOME_MANAGER_POLL_INTERVAL_SECONDS" in env or "pollIntervalSeconds" in data.get(
            "homeManager", {}
        ):
            intervals.add("home-manager")
        config = replace(config, interval_overrides=frozenset(intervals))
    if hm.enabled:
        if not hm.serial.isdecimal() or not 0 < int(hm.serial) <= 0xFFFFFFFF:
            raise ConfigError("Home Manager requires a numeric serial selector")
        if hm.host and hm.transport == "udp":
            try:
                ipaddress.IPv4Address(hm.host)
            except ValueError:
                raise ConfigError("Home Manager sender filter must be an IPv4 address") from None
    ec = password(ec, ec.enabled)
    portal = password(portal, portal.enabled)
    if ec.enabled or ec.semp_enabled:
        require_host(ec.host, "eCharger")
    if ec.enabled:
        if not ec.username or not ec.password or not ec.expected_serial:
            raise ConfigError("Local API requires username, password and expected serial")
        if ec.tls_server_name:
            require_host(ec.tls_server_name, "eCharger TLS server name")
        echarger_ssl_context(ec)
    if ec.semp_enabled and not ec.semp_device_id:
        raise ConfigError("SEMP requires a configured device ID")
    if (
        not ec.semp_path.startswith("/")
        or any(c in ec.semp_path for c in "?#")
        or ".." in ec.semp_path
    ):
        raise ConfigError("Invalid SEMP path")
    for value in (portal.base_url, portal.api_base_url, portal.auth_base_url):
        if not https_url(value):
            raise ConfigError("Portal endpoints require a verified HTTPS origin")
    if portal.enabled and not all(
        (portal.username, portal.password, portal.plant_id, portal.device_id)
    ):
        raise ConfigError("Portal requires separate credentials and plant/device selectors")
    if any(i.commands_enabled for i in inverters):
        raise ConfigError("Inverter command paths are not implemented")
    if ec.commands_enabled and not ec.enabled:
        raise ConfigError("Local commands require the enabled eCharger API")
    if portal.commands_enabled and not portal.enabled:
        raise ConfigError("Portal commands require the enabled portal adapter")
    if commands.enabled and not (ec.commands_enabled or portal.commands_enabled):
        raise ConfigError("Global commands require a supported per-device command gate")
    return replace(config, mqtt=mqtt, echarger=ec, portal=portal)
