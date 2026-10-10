"""Explicit local command allowlist, fresh preflight and durable uncertain-write guard."""

import asyncio
import os
from pathlib import Path

from .adapters.echarger import EChargerReader, SETTINGS, parameter_catalog, settings_values
from .errors import ProtocolError
from .health import atomic_json
from .model import utc_timestamp

# Target mode is deliberately excluded until an atomic plan transaction exists.
LOCAL_COMMANDS = {id: (channel, mapping, fmt) for id, channel, _, _, mapping, fmt in SETTINGS
                  if id not in {"plan-energy", "plan-end", "stop-delay"}}


def command_target(key, text, catalog):
    if key not in LOCAL_COMMANDS:
        raise ProtocolError("Command property is not allowed")
    channel, mapping, fmt = LOCAL_COMMANDS[key]
    entry = catalog.get(channel, {})
    if entry.get("editable") is not True or entry.get("state") != "Confirmed":
        raise ProtocolError("Parameter is not confirmed and writable")
    if mapping is not None:
        if text not in {"true", "false"}:
            raise ProtocolError("Boolean command must be true or false")
        target = next(k for k, v in mapping.items() if v == (text == "true"))
    else:
        allowed = fmt.split(",")
        if text not in allowed or (key == "charge-mode" and text == "4720"):
            raise ProtocolError("Enum command is not supported; target charging needs a plan")
        target = text
    choices = entry.get("possibleValues")
    if not isinstance(choices, list) or target not in [str(v) for v in choices]:
        raise ProtocolError("Target is not offered by current parameter metadata")
    return channel, target


class LocalCommands:
    def __init__(self, config, api_state, result_state, reader=None):
        self.config, self.api_state, self.result_state = config, api_state, result_state
        self.reader = reader or EChargerReader(config.echarger, config.runtime.max_response_bytes)
        self.reader.http.allow_put = True
        self.journal = Path(config.runtime.state_dir) / "echarger-command-pending.json"
        self.lock = self.reader.lock

    def result(self, status):
        self.result_state.update({"commands/local-result": status})

    def sync_directory(self):
        fd = os.open(self.journal.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    async def catalog(self):
        r = self.reader
        token = await r.access_token()
        reply = await r.http.get_json("POST", r.url + "/api/v1/parameters/search", token=token,
                                      json={"queryItems": [{"componentId": "IGULD:SELF"}]})
        return parameter_catalog(reply, self.config.echarger.expected_serial)

    async def handle(self, key, data, retained=False):
        if retained:
            self.result("rejected-retained")
            return
        if not (self.config.commands.enabled and self.config.echarger.commands_enabled and self.config.echarger.enabled):
            self.result("rejected-disabled")
            return
        if self.lock.locked():
            self.result("rejected-busy")
            return
        async with self.lock:
            sent = False
            try:
                if not isinstance(data, bytes) or len(data) > 64:
                    raise ProtocolError("Invalid command payload")
                text = data.decode("utf-8")
                if key not in LOCAL_COMMANDS:
                    raise ProtocolError("Command property is not allowed")
                # Uncertainty survives MQTT reconnect and process/container restart.
                # Reading/polling never clears this guard or replays the saved target.
                if self.journal.exists():
                    self.result("blocked-uncertain")
                    return
                catalog = await self.catalog()
                channel, target = command_target(key, text, catalog)
                if str(catalog[channel].get("value")) == target:
                    self.api_state.update({"settings/" + key: settings_values(catalog)["settings/" + key]})
                    self.result("already-confirmed")
                    return
                atomic_json(self.journal, {"schemaVersion": 1, "property": key, "target": target,
                                           "timestamp": utc_timestamp()})
                self.sync_directory()
                sent = True
                self.result("pending")
                r = self.reader
                # Exactly one write attempt; no token refresh/retry around this request.
                status, _, _ = await r.http.request("PUT", r.url + "/api/v1/parameters/IGULD:SELF",
                    token=await r.access_token(), json={"values": [{"channelId": channel,
                        "timestamp": utc_timestamp(), "value": target}]})
                if not 200 <= status < 300:
                    raise ProtocolError("Device action could not be confirmed")
                async with asyncio.timeout(self.config.commands.readback_timeout_seconds):
                    while True:
                        catalog = await self.catalog()
                        entry = catalog.get(channel, {})
                        if entry.get("state") == "Confirmed" and str(entry.get("value")) == target:
                            self.api_state.update({"settings/" + key: settings_values(catalog)["settings/" + key]})
                            self.journal.unlink()
                            self.sync_directory()
                            self.result("confirmed")
                            return
                        await asyncio.sleep(self.config.commands.readback_interval_seconds)
            except asyncio.CancelledError:
                if sent:
                    self.result("uncertain")
                raise
            except Exception:
                # Never expose raw authenticated errors or echo the command payload.
                self.result("uncertain" if sent else "rejected")

    async def close(self):
        await self.reader.close()
