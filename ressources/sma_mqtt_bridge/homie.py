"""Retained Homie 4 metadata/state, one supervised connection/Last Will per device."""

import asyncio
from contextlib import asynccontextmanager
import json
import logging
from pathlib import Path
import random
import socket
import time

import aiomqtt

from .config import ID, ssl_context
from .health import atomic_json
from .model import Property

LOG = logging.getLogger(__name__)


def discovery(prefix, device, properties):
    base = prefix + "/" + device
    topics = {base + "/$homie": "4.0.0", base + "/$name": device, base + "/$state": "init",
              base + "/$extensions": ""}
    nodes = sorted({p.node for p in properties})
    topics[base + "/$nodes"] = ",".join(nodes)
    for node in nodes:
        root = base + "/" + node
        topics[root + "/$name"] = node.replace("-", " ").title()
        topics[root + "/$properties"] = ",".join(sorted(p.id for p in properties if p.node == node))
    for p in properties:
        root = base + "/" + p.key
        topics.update({root + "/$name": p.name, root + "/$datatype": p.datatype,
                       root + "/$settable": str(p.settable).lower(), root + "/$retained": "true"})
        if p.unit:
            topics[root + "/$unit"] = p.unit
        if p.format:
            topics[root + "/$format"] = p.format
    return topics


def backoff(attempt, minimum, maximum, random_value=None):
    cap = min(maximum, minimum * 2 ** min(attempt, 30))
    return max(minimum, cap * (.5 + .5 * (random.random() if random_value is None else random_value)))


async def wait_stop(stop, seconds):
    try:
        await asyncio.wait_for(stop.wait(), seconds)
    except asyncio.TimeoutError:
        pass


