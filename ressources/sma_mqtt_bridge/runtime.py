"""Independent read supervisors, monotonic scheduling and main-loop liveness."""

import asyncio
import logging
import signal
import time
from dataclasses import replace
from pathlib import Path

from .adapters.echarger import EChargerReader, SempReader
from .adapters.home_manager_modbus import HomeManagerModbusReader
from .adapters.meter import MeterReader
from .adapters.modbus import ModbusReader
from .adapters.portal import PortalReader
from .availability import Availability, is_timeout
from .charging_session import ChargingSession
from .commands import LOCAL_COMMANDS, LocalCommands
from .errors import AuthenticationError
from .health import atomic_json, heartbeat
from .homie import HomiePublisher, backoff, wait_stop
from .model import Property, SourceState
from .portal_commands import CommandRouter, PortalCommands
from .portal_refresh import PortalRefresh
from .storage import journal_status, state_lock
from .timestamp_diagnostics import TimestampDiagnostics

LOG = logging.getLogger(__name__)

PORTAL_REFRESH_PROPERTIES = (
    Property("portal", "refresh", "Refresh portal", "string", settable=True, channel_group="basic"),
)

LOCAL_COMMAND_PROPERTIES = (
    Property("commands", "local-result", "Local command result", "string", channel_group="basic"),
    Property(
        "commands",
        "plan",
        "Confirmed charging plan",
        "string",
        settable=True,
        channel_group="basic",
    ),
)

PORTAL_COMMAND_PROPERTIES = (
    Property("commands", "portal-result", "Portal command result", "string", channel_group="basic"),
)


def sources(config):
    result = []
    limit = config.runtime.max_response_bytes
    for device in config.inverters:
        if device.enabled:
            reader = ModbusReader(
                device,
                config.profiles[device.id],
                device.id in config.interval_overrides,
                debug_interval_seconds=config.plant.debug_interval_seconds
                if config.plant.enabled
                and config.plant.debug_enabled
                and (device.role != "none" or config.plant.grid_source == device.id)
                else 0,
            )
            interval = min(
                (reader.interval(p) for p in reader.pollers), default=device.poll_interval_seconds
            )
            result.append(
                (
                    SourceState(
                        device.id,
                        device.homie_id,
                        reader.properties,
                        device.stale_seconds,
                        diagnostics_enabled=device.diagnostics_enabled,
                    ),
                    reader,
                    interval,
                )
            )
    hm, ec, portal = config.home_manager, config.echarger, config.portal
    timestamp_observer = (
        TimestampDiagnostics(
            config.runtime.state_dir,
            ec.timestamp_diagnostics_max_bytes,
            ec.timestamp_diagnostics_summary_interval_seconds,
        )
        if ec.timestamp_diagnostics_enabled and (ec.enabled or ec.semp_enabled)
        else None
    )
    if hm.enabled:
        if hm.transport == "modbus-tcp":
            reader = HomeManagerModbusReader(
                hm, config.profiles["home-manager"], "home-manager" in config.interval_overrides
            )
            interval = hm.poll_interval_seconds
        else:
            reader, interval = MeterReader(hm), None
        result.append(
            (
                SourceState(
                    "home-manager",
                    hm.homie_id,
                    reader.properties,
                    hm.stale_seconds,
                    diagnostics_enabled=hm.diagnostics_enabled,
                ),
                reader,
                interval,
            )
        )
    if ec.enabled:
        reader = EChargerReader(
            ec, limit, include_base=not ec.semp_enabled, timestamp_observer=timestamp_observer
        )
        result.append(
            (
                SourceState(
                    "api",
                    ec.homie_id,
                    reader.properties,
                    ec.stale_seconds,
                    diagnostics_enabled=ec.diagnostics_enabled,
                ),
                reader,
                ec.api_poll_interval_seconds,
            )
        )
    if ec.semp_enabled:
        reader = SempReader(
            ec, limit, include_settings=not ec.enabled, timestamp_observer=timestamp_observer
        )
        result.append(
            (
                SourceState(
                    "semp",
                    ec.homie_id,
                    reader.properties,
                    ec.stale_seconds,
                    diagnostics_enabled=ec.diagnostics_enabled,
                ),
                reader,
                ec.semp_poll_interval_seconds,
            )
        )
    if portal.enabled:
        reader = PortalReader(portal, limit)
        result.append(
            (
                SourceState(
                    "portal",
                    ec.homie_id,
                    reader.properties,
                    portal.stale_seconds,
                    diagnostics_enabled=portal.diagnostics_enabled,
                ),
                reader,
                portal.poll_interval_seconds,
            )
        )
    settings = {d.id: (d, "ready_properties") for d in config.inverters}
    settings.update(
        {
            "home-manager": (hm, "ready_properties"),
            "api": (ec, "api_ready_properties"),
            "semp": (ec, "semp_ready_properties"),
            "portal": (portal, "ready_properties"),
        }
    )
    for state, reader, _interval in result:
        state.max_payload_bytes = config.runtime.max_payload_bytes
        device, attr = settings[state.id]
        value = getattr(device, attr)
        state.ready_properties = tuple(value.split(",")) if value else ()
        state.__post_init__()  # Reject filtered or unknown readiness keys before device I/O.
        if isinstance(reader, HomeManagerModbusReader):
            # Paced Modbus reads populate readiness properties over multiple calls.
            state.initialization_deadline = (
                time.monotonic() + config.runtime.read_cycle_timeout_seconds
            )
    return result


