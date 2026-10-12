"""Known eCharger read channels, separate API/SEMP sessions and no setters."""

import asyncio
import time
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType

from ..config import echarger_ssl_context
from ..errors import AuthenticationError, ProtocolError
from ..model import Property, SampleValues, number
from .http import HTTP

NS = "http://www.sma.de/communication/schema/SEMP/v1"
VEHICLE = {
    "200111": "Nicht verbunden",
    "200112": "Verbunden / wartend",
    "200113": "Lädt",
    "5169": "Gesperrt",
    "200115": "Fehler am Ladepunkt",
}
HEALTH = {"307": "OK", "35": "Fehler", "455": "Warnung", "303": "Aus", "308": "Ein"}
APPROVAL = {"5171": "Gesperrt", "5172": "Freigegeben"}

# Verified for this model/firmware from local metadata and working protocol references.
# See docs/VALIDATION.md; do not infer these units for other firmware versions.
VERIFIED_LOCAL_UNITS = {
    "Parameter.Chrg.Plan.En": "kWh",
    "Parameter.Chrg.Plan.StopTm": "s",
    "Parameter.Chrg.StpWhenFlTm": "min",
    "Parameter.Inverter.WMaxIn": "W",
}


@dataclass(frozen=True, kw_only=True)
class SettingDefinition:
    """Named read metadata shared with the explicit command allowlist."""

    id: str
    channel: str
    datatype: str
    unit: str = ""
    mapping: Mapping[str, bool] | None = None
    format: str = ""

    def __post_init__(self):
        if self.mapping is not None:
            object.__setattr__(self, "mapping", MappingProxyType(dict(self.mapping)))


# Explicit read mapping from working references, not the entire installer catalog.
SETTINGS = (
    SettingDefinition(
        id="charge-mode",
        channel="Parameter.Chrg.ActChaMod",
        datatype="enum",
        format="4718,4719,4720,4721",
    ),
    SettingDefinition(
        id="charging-release",
        channel="Parameter.Chrg.ChrgApv",
        datatype="boolean",
        mapping={"5172": True, "5171": False},
    ),
    SettingDefinition(
        id="approval-required",
        channel="Parameter.Chrg.ChrgLok",
        datatype="boolean",
        mapping={"1129": True, "1130": False},
    ),
    SettingDefinition(
        id="stop-when-full",
        channel="Parameter.Chrg.StpWhenFl",
        datatype="boolean",
        mapping={"1129": True, "1130": False},
    ),
    SettingDefinition(
        id="stop-delay", channel="Parameter.Chrg.StpWhenFlTm", datatype="integer", unit="min"
    ),
    SettingDefinition(
        id="cable-lock",
        channel="Parameter.Chrg.CblLok",
        datatype="boolean",
        mapping={"308": True, "303": False},
    ),
    SettingDefinition(
        id="led-brightness",
        channel="Parameter.Sys.DevSigBri",
        datatype="enum",
        format="5191,5190,5173",
    ),
    SettingDefinition(
        id="ambient-brightness",
        channel="Parameter.Sys.AmbLghtBri",
        datatype="enum",
        format="5191,5190,5173",
    ),
    SettingDefinition(
        id="ambient-enabled",
        channel="Parameter.Sys.UseAmbLght",
        datatype="boolean",
        mapping={"308": True, "303": False},
    ),
    SettingDefinition(
        id="plan-energy", channel="Parameter.Chrg.Plan.En", datatype="float", unit="kWh"
    ),
    SettingDefinition(id="plan-end", channel="Parameter.Chrg.Plan.StopTm", datatype="string"),
)
# The local WebUI labels maxChargePower with metadata 12195 (WMaxIn), not WMax.
# SEMP does not expose this setting; it remains owned by the local API.
API_SETTINGS = SETTINGS + (
    SettingDefinition(
        id="max-charge-power", channel="Parameter.Inverter.WMaxIn", datatype="integer", unit="W"
    ),
)
EXTRA = [
    (
        "total-energy",
        ("Measurement.Metering.GridMs.TotWhIn.ChaSta", "Measurement.Metering.GridMs.TotWhIn"),
        "kWh",
    )
]
PHASE_POWER_CHANNELS = frozenset(f"Measurement.GridMs.W.phs{phase}" for phase in "ABC")