class HomiePublisher:
    def __init__(self, config, states, client_factory=aiomqtt.Client):
        self.config, self.states, self.client_factory = config, states, client_factory
        self.status = {}
        self.path = Path(config.runtime.state_dir) / "mqtt-topics.json"
        self.owned = self.load_owned()
        self.command_controller = None

    async def receive_commands(self, client, base, properties):
        topics = {base + "/" + p.key + "/set": p.id for p in properties if p.settable}
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
                    active = asyncio.create_task(self.command_controller.handle(key, message.payload))
        finally:
            if active is not None:
                if not active.done():
                    active.cancel()
                await asyncio.gather(active, return_exceptions=True)

    def load_owned(self):
        try:
            data = json.loads(self.path.read_text())
            if not isinstance(data, dict) or data.get("schemaVersion") != 1:
                return {}
            result = {}
            for device, topics in data.get("devices", {}).items():
                if ID.fullmatch(device) and isinstance(topics, list) and all(isinstance(t, str) and len(t.split("/")) >= 3 and ID.fullmatch(t.split("/")[0]) and t.split("/")[1] == device and not any(c in t for c in "+#\0") for t in topics):
                    result[device] = set(topics)
            return result
        except (OSError, ValueError, TypeError, AttributeError):
            return {}

    def save_owned(self):
        atomic_json(self.path, {"schemaVersion": 1, "prefix": self.config.mqtt.homie_prefix,
                               "devices": {d: sorted(t) for d, t in self.owned.items()}})

    def properties(self, states):
        props = [p for state in states for p in state.properties]
        for state in states:
            if not state.diagnostics_enabled:
                continue
            status_key, time_key = state.diagnostic_keys
            props += [Property(*status_key.split("/"), "Source availability", "enum", format="init,ready,stale,error"),
                      Property(*time_key.split("/"), "Last successful receipt (UTC)", "string")]
        if len({p.key for p in props}) != len(props):
            raise ValueError("Duplicate Homie property ownership")
        return tuple(props)

    def snapshot(self, states, now=None):
        result = {}
        for state in states:
            result.update(state.fresh_values(now))
            if state.diagnostics_enabled:
                result[state.diagnostic_keys[0]] = state.status(now)
                if state.last_timestamp:
                    result[state.diagnostic_keys[1]] = state.last_timestamp
        status = "ready" if any(s.status(now) == "ready" for s in states) else "alert"
        return result, status

    async def serve_device(self, device, states, stop):
        mqtt, runtime = self.config.mqtt, self.config.runtime
        base = mqtt.homie_prefix + "/" + device
        props = self.properties(states)
        metadata = discovery(mqtt.homie_prefix, device, props) if states else {}
        all_topics = set(metadata) | {base + "/" + p.key for p in props}
        previous = self.owned.get(device, set()).copy()
        self.owned[device] = previous | all_topics
        self.save_owned()  # Record ownership before any retained publication.
        attempt = 0
        while not stop.is_set():
            props = self.properties(states)
            metadata = discovery(mqtt.homie_prefix, device, props) if states else {}
            all_topics = set(metadata) | {base + "/" + p.key for p in props}
            previous = self.owned.get(device, set()).copy()
            self.owned[device] = previous | all_topics
            self.save_owned()
            self.status[device] = False
            client = self.client_factory(
                mqtt.host, mqtt.port, username=mqtt.username or None, password=mqtt.password or None,
                identifier=mqtt.client_id + "-" + device, clean_session=True,
                keepalive=mqtt.keepalive_seconds, timeout=mqtt.connect_timeout_seconds,
                tls_context=ssl_context(mqtt.tls_ca_file, mqtt.tls_cert_file, mqtt.tls_key_file, verify=mqtt.tls_verify) if mqtt.tls else None,
                will=aiomqtt.Will(base + "/$state", "lost", qos=mqtt.qos, retain=True),
                max_queued_outgoing_messages=mqtt.max_queue_messages,
                max_queued_incoming_messages=mqtt.max_queue_messages,
            )
            transport = getattr(client, "_client", None)
            if transport is not None:
                transport.connect_timeout = mqtt.connect_timeout_seconds
            try:
                async with mqtt_session(client, mqtt.connect_timeout_seconds, runtime.shutdown_timeout_seconds):
                    self.status[device] = True
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
                    # Clear every current value on reconnect before publishing fresh samples.
                    for p in props:
                        await client.publish(base + "/" + p.key, b"", qos=mqtt.qos, retain=True)
                    self.owned[device] = all_topics
                    self.save_owned()
                    previous = all_topics.copy()
                    consumer = None
                    if self.command_controller is not None and any(p.settable for p in props):
                        for p in props:
                            if p.settable:
                                await client.subscribe(base + "/" + p.key + "/set", qos=mqtt.qos)
                        consumer = asyncio.create_task(self.receive_commands(client, base, props))
                    attempt = 0
                    try:
                        await self.publish_values(client, base, states, stop, sent, last_status, consumer, props)
                    finally:
                        if consumer is not None:
                            consumer.cancel()
                            await asyncio.gather(consumer, return_exceptions=True)
                    # Publish waits for QoS acknowledgement. Timeout causes an abrupt close,
                    # leaving the broker's Will responsible for reporting loss.
                    await client.publish(base + "/$state", "disconnected", qos=mqtt.qos, retain=True,
                                         timeout=runtime.shutdown_timeout_seconds)
                    return
            except (aiomqtt.MqttError, OSError, asyncio.TimeoutError):
                self.status[device] = False
                if stop.is_set():
                    return
                LOG.warning("MQTT connection/publication failed; retrying with bounded backoff")
                await wait_stop(stop, backoff(attempt, runtime.reconnect_min_seconds, runtime.reconnect_max_seconds))
                attempt += 1
            finally:
                self.status[device] = False

    async def publish_values(self, client, base, states, stop, sent, last_status, consumer, declared=None):
        mqtt, runtime = self.config.mqtt, self.config.runtime
        declared = self.properties(states) if declared is None else declared
        while not stop.is_set():
            current = self.properties(states)
            if current != declared:
                # Inventory changes require a new Homie description and retained retirement.
                device = states[0].device
                metadata = discovery(mqtt.homie_prefix, device, current)
                topics = set(metadata) | {base + "/" + p.key for p in current}
                previous = self.owned.get(device, set())
                self.owned[device] = previous | topics
                self.save_owned()
                await client.publish(base + "/$state", "init", qos=mqtt.qos, retain=True)
                for topic in sorted(previous - topics):
                    await client.publish(topic, b"", qos=mqtt.qos, retain=True)
                    sent.pop(topic, None)
                old_keys = {p.key for p in declared}
                for p in current:
                    if p.key not in old_keys:
                        await client.publish(base + "/" + p.key, b"", qos=mqtt.qos, retain=True)
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
            desired = {base + "/" + key: value for key, value in values.items()}
            desired[base + "/$state"] = state
            for topic in sent.keys() - desired.keys():
                await client.publish(topic, b"", qos=mqtt.qos, retain=True)
            for topic, value in desired.items():
                if sent.get(topic) != value or (topic == base + "/$state" and time.monotonic() - last_status >= min(runtime.health_interval_seconds, 1)):
                    await client.publish(topic, value, qos=mqtt.qos, retain=True)
            last_status = time.monotonic()
            sent = desired
            await wait_stop(stop, min(runtime.health_interval_seconds, 1))

    async def run(self, stop):
        devices = {s.device for s in self.states} | set(self.owned)
        await asyncio.gather(*(self.serve_device(device, [s for s in self.states if s.device == device], stop)
                               for device in sorted(devices)))


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
        abort_client(client)
        raise
