"""Independent read supervisors, monotonic scheduling and main-loop liveness."""

import asyncio
from dataclasses import replace
import logging
from pathlib import Path
import signal

from .adapters.echarger import EChargerReader, SempReader
from .adapters.meter import MeterReader
from .adapters.home_manager_modbus import HomeManagerModbusReader
from .adapters.modbus import ModbusReader
from .adapters.portal import PortalReader
from .errors import AuthenticationError
from .commands import LOCAL_COMMANDS, LocalCommands
from .portal_commands import CommandRouter, PortalCommands
from .health import atomic_json, heartbeat
from .homie import HomiePublisher, backoff, wait_stop
from .model import Property, SourceState

LOG = logging.getLogger(__name__)


def sources(config):
    result = []
    limit = config.runtime.max_response_bytes
    for device in config.inverters:
        if device.enabled:
            reader = ModbusReader(device, config.profiles[device.id], device.id in config.interval_overrides)
            interval = min((reader.interval(p) for p in reader.pollers), default=device.poll_interval_seconds)
            result.append((SourceState(device.id, device.homie_id, reader.properties, device.stale_seconds,
                                       diagnostics_enabled=device.diagnostics_enabled), reader, interval))
    hm, ec, portal = config.home_manager, config.echarger, config.portal
    if hm.enabled:
        if hm.transport == "modbus-tcp":
            reader = HomeManagerModbusReader(hm, config.profiles["home-manager"], "home-manager" in config.interval_overrides)
            interval = hm.poll_interval_seconds
        else:
            reader, interval = MeterReader(hm), None
        result.append((SourceState("home-manager", hm.homie_id, reader.properties, hm.stale_seconds,
                                       diagnostics_enabled=hm.diagnostics_enabled), reader, interval))
    if ec.enabled:
        reader = EChargerReader(ec, limit, include_base=not ec.semp_enabled)
        result.append((SourceState("api", ec.homie_id, reader.properties, ec.stale_seconds,
                                       diagnostics_enabled=ec.diagnostics_enabled), reader, ec.api_poll_interval_seconds))
    if ec.semp_enabled:
        reader = SempReader(ec, limit, include_settings=not ec.enabled)
        result.append((SourceState("semp", ec.homie_id, reader.properties, ec.stale_seconds,
                                       diagnostics_enabled=ec.diagnostics_enabled), reader, ec.semp_poll_interval_seconds))
    if portal.enabled:
        reader = PortalReader(portal, limit)
        result.append((SourceState("portal", ec.homie_id, reader.properties, portal.stale_seconds,
                                       diagnostics_enabled=portal.diagnostics_enabled), reader, portal.poll_interval_seconds))
    return result


async def supervise(state, reader, interval, config, stop, refresh_portal=False):
    attempt = 0
    try:
        if interval == 0 and not refresh_portal:
            await stop.wait()
            return
        while not stop.is_set():
            try:
                # HTTP timeout bounds individual requests; this also bounds a whole cycle.
                values = await reader.read()
                if isinstance(reader, HomeManagerModbusReader):
                    state.properties = reader.properties
                    keys = {p.key for p in state.properties}
                    state.values = {k: v for k, v in state.values.items() if k in keys}
                state.update(values)
                if values and not state.fresh_values():
                    state.error = True
                attempt = 0
                if interval == 0:
                    await stop.wait()
                elif interval is not None:
                    await wait_stop(stop, reader.delay() if isinstance(reader, ModbusReader) else interval)
            except AuthenticationError as error:
                state.error = True
                LOG.error("Source authentication blocked: %s", error)
                await stop.wait()  # No credential retry storm.
            except Exception as error:
                # Uncontrolled third-party exception text may contain authenticated data.
                state.error = True
                LOG.warning("Source read failed (%s); retrying with bounded backoff", type(error).__name__)
                await wait_stop(stop, backoff(attempt, config.runtime.reconnect_min_seconds,
                                              config.runtime.reconnect_max_seconds))
                attempt += 1
    finally:
        await reader.close()


async def run(config, refresh_portal=False, stop=None, publisher_factory=HomiePublisher):
    stop = asyncio.Event() if stop is None else stop
    loop = asyncio.get_running_loop()
    installed = []
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
            installed.append(sig)
        except (NotImplementedError, RuntimeError):
            pass
    readers = sources(config)
    states = [s for s, _, _ in readers]
    controller = None
    local_controller, portal_controller = None, None
    if config.commands.enabled and config.echarger.commands_enabled:
        api_state = next(s for s in states if s.id == "api")
        api_state.properties = tuple(replace(p, settable=True) if p.node == "settings" and p.id in LOCAL_COMMANDS else p
                                     for p in api_state.properties)
        result_state = SourceState("commands", config.echarger.homie_id,
                                   (Property("commands", "local-result", "Local command result", "string"),
                                    Property("commands", "plan", "Confirmed charging plan", "string", settable=True)),
                                   config.echarger.stale_seconds, diagnostics_enabled=config.echarger.diagnostics_enabled)
        states.append(result_state)
        api_reader = next(r for s, r, _ in readers if s.id == "api")
        local_controller = LocalCommands(config, api_state, result_state, reader=api_reader)
    if config.commands.enabled and config.portal.commands_enabled:
        portal_state = next(s for s in states if s.id == "portal")
        portal_state.properties = tuple(replace(p, settable=True, format="0:100") if p.id == "pv-minimum" else p
                                        for p in portal_state.properties)
        result_state = SourceState("portal-commands", config.echarger.homie_id,
                                   (Property("commands", "portal-result", "Portal command result", "string"),),
                                   config.portal.stale_seconds, diagnostics_enabled=config.portal.diagnostics_enabled)
        states.append(result_state)
        portal_reader = next(r for s, r, _ in readers if s.id == "portal")
        portal_controller = PortalCommands(config, portal_state, result_state, reader=portal_reader)
    if local_controller is not None or portal_controller is not None:
        controller = CommandRouter(local_controller, portal_controller)
    publisher = publisher_factory(config, states)
    if controller is not None:
        publisher.command_controller = controller
    tasks = [asyncio.create_task(supervise(state, reader, interval, config, stop,
                                          refresh_portal and state.id == "portal"))
             for state, reader, interval in readers]
    tasks.append(asyncio.create_task(publisher.run(stop)))
    try:
        while not stop.is_set():
            # A failed supervisor must not leave an apparently healthy process behind.
            for task in tasks:
                if task.done() and task.exception() is not None:
                    raise RuntimeError("A runtime supervisor stopped unexpectedly")
            heartbeat(config, states, publisher.status)
            await wait_stop(stop, config.runtime.health_interval_seconds)
    finally:
        stop.set()
        _, pending = await asyncio.wait(tasks, timeout=config.runtime.shutdown_timeout_seconds)
        for task in pending:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        if controller is not None:
            await controller.close()
        atomic_json(Path(config.runtime.state_dir) / "heartbeat.json", {"status": "stopped"})
        for sig in installed:
            loop.remove_signal_handler(sig)