for i, phase in enumerate("ABC", 1):
    EXTRA += [
        (f"current-l{i}", (f"Measurement.GridMs.A.phs{phase}",), "A"),
        (f"voltage-l{i}", (f"Measurement.GridMs.PhV.phs{phase}",), "V"),
        (f"power-l{i}", (f"Measurement.GridMs.W.phs{phase}",), "W"),
    ]
EXTRA.append(("frequency", ("Measurement.GridMs.Hz",), "Hz"))
BASE = (
    Property("measurements", "power", "Charging power", unit="W", required_for_ready=True),
    Property("measurements", "session-energy", "Session energy", unit="kWh"),
    Property("measurements", "vehicle-status", "Vehicle status", "string"),
    Property("measurements", "vehicle-status-code", "Vehicle status code", "integer"),
    Property("measurements", "health", "Device health", "string"),
    Property("parameters", "nameplate-pkgrev", "Firmware", "string"),
    Property("settings", "charge-mode", "Charging mode", "enum", format="4718,4719,4720,4721"),
    Property("measurements", "manual-approval", "Manual approval", "string"),
)
SEMP_EXTRA = (
    ("measurements", "health-code", "Measurement.Operation.Health"),
    ("measurements", "vehicle-health", "Measurement.Operation.EVeh.Health"),
    ("measurements", "event-code", "Measurement.Operation.Evt.Msg"),
    ("measurements", "mode-switch-code", "Measurement.Chrg.ModSw"),
    ("measurements", "auth-registration-code", "Measurement.Acs.AuthRegistStt"),
    ("parameters", "inverter-outphs", "Parameter.Inverter.OutPhs"),
    ("control", "active-charging-count", "Setpoint.PlantControl.PCC.ChrgActCnt"),
    (
        "control",
        "power-setpoint-max-percent",
        "Setpoint.PlantControl.Inverter.WModCfg.WCtlComCfg.WSptMaxNom",
    ),
    (
        "control",
        "power-setpoint-min-percent",
        "Setpoint.PlantControl.Inverter.WModCfg.WCtlComCfg.WSptMinNom",
    ),
    ("parameters", "chrg-plan-en-raw", "Parameter.Chrg.Plan.En"),
    ("parameters", "chrg-stpwhenfltm-raw", "Parameter.Chrg.StpWhenFlTm"),
)


ADVANCED_BASE_KEYS = {"parameters/nameplate-pkgrev"}


# Only channels observed refreshing timestamps with unchanged numeric values.
# Session energy, voltage, phase power and unresolved states retain their old policy.
REFRESHED_CHANNELS = frozenset(
    {
        "Measurement.Metering.GridMs.TotWIn.ChaSta",
        "Measurement.Metering.GridMs.TotWhIn.ChaSta",
        "Measurement.Operation.EVeh.ChaStt",
        "Setpoint.PlantControl.PCC.ChrgActCnt",
        "Setpoint.PlantControl.Inverter.WModCfg.WCtlComCfg.WSptMaxNom",
        "Setpoint.PlantControl.Inverter.WModCfg.WCtlComCfg.WSptMinNom",
    }
    | {f"Measurement.GridMs.A.phs{phase}" for phase in "ABC"}
)
BASE_TIMED_CHANNELS = {
    "measurements/power": "Measurement.Metering.GridMs.TotWIn.ChaSta",
    "measurements/vehicle-status": "Measurement.Operation.EVeh.ChaStt",
    "measurements/vehicle-status-code": "Measurement.Operation.EVeh.ChaStt",
}


