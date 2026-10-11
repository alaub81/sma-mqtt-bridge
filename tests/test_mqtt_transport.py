"""Real Python MQTT stack against an ephemeral deterministic loopback broker."""

import asyncio
from dataclasses import replace
import tempfile
import unittest

from sma_mqtt_bridge.config import load_config
from sma_mqtt_bridge.homie import HomiePublisher
from sma_mqtt_bridge.model import Property, SourceState


async def packet(reader):
    command = (await reader.readexactly(1))[0]
    length, multiplier = 0, 1
    for _ in range(4):
        byte = (await reader.readexactly(1))[0]
        length += (byte & 127) * multiplier
        if not byte & 128:
            return command, await reader.readexactly(length)
        multiplier *= 128
    raise ValueError('Invalid MQTT fixture packet length')


def string(data, offset):
    length = int.from_bytes(data[offset:offset + 2], 'big')
    end = offset + 2 + length
    return data[offset + 2:end].decode(), end


class MQTTTransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_actual_stack_retains_metadata_and_confirms_disconnect(self):
        await self.exercise_broker(False)

    async def test_actual_stack_recovers_after_broker_drops_unacknowledged_publish(self):
        await self.exercise_broker(True)

    async def test_actual_stack_recovers_with_delayed_publish_acknowledgement(self):
        await self.exercise_broker(True, acknowledgement_delay=.15)

    async def exercise_broker(self, drop_first, acknowledgement_delay=0):
        stop, received, connects, failures = asyncio.Event(), [], [], []
        disconnected = asyncio.Event()
        handlers = set()
        async def broker(reader, writer):
            handler = asyncio.current_task()
            handlers.add(handler)
            try:
                command, body = await packet(reader)
                self.assertEqual(command, 0x10)
                protocol, offset = string(body, 0)
                self.assertEqual(protocol, 'MQTT')
                flags = body[offset + 1]
                self.assertTrue(flags & 0x04)  # Will flag.
                self.assertTrue(flags & 0x20)  # Retained Will flag.
                client_id, offset = string(body, offset + 4)
                will_topic, offset = string(body, offset)
                will_payload, offset = string(body, offset)
                connects.append((client_id, will_topic, will_payload))
                writer.write(b'\x20\x02\x00\x00')
                await writer.drain()
                while True:
                    command, body = await packet(reader)
                    if command >> 4 == 3:
                        topic, offset = string(body, 0)
                        qos = (command >> 1) & 3
                        mid = body[offset:offset + 2] if qos else b''
                        offset += 2 if qos else 0
                        value = body[offset:].decode()
                        received.append((topic, value, bool(command & 1)))
                        if drop_first and len(connects) == 1:
                            # Lose the first publication before its QoS acknowledgement.
                            return
                        if qos == 1:
                            if acknowledgement_delay and value == 'init':
                                # Exercise an ACK slower than the former 100 ms test timeout.
                                await asyncio.sleep(acknowledgement_delay)
                            writer.write(b'\x40\x02' + mid)
                            await writer.drain()
                        if topic.endswith('/$state') and value == 'ready':
                            stop.set()
                    elif command == 0xc0:
                        writer.write(b'\xd0\x00')
                        await writer.drain()
                    elif command == 0xe0:
                        disconnected.set()
                        break
                    else:
                        raise AssertionError('Unexpected MQTT fixture command')
            except Exception as error:
                failures.append(error)
                stop.set()
            finally:
                writer.close()
                try:
                    await writer.wait_closed()
                finally:
                    handlers.discard(handler)
        server = await asyncio.start_server(broker, '127.0.0.1', 0)
        port = server.sockets[0].getsockname()[1]
        try:
            with tempfile.TemporaryDirectory() as tmp:
                config = load_config({'SMAB_STATE_DIR': tmp, 'SMAB_MQTT_TLS': 'false',
                                      'SMAB_MQTT_HOST': '127.0.0.1', 'SMAB_MQTT_PORT': str(port)})
                config = replace(config, runtime=replace(config.runtime, health_interval_seconds=.01,
                                                        reconnect_min_seconds=.001, reconnect_max_seconds=.002),
                                 mqtt=replace(config.mqtt, connect_timeout_seconds=2))
                state = SourceState('fixture', 'test-device', (Property('measurements', 'power', 'Power'),), 5)
                state.update({'measurements/power': 123})
                publisher = HomiePublisher(config, [state])
                await asyncio.wait_for(publisher.run(stop), 10)
                await asyncio.wait_for(disconnected.wait(), 2)
                if handlers:
                    await asyncio.wait_for(asyncio.gather(*handlers), 2)
                self.assertEqual(failures, [])
                self.assertEqual(connects, [('sma-mqtt-bridge-test-device', 'homie/test-device/$state', 'lost')] * (2 if drop_first else 1))
                self.assertIn(('homie/test-device/measurements/power', '123', True), received)
                self.assertIn(('homie/test-device/$state', 'disconnected', True), received)
                self.assertTrue(all(retain for _, _, retain in received))
                # Retrieving a failed future must not hide the supervised outage.
                self.assertEqual(publisher.monitors['test-device'].failures, 1 if drop_first else 0)
        finally:
            server.close()
            await server.wait_closed()
            for handler in handlers:
                handler.cancel()
            await asyncio.gather(*handlers, return_exceptions=True)
