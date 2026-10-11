"""Explicit local command allowlist, fresh preflight and durable uncertain-write guard."""

import asyncio
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from .adapters.echarger import (
    API_SETTINGS,
    EChargerReader,
    parameter_catalog,
    parameter_unit,
    settings_values,
)
from .adapters.http import json_data
from .errors import ProtocolError
from .model import number, utc_timestamp
from .storage import journal_status, write_state

# Individual plan fields are never writable; mode 4720 needs the combined plan command.
LOCAL_COMMANDS = {
    id: (channel, mapping, fmt)
    for id, channel, _, _, mapping, fmt in API_SETTINGS
    if id not in {"plan-energy", "plan-end", "stop-delay"}
}


def command_target(key, text, catalog):
    if key not in LOCAL_COMMANDS:
        raise ProtocolError("Command property is not allowed")
    channel, mapping, fmt = LOCAL_COMMANDS[key]
    entry = catalog.get(channel, {})
    if entry.get("editable") is not True or entry.get("state") != "Confirmed":
        raise ProtocolError("Parameter is not confirmed and writable")
    if key == "max-charge-power":
        if not re.fullmatch(r"[1-9][0-9]{0,4}", text) or parameter_unit(catalog, channel) != "W":
            raise ProtocolError("Power command requires whole watts and a verified W unit")
        value, lower, upper = (number(v) for v in (text, entry.get("min"), entry.get("max")))
        if (
            lower is None
            or upper is None
            or not 1380 <= lower <= upper <= 22000
            or not lower <= value <= upper
        ):
            raise ProtocolError("Power target violates verified device bounds")
        if "step" in entry:
            step = number(entry["step"])
            if step is None or step <= 0 or (value - lower) % step:
                raise ProtocolError("Power target violates device step")
        choices = entry.get("possibleValues")
        if choices is not None and (
            not isinstance(choices, list) or (choices and value not in [number(v) for v in choices])
        ):
            raise ProtocolError("Power target is not offered")
        return channel, text
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


def command_matches(key, channel, target, catalog):
    entry = catalog.get(channel, {})
    if entry.get("state") != "Confirmed":
        return False
    if key == "max-charge-power":
        return parameter_unit(catalog, channel) == "W" and number(entry.get("value")) == number(
            target
        )
    return str(entry.get("value")) == target


def plan_input(text):
    plan = json_data(text)
    if not isinstance(plan, dict) or set(plan) != {"energyKWh", "endTime"}:
        raise ProtocolError("Plan requires energyKWh and endTime")
    energy = number(plan["energyKWh"]) if type(plan["energyKWh"]) in (int, float) else None
    if energy is None or energy <= 0 or not isinstance(plan["endTime"], str):
        raise ProtocolError("Plan energy must be positive")
    try:
        end = datetime.fromisoformat(plan["endTime"].replace("Z", "+00:00"))
        if end.tzinfo is None or end.microsecond or end <= datetime.now(timezone.utc):
            raise ValueError
        seconds = int(end.timestamp())
    except ValueError, OverflowError, OSError:
        raise ProtocolError(
            "Plan end needs a future time with explicit timezone and whole seconds"
        ) from None
    return {"Parameter.Chrg.Plan.En": str(energy), "Parameter.Chrg.Plan.StopTm": str(seconds)}


