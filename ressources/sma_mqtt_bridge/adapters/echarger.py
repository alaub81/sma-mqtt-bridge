"""Known eCharger read channels, separate API/SEMP sessions and no setters."""

from datetime import datetime, timezone
import asyncio
import time
import xml.etree.ElementTree as ET

from ..config import echarger_ssl_context
from ..errors import AuthenticationError, ProtocolError
from ..model import Property, number
from .http import HTTP

NS = "http://www.sma.de/communication/schema/SEMP/v1"
VEHICLE = {"200111": "Nicht verbunden", "200112": "Verbunden / wartend", "200113": "Lädt",
           "5169": "Gesperrt", "200115": "Fehler am Ladepunkt"}
HEALTH = {"307": "OK", "35": "Fehler", "455": "Warnung", "303": "Aus", "308": "Ein"}
APPROVAL = {"5171": "Gesperrt", "5172": "Freigegeben"}

# Verified from this firmware's local SMA WebUI metadata and scalar formatter.
# See docs/VALIDATION.md; do not infer these units for other firmware versions.
VERIFIED_LOCAL_UNITS = {
    "Parameter.Chrg.Plan.En": "kWh",
    "Parameter.Chrg.StpWhenFlTm": "min",
    "Parameter.Inverter.WMaxIn": "W",
}

# Explicit read mapping from working references, not the entire installer catalog.
SETTINGS = (
    ("charge-mode", "Parameter.Chrg.ActChaMod", "enum", "", None, "4718,4719,4720,4721"),
    ("charging-release", "Parameter.Chrg.ChrgApv", "boolean", "", {"5172": True, "5171": False}, ""),
    ("approval-required", "Parameter.Chrg.ChrgLok", "boolean", "", {"1129": True, "1130": False}, ""),
    ("stop-when-full", "Parameter.Chrg.StpWhenFl", "boolean", "", {"1129": True, "1130": False}, ""),
    ("stop-delay", "Parameter.Chrg.StpWhenFlTm", "integer", "min", None, ""),
    ("cable-lock", "Parameter.Chrg.CblLok", "boolean", "", {"308": True, "303": False}, ""),
    ("led-brightness", "Parameter.Sys.DevSigBri", "enum", "", None, "5191,5190,5173"),
    ("ambient-brightness", "Parameter.Sys.AmbLghtBri", "enum", "", None, "5191,5190,5173"),
    ("ambient-enabled", "Parameter.Sys.UseAmbLght", "boolean", "", {"308": True, "303": False}, ""),
    ("plan-energy", "Parameter.Chrg.Plan.En", "float", "kWh", None, ""),
    ("plan-end", "Parameter.Chrg.Plan.StopTm", "string", "", None, ""),
)
# The local WebUI labels maxChargePower with metadata 12195 (WMaxIn), not WMax.
# SEMP does not expose this setting; it remains owned by the local API.
API_SETTINGS = SETTINGS + (
    ("max-charge-power", "Parameter.Inverter.WMaxIn", "integer", "W", None, ""),
)
EXTRA = [("total-energy", ("Measurement.Metering.GridMs.TotWhIn.ChaSta", "Measurement.Metering.GridMs.TotWhIn"), "Wh")]
for i, phase in enumerate("ABC", 1):
    EXTRA += [(f"current-l{i}", (f"Measurement.GridMs.A.phs{phase}",), "A"),
              (f"voltage-l{i}", (f"Measurement.GridMs.PhV.phs{phase}",), "V")]
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
    ("control", "power-setpoint-max-percent", "Setpoint.PlantControl.Inverter.WModCfg.WCtlComCfg.WSptMaxNom"),
    ("control", "power-setpoint-min-percent", "Setpoint.PlantControl.Inverter.WModCfg.WCtlComCfg.WSptMinNom"),
    ("parameters", "chrg-plan-en-raw", "Parameter.Chrg.Plan.En"),
    ("parameters", "chrg-stpwhenfltm-raw", "Parameter.Chrg.StpWhenFlTm"),
)


ADVANCED_BASE_KEYS = {"measurements/vehicle-status-code", "parameters/nameplate-pkgrev"}


def base_properties(advanced):
    return tuple(p for p in BASE if advanced or p.key not in ADVANCED_BASE_KEYS)


def extra_channels(advanced, diagnostics):
    return tuple(p for p in SEMP_EXTRA if (diagnostics if p[0] == "measurements" else advanced))


