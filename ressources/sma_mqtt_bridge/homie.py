"""Retained Homie 4 metadata/state, one supervised connection/Last Will per device."""

import asyncio
import logging
import random
import socket
import time
from contextlib import asynccontextmanager
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import aiomqtt

from .availability import Availability, is_timeout
from .config import ID, ssl_context
from .errors import ConfigError, StateError
from .model import Property, number
from .storage import MISSING, read_state, write_state
from .translation import load_translation

LOG = logging.getLogger(__name__)

# Presentation aliases do not change protocol keys or durable energy fingerprints.
HOME_MANAGER_ALIASES = {
    "measurements/power-import": ("measurements/power-drawn", "Power drawn"),
    "measurements/power-export": ("measurements/power-grid-feed-in", "Power grid feed-in"),
}
INVERTER_ALIASES = {
    **{
        f"measurements/volt-g{i}": (f"measurements/voltage-l{i}", f"Voltage L{i}")
        for i in (1, 2, 3)
    },
    "measurements/pres-bat-charge": ("measurements/battery-charge-power", "Battery charging power"),
    "measurements/pres-batt-discharge": (
        "measurements/battery-discharge-power",
        "Battery discharging power",
    ),
    "measurements/current-bat-stat-charge": (
        "measurements/battery-state-of-charge",
        "Battery state of charge",
    ),
    "measurements/current-bat-temp": ("measurements/battery-temperature", "Battery temperature"),
    "measurements/day-yield": ("measurements/daily-yield", "Daily yield"),
    "measurements/battery-efficiency": (
        "measurements/battery-energy-return-ratio",
        "Battery energy return ratio",
    ),
    "measurements/max-power": ("measurements/rated-active-power", "Rated active power WMaxOutRtg"),
    "measurements/set-max-power": (
        "measurements/configured-active-power-limit",
        "Set active power limit",
    ),
}
PLANT_ALIASES = {
    "pv/total-earnings": ("grid/total-earnings", "Total feed-in remuneration"),
    "pv/totaldayyield": ("pv/totaldailyyield", "Total PV daily yield"),
    "battery/totalpresbatcharge": ("battery/totalchargepower", "Total battery charging power"),
    "battery/totalpresbattdischarge": (
        "battery/totaldischargepower",
        "Total battery discharging power",
    ),
    "house/consumption": ("house/consumption-power", "Calculated house consumption"),
    "house/consumptionwithcharging": (
        "house/consumption-power-with-battery-charging",
        "House consumption including battery charging",
    ),
}
CHARGER_ALIASES = {"parameters/nameplate-pkgrev": ("identity/firmware", "Firmware version")}
ENERGY_OFFSETS = {
    "measurements/energy-import": "energy_import_offset_kwh",
    "measurements/energy-export": "energy_export_offset_kwh",
}


def publication_aliases(state):
    if state.id == "home-manager":
        return HOME_MANAGER_ALIASES
    if state.id.startswith("inverter"):
        return INVERTER_ALIASES
    if state.id == "plant":
        return PLANT_ALIASES
    if state.id in ("api", "semp"):
        return CHARGER_ALIASES
    return {}


def publication_key(state, key):
    return publication_aliases(state).get(key, (key, ""))[0]


def publication_property(state, prop):
    alias = publication_aliases(state).get(prop.key)
    if alias is not None:
        key, name = alias
        node, identifier = key.split("/")
        return replace(prop, node=node, id=identifier, name=name)
    if state.id == "home-manager" and prop.key in ENERGY_OFFSETS:
        direction = "import" if prop.key.endswith("import") else "export"
        return replace(prop, name=f"Corrected grid {direction} energy")
    return prop


def raw_energy(state, key, value):
    prop = state.property_index().get(key)
    raw = number(value)
    if prop is None or prop.unit != "kWh" or prop.datatype not in ("integer", "float"):
        return None
    return raw if raw is not None and raw >= 0 else None


def publication_energy(config, state, key, value):
    """Correct only published Home Manager totals, leaving raw accounting intact."""
    if state.id == "plant" and key == "diagnostics/valid-properties":
        names = {wire_key(old): wire_key(new) for old, (new, _) in PLANT_ALIASES.items()}
        return ",".join(sorted(names.get(name, name) for name in value.split(",") if name))
    if state.id != "home-manager" or key not in ENERGY_OFFSETS:
        return value
    raw = raw_energy(state, key, value)
    if raw is None:
        return None
    offset = Decimal(str(getattr(config.home_manager, ENERGY_OFFSETS[key])))
    if offset == 0:
        return value
    result = raw + offset
    return str(result) if result >= 0 else None