async def reset_reader(reader, config):
    """Reset only read sessions; never close a session owned by an active command."""
    lock = getattr(reader, "lock", None)
    if isinstance(lock, asyncio.Lock):
        if lock.locked():
            return
        async with lock:
            async with asyncio.timeout(config.runtime.shutdown_timeout_seconds):
                await reader.close()
    else:
        async with asyncio.timeout(config.runtime.shutdown_timeout_seconds):
            await reader.close()


async def supervise(
    state,
    reader,
    interval,
    config,
    stop,
    refresh_portal=False,
    refresh=None,
    on_change=None,
    session=None,
):
    attempt = 0
    state.monitor = state.monitor or Availability(
        "Source " + state.id, config.runtime.failure_log_interval_seconds
    )
    monitor = state.monitor
    try:
        if interval == 0 and not refresh_portal:
            monitor.progress("idle")
            if refresh is None:
                await stop.wait()
                return
            await refresh.wait(stop)
        while not stop.is_set():
            try:
                if refresh is not None:
                    refresh.begin()
                monitor.progress("reading")
                # A whole-cycle deadline also catches locks or non-network waits.
                async with asyncio.timeout(config.runtime.read_cycle_timeout_seconds) as deadline:
                    values = await reader.read()
                if deadline.expired():
                    raise TimeoutError  # A reader must not turn swallowed cancellation into success.
                monitor.progress("received")
                if isinstance(reader, HomeManagerModbusReader):
                    state.properties = reader.properties
                    keys = {p.key for p in state.properties}
                    state.values = {k: v for k, v in state.values.items() if k in keys}
                state.identity_fingerprint = getattr(reader, "identity_fingerprint", "")
                state.update(values)
                if session is not None:
                    session.update(getattr(values, "session_observation", None))
                if refresh is not None:
                    refresh.finish("completed")
                if values and not state.fresh_values():
                    state.initialization_deadline = None
                    state.error = True
                    monitor.failure(reason="UnavailableSamples")
                if state.status() == "ready":
                    monitor.success()
                monitor.observe(state.status())
                if on_change is not None:
                    on_change()
                attempt = 0
                if interval == 0:
                    monitor.progress("idle")
                    if refresh is None:
                        await stop.wait()
                    else:
                        await refresh.wait(stop)
                elif interval is not None:
                    monitor.progress("waiting")
                    delay = reader.delay() if isinstance(reader, ModbusReader) else interval
                    if refresh is None:
                        await wait_stop(stop, delay)
                    else:
                        await refresh.wait(stop, delay)
            except AuthenticationError:
                if refresh is not None:
                    refresh.blocked = True
                    refresh.finish("auth-blocked")
                state.initialization_deadline = None
                state.error = True
                monitor.failure(reason="AuthenticationError")
                monitor.progress("auth-blocked")
                monitor.observe("error")
                if on_change is not None:
                    on_change()
                LOG.error(
                    "Source %s authentication blocked; resolve credentials/permissions before restart",
                    state.id,
                )
                await stop.wait()  # No credential retry storm.
            except Exception as error:
                if refresh is not None:
                    refresh.finish("failed")
                state.initialization_deadline = None
                # Uncontrolled third-party exception text may contain authenticated data.
                state.error = True
                monitor.failure(is_timeout(error), type(error).__name__)
                monitor.progress("retrying")
                monitor.observe("error")
                if on_change is not None:
                    on_change()
                if is_timeout(error):
                    await reset_reader(reader, config)
                await wait_stop(
                    stop,
                    backoff(
                        attempt,
                        config.runtime.reconnect_min_seconds,
                        config.runtime.reconnect_max_seconds,
                    ),
                )
                attempt += 1
    finally:
        monitor.progress("stopped")
        async with asyncio.timeout(config.runtime.shutdown_timeout_seconds):
            await reader.close()


