"""SMA Energy Meter 0x6069 UDP frames; no NSD or charging-control traffic."""

import asyncio
import socket
import time
from decimal import Decimal

from ..errors import ProtocolError
from ..model import Property

# Protocol field definitions, checked against official openHAB ObisId documentation.
OBIS = {
    0x00010400: ("power-import", "W", 10),
    0x00020400: ("power-export", "W", 10),
    0x00010800: ("energy-import", "kWh", 3600000),
    0x00020800: ("energy-export", "kWh", 3600000),
}


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
        if code in OBIS:
            name, _, divisor = OBIS[code]
            raw = int.from_bytes(data[offset : offset + size], "big")
            result["measurements/" + name] = Decimal(raw) / divisor
        offset += size
    return timestamp, result


class MeterReader:
    def __init__(self, settings):
        self.settings = settings
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
            )
            for name, unit, _ in OBIS.values()
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
                return values

        return await asyncio.wait_for(receive(), self.settings.timeout_seconds)

    async def close(self):
        if self.socket is not None:
            self.socket.close()
            self.socket = None