def observation_time(channel, value, timestamp, stale_seconds, now, monotonic):
    """Anchor accepted device age to a monotonic clock before further processing."""
    if channel not in REFRESHED_CHANNELS or value is None:
        return None
    if current_measurement(value, timestamp, stale_seconds, now) is None:
        return None
    measured = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    return monotonic - (now - measured).total_seconds()


def timed_values(values, channel_times, channels):
    return SampleValues(
        values,
        {
            key: channel_times[channel]
            for key, channel in channels.items()
            if key in values and values[key] is not None and channel in channel_times
        },
    )


def base_properties(advanced):
    return tuple(p for p in BASE if advanced or p.key not in ADVANCED_BASE_KEYS)


def extra_channels(advanced, diagnostics):
    return tuple(p for p in SEMP_EXTRA if (diagnostics if p[0] == "measurements" else advanced))


def base_values(catalog, advanced=True):
    vehicle = catalog.get("Measurement.Operation.EVeh.ChaStt")
    result = {
        "measurements/power": number(catalog.get("Measurement.Metering.GridMs.TotWIn.ChaSta")),
        "measurements/session-energy": None
        if number(catalog.get("Measurement.ChaSess.WhIn")) is None
        else number(catalog["Measurement.ChaSess.WhIn"]) / 1000,
        "measurements/vehicle-status": VEHICLE.get(str(vehicle), "Unbekannter Fahrzeugstatus")
        if vehicle is not None
        else None,
        "measurements/vehicle-status-code": number(vehicle),
        "measurements/health": HEALTH.get(str(catalog.get("Measurement.Operation.Health")))
        if catalog.get("Measurement.Operation.Health") is not None
        else None,
        "settings/charge-mode": catalog.get("Parameter.Chrg.ActChaMod"),
        "measurements/manual-approval": APPROVAL.get(str(catalog.get("Parameter.Chrg.ChrgApv"))),
    }

    if advanced:
        result["parameters/nameplate-pkgrev"] = catalog.get("Parameter.Nameplate.PkgRev")
    return result


def parameter_catalog(reply, expected_serial):
    if not isinstance(reply, list):
        raise ProtocolError("Unexpected eCharger parameter response")
    components = [c for c in reply if isinstance(c, dict) and c.get("componentId") == "IGULD:SELF"]
    if len(components) != 1 or not isinstance(components[0].get("values"), list):
        raise ProtocolError("Missing/ambiguous eCharger parameter component")
    catalog = {}
    for p in components[0]["values"]:
        if (
            not isinstance(p, dict)
            or not isinstance(p.get("channelId"), str)
            or p["channelId"] in catalog
        ):
            raise ProtocolError("Invalid/duplicate eCharger parameter metadata")
        catalog[p["channelId"]] = p
    if str(catalog.get("Parameter.Nameplate.SerNum", {}).get("value")) != expected_serial:
        raise ProtocolError("Local eCharger identity does not match expected serial")
    if catalog.get("Parameter.Nameplate.ModelStr", {}).get("value") != "EVC22-3AC-20":
        raise ProtocolError("Local API did not identify the expected eCharger model")
    return catalog


def parameter_unit(catalog, channel):
    unit = catalog.get(channel, {}).get("unit")
    verified_local = (
        catalog.get("Parameter.Nameplate.ModelStr", {}).get("value") == "EVC22-3AC-20"
        and catalog.get("Parameter.Nameplate.PkgRev", {}).get("value") == "2.6.37.R"
    )
    return VERIFIED_LOCAL_UNITS.get(channel) if unit is None and verified_local else unit


def phase_power_unit_verified(catalog, explicit_units):
    """Accept explicit watts or the verified model/firmware WebUI scalar-W contract."""
    units = tuple(unit for unit in explicit_units if unit is not None)
    if units:
        return all(unit == "W" for unit in units)
    return (
        catalog.get("Parameter.Nameplate.ModelStr", {}).get("value") == "EVC22-3AC-20"
        and catalog.get("Parameter.Nameplate.PkgRev", {}).get("value") == "2.6.37.R"
    )