async def run(config, refresh_portal=False, stop=None, publisher_factory=HomiePublisher):
    with state_lock(config.runtime.state_dir):
        for name in ("echarger-command-pending.json", "portal-command-pending.json"):
            status = journal_status(
                Path(config.runtime.state_dir) / name, config.runtime.max_state_bytes
            )
            if status:
                LOG.error("Command journal %s: %s; manual reconciliation required", name, status)
        await run_locked(config, refresh_portal, stop, publisher_factory)


def log_startup_status(config, states, mqtt_status, deadline, now=None):
    """Report initial availability once ready, or after the bounded startup window."""
    now = time.monotonic() if now is None else now
    source_status = {
        state.id: state.status(now) for state in states if state.contributes_availability
    }
    devices = sorted({state.device for state in states})
    complete = all(value == "ready" for value in source_status.values()) and all(
        mqtt_status.get(device, False) for device in devices
    )
    if not complete and now < deadline:
        return False
    configured = [device.id for device in config.inverters] + [
        "home-manager",
        "api",
        "semp",
        "portal",
    ]
    if config.plant.enabled:
        configured.append("plant")
    sources_text = ", ".join(f"{key}={source_status.get(key, 'disabled')}" for key in configured)
    mqtt_text = (
        ", ".join(
            f"{key}={'connected' if mqtt_status.get(key, False) else 'disconnected'}"
            for key in devices
        )
        or "none"
    )
    LOG.info(
        "Startup status (%s): sources [%s]; MQTT [%s]",
        "ready" if complete else "startup window elapsed",
        sources_text,
        mqtt_text,
    )
    return True