def wire_key(key):
    """Keep internal protocol keys stable; expose compact Homie node/property IDs."""
    return key.replace("-", "")


def discovery(prefix, device, properties, labels=None, device_name=None):
    labels = labels or {}
    if len({wire_key(p.key) for p in properties}) != len(properties):
        raise ConfigError("Compact Homie IDs collide")
    base = prefix + "/" + device
    topics = {
        base + "/$homie": "4.0.0",
        base + "/$name": labels.get(
            device, labels.get(device_name or device, device_name or device)
        ),
        base + "/$state": "init",
        base + "/$extensions": "",
    }
    nodes = sorted({p.node for p in properties})
    if len({wire_key(node) for node in nodes}) != len(nodes):
        raise ConfigError("Compact Homie node IDs collide")
    topics[base + "/$nodes"] = ",".join(wire_key(node) for node in nodes)
    for node in nodes:
        root = base + "/" + wire_key(node)
        name = node.replace("-", " ").title()
        node_type = node
        if node.startswith("device-") and node[7:].isdigit():
            node_type = "device"
            name = labels.get("Device {number}", "Device {number}").replace("{number}", node[7:])
        topics[root + "/$name"] = labels.get(name, name)
        topics[root + "/$type"] = node_type
        topics[root + "/$properties"] = ",".join(
            sorted(wire_key(p.id) for p in properties if p.node == node)
        )
    for p in properties:
        root = base + "/" + wire_key(p.key)
        topics.update(
            {
                root + "/$name": labels.get(p.name, p.name),
                root + "/$datatype": p.datatype,
                root + "/$settable": str(p.settable).lower(),
                root + "/$retained": "true",
            }
        )
        if p.unit:
            topics[root + "/$unit"] = p.unit
        if p.format:
            topics[root + "/$format"] = p.format
    return topics


def backoff(attempt, minimum, maximum, random_value=None):
    cap = min(maximum, minimum * 2 ** min(attempt, 30))
    return max(
        minimum, cap * (0.5 + 0.5 * (random.random() if random_value is None else random_value))
    )


async def wait_stop(stop, seconds):
    try:
        await asyncio.wait_for(stop.wait(), seconds)
    except asyncio.TimeoutError:
        pass