def base_values(catalog, advanced=True):
    vehicle = catalog.get("Measurement.Operation.EVeh.ChaStt")
    result = {
        "measurements/power": number(catalog.get("Measurement.Metering.GridMs.TotWIn.ChaSta")),
        "measurements/session-energy": None if number(catalog.get("Measurement.ChaSess.WhIn")) is None else number(catalog["Measurement.ChaSess.WhIn"]) / 1000,
        "measurements/vehicle-status": VEHICLE.get(str(vehicle), "Unbekannter Fahrzeugstatus") if vehicle is not None else None,
        "measurements/health": HEALTH.get(str(catalog.get("Measurement.Operation.Health"))) if catalog.get("Measurement.Operation.Health") is not None else None,
        "settings/charge-mode": catalog.get("Parameter.Chrg.ActChaMod"),
        "measurements/manual-approval": APPROVAL.get(str(catalog.get("Parameter.Chrg.ChrgApv"))),
    }

    if advanced:
        result["measurements/vehicle-status-code"] = number(vehicle)
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
        if not isinstance(p, dict) or not isinstance(p.get("channelId"), str) or p["channelId"] in catalog:
            raise ProtocolError("Invalid/duplicate eCharger parameter metadata")
        catalog[p["channelId"]] = p
    if str(catalog.get("Parameter.Nameplate.SerNum", {}).get("value")) != expected_serial:
        raise ProtocolError("Local eCharger identity does not match expected serial")
    if catalog.get("Parameter.Nameplate.ModelStr", {}).get("value") != "EVC22-3AC-20":
        raise ProtocolError("Local API did not identify the expected eCharger model")
    return catalog


def parameter_unit(catalog, channel):
    unit = catalog.get(channel, {}).get("unit")
    verified_local = (catalog.get("Parameter.Nameplate.ModelStr", {}).get("value") == "EVC22-3AC-20"
                      and catalog.get("Parameter.Nameplate.PkgRev", {}).get("value") == "2.6.37.R")
    return VERIFIED_LOCAL_UNITS.get(channel) if unit is None and verified_local else unit


def settings_values(catalog, include_api_only=True):
    result = {}
    for id, channel, datatype, unit, mapping, fmt in API_SETTINGS if include_api_only else SETTINGS:
        entry = catalog.get(channel, {})
        raw = entry.get("value")
        value = mapping.get(str(raw)) if mapping is not None else raw
        if unit:
            value = number(raw) if parameter_unit(catalog, channel) == unit else None
        if id == "max-charge-power" and (entry.get("state") != "Confirmed" or value is None
                                         or value != value.to_integral_value() or not 1380 <= value <= 22000):
            value = None
        if id == "plan-end":
            seconds = number(raw)
            try:
                value = datetime.fromtimestamp(float(seconds), timezone.utc).isoformat() if seconds is not None and seconds > 0 else None
            except (OverflowError, OSError, ValueError):
                value = None
        result["settings/" + id] = value
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
    except (TypeError, ValueError, AttributeError):
        return None


def semp_values(text, stale_seconds, now=None, advanced=True, diagnostics=True):
    root = xml_root(text)
    catalog = {}
    now = datetime.now(timezone.utc) if now is None else now
    for p in root.findall(f"{{{NS}}}Parameters/{{{NS}}}Parameter"):
        channel = p.findtext(f"{{{NS}}}channelId")
        if not channel or channel in catalog:
            raise ProtocolError("Missing/duplicate SEMP parameter channel")
        raw = p.findtext(f"{{{NS}}}value")
        stamp = p.findtext(f"{{{NS}}}timestamp")
        if channel.startswith(("Measurement.", "Setpoint.")):
            raw = current_measurement(raw, stamp, stale_seconds, now)
        catalog[channel] = raw
    result = base_values(catalog, advanced)
    result.update(settings_values({k: {"value": v} for k, v in catalog.items()}, include_api_only=False))
    result.update({node + "/" + id: number(catalog.get(channel)) for node, id, channel in extra_channels(advanced, diagnostics)})
    return result


