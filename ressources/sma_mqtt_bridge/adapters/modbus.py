"""Generic FC03/FC04 reader with profile-defined decoding and identity gate."""

import asyncio
import hashlib
import math
import struct
import time
from datetime import datetime, timezone
from decimal import Decimal

from ..errors import ProtocolError
from ..model import Property, channel_group_enabled
from ..plant_debug import PlantDebug
from ..profiles import verify_identity


class ModbusException(ProtocolError):
    """A validated Modbus exception response, without request/response contents."""

    def __init__(self, code):
        self.code = code
        super().__init__("Modbus read was rejected by the device")


def decode(registers, prop):
    words = registers[prop["offset"] : prop["offset"] + prop["length"]]
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
        # Explicit profile compatibility for successfully read power sentinels only.
        return Decimal(0) if prop.get("invalidAsZero", False) else None
    if prop.get("format") == "unix-time-iso":
        return datetime.fromtimestamp(value, timezone.utc).isoformat().replace("+00:00", "Z")
    if prop.get("format") == "sma-firmware":
        major, minor, build, release = value.to_bytes(4, "big")
        if any(b >> 4 > 9 or b & 15 > 9 for b in (major, minor)):
            return None
        major, minor = ((b >> 4) * 10 + (b & 15) for b in (major, minor))
        revision = ("N", "E", "A", "B", "R", "S")[release] if release <= 5 else str(release)
        return f"{major}.{minor:02d}.{build:02d}.{revision}"
    if "valueMap" in prop:
        mapped = prop["valueMap"].get(str(value))
        return (
            (mapped == "true") if prop["datatype"] == "boolean" and mapped is not None else mapped
        )
    if isinstance(value, str):
        return value
    scaled = Decimal(str(value)) * Decimal(str(prop["scale"]))
    if "minimum" in prop and scaled < Decimal(str(prop["minimum"])):
        return None
    if "maximum" in prop and scaled > Decimal(str(prop["maximum"])):
        return None
    return scaled


def profile_channel_group(definition):
    """Keep legacy host-profile defaults; bundled mappings declare their groups."""
    return definition.get(
        "channelGroup",
        "advanced"
        if definition["node"] in ("identity", "parameters")
        else "diagnostics"
        if definition["node"] == "diagnostics"
        else "basic",
    )


def profile_property(definition, *, node, stale_seconds, include_format, required_for_ready=False):
    """Build read metadata while callers retain format and readiness policies."""
    return Property(
        node=node,
        id=definition["id"],
        name=definition["name"],
        datatype=definition["datatype"],
        unit=definition["unit"],
        format=",".join(dict.fromkeys(definition.get("valueMap", {}).values()))
        if include_format
        else "",
        stale_seconds=stale_seconds,
        required_for_ready=required_for_ready,
        channel_group=profile_channel_group(definition),
    )