def settings_values(catalog, *, from_api=True):
    """Require confirmed API settings; SEMP provides raw parameters without API metadata."""
    result = {}
    for setting in API_SETTINGS if from_api else SETTINGS:
        entry = catalog.get(setting.channel, {})
        if from_api and entry.get("state") != "Confirmed":
            result["settings/" + setting.id] = None
            continue
        raw = entry.get("value")
        value = setting.mapping.get(str(raw)) if setting.mapping is not None else raw
        if setting.unit:
            value = (
                number(raw) if parameter_unit(catalog, setting.channel) == setting.unit else None
            )
        if setting.id == "max-charge-power" and (
            value is None or value != value.to_integral_value() or not 1380 <= value <= 22000
        ):
            value = None
        if setting.id == "plan-end":
            seconds = (
                number(raw)
                if not from_api or parameter_unit(catalog, setting.channel) == "s"
                else None
            )
            try:
                value = (
                    datetime.fromtimestamp(float(seconds), timezone.utc).isoformat()
                    if seconds is not None and seconds > 0
                    else None
                )
            except OverflowError, OSError, ValueError:
                value = None
        result["settings/" + setting.id] = value
    return result


def xml_root(text):
    if "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
        raise ProtocolError("XML declarations/entities are not accepted")
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        raise ProtocolError("Invalid SEMP XML") from None
    if root.tag != "{" + NS + "}Device2EM":
        raise ProtocolError("Unexpected SEMP root/namespace")
    return root


def validate_semp_identity(text, expected_id, expected_serial=""):
    root = xml_root(text)
    identities = root.findall(f"{{{NS}}}DeviceInfo/{{{NS}}}Identification")
    matches = [i for i in identities if i.findtext(f"{{{NS}}}DeviceId") == expected_id]
    if len(matches) != 1:
        raise ProtocolError("SEMP device identity mismatch")
    if expected_serial and matches[0].findtext(f"{{{NS}}}DeviceSerial") != expected_serial:
        raise ProtocolError("SEMP serial identity mismatch")


def current_measurement(value, timestamp, stale_seconds, now=None):
    now = datetime.now(timezone.utc) if now is None else now
    try:
        measured = datetime.fromisoformat((timestamp or "").replace("Z", "+00:00"))
        age = (now - measured).total_seconds()
        return value if 0 <= age <= stale_seconds else None
    except TypeError, ValueError, AttributeError:
        return None


def semp_values(
    text, stale_seconds, now=None, advanced=True, diagnostics=True, timestamp_observer=None
):
    root = xml_root(text)
    catalog, channel_times = {}, {}
    monotonic = time.monotonic()
    now = datetime.now(timezone.utc) if now is None else now
    for p in root.findall(f"{{{NS}}}Parameters/{{{NS}}}Parameter"):
        channel = p.findtext(f"{{{NS}}}channelId")
        if not channel or channel in catalog:
            raise ProtocolError("Missing/duplicate SEMP parameter channel")
        raw = p.findtext(f"{{{NS}}}value")
        stamp = p.findtext(f"{{{NS}}}timestamp")
        if channel.startswith(("Measurement.", "Setpoint.")):
            if timestamp_observer is not None:
                timestamp_observer.observe("semp", channel, raw, stamp, stale_seconds, now)
            raw = current_measurement(raw, stamp, stale_seconds, now)
            observed = observation_time(channel, raw, stamp, stale_seconds, now, monotonic)
            if observed is not None:
                channel_times[channel] = observed
        catalog[channel] = raw
    result = base_values(catalog, advanced)
    # SEMP has no API confirmation/unit metadata; preserve its known raw-parameter contract.
    result.update(settings_values({k: {"value": v} for k, v in catalog.items()}, from_api=False))
    result.update(
        {
            node + "/" + id: number(catalog.get(channel))
            for node, id, channel in extra_channels(advanced, diagnostics)
        }
    )
    channels = BASE_TIMED_CHANNELS | {
        node + "/" + id: channel for node, id, channel in extra_channels(advanced, diagnostics)
    }
    return timed_values(result, channel_times, channels)


