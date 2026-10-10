"""Generic FC03/FC04 reader with profile-defined decoding and identity gate."""

import asyncio
from decimal import Decimal
import math
import struct
import time

from ..errors import ProtocolError
from ..model import Property
from ..profiles import verify_identity


class ModbusException(ProtocolError):
    """A validated Modbus exception response, without request/response contents."""

    def __init__(self, code):
        self.code = code
        super().__init__("Modbus read was rejected by the device")


def decode(registers, prop):
    words = registers[prop["offset"]:prop["offset"] + prop["length"]]
    if len(words) != prop["length"]:
        raise ProtocolError("Truncated register value")
    if prop["wordOrder"] == "little":
        words = words[::-1]
    raw = b"".join(w.to_bytes(2, prop["byteOrder"]) for w in words)
    kind = prop["type"]
    if kind == "string":
        try:
            value = raw.rstrip(b"\0").decode("ascii")
        except UnicodeError:
            return None
    elif kind == "float32":
        value = struct.unpack(">f", raw)[0]
        if not math.isfinite(value):
            return None
    else:
        value = int.from_bytes(raw, "big", signed=kind.startswith("int"))
    if value in prop["invalid"] or str(value) in prop["invalid"]:
        return None
    if prop.get("format") == "sma-firmware":
        major, minor, build, release = value.to_bytes(4, "big")
        if any(b >> 4 > 9 or b & 15 > 9 for b in (major, minor)):
            return None
        major, minor = ((b >> 4) * 10 + (b & 15) for b in (major, minor))
        revision = ("N", "E", "A", "B", "R", "S")[release] if release <= 5 else str(release)
        return f"{major}.{minor:02d}.{build:02d}.{revision}"
    if "valueMap" in prop:
        mapped = prop["valueMap"].get(str(value))
        return (mapped == "true") if prop["datatype"] == "boolean" and mapped is not None else mapped
    if isinstance(value, str):
        return value
    scaled = Decimal(str(value)) * Decimal(str(prop["scale"]))
    if "minimum" in prop and scaled < Decimal(str(prop["minimum"])):
        return None
    if "maximum" in prop and scaled > Decimal(str(prop["maximum"])):
        return None
    return scaled


class ModbusReader:
    def __init__(self, settings, profile, interval_override=False):
        self.settings, self.profile = settings, profile
        self.interval_override = interval_override
        self.next_due = {}
        self.transaction = 0
        self.definitions = [p for p in profile["properties"] if self.channel_enabled(p)]
        active = {p["poller"] for p in self.definitions}
        self.pollers = [p for p in profile["pollers"] if p["id"] in active]
        self.properties = tuple(Property(p["node"], p["id"], p["name"], p["datatype"], p["unit"],
                                         ",".join(dict.fromkeys(p.get("valueMap", {}).values())) if p["datatype"] == "enum" else "",
                                         max(settings.stale_seconds, 2 * self.interval(next(b for b in profile["pollers"] if b["id"] == p["poller"]))))
                                for p in self.definitions)

    def channel_enabled(self, prop):
        group = prop.get("channelGroup", "advanced" if prop["node"] in ("identity", "parameters")
                         else "diagnostics" if prop["node"] == "diagnostics" else "basic")
        return ((group != "advanced" or self.settings.advanced_channels_enabled)
                and (group != "diagnostics" or self.settings.diagnostics_enabled))

    def interval(self, poller):
        if self.interval_override:
            return self.settings.poll_interval_seconds
        return poller.get("intervalSeconds", self.settings.poll_interval_seconds)

    def delay(self):
        now = time.monotonic()
        return max(0, min((self.next_due.get(p["id"], now) for p in self.pollers), default=now + self.settings.poll_interval_seconds) - now)

    async def read_block(self, reader, writer, poller):
        self.transaction = (self.transaction + 1) % 65536
        pdu = struct.pack(">BHH", poller["function"], poller["start"], poller["count"])
        unit = poller.get("unitId", self.settings.unit_id)
        writer.write(struct.pack(">HHHB", self.transaction, 0, len(pdu) + 1, unit) + pdu)
        await writer.drain()
        header = await reader.readexactly(7)
        tx, proto, length, unit = struct.unpack(">HHHB", header)
        if tx != self.transaction or proto != 0 or unit != poller.get("unitId", self.settings.unit_id) or not 2 <= length <= 254:
            raise ProtocolError("Invalid Modbus response header")
        body = await reader.readexactly(length - 1)
        if body[0] == poller["function"] | 0x80 and len(body) == 2:
            raise ModbusException(body[1])
        if body[0] != poller["function"] or len(body) != 2 + poller["count"] * 2 or body[1] != poller["count"] * 2:
            raise ProtocolError("Invalid Modbus response payload")
        return list(struct.unpack(">" + "H" * poller["count"], body[2:]))

    async def read(self):
        """Verify local identity on every new session before measurement reads."""
        async def operation():
            reader, writer = await asyncio.open_connection(self.settings.host, self.settings.port)
            try:
                identity_refs = set(self.profile["identity"].values())
                identity_pollers = {p["poller"] for p in self.profile["properties"] if p["id"] in identity_refs}
                blocks, values = {}, {}
                for poller in self.profile["pollers"]:
                    if poller["id"] in identity_pollers:
                        blocks[poller["id"]] = await self.read_block(reader, writer, poller)
                for p in self.profile["properties"]:
                    if p["id"] in identity_refs:
                        values[p["id"]] = decode(blocks[p["poller"]], p)
                verify_identity(self.profile, values, self.settings.expected_serial)
                now, selected = time.monotonic(), set()
                for poller in self.pollers:
                    if now >= self.next_due.get(poller["id"], 0):
                        if poller["id"] not in blocks:
                            blocks[poller["id"]] = await self.read_block(reader, writer, poller)
                        selected.add(poller["id"])
                result = {p["node"] + "/" + p["id"]: decode(blocks[p["poller"]], p)
                        for p in self.definitions if p["poller"] in selected}
                for poller in self.pollers:
                    if poller["id"] in selected:
                        self.next_due[poller["id"]] = now + self.interval(poller)
                return result
            finally:
                writer.close()
                try:
                    await asyncio.wait_for(writer.wait_closed(), self.settings.timeout_seconds)
                except (asyncio.TimeoutError, OSError):
                    pass
        return await asyncio.wait_for(operation(), self.settings.timeout_seconds)

    async def close(self):
        pass
