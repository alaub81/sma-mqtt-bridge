"""Shared read deadlines and immutable, complete plant power cycles."""

import math


class ReadSchedule:
    """Keep contributing pollers on one origin without changing counter intervals."""

    def __init__(self, origin, power_seconds, power_pollers, energy_pollers):
        self.origin = origin
        self.power_seconds = power_seconds
        self.power_pollers = frozenset(power_pollers)
        self.energy_pollers = frozenset(energy_pollers)

    def cycle(self, now):
        return math.floor((now - self.origin) / self.power_seconds)

    def next_due(self, poller, interval, now):
        return self.origin + (math.floor((now - self.origin) / interval) + 1) * interval

    def priority(self, poller):
        return (
            0
            if poller["id"] in self.power_pollers
            else 1
            if poller["id"] in self.energy_pollers
            else 2
        )

    def groups(self, pollers):
        """Merge only adjacent, selected, fully described ranges on the same unit/function."""
        result = []
        for poller in sorted(
            pollers, key=lambda p: (self.priority(p), p.get("unitId", 0), p["function"], p["start"])
        ):
            if result:
                previous = result[-1]
                end = previous[-1]["start"] + previous[-1]["count"]
                first = previous[0]
                if (
                    self.priority(poller) < 2
                    and self.priority(first) == self.priority(poller)
                    and first.get("unitId") == poller.get("unitId")
                    and first["function"] == poller["function"]
                    and end == poller["start"]
                    and end + poller["count"] - first["start"] <= 125
                ):
                    previous.append(poller)
                    continue
            result.append([poller])
        return result


class PowerCycles:
    """Freeze each complete cycle once; never substitute a different cycle's samples."""

    def __init__(self, references, origin, seconds, *, label_attribute="power_cycle"):
        self.references = frozenset(references)
        self.label_attribute = label_attribute
        self.origin, self.seconds = origin, seconds
        self.pending = {}
        self.snapshot = None
        self.completed = -1
        self.captured_at = None
        self.failed = set()
        self.identities = {}

    def cycle(self, now):
        return math.floor((now - self.origin) / self.seconds)

    def observe(self, state, values, now):
        relevant = [ref for ref in self.references if ref.source == state.id]
        if not relevant:
            return
        identity = getattr(state, "identity_fingerprint", "")
        if state.id in self.identities and self.identities[state.id] != identity:
            self.snapshot = None
            self.pending.clear()
            self.failed.add(state.id)
        self.identities[state.id] = identity
        current = self.cycle(now)
        self.pending = {k: v for k, v in self.pending.items() if k >= current - 1}
        if values is None:
            self.failed.add(state.id)
            for frame in self.pending.values():
                for ref in relevant:
                    frame.pop(ref, None)
            return
        label = getattr(values, self.label_attribute, None) if self.label_attribute else None
        # UDP telegrams have no request label: their genuine receipt time chooses the cycle.
        label = current if label is None else label
        if label != current or label <= self.completed:
            return
        frame = self.pending.setdefault(label, {})
        changed = False
        for ref in relevant:
            if ref.key not in values:
                continue
            observation = state.values.get(ref.key)
            if observation is not None:
                start = self.origin + label * self.seconds
                if not start <= observation[1] < start + self.seconds:
                    continue
            frame[ref] = observation
            changed = True
        if changed and all(ref in frame for ref in relevant):
            self.failed.discard(state.id)
        if self.references <= frame.keys():
            self.snapshot = dict(frame)
            self.completed, self.captured_at = label, now
            self.pending = {k: v for k, v in self.pending.items() if k > label}

    @property
    def deadline(self):
        return self.origin + (self.completed + 2) * self.seconds

    def available(self, now):
        return self.snapshot is not None and not self.failed and now < self.deadline

    def evidence(self, now):
        current = self.cycle(now)
        pending = self.pending.get(current, {})
        return {
            "originMonotonic": self.origin,
            "intervalSeconds": self.seconds,
            "completedCycle": self.completed,
            "capturedMonotonic": self.captured_at,
            "deadlineMonotonic": self.deadline if self.snapshot is not None else None,
            "available": self.available(now),
            "waitingFor": sorted(ref.identity for ref in self.references - pending.keys())
            if current > self.completed
            else [],
            "failedSources": sorted(self.failed),
        }


class CounterReadCadence:
    """Anchor independent counter reads after the common round start, without bursts."""

    def __init__(self, origin, interval, collection_seconds):
        self.origin = origin + min(interval / 2, collection_seconds / 2)
        self.interval = interval

    def delay(self, now):
        if now < self.origin:
            return self.origin - now
        next_slot = math.floor((now - self.origin) / self.interval) + 1
        return self.origin + next_slot * self.interval - now