class SempReader:
    def __init__(self, settings, max_bytes, include_settings=True, timestamp_observer=None):
        self.settings, self.include_settings = settings, include_settings
        self.timestamp_observer = timestamp_observer
        self.http = HTTP(settings.timeout_seconds, max_bytes)
        props = [
            p for p in base_properties(settings.advanced_channels_enabled) if p.node != "settings"
        ]
        if include_settings:
            props += [
                Property(
                    "settings",
                    setting.id,
                    setting.id.replace("-", " ").title(),
                    setting.datatype,
                    setting.unit,
                    setting.format,
                )
                for setting in SETTINGS
            ]
        props += [
            Property(node, id, channel + " (raw code/value)", "float")
            for node, id, channel in extra_channels(
                settings.advanced_channels_enabled, settings.diagnostics_enabled
            )
        ]
        self.properties = tuple(props)
        host = "[" + settings.host + "]" if ":" in settings.host else settings.host
        self.url = f"http://{host}:{settings.semp_port}" + settings.semp_path.rstrip("/")

    async def read(self):
        status, _, body = await self.http.request("GET", self.url + "/")
        if status != 200:
            raise ProtocolError("SEMP identity read failed")
        validate_semp_identity(body, self.settings.semp_device_id, self.settings.expected_serial)
        status, _, body = await self.http.request("GET", self.url + "/Parameters")
        if status != 200:
            raise ProtocolError("SEMP parameter read failed")
        values = semp_values(
            body,
            self.settings.stale_seconds,
            advanced=self.settings.advanced_channels_enabled,
            diagnostics=self.settings.diagnostics_enabled,
            timestamp_observer=self.timestamp_observer,
        )
        if not self.include_settings:
            for key in tuple(values):
                if key.startswith("settings/"):
                    del values[key]
        return values

    async def close(self):
        await self.http.close()