async def run_locked(config, refresh_portal=False, stop=None, publisher_factory=HomiePublisher):
    stop = asyncio.Event() if stop is None else stop
    loop = asyncio.get_running_loop()
    installed = []
    readers = sources(config)
    states = [s for s, _, _ in readers]
    session = None
    if config.echarger.enabled or config.echarger.semp_enabled:
        session = ChargingSession(config)
        states.append(session.state)
    plant = None
    if config.plant.enabled:
        from .plant import PlantEngine

        plant = PlantEngine(config, states)
        states.extend(plant.output_states)
    controller = None
    local_controller, portal_controller = None, None
    portal_refresh = None
    if config.portal.enabled:
        refresh_state = SourceState(
            "portal-refresh",
            config.echarger.homie_id,
            PORTAL_REFRESH_PROPERTIES,
            config.portal.stale_seconds,
            diagnostics_enabled=False,
            contributes_availability=False,
        )
        states.append(refresh_state)
        portal_refresh = PortalRefresh(refresh_state)
    if config.commands.enabled and config.echarger.commands_enabled:
        api_state = next(s for s in states if s.id == "api")
        api_state.properties = tuple(
            replace(p, settable=True) if p.node == "settings" and p.id in LOCAL_COMMANDS else p
            for p in api_state.properties
        )
        result_state = SourceState(
            "commands",
            config.echarger.homie_id,
            LOCAL_COMMAND_PROPERTIES,
            config.echarger.stale_seconds,
            diagnostics_enabled=config.echarger.diagnostics_enabled,
            contributes_availability=False,
        )
        states.append(result_state)
        api_reader = next(r for s, r, _ in readers if s.id == "api")
        local_controller = LocalCommands(config, api_state, result_state, reader=api_reader)
    if config.commands.enabled and config.portal.commands_enabled:
        portal_state = next(s for s in states if s.id == "portal")
        portal_state.properties = tuple(
            replace(p, settable=True, format="0:100") if p.id == "pv-minimum" else p
            for p in portal_state.properties
        )
        result_state = SourceState(
            "portal-commands",
            config.echarger.homie_id,
            PORTAL_COMMAND_PROPERTIES,
            config.portal.stale_seconds,
            diagnostics_enabled=config.portal.diagnostics_enabled,
            contributes_availability=False,
        )
        states.append(result_state)
        portal_reader = next(r for s, r, _ in readers if s.id == "portal")
        portal_controller = PortalCommands(config, portal_state, result_state, reader=portal_reader)
    if any((local_controller, portal_controller, portal_refresh, plant)):
        controller = CommandRouter(
            local_controller,
            portal_controller,
            portal_refresh,
            plant_price=plant.price if plant is not None else None,
            feed_in_price=plant.feed_in_price if plant is not None else None,
        )
    for state in states:
        state.max_payload_bytes = config.runtime.max_payload_bytes
    publisher = publisher_factory(config, states)
    if controller is not None:
        publisher.command_controller = controller
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
            installed.append(sig)
        except NotImplementedError, RuntimeError:
            pass
    tasks = [
        asyncio.create_task(
            supervise(
                state,
                reader,
                interval,
                config,
                stop,
                refresh_portal and state.id == "portal",
                portal_refresh if state.id == "portal" else None,
                plant.changed.set if plant is not None else None,
                session
                if state.id == ("semp" if config.echarger.semp_enabled else "api")
                else None,
            )
        )
        for state, reader, interval in readers
    ]
    if plant is not None:
        tasks.append(asyncio.create_task(plant.run(stop)))
    tasks.append(asyncio.create_task(publisher.run(stop)))
    startup_deadline = time.monotonic() + config.runtime.read_cycle_timeout_seconds
    startup_reported = False
    try:
        while not stop.is_set():
            # A failed supervisor must not leave an apparently healthy process behind.
            for task in tasks:
                if task.done() and (
                    task.cancelled() or task.exception() is not None or bool(readers)
                ):
                    raise RuntimeError("A runtime supervisor stopped unexpectedly")
            for state in states:
                if state.monitor is not None:
                    state.monitor.observe(state.status())
            if not startup_reported:
                startup_reported = log_startup_status(
                    config, states, publisher.status, startup_deadline
                )
            heartbeat(
                config,
                states,
                publisher.status,
                {d: m.snapshot() for d, m in getattr(publisher, "monitors", {}).items()},
            )
            await wait_stop(stop, config.runtime.health_interval_seconds)
    finally:
        stop.set()
        _, pending = await asyncio.wait(tasks, timeout=config.runtime.shutdown_timeout_seconds)
        for task in pending:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        if controller is not None:
            await controller.close()
        atomic_json(
            Path(config.runtime.state_dir) / "heartbeat.json", {"status": "stopped"}, durable=False
        )
        for sig in installed:
            loop.remove_signal_handler(sig)