def validate_plan(catalog, targets):
    if number(targets["Parameter.Chrg.Plan.StopTm"]) <= number(
        datetime.now(timezone.utc).timestamp()
    ):
        raise ProtocolError("Plan end has elapsed")
    for channel, target in targets.items():
        entry = catalog.get(channel, {})
        if entry.get("editable") is not True or entry.get("state") != "Confirmed":
            raise ProtocolError("Plan parameter is not confirmed and writable")
        expected_unit = "kWh" if channel.endswith(".En") else "s"
        if parameter_unit(catalog, channel) != expected_unit:
            raise ProtocolError("Plan unit is not verified")
        value = number(target)
        # Validate every offered bound; the working catalog offers min without max.
        for bound in ("min", "max"):
            if bound in entry:
                limit = number(entry[bound])
                if (
                    limit is None
                    or (bound == "min" and value < limit)
                    or (bound == "max" and value > limit)
                ):
                    raise ProtocolError("Plan target violates device bounds")
        choices = entry.get("possibleValues")
        if choices is not None and (
            not isinstance(choices, list) or (choices and value not in [number(v) for v in choices])
        ):
            raise ProtocolError("Plan target is not offered")
    mode = catalog.get("Parameter.Chrg.ActChaMod", {})
    if (
        mode.get("editable") is not True
        or mode.get("state") != "Confirmed"
        or not isinstance(mode.get("possibleValues"), list)
        or "4720" not in [str(v) for v in mode["possibleValues"]]
    ):
        raise ProtocolError("Target charging mode is not offered")


def plan_matches(catalog, targets):
    return all(
        catalog.get(channel, {}).get("state") == "Confirmed"
        and parameter_unit(catalog, channel) == ("kWh" if channel.endswith(".En") else "s")
        and number(catalog[channel].get("value")) == number(target)
        for channel, target in targets.items()
    )