class ModbusReader:
    def __init__(self, settings, profile, interval_override=False, *, debug_interval_seconds=0):
        self.settings, self.profile = settings, profile
        self.interval_override = interval_override
        self.next_due = {}
        self.debug = PlantDebug(debug_interval_seconds)
        self.transaction = 0
        self.definitions = [p for p in profile["properties"] if self.channel_enabled(p)]
        active = {p["poller"] for p in self.definitions}
        self.pollers = [p for p in profile["pollers"] if p["id"] in active]
        self.properties = tuple(
            profile_property(
                p,
                node=p["node"],
                stale_seconds=max(
                    settings.stale_seconds,
                    2
                    * self.interval(next(b for b in profile["pollers"] if b["id"] == p["poller"])),
                ),
                include_format=p["datatype"] == "enum",
                required_for_ready=p.get("requiredForReady", False),
            )
            for p in self.definitions
        )
        energies = {
            p["id"]: p
            for p in self.definitions
            if p["node"] == "measurements"
            and p["id"] in ("battery-charge-energy", "battery-discharge-energy")
        }
        self.energy_ratio = (
            len(energies) == 2
            and len({p["poller"] for p in energies.values()}) == 1
            and all(p["unit"] == "kWh" for p in energies.values())
        )
        if self.energy_ratio:
            lifetime = min(p.stale_seconds for p in self.properties if p.id in energies)
            self.properties += (
                Property(
                    "measurements",
                    "battery-efficiency",
                    "Battery energy return ratio",
                    "float",
                    "%",
                    stale_seconds=lifetime,
                    channel_group="basic",
                ),
            )

    def channel_enabled(self, prop):
        return channel_group_enabled(
            profile_channel_group(prop),
            advanced=self.settings.advanced_channels_enabled,
            diagnostics=self.settings.diagnostics_enabled,
        )

    def interval(self, poller):
        if self.interval_override:
            return self.settings.poll_interval_seconds
        return poller.get("intervalSeconds", self.settings.poll_interval_seconds)

    def delay(self):
        now = time.monotonic()
        return max(
            0,
            min(
                (self.next_due.get(p["id"], now) for p in self.pollers),
                default=now + self.settings.poll_interval_seconds,
            )
            - now,
        )

    async def read_block(self, reader, writer, poller):
        self.transaction = (self.transaction + 1) % 65536
        pdu = struct.pack(">BHH", poller["function"], poller["start"], poller["count"])
        unit = poller.get("unitId", self.settings.unit_id)
        writer.write(struct.pack(">HHHB", self.transaction, 0, len(pdu) + 1, unit) + pdu)
        await writer.drain()
        header = await reader.readexactly(7)
        tx, proto, length, unit = struct.unpack(">HHHB", header)
        if (
            tx != self.transaction
            or proto != 0
            or unit != poller.get("unitId", self.settings.unit_id)
            or not 2 <= length <= 254
        ):
            raise ProtocolError("Invalid Modbus response header")
        body = await reader.readexactly(length - 1)
        if body[0] == poller["function"] | 0x80 and len(body) == 2:
            raise ModbusException(body[1])
        if (
            body[0] != poller["function"]
            or len(body) != 2 + poller["count"] * 2
            or body[1] != poller["count"] * 2
        ):
            raise ProtocolError("Invalid Modbus response payload")
        return list(struct.unpack(">" + "H" * poller["count"], body[2:]))

    def conditional_zero(self, prop, blocks):
        """Require guard observations from this read, never cached values."""
        guards = prop.get("invalidAsZeroWhen", {})
        definitions = {p["id"]: p for p in self.profile["properties"]}
        return bool(guards) and all(
            definitions[ref]["poller"] in blocks
            and decode(blocks[definitions[ref]["poller"]], definitions[ref]) in values
            for ref, values in guards.items()
        )

    async def read(self):
        """Verify local identity on every new session before measurement reads."""

        async def operation():
            reader, writer = await asyncio.open_connection(self.settings.host, self.settings.port)
            try:
                identity_refs = set(self.profile["identity"].values())
                identity_pollers = {
                    p["poller"] for p in self.profile["properties"] if p["id"] in identity_refs
                }
                blocks, values = {}, {}
                for poller in self.profile["pollers"]:
                    if poller["id"] in identity_pollers:
                        blocks[poller["id"]] = await self.read_block(reader, writer, poller)
                for p in self.profile["properties"]:
                    if p["id"] in identity_refs:
                        values[p["id"]] = decode(blocks[p["poller"]], p)
                verify_identity(self.profile, values, self.settings.expected_serial)
                self.identity_fingerprint = hashlib.sha256(
                    str(values[self.profile["identity"]["serial"]]).encode()
                ).hexdigest()
                now, selected = time.monotonic(), set()
                for poller in self.pollers:
                    if now >= self.next_due.get(poller["id"], 0):
                        if poller["id"] not in blocks:
                            blocks[poller["id"]] = await self.read_block(reader, writer, poller)
                        selected.add(poller["id"])
                # Read each guard on the same connection as its dependent DC sample.
                refs = {
                    ref
                    for p in self.definitions
                    if p["poller"] in selected
                    for ref in p.get("invalidAsZeroWhen", {})
                }
                guard_pollers = {p["poller"] for p in self.profile["properties"] if p["id"] in refs}
                for poller in self.profile["pollers"]:
                    if poller["id"] in guard_pollers and poller["id"] not in blocks:
                        blocks[poller["id"]] = await self.read_block(reader, writer, poller)
                result = {
                    p["node"] + "/" + p["id"]: decode(
                        blocks[p["poller"]],
                        p | {"invalidAsZero": True} if self.conditional_zero(p, blocks) else p,
                    )
                    for p in self.definitions
                    if p["poller"] in selected
                }
                if self.energy_ratio and "measurements/battery-charge-energy" in result:
                    charged = result["measurements/battery-charge-energy"]
                    discharged = result.get("measurements/battery-discharge-energy")
                    result["measurements/battery-efficiency"] = energy_return_ratio(
                        charged, discharged
                    )
                for poller in self.pollers:
                    if poller["id"] in selected:
                        self.next_due[poller["id"]] = now + self.interval(poller)
                self.debug.modbus(self, blocks, selected, now, result)
                return result
            finally:
                writer.close()
                try:
                    await asyncio.wait_for(writer.wait_closed(), self.settings.timeout_seconds)
                except asyncio.TimeoutError, OSError:
                    pass

        return await asyncio.wait_for(operation(), self.settings.timeout_seconds)

    async def close(self):
        pass


def energy_return_ratio(charged, discharged):
    """Cumulative counter ratio, not an independently verified physical efficiency."""
    if charged is None or discharged is None or charged <= 0 or discharged < 0:
        return None
    return (discharged / charged * 100).quantize(Decimal("0.01"))
