"""SMA Energy Meter 0x6069 UDP frames; no NSD or charging-control traffic."""

import asyncio
import socket
import time
from decimal import Decimal

from ..errors import ProtocolError
from ..model import Property

# SMA EMETER-Protocol-TI-en-10 sections 3.1/3.3: W/10, A/1000, V/1000.
OBIS = {
    0x00010400: ("power-import", "W", 10),
    0x00020400: ("power-export", "W", 10),
    0x00010800: ("energy-import", "kWh", 3600000),
    0x00020800: ("energy-export", "kWh", 3600000),
}

# Class B=0 follows the existing meter dialect; C indexes identify the phases.
PHASE_OBIS = {}
for phase, base in enumerate((20, 40, 60), 1):
    for offset, name, unit, divisor in (
        (1, "power-drawn", "W", 10),
        (2, "power-grid-feed-in", "W", 10),
        (11, "current", "A", 1000),
        (12, "voltage", "V", 1000),
    ):
        PHASE_OBIS[((base + offset) << 16) | 0x0400] = (f"{name}-l{phase}", unit, divisor)
OBIS.update(PHASE_OBIS)
PHASE_KEYS = frozenset("measurements/" + name for name, _, _ in PHASE_OBIS.values())


def parse_telegram(data, expected_serial):
    if len(data) < 28 or data[:4] != b"SMA\0" or data[16:18] != b"\x60\x69":
        raise ProtocolError("Invalid or unsupported SMA meter frame")
    if int.from_bytes(data[20:24], "big") != int(expected_serial):
        return None
    timestamp = int.from_bytes(data[24:28], "big")
    offset, result, seen = 28, {}, set()
    while offset < len(data):
        if offset + 4 > len(data):
            raise ProtocolError("Truncated OBIS header")
        code = int.from_bytes(data[offset : offset + 4], "big")
        offset += 4
        if code == 0:
            if offset != len(data):
                raise ProtocolError("Unexpected data after meter terminator")
            break
        size = 4 if code == 0x90000000 else (code >> 8) & 0xFF
        if size not in (4, 8) or offset + size > len(data) or code in seen:
            raise ProtocolError("Invalid/truncated/duplicate OBIS record")
        seen.add(code)
        # Accept documented channel B=1 and existing B=0 telegrams.
        lookup = code & 0x00FFFFFF if code >> 24 == 1 else code
        if lookup in OBIS:
            name, _, divisor = OBIS[lookup]
            if "measurements/" + name in result:
                raise ProtocolError("Duplicate meter measurement")
            raw = int.from_bytes(data[offset : offset + size], "big")
            result["measurements/" + name] = Decimal(raw) / divisor
        offset += size
    return timestamp, result


class MeterReader:
    def __init__(self, settings, *, phases_only=False):
        self.settings = settings
        self.phases_only = phases_only
        self.socket = None
        self.last_counter = None
        self.last_received = None
        self.properties = tuple(
            Property(
                "measurements",
                name,
                name.replace("-", " ").title(),
                unit=unit,
                required_for_ready=name in ("power-import", "power-export"),
                channel_group="basic",
            )
            for name, unit, _ in (PHASE_OBIS if phases_only else OBIS).values()
        )

    async def read(self):
        if self.socket is None:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind((self.settings.bind_address, self.settings.port))
                if self.settings.multicast_enabled:
                    membership = socket.inet_aton(self.settings.multicast_group) + socket.inet_aton(
                        self.settings.interface_address
                    )
                    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)
                sock.setblocking(False)
                self.socket = sock
            except BaseException:
                sock.close()
                raise

        async def receive():
            while True:
                data, sender = await asyncio.get_running_loop().sock_recvfrom(self.socket, 65536)
                if self.settings.host and sender[0] != self.settings.host:
                    continue
                parsed = parse_telegram(data, self.settings.serial)
                if parsed is None:
                    continue
                counter, values = parsed
                now = time.monotonic()
                if self.last_counter is not None:
                    delta = (counter - self.last_counter) & 0xFFFFFFFF
                    if delta == 0 or (
                        delta >= 0x80000000
                        and now - self.last_received < self.settings.stale_seconds
                    ):
                        continue
                self.last_counter, self.last_received = counter, now
                if self.phases_only:
                    return {key: value for key, value in values.items() if key in PHASE_KEYS}
                return values

        return await asyncio.wait_for(receive(), self.settings.timeout_seconds)

    async def close(self):
        if self.socket is not None:
            self.socket.close()
            self.socket = None
