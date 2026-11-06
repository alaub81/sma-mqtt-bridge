"""Bounded BYD RTU-over-TCP monitoring; selectors cannot change charging settings."""

import asyncio
import hashlib
import json
import logging
import struct
import time

from ..byd_properties import properties
from ..byd_values import base_values, detail_values, identity_values, log_values
from ..errors import ProtocolError
from ..model import SampleValues, utc_timestamp

LOG = logging.getLogger(__name__)


def crc16(data):
    value = 65535
    for byte in data:
        value ^= byte
        for _ in range(8):
            value = (value >> 1) ^ (0xA001 if value & 1 else 0)
    return value


class BYDReader:
    def __init__(self, settings, profile, max_payload_bytes=4096):
        self.settings, self.profile = settings, profile
        self.max_payload_bytes = max_payload_bytes
        self.properties = properties(settings, profile)
        self.keys = {p.key for p in self.properties}
        self.stage_keys = {stage: set() for stage in ("detail", "log")}
        for prop in self.properties:
            if (
                prop.node == "events"
                or prop.id.endswith("logrecords")
                or prop.id == "bydloglastsuccess"
            ):
                self.stage_keys["log"].add(prop.key)
            elif (
                prop.node.startswith("tower")
                or prop.id.startswith("tower")
                or prop.id
                in (
                    "bmsfirmwarea",
                    "bmsfirmwareb",
                    "parametertablea",
                    "parametertableb",
                    "byddetaillastsuccess",
                )
            ):
                self.stage_keys["detail"].add(prop.key)
        self.lock = asyncio.Lock()
        self.reader = self.writer = None
        self.next_due = {"detail": 0, "log": 0}
        self.identity_fingerprint = ""
        self.identity_changed = False

    async def close(self):
        writer, self.writer, self.reader = self.writer, None, None
        if writer is not None:
            writer.close()
            try:
                await asyncio.wait_for(writer.wait_closed(), self.settings.timeout_seconds)
            except OSError, TimeoutError:
                pass

    async def exchange(self, pdu):
        if self.writer is None:
            raise ProtocolError("BYD read connection unavailable")
        async with asyncio.timeout(self.settings.timeout_seconds):
            self.writer.write(pdu + struct.pack("<H", crc16(pdu)))
            await self.writer.drain()
            head = await self.reader.readexactly(2)
            if head[0] != self.settings.unit_id:
                raise ProtocolError("BYD response unit mismatch")
            if head[1] == pdu[1] | 0x80:
                response = head + await self.reader.readexactly(3)
            elif head[1] == pdu[1] == 3:
                size = await self.reader.readexactly(1)
                if size[0] > 250:
                    raise ProtocolError("BYD response exceeds read bound")
                response = head + size + await self.reader.readexactly(size[0] + 2)
            elif head[1] == pdu[1] == 16:
                response = head + await self.reader.readexactly(6)
            else:
                raise ProtocolError("BYD response function mismatch")
            if crc16(response):
                raise ProtocolError("BYD response CRC mismatch")
            if response[1] & 0x80:
                raise ProtocolError("BYD rejected diagnostic request")
            return response

    async def read_registers(self, address, count):
        if (address, count) not in {
            (0, 102),
            (0x500, 25),
            (0x551, 1),
            (0x558, 65),
            (0x5A1, 1),
            (0x5A8, 65),
        }:
            raise ProtocolError("BYD read outside request allowlist")
        response = await self.exchange(
            struct.pack(">BBHH", self.settings.unit_id, 3, address, count)
        )
        if response[2] != count * 2:
            raise ProtocolError("BYD response length mismatch")
        return list(struct.unpack(">" + str(count) + "H", response[3:-2]))

    async def select_buffer(self, address, unit):
        if not ((address == 0x550 and unit == 1) or (address == 0x5A0 and unit in (0, 1))):
            raise ProtocolError("BYD non-monitoring write refused")
        pdu = struct.pack(">BBHHBHH", self.settings.unit_id, 16, address, 2, 4, unit, 0x8100)
        response = await self.exchange(pdu)
        if response[2:6] != pdu[2:6]:
            raise ProtocolError("BYD diagnostic selector acknowledgment mismatch")
        async with asyncio.timeout(self.settings.buffer_ready_timeout_seconds):
            while True:
                await asyncio.sleep(self.settings.buffer_poll_interval_seconds)
                if await self.read_registers(address + 1, 1) == [0x8801]:
                    return

    async def buffer_pages(self, address, unit, count):
        await self.select_buffer(address, unit)
        pages = [await self.read_registers(address + 8, 65) for _ in range(count)]
        if any(page[0] != 128 for page in pages):
            raise ProtocolError("BYD diagnostic page marker mismatch")
        return [word for page in pages for word in page[1:]]

    async def open_identity(self):
        self.reader, self.writer = await asyncio.wait_for(
            asyncio.open_connection(self.settings.host, self.settings.port),
            self.settings.timeout_seconds,
        )
        raw = await self.read_registers(0, 102)
        values = identity_values(raw, self.profile, self.settings.expected_serial)
        fingerprint = hashlib.sha256(
            json.dumps([values["identity/serial"], self.profile], sort_keys=True).encode()
        ).hexdigest()
        self.identity_changed |= bool(
            self.identity_fingerprint and self.identity_fingerprint != fingerprint
        )
        self.identity_fingerprint = fingerprint
        return values

    async def read(self):
        if not self.settings.enabled or self.settings.paused:
            return SampleValues({}, {})
        async with self.lock:
            values, times = {}, {}
            try:
                identity = await self.open_identity()
                raw = await self.read_registers(0x500, 25)
                base = base_values(raw, self.profile) | identity
                now = time.monotonic()
                values.update(base)
                times.update(dict.fromkeys(base, now))
                if self.identity_changed:
                    values.update(dict.fromkeys(self.stage_keys["detail"] | self.stage_keys["log"]))
                    self.next_due = dict.fromkeys(self.next_due, 0)
                for stage in ("detail", "log"):
                    if not self.stage_keys[stage] or now < self.next_due[stage]:
                        continue
                    self.next_due[stage] = now + getattr(
                        self.settings, stage + "_poll_interval_seconds"
                    )
                    try:
                        if stage == "detail":
                            data = await self.buffer_pages(0x550, 1, 4)
                            more = detail_values(data, self.profile, identity)
                        else:
                            more = {}
                            for unit, name in ((0, "bmu"), (1, "tower1")):
                                data = await self.buffer_pages(0x5A0, unit, 5)
                                more.update(log_values(data, name, self.max_payload_bytes))
                        more["diagnostics/byd" + stage + "lastsuccess"] = utc_timestamp()
                        values.update(more)
                        times.update(dict.fromkeys(more, time.monotonic()))
                    except (
                        OSError,
                        TimeoutError,
                        ProtocolError,
                        ValueError,
                        asyncio.IncompleteReadError,
                    ) as error:
                        # An uncertain selector is not repeated in this acquisition cycle.
                        values.update(dict.fromkeys(self.stage_keys[stage]))
                        LOG.warning("BYD %s acquisition failed (%s)", stage, type(error).__name__)
                        # A partial RTU frame must never be reused for another request.
                        break
            finally:
                await self.close()
            self.identity_changed = False
            return SampleValues({k: v for k, v in values.items() if k in self.keys}, times)
