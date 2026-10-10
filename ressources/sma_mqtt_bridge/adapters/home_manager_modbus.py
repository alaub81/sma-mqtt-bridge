"""Persistent, paced Home Manager NSD reads; never sends a write or Grid Guard login."""

import asyncio
import time

from ..config import Inverter
from ..errors import ProtocolError
from ..model import Property
from .modbus import ModbusException, ModbusReader, decode


class HomeManagerModbusReader(ModbusReader):
    def __init__(self, settings, profile, interval_override=False):
        transport = Inverter(advanced_channels_enabled=settings.advanced_channels_enabled,
                             diagnostics_enabled=settings.diagnostics_enabled, host=settings.host, port=settings.modbus_port, unit_id=1,
                             poll_interval_seconds=settings.poll_interval_seconds,
                             timeout_seconds=settings.timeout_seconds, stale_seconds=settings.stale_seconds)
        super().__init__(transport, profile, interval_override)
        self.home_settings = settings
        self.stream = self.writer = None
        self.last_closed = self.last_transaction = None
        self.assignments = {}
        self.assignment_received = {}
        self.rejected = set()
        self.core_properties = self.properties
        self.core_pollers = self.pollers
        self.core_definitions = self.definitions
        self.inventory_pollers = []
        inv = profile['inventory']
        # Preserve four-register assignment records; no block exceeds 125 registers.
        for slot in range(0, inv['slots'] if settings.advanced_channels_enabled else 0, 30):
            self.inventory_pollers.append({'id': f'inventory-{slot}', 'function': 4, 'unitId': 1,
                                          'start': inv['start'] + slot * 4,
                                          'count': min(30, inv['slots'] - slot) * 4,
                                          'slot': slot, 'intervalSeconds': inv['intervalSeconds']})
        self.pollers = list(self.core_pollers) + self.inventory_pollers
        self.definitions = {p['id']: [v for v in self.core_definitions if v['poller'] == p['id']]
                            for p in self.core_pollers}
        self.refresh_properties()

    def interval(self, poller):
        if self.interval_override and poller.get('unitId') == 2:
            return self.settings.poll_interval_seconds
        return poller.get('intervalSeconds', self.settings.poll_interval_seconds)

    def refresh_properties(self):
        props = list(self.core_properties)
        units = set()
        for slot, (_, _, unit) in sorted(self.assignments.items()):
            node = f'device-{slot + 1}'
            props += [Property(node, 'susy-id', 'Assigned SUSy ID', 'integer', stale_seconds=self.inventory_expiry()),
                      Property(node, 'serial', 'Assigned serial', 'integer', stale_seconds=self.inventory_expiry()),
                      Property(node, 'unit-id', 'Assigned Modbus unit', 'integer', stale_seconds=self.inventory_expiry())]
            if 3 <= unit <= 247 and unit not in units:
                units.add(unit)
                for v in self.profile['delegated']['properties']:
                    p = next(p for p in self.profile['delegated']['pollers'] if p['id'] == v['poller'])
                    props.append(Property(node, v['id'], v['name'], v['datatype'], v['unit'],
                                          ','.join(dict.fromkeys(v.get('valueMap', {}).values())),
                                          max(self.settings.stale_seconds, 2 * self.interval(p))))
        if self.home_settings.diagnostics_enabled:
            props.append(Property('diagnostics', 'modbus-rejected-blocks', 'Rejected read blocks', 'integer'))
        self.properties = tuple(props)

    def inventory_expiry(self):
        return max(self.settings.stale_seconds, 2 * self.profile['inventory']['intervalSeconds'])

    def rebuild_delegated(self):
        self.pollers = list(self.core_pollers) + self.inventory_pollers
        self.definitions = {p['id']: [v for v in self.core_definitions if v['poller'] == p['id']]
                            for p in self.core_pollers}
        now = time.monotonic()
        units = set()
        for slot, (_, serial, unit) in sorted(self.assignments.items()):
            # SMA resolves duplicate units to the first slot in the assignment table.
            if not 3 <= unit <= 247 or unit in units:
                continue
            units.add(unit)
            for original in self.profile['delegated']['pollers']:
                id = f'device-{slot + 1}-{serial}-{unit}-{original["id"]}'
                self.pollers.append({**original, 'id': id, 'unitId': unit, 'assignedSlot': slot})
                self.next_due.setdefault(id, now + self.interval(original))
                self.definitions[id] = [{**v, 'node': f'device-{slot + 1}'}
                                        for v in self.profile['delegated']['properties'] if v['poller'] == original['id']]
        active = {p['id'] for p in self.pollers}
        self.next_due = {k: v for k, v in self.next_due.items() if k in active}
        self.rejected &= active
        self.refresh_properties()

    async def paced_read(self, poller):
        if self.last_transaction is not None:
            delay = self.home_settings.transaction_delay_seconds - (time.monotonic() - self.last_transaction)
            if delay > 0:
                await asyncio.sleep(delay)
        try:
            return await asyncio.wait_for(self.read_block(self.stream, self.writer, poller), self.settings.timeout_seconds)
        finally:
            self.last_transaction = time.monotonic()

    async def connect(self):
        if self.writer is not None:
            return {}
        if self.last_closed is not None:
            delay = self.home_settings.reconnect_delay_seconds - (time.monotonic() - self.last_closed)
            if delay > 0:
                await asyncio.sleep(delay)
        self.stream, self.writer = await asyncio.wait_for(
            asyncio.open_connection(self.settings.host, self.settings.port), self.home_settings.connect_timeout_seconds)
        await asyncio.sleep(self.home_settings.after_connection_delay_seconds)
        refs = self.profile['identity']
        ids = set(refs.values())
        blocks = {}
        for p in self.profile['pollers']:
            if any(v['id'] in ids and v['poller'] == p['id'] for v in self.profile['properties']):
                blocks[p['id']] = await self.paced_read(p)
        identity = {v['id']: decode(blocks[v['poller']], v) for v in self.profile['properties'] if v['id'] in ids}
        expected = {'model': 9343, 'deviceClass': 8128, 'manufacturer': 461,
                    'serial': int(self.home_settings.serial), 'serialCopy': int(self.home_settings.serial)}
        if any(identity[refs[k]] != value for k, value in expected.items()):
            raise ProtocolError('Home Manager identity does not match the configured device')
        # Reconnect invalidates prior assignment knowledge before delegated access resumes.
        self.assignments.clear()
        self.assignment_received.clear()
        self.rebuild_delegated()
        for p in self.inventory_pollers:
            self.next_due.pop(p['id'], None)
        return {v['node'] + '/' + v['id']: identity[v['id']] for v in self.profile['properties'] if v['id'] in ids
                and v['node'] + '/' + v['id'] in {p.key for p in self.core_properties}}

    def delay(self):
        now = time.monotonic()
        return max(0, min(self.next_due.get(p['id'], now) for p in self.pollers) - now)

    def inventory_values(self, poller, words):
        first = poller['slot']
        old = dict(self.assignments)
        for offset in range(0, poller['count'], 4):
            slot = first + offset // 4
            self.assignments.pop(slot, None)
            self.assignment_received.pop(slot, None)
            if words is None:
                continue
            susy, hi, lo, unit = words[offset:offset + 4]
            serial = hi * 65536 + lo
            if susy not in (0, 65535) and serial not in (0, 4294967295) and unit not in (0, 65535):
                self.assignments[slot] = (susy, serial, unit)
                self.assignment_received[slot] = time.monotonic()
        self.rebuild_delegated()
        values = {}
        for slot, assignment in sorted(self.assignments.items()):
            for id, value in zip(('susy-id', 'serial', 'unit-id'), assignment, strict=True):
                values[f'device-{slot + 1}/{id}'] = value
            if old.get(slot) != assignment:
                for v in self.profile['delegated']['properties']:
                    if f'device-{slot + 1}/{v["id"]}' in {p.key for p in self.properties}:
                        values[f'device-{slot + 1}/{v["id"]}'] = None
        # Only this received inventory block refreshes assignment timestamps.
        return {k: v for k, v in values.items()
                if first <= int(k.split('/')[0].removeprefix('device-')) - 1 < first + poller['count'] // 4}

    async def read(self):
        try:
            values = await self.connect()
            now = time.monotonic()
            expired = [slot for slot, received in self.assignment_received.items()
                       if now - received > self.inventory_expiry()]
            for slot in expired:
                self.assignments.pop(slot, None)
                self.assignment_received.pop(slot, None)
            if expired:
                self.rebuild_delegated()
            due = [p for p in self.pollers if self.next_due.get(p['id'], now) <= now]
            if not due:
                return values
            # Short-period power reads cannot be starved by a large parameter inventory.
            p = min(due, key=lambda p: self.next_due.get(p['id'], now) + self.interval(p))
            words = None
            try:
                words = await self.paced_read(p)
                self.rejected.discard(p['id'])
            except ModbusException:
                self.rejected.add(p['id'])
            self.next_due[p['id']] = time.monotonic() + self.interval(p)
            if 'slot' in p:
                values.update(self.inventory_values(p, words))
            else:
                values.update({v['node'] + '/' + v['id']: decode(words, v) if words is not None else None
                               for v in self.definitions[p['id']]})
            if self.home_settings.diagnostics_enabled:
                values['diagnostics/modbus-rejected-blocks'] = len(self.rejected)
            return values
        except BaseException:
            await self.close()
            raise

    async def close(self):
        writer, self.writer = self.writer, None
        self.stream = None
        if writer is not None:
            writer.close()
            self.last_closed = time.monotonic()
            try:
                await asyncio.wait_for(writer.wait_closed(), self.settings.timeout_seconds)
            except (OSError, asyncio.TimeoutError):
                pass
