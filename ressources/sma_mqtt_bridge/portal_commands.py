"""Guarded minimum PV preference writes preserving the other portal options."""

import asyncio
import re
from pathlib import Path

from .adapters.portal import PortalReader, portal_values
from .commands import DurableCommands
from .errors import ProtocolError
from .model import utc_timestamp
from .storage import write_state


class PortalCommands(DurableCommands):
    def __init__(self, config, portal_state, result_state, reader=None):
        self.config, self.portal_state, self.result_state = config, portal_state, result_state
        self.reader = reader or PortalReader(config.portal, config.runtime.max_response_bytes)
        self.reader.http.allow_put = True
        self.lock = self.reader.lock
        self.journal = Path(config.runtime.state_dir) / "portal-command-pending.json"
        guard = self.guard()
        if guard:
            self.result(guard)

    def result(self, status):
        self.result_state.update({"commands/portal-result": status})

    def validated(self, device):
        s = self.config.portal
        return portal_values(device, s.plant_id, s.device_id)

    async def handle(self, key, data, retained=False):
        if retained:
            self.result("rejected-retained")
            return
        if not (
            self.config.commands.enabled
            and self.config.portal.commands_enabled
            and self.config.portal.enabled
        ):
            self.result("rejected-disabled")
            return
        if self.lock.locked():
            self.result("rejected-busy")
            return
        async with self.lock:
            sent = False
            try:
                if (
                    key != "pv-minimum"
                    or not isinstance(data, bytes)
                    or not re.fullmatch(rb"(?:0|[1-9][0-9]?|100)", data)
                ):
                    raise ProtocolError("PV preference needs a whole percentage from 0 to 100")
                guard = self.guard()
                if guard:
                    self.result(guard)
                    return
                target = int(data)
                device = await self.reader.read_device()
                observed = self.validated(device)
                demand = device["optionalEnergyDemand"]
                if (
                    not {"minPvPercentage", "pvSurplusOnly", "usePriceLimit", "priceLimit"}
                    <= demand.keys()
                ):
                    raise ProtocolError("Portal options are incomplete")
                if (
                    not observed["portal/writable"]
                    or demand["usePriceLimit"]
                    or demand.get("pvSurplusOnly") is True
                ):
                    raise ProtocolError("Portal preference is unavailable in this mode or account")
                expected = {
                    "minPvPercentage": target,
                    "pvSurplusOnly": demand.get("pvSurplusOnly"),
                    "usePriceLimit": demand["usePriceLimit"],
                    "priceLimit": demand.get("priceLimit"),
                }
                if demand["minPvPercentage"] == target:
                    self.portal_state.update(observed)
                    self.result("already-confirmed")
                    return
                write_state(
                    self.journal,
                    {
                        "schemaVersion": 1,
                        "property": key,
                        "target": expected,
                        "timestamp": utc_timestamp(),
                    },
                    self.config.runtime.max_state_bytes,
                )
                self.sync_directory()
                sent = True
                self.result("pending")
                # No refresh/retry of this PUT, even after 401 or an uncertain response.
                status, _, _ = await self.reader.http.request(
                    "PUT",
                    self.reader.device_url() + "/optionalenergydemand",
                    token=await self.reader.access_token(),
                    json=expected,
                )
                if not 200 <= status < 300:
                    raise ProtocolError("Portal write could not be confirmed")
                async with asyncio.timeout(self.config.commands.readback_timeout_seconds):
                    while True:
                        device = await self.reader.read_device()
                        observed = self.validated(device)
                        actual = device["optionalEnergyDemand"]
                        if all(actual.get(k) == v for k, v in expected.items()):
                            self.portal_state.update(observed)
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
                self.result("uncertain" if sent else "rejected")


class CommandRouter:
    """Route the independently gated sources through the single MQTT consumer."""

    def __init__(self, local=None, portal=None):
        self.local, self.portal = local, portal

    def reject(self, key, status):
        controller = self.portal if key == "pv-minimum" else self.local
        if controller is not None:
            controller.result(status)

    async def handle(self, key, data):
        controller = self.portal if key == "pv-minimum" else self.local
        if controller is not None:
            await controller.handle(key, data)

    async def close(self):
        for controller in (self.local, self.portal):
            if controller is not None:
                await controller.close()