class HomiePublisher:
    def __init__(self, config, states, client_factory=aiomqtt.Client):
        self.config, self.states, self.client_factory = config, states, client_factory
        self.status = {}
        self.monitors = {}
        self.path = Path(config.runtime.state_dir) / "mqtt-topics.json"
        self.owned = self.load_owned()
        self.command_controller = None
        self.labels = load_translation(config.runtime.language, config.runtime.translate_dir)
        for device in {s.device for s in states}:
            self.metadata(device, self.properties([s for s in states if s.device == device]))

    def metadata(self, device, properties):
        states = [s for s in self.states if s.device == device]
        inverter = next((s.id[8:] for s in states if s.id.startswith("inverter")), None)
        role = (
            "Plant"
            if any(s.id == "plant" for s in states)
            else "Home Manager"
            if any(s.id == "home-manager" for s in states)
            else ("eCharger" if any(s.id in ("api", "semp", "portal") for s in states) else device)
        )
        if inverter is not None:
            role = self.labels.get("Inverter", "Inverter") + " " + inverter
        return discovery(self.config.mqtt.homie_prefix, device, properties, self.labels, role)

    async def receive_commands(self, client, base, properties):
        topics = {base + "/" + wire_key(p.key) + "/set": p.id for p in properties if p.settable}
        active = None
        try:
            async for message in client.messages:
                key = topics.get(str(message.topic))
                if key is None:
                    continue
                if message.retain:
                    self.command_controller.reject(key, "rejected-retained")
                elif active is not None and not active.done():
                    self.command_controller.reject(key, "rejected-busy")
                else:
                    active = asyncio.create_task(
                        self.command_controller.handle(key, message.payload)
                    )
        finally:
            if active is not None:
                if not active.done():
                    active.cancel()
                await asyncio.gather(active, return_exceptions=True)

    def load_owned(self):
        data = read_state(self.path, self.config.runtime.max_state_bytes)
        if data is MISSING:
            return {}
        try:
            if (
                not isinstance(data, dict)
                or set(data) != {"schemaVersion", "prefix", "devices"}
                or type(data["schemaVersion"]) is not int
                or data["schemaVersion"] != 1
                or not isinstance(data["prefix"], str)
                or not ID.fullmatch(data["prefix"])
                or not isinstance(data["devices"], dict)
            ):
                raise ValueError
            result = {}
            for device, topics in data["devices"].items():
                if (
                    not ID.fullmatch(device)
                    or not isinstance(topics, list)
                    or any(
                        not isinstance(t, str)
                        or len(t.split("/")) < 3
                        or not ID.fullmatch(t.split("/")[0])
                        or t.split("/")[1] != device
                        or any(not level for level in t.split("/"))
                        or any(c in t for c in "+#")
                        or any(ord(c) < 32 for c in t)
                        for t in topics
                    )
                    or len(topics) != len(set(topics))
                ):
                    raise ValueError
                result[device] = set(topics)
            return result
        except ValueError, TypeError, AttributeError, KeyError:
            raise StateError(
                "MQTT topic manifest is corrupt; restore or reconcile it before startup"
            ) from None

    def save_owned(self):
        write_state(
            self.path,
            {
                "schemaVersion": 1,
                "prefix": self.config.mqtt.homie_prefix,
                "devices": {d: sorted(t) for d, t in self.owned.items()},
            },
            self.config.runtime.max_state_bytes,
        )

    def properties(self, states):
        props = [
            publication_property(state, p) for state in states for p in state.published_properties
        ]
        for state in states:
            if state.id == "home-manager" and state.diagnostics_enabled:
                props += [
                    Property(
                        "diagnostics",
                        "raw-energy-import",
                        "Raw grid import energy",
                        unit="kWh",
                        channel_group="diagnostics",
                    ),
                    Property(
                        "diagnostics",
                        "raw-energy-export",
                        "Raw grid export energy",
                        unit="kWh",
                        channel_group="diagnostics",
                    ),
                ]
            status_key, time_key = state.diagnostic_keys
            # Operational source availability stays usable when optional diagnostics are disabled.
            if state.contributes_availability or state.diagnostics_enabled:
                props.append(
                    Property(
                        *status_key.split("/"),
                        "Source availability",
                        "enum",
                        format="init,ready,stale,error",
                        channel_group="basic" if state.contributes_availability else "diagnostics",
                    )
                )
            if not state.diagnostics_enabled:
                continue
            props.append(
                Property(
                    *time_key.split("/"),
                    "Last successful receipt (UTC)",
                    "string",
                    channel_group="diagnostics",
                )
            )
            if state.monitor is not None:
                props += [
                    Property(
                        *key.split("/"),
                        "Source " + name,
                        datatype,
                        unit,
                        channel_group="diagnostics",
                    )
                    for name, key, datatype, unit in self.metric_properties(state)
                ]
        if len({p.key for p in props}) != len(props):
            raise ValueError("Duplicate Homie property ownership")
        return tuple(props)

    @staticmethod
    def metric_properties(state):
        root = "portal/" if state.id == "portal" else "diagnostics/" + state.id + "-"
        return (
            ("failures", root + "failures", "integer", ""),
            ("consecutiveFailures", root + "consecutive-failures", "integer", ""),
            ("timeouts", root + "timeouts", "integer", ""),
            ("outageSeconds", root + "outage-seconds", "float", "s"),
            ("phase", root + "phase", "string", ""),
            ("missingCritical", root + "missing-critical", "integer", ""),
        )

    def snapshot(self, states, now=None):
        result = {}
        for state in states:
            published = {p.key for p in state.published_properties}
            fresh = state.fresh_values(now)
            for key, value in fresh.items():
                if key in published:
                    corrected = publication_energy(self.config, state, key, value)
                    if corrected is not None:
                        result[publication_key(state, key)] = corrected
            if state.id == "home-manager" and state.diagnostics_enabled:
                for key in ENERGY_OFFSETS:
                    raw = raw_energy(state, key, fresh.get(key))
                    if raw is not None:
                        result["diagnostics/raw-" + key.split("/")[1]] = str(raw)
            if state.contributes_availability or state.diagnostics_enabled:
                result[state.diagnostic_keys[0]] = state.status(now)
            if state.diagnostics_enabled:
                if state.last_timestamp:
                    result[state.diagnostic_keys[1]] = state.last_timestamp
                if state.monitor is not None:
                    metrics = state.monitor.snapshot(now) | {
                        "missingCritical": len(state.missing_critical(now))
                    }
                    result.update(
                        {
                            key: str(round(metrics[name], 1))
                            if datatype == "float"
                            else str(metrics[name])
                            for name, key, datatype, _ in self.metric_properties(state)
                        }
                    )
        available = [s for s in states if s.contributes_availability]
        status = "ready" if any(s.status(now) == "ready" for s in available) else "alert"
        # Keep the bounded paced initialization visible instead of reporting a premature outage.
        if available and all(
            s.initialization_deadline is not None and s.status(now) == "init" for s in available
        ):
            status = "init"
        return result, status

    async def serve_device(self, device, states, stop):
        mqtt, runtime = self.config.mqtt, self.config.runtime
        monitor = self.monitors.setdefault(
            device, Availability("MQTT " + device, runtime.failure_log_interval_seconds)
        )
        base = mqtt.homie_prefix + "/" + device
        props = self.properties(states)
        metadata = self.metadata(device, props) if states else {}
        all_topics = set(metadata) | {base + "/" + wire_key(p.key) for p in props}
        previous = self.owned.get(device, set()).copy()
        self.owned[device] = previous | all_topics
        self.save_owned()  # Record ownership before any retained publication.
        attempt = 0
        while not stop.is_set():
            props = self.properties(states)
            metadata = self.metadata(device, props) if states else {}
            all_topics = set(metadata) | {base + "/" + wire_key(p.key) for p in props}
            previous = self.owned.get(device, set()).copy()
            self.owned[device] = previous | all_topics
            self.save_owned()
            self.status[device] = False
            monitor.progress("connecting")
            client = self.client_factory(
                mqtt.host,
                mqtt.port,
                username=mqtt.username or None,
                password=mqtt.password or None,
                identifier=mqtt.client_id + "-" + device,
                clean_session=True,
                keepalive=mqtt.keepalive_seconds,
                timeout=mqtt.connect_timeout_seconds,
                tls_context=ssl_context(
                    mqtt.tls_ca_file, mqtt.tls_cert_file, mqtt.tls_key_file, verify=mqtt.tls_verify
                )
                if mqtt.tls
                else None,
                will=aiomqtt.Will(base + "/$state", "lost", qos=mqtt.qos, retain=True),
                max_queued_outgoing_messages=mqtt.max_queue_messages,
                max_queued_incoming_messages=mqtt.max_queue_messages,
            )
            transport = getattr(client, "_client", None)
            if transport is not None:
                transport.connect_timeout = mqtt.connect_timeout_seconds
            try:
                async with mqtt_session(
                    client, mqtt.connect_timeout_seconds, runtime.shutdown_timeout_seconds
                ):
                    self.status[device] = True
                    monitor.progress("discovery")
                    for topic in sorted(previous - all_topics):
                        await client.publish(topic, b"", qos=mqtt.qos, retain=True)
                    if not states:
                        self.owned.pop(device, None)
                        self.save_owned()
                        return
                    for topic, value in metadata.items():
                        await client.publish(topic, value, qos=mqtt.qos, retain=True)
                    sent = {}
                    last_status = 0.0
                    # Retained values remain the last known observation across reconnects.
                    self.owned[device] = all_topics
                    self.save_owned()
                    previous = all_topics.copy()
                    consumer = None
                    if self.command_controller is not None and any(p.settable for p in props):
                        for p in props:
                            if p.settable:
                                await client.subscribe(
                                    base + "/" + wire_key(p.key) + "/set", qos=mqtt.qos
                                )
                        consumer = asyncio.create_task(self.receive_commands(client, base, props))
                    attempt = 0
                    try:
                        await self.publish_values(
                            client, base, states, stop, sent, last_status, consumer, props
                        )
                    finally:
                        if consumer is not None:
                            consumer.cancel()
                            await asyncio.gather(consumer, return_exceptions=True)
                    # Publish waits for QoS acknowledgement. Timeout causes an abrupt close,
                    # leaving the broker's Will responsible for reporting loss.
                    await client.publish(
                        base + "/$state",
                        "disconnected",
                        qos=mqtt.qos,
                        retain=True,
                        timeout=runtime.shutdown_timeout_seconds,
                    )
                    monitor.progress("stopped")
                    return
            except (aiomqtt.MqttError, OSError, asyncio.TimeoutError) as error:
                self.status[device] = False
                if stop.is_set():
                    return
                monitor.failure(is_timeout(error), type(error).__name__)
                monitor.progress("retrying")
                monitor.observe("lost")
                await wait_stop(
                    stop,
                    backoff(attempt, runtime.reconnect_min_seconds, runtime.reconnect_max_seconds),
                )
                attempt += 1
            finally:
                self.status[device] = False

    async def publish_values(
        self, client, base, states, stop, sent, last_status, consumer, declared=None
    ):
        mqtt, runtime = self.config.mqtt, self.config.runtime
        declared = self.properties(states) if declared is None else declared
        current = declared
        inventory = None
        while not stop.is_set():
            observed_inventory = tuple(
                (
                    s.id,
                    s.published_properties,
                    s.contributes_availability,
                    s.diagnostics_enabled,
                    s.monitor is not None,
                )
                for s in states
            )
            if observed_inventory != inventory:
                current = self.properties(states)
                inventory = observed_inventory
            if current != declared:
                # Inventory changes require a new Homie description and retained retirement.
                device = states[0].device
                metadata = self.metadata(device, current)
                topics = set(metadata) | {base + "/" + wire_key(p.key) for p in current}
                previous = self.owned.get(device, set())
                self.owned[device] = previous | topics
                self.save_owned()
                await client.publish(base + "/$state", "init", qos=mqtt.qos, retain=True)
                for topic in sorted(previous - topics):
                    await client.publish(topic, b"", qos=mqtt.qos, retain=True)
                    sent.pop(topic, None)
                for topic, value in metadata.items():
                    await client.publish(topic, value, qos=mqtt.qos, retain=True)
                self.owned[device] = topics
                self.save_owned()
                declared = current
                sent.pop(base + "/$state", None)
            if consumer is not None and consumer.done():
                if consumer.exception() is not None:
                    raise consumer.exception()
                raise aiomqtt.MqttError("Command subscription stopped")
            values, state = self.snapshot(states)
            desired = {base + "/" + wire_key(key): value for key, value in values.items()}
            desired[base + "/$state"] = state
            # Missing/expired values are not new observations; retain the last publication.
            for topic, value in desired.items():
                if sent.get(topic) != value or (
                    topic == base + "/$state"
                    and time.monotonic() - last_status >= min(runtime.health_interval_seconds, 1)
                ):
                    await client.publish(topic, value, qos=mqtt.qos, retain=True)
            last_status = time.monotonic()
            monitor = self.monitors.get(base.split("/")[1])
            if monitor is not None:
                monitor.progress("publishing")
                monitor.success()  # Only after the full batch's QoS acknowledgements.
                monitor.observe("ready")
            sent.update(desired)
            await wait_stop(stop, min(runtime.health_interval_seconds, 1))

    async def run(self, stop):
        devices = {s.device for s in self.states} | set(self.owned)
        tasks = [
            asyncio.create_task(
                self.serve_device(device, [s for s in self.states if s.device == device], stop)
            )
            for device in sorted(devices)
        ]
        try:
            await asyncio.gather(*tasks)
        finally:
            # gather does not cancel siblings after a failure; never orphan MQTT sessions.
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)