class EChargerReader:
    def __init__(self, settings, max_bytes, include_base=True, timestamp_observer=None):
        self.settings, self.include_base = settings, include_base
        self.timestamp_observer = timestamp_observer
        self.http = HTTP(
            settings.timeout_seconds,
            max_bytes,
            echarger_ssl_context(settings),
            server_name=settings.tls_server_name or None,
        )
        host = "[" + settings.host + "]" if ":" in settings.host else settings.host
        self.url = f"https://{host}:{settings.port}"
        self.token, self.expires = None, 0
        self.lock = asyncio.Lock()
        props = [
            Property(
                "settings",
                setting.id,
                setting.id.replace("-", " ").title(),
                setting.datatype,
                setting.unit,
                setting.format,
            )
            for setting in API_SETTINGS
        ]
        props += [
            Property(
                "measurements",
                id,
                id.replace("-", " ").title(),
                unit=unit,
                required_for_ready=id in ("current-l1", "voltage-l1"),
            )
            for id, _, unit in EXTRA
        ]
        if include_base:
            props += [
                p
                for p in base_properties(settings.advanced_channels_enabled)
                if p.node != "settings"
            ]
        self.properties = tuple(props)

    async def access_token(self):
        if self.token and time.monotonic() < self.expires:
            return self.token
        reply = await self.http.get_json(
            "POST",
            self.url + "/api/v1/token",
            data={
                "grant_type": "password",
                "username": self.settings.username,
                "password": self.settings.password,
            },
        )
        lifetime = number(reply.get("expires_in")) if isinstance(reply, dict) else None
        token = reply.get("access_token") if isinstance(reply, dict) else None
        if (
            not isinstance(token, str)
            or not token
            or any(c.isspace() for c in token)
            or lifetime is None
            or lifetime <= 0
        ):
            raise AuthenticationError("Local login did not return a valid token/lifetime")
        self.token, self.expires = token, time.monotonic() + max(0, float(lifetime) * 0.9 - 5)
        return token

    async def read(self):
        async with self.lock:
            return await self.read_locked()

    async def read_locked(self):
        for attempt in range(2):
            token = await self.access_token()
            try:
                reply = await self.http.get_json(
                    "POST",
                    self.url + "/api/v1/parameters/search",
                    token=token,
                    json={"queryItems": [{"componentId": "IGULD:SELF"}]},
                )
                catalog = parameter_catalog(reply, self.settings.expected_serial)
                result = settings_values(catalog)
                live = await self.http.get_json(
                    "POST",
                    self.url + "/api/v1/measurements/live",
                    token=token,
                    json=[{"componentId": "IGULD:SELF"}],
                )
                if not isinstance(live, list):
                    raise ProtocolError("Unexpected live-measurement response")
                values, phase_power_units, channel_times = {}, {}, {}
                property_channels = {}
                for m in live:
                    if (
                        not isinstance(m, dict)
                        or not isinstance(m.get("channelId"), str)
                        or m["channelId"] in values
                    ):
                        raise ProtocolError("Invalid/duplicate live measurement")
                    entries = m.get("values", [])
                    if not isinstance(entries, list) or len(entries) > 1:
                        raise ProtocolError("Ambiguous live measurement component")
                    entry = entries[0] if entries else {}
                    if not isinstance(entry, dict):
                        raise ProtocolError("Invalid live measurement entry")
                    if m["channelId"] in PHASE_POWER_CHANNELS:
                        phase_power_units[m["channelId"]] = tuple(
                            obj["unit"] for obj in (m, entry) if "unit" in obj
                        )
                    stamp = entry.get("timestamp", entry.get("time"))
                    if (
                        "timestamp" in entry
                        and "time" in entry
                        and entry["timestamp"] != entry["time"]
                    ):
                        raise ProtocolError("Conflicting live measurement timestamps")
                    monotonic = time.monotonic()
                    now = datetime.now(timezone.utc)
                    values[m["channelId"]] = current_measurement(
                        entry.get("value"), stamp, self.settings.stale_seconds, now
                    )
                    observed = observation_time(
                        m["channelId"],
                        values[m["channelId"]],
                        stamp,
                        self.settings.stale_seconds,
                        now,
                        monotonic,
                    )
                    if observed is not None:
                        channel_times[m["channelId"]] = observed
                    if self.timestamp_observer is not None:
                        self.timestamp_observer.observe(
                            "api",
                            m["channelId"],
                            entry.get("value"),
                            stamp,
                            self.settings.stale_seconds,
                            now,
                        )
                for id, channels, _ in EXTRA:
                    selected = next(
                        (c for c in channels if c in values and number(values[c]) is not None),
                        None,
                    )
                    value = number(values[selected]) if selected is not None else None
                    if selected is not None:
                        property_channels["measurements/" + id] = selected
                    if channels[0] in PHASE_POWER_CHANNELS and not phase_power_unit_verified(
                        catalog, phase_power_units.get(channels[0], ())
                    ):
                        value = None
                    # Both total-energy channels report Wh; publish the engineering value in kWh.
                    result["measurements/" + id] = (
                        value / 1000 if id == "total-energy" and value is not None else value
                    )
                if self.include_base:
                    # Do not bypass confirmation through the manual-approval display alias.
                    combined = {
                        k: v.get("value")
                        for k, v in catalog.items()
                        if k.startswith("Parameter.Nameplate.") or v.get("state") == "Confirmed"
                    }
                    combined.update(values)
                    baseline = base_values(combined, self.settings.advanced_channels_enabled)
                    baseline.pop("settings/charge-mode")
                    result.update(baseline)
                    property_channels.update(BASE_TIMED_CHANNELS)
                return timed_values(result, channel_times, property_channels)
            except AuthenticationError:
                self.token, self.expires = None, 0
                if attempt:
                    raise

    async def close(self):
        self.token = None
        await self.http.close()