# Subclasses provide result(), journal, config and reader.
class DurableCommands:  # pylint: disable=no-member
    """Shared disk synchronization and session cleanup for command guards."""

    def reject(self, key, status):
        self.result(status)

    def guard(self):
        return journal_status(self.journal, self.config.runtime.max_state_bytes)

    def sync_directory(self):
        fd = os.open(self.journal.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    async def close(self):
        await self.reader.close()


class LocalCommands(DurableCommands):
    def __init__(self, config, api_state, result_state, reader=None):
        self.config, self.api_state, self.result_state = config, api_state, result_state
        self.reader = reader or EChargerReader(config.echarger, config.runtime.max_response_bytes)
        self.reader.http.allow_put = True
        self.journal = Path(config.runtime.state_dir) / "echarger-command-pending.json"
        self.lock = self.reader.lock
        guard = self.guard()
        if guard:
            self.result(guard)

    def result(self, status):
        self.result_state.update({"commands/local-result": status})

    async def catalog(self):
        r = self.reader
        token = await r.access_token()
        reply = await r.http.get_json(
            "POST",
            r.url + "/api/v1/parameters/search",
            token=token,
            json={"queryItems": [{"componentId": "IGULD:SELF"}]},
        )
        return parameter_catalog(reply, self.config.echarger.expected_serial)

    async def apply_plan(self, targets, catalog):
        validate_plan(catalog, targets)
        mode_channel = "Parameter.Chrg.ActChaMod"
        changed = {c: v for c, v in targets.items() if number(catalog[c].get("value")) != number(v)}
        if changed and str(catalog[mode_channel].get("value")) == "4720":
            raise ProtocolError("Leave active target mode before replacing its plan")
        wrote = False
        for phase in ("parameters", "mode"):
            validate_plan(catalog, targets)
            values = (
                changed
                if phase == "parameters"
                else (
                    {mode_channel: "4720"}
                    if str(catalog[mode_channel].get("value")) != "4720"
                    else {}
                )
            )
            if not values:
                continue
            write_state(
                self.journal,
                {
                    "schemaVersion": 1,
                    "property": "plan",
                    "targets": targets,
                    "phase": phase,
                    "timestamp": utc_timestamp(),
                },
                self.config.runtime.max_state_bytes,
            )
            self.sync_directory()
            self.result("pending")
            wrote = True
            stamp = utc_timestamp()
            status, _, _ = await self.reader.http.request(
                "PUT",
                self.reader.url + "/api/v1/parameters/IGULD:SELF",
                token=await self.reader.access_token(),
                json={
                    "values": [
                        {"channelId": c, "timestamp": stamp, "value": v} for c, v in values.items()
                    ]
                },
            )
            if not 200 <= status < 300:
                raise ProtocolError("Plan action could not be confirmed")
            async with asyncio.timeout(self.config.commands.readback_timeout_seconds):
                while True:
                    catalog = await self.catalog()
                    if plan_matches(catalog, targets) and (
                        phase == "parameters"
                        or (
                            catalog.get(mode_channel, {}).get("state") == "Confirmed"
                            and str(catalog[mode_channel].get("value")) == "4720"
                        )
                    ):
                        break
                    await asyncio.sleep(self.config.commands.readback_interval_seconds)
        values = settings_values(catalog)
        self.api_state.update(
            {
                "settings/" + key: values["settings/" + key]
                for key in ("plan-energy", "plan-end", "charge-mode")
            }
        )
        end = datetime.fromtimestamp(
            int(targets["Parameter.Chrg.Plan.StopTm"]), timezone.utc
        ).isoformat()
        self.result_state.update(
            {
                "commands/plan": json.dumps(
                    {"energyKWh": float(targets["Parameter.Chrg.Plan.En"]), "endTime": end},
                    separators=(",", ":"),
                )
            }
        )
        if wrote:
            self.journal.unlink()
            self.sync_directory()
        self.result("confirmed" if wrote else "already-confirmed")

    async def handle(self, key, data, retained=False):
        if retained:
            self.result("rejected-retained")
            return
        if not (
            self.config.commands.enabled
            and self.config.echarger.commands_enabled
            and self.config.echarger.enabled
        ):
            self.result("rejected-disabled")
            return
        if self.lock.locked():
            self.result("rejected-busy")
            return
        async with self.lock:
            sent = False
            try:
                if not isinstance(data, bytes) or len(data) > (512 if key == "plan" else 64):
                    raise ProtocolError("Invalid command payload")
                text = data.decode("utf-8")
                if key not in LOCAL_COMMANDS and key != "plan":
                    raise ProtocolError("Command property is not allowed")
                targets = plan_input(text) if key == "plan" else None
                # Uncertainty survives MQTT reconnect and process/container restart.
                # Reading/polling never clears this guard or replays the saved target.
                guard = self.guard()
                if guard:
                    self.result(guard)
                    return
                catalog = await self.catalog()
                if targets is not None:
                    await self.apply_plan(targets, catalog)
                    return
                channel, target = command_target(key, text, catalog)
                if command_matches(key, channel, target, catalog):
                    self.api_state.update(
                        {"settings/" + key: settings_values(catalog)["settings/" + key]}
                    )
                    self.result("already-confirmed")
                    return
                write_state(
                    self.journal,
                    {
                        "schemaVersion": 1,
                        "property": key,
                        "target": target,
                        "timestamp": utc_timestamp(),
                    },
                    self.config.runtime.max_state_bytes,
                )
                self.sync_directory()
                sent = True
                self.result("pending")
                r = self.reader
                # Exactly one write attempt; no token refresh/retry around this request.
                status, _, _ = await r.http.request(
                    "PUT",
                    r.url + "/api/v1/parameters/IGULD:SELF",
                    token=await r.access_token(),
                    json={
                        "values": [
                            {"channelId": channel, "timestamp": utc_timestamp(), "value": target}
                        ]
                    },
                )
                if not 200 <= status < 300:
                    raise ProtocolError("Device action could not be confirmed")
                async with asyncio.timeout(self.config.commands.readback_timeout_seconds):
                    while True:
                        catalog = await self.catalog()
                        if command_matches(key, channel, target, catalog):
                            self.api_state.update(
                                {"settings/" + key: settings_values(catalog)["settings/" + key]}
                            )
                            self.journal.unlink()
                            self.sync_directory()
                            self.result("confirmed")
                            return
                        await asyncio.sleep(self.config.commands.readback_interval_seconds)
            except asyncio.CancelledError:
                if sent or self.journal.exists():
                    self.result("uncertain")
                raise
            except Exception:
                # Never expose raw authenticated errors or echo the command payload.
                self.result("uncertain" if sent or self.journal.exists() else "rejected")