def abort_client(client):
    """Close TCP before MQTT DISCONNECT so an unacknowledged exit retains its Will."""
    # aiomqtt 2.5.1 exposes the underlying Paho transport here; pin and regression-test it.
    transport = getattr(client, "_client", None)
    sock = transport.socket() if transport is not None else None
    if sock is not None:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass


@asynccontextmanager
async def mqtt_session(client, connect_timeout, shutdown_timeout):
    failed = False
    try:
        await asyncio.wait_for(client.__aenter__(), connect_timeout)
        try:
            yield client
        except BaseException:
            abort_client(client)
            raise
        finally:
            await asyncio.wait_for(client.__aexit__(None, None, None), shutdown_timeout)
    except BaseException:
        failed = True
        abort_client(client)
        raise
    finally:
        finish_disconnect(client, failed)


def finish_disconnect(client, failed):
    """Retrieve aiomqtt's disconnect error without replacing an active session failure."""
    # aiomqtt 2.5.1 returns early in __aexit__ when this future is already done.
    future = getattr(client, "_disconnected", None)
    if not isinstance(future, asyncio.Future):
        return
    if future.done():
        if not future.cancelled():
            error = future.exception()
            if error is not None and not failed:
                raise error
    elif failed:
        # An abort callback can arrive after bounded cleanup failed. That session's
        # original error is already propagated; still retrieve the late future error.
        future.add_done_callback(retrieve_disconnect_error)


def retrieve_disconnect_error(future):
    if not future.cancelled():
        future.exception()