class SempReader:
    def __init__(self, settings, max_bytes, include_settings=True):
        self.settings, self.include_settings = settings, include_settings
        self.http = HTTP(settings.timeout_seconds, max_bytes)
        props = [p for p in base_properties(settings.advanced_channels_enabled) if p.node != "settings"]
        if include_settings:
            props += [Property("settings", id, id.replace("-", " ").title(), datatype, unit, fmt)
                      for id, _, datatype, unit, _, fmt in SETTINGS]
        props += [Property(node, id, channel + " (raw code/value)", "float") for node, id, channel in extra_channels(settings.advanced_channels_enabled, settings.diagnostics_enabled)]
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
        values = semp_values(body, self.settings.stale_seconds, advanced=self.settings.advanced_channels_enabled,
                             diagnostics=self.settings.diagnostics_enabled)
        if not self.include_settings:
            values = {k: v for k, v in values.items() if not k.startswith("settings/")}
        return values

    async def close(self):
        await self.http.close()


class EChargerReader:
    def __init__(self, settings, max_bytes, include_base=True):
        self.settings, self.include_base = settings, include_base
        self.http = HTTP(settings.timeout_seconds, max_bytes, echarger_ssl_context(settings),
                         server_name=settings.tls_server_name or None)
        host = "[" + settings.host + "]" if ":" in settings.host else settings.host
        self.url = f"https://{host}:{settings.port}"
        self.token, self.expires = None, 0
        self.lock = asyncio.Lock()
        props = [Property("settings", id, id.replace("-", " ").title(), datatype, unit, fmt)
                 for id, _, datatype, unit, _, fmt in API_SETTINGS]
        props += [Property("measurements", id, id.replace("-", " ").title(), unit=unit,
                           required_for_ready=id in ("current-l1", "voltage-l1")) for id, _, unit in EXTRA]
        if include_base:
            props += [p for p in base_properties(settings.advanced_channels_enabled) if p.node != "settings"]
        self.properties = tuple(props)

    async def access_token(self):
        if self.token and time.monotonic() < self.expires:
            return self.token
        reply = await self.http.get_json("POST", self.url + "/api/v1/token",
                                         data={"grant_type": "password", "username": self.settings.username,
                                               "password": self.settings.password})
        lifetime = number(reply.get("expires_in")) if isinstance(reply, dict) else None
        token = reply.get("access_token") if isinstance(reply, dict) else None
        if not isinstance(token, str) or not token or any(c.isspace() for c in token) or lifetime is None or lifetime <= 0:
            raise AuthenticationError("Local login did not return a valid token/lifetime")
        self.token, self.expires = token, time.monotonic() + max(0, float(lifetime) * .9 - 5)
        return token

    async def read(self):
        async with self.lock:
            return await self.read_locked()

    async def read_locked(self):
        for attempt in range(2):
            token = await self.access_token()
            try:
                reply = await self.http.get_json("POST", self.url + "/api/v1/parameters/search", token=token,
                                                 json={"queryItems": [{"componentId": "IGULD:SELF"}]})
                catalog = parameter_catalog(reply, self.settings.expected_serial)
                result = settings_values(catalog)
                live = await self.http.get_json("POST", self.url + "/api/v1/measurements/live", token=token,
                                                json=[{"componentId": "IGULD:SELF"}])
                if not isinstance(live, list):
                    raise ProtocolError("Unexpected live-measurement response")
                values = {}
                for m in live:
                    if not isinstance(m, dict) or not isinstance(m.get("channelId"), str) or m["channelId"] in values:
                        raise ProtocolError("Invalid/duplicate live measurement")
                    entries = m.get("values", [])
                    if not isinstance(entries, list) or len(entries) > 1:
                        raise ProtocolError("Ambiguous live measurement component")
                    entry = entries[0] if entries else {}
                    if not isinstance(entry, dict):
                        raise ProtocolError("Invalid live measurement entry")
                    stamp = entry.get("timestamp", entry.get("time"))
                    if "timestamp" in entry and "time" in entry and entry["timestamp"] != entry["time"]:
                        raise ProtocolError("Conflicting live measurement timestamps")
                    values[m["channelId"]] = current_measurement(entry.get("value"), stamp, self.settings.stale_seconds)
                for id, channels, _ in EXTRA:
                    result["measurements/" + id] = next((number(values[c]) for c in channels if c in values and number(values[c]) is not None), None)
                if self.include_base:
                    combined = {k: v.get("value") for k, v in catalog.items()}
                    combined.update(values)
                    baseline = base_values(combined, self.settings.advanced_channels_enabled)
                    baseline.pop("settings/charge-mode")
                    result.update(baseline)
                return result
            except AuthenticationError:
                self.token, self.expires = None, 0
                if attempt:
                    raise

    async def close(self):
        self.token = None
        await self.http.close()
