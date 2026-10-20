"""Durable counter baselines with local calendar, reset and partial-day guards."""

import copy
import os
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from .energy_profile_compat import precision_inputs as configured_precision_inputs
from .errors import StateError
from .model import number
from .storage import MISSING, read_state, state_lock, write_state

ACCOUNT_FIELDS = {
    "date",
    "dailyBase",
    "totalBase",
    "last",
    "lastTime",
    "oldestTime",
    "start",
    "hardware",
    "dailyStatus",
    "totalStatus",
    "dailyValue",
    "totalValue",
}
DAY_STATES = {"partial", "complete", "gap", "reset"}


def utc_time(text):
    value = datetime.fromisoformat(text)
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError
    return value


def counter_vector(value):
    if not isinstance(value, dict) or not value:
        raise ValueError
    for key, text in value.items():
        if (
            not isinstance(key, str)
            or len(key) > 512
            or any(ord(c) < 32 for c in key)
            or not isinstance(text, str)
            or len(text) > 128
        ):
            raise ValueError
        parsed = number(text)
        if parsed is None or parsed < 0 or not -128 <= parsed.adjusted() <= 127:
            raise ValueError
    return {key: Decimal(text) for key, text in value.items()}


def validate_ledger(data):
    try:
        if (
            not isinstance(data, dict)
            or set(data)
            != (
                {"schemaVersion", "signature", "accounts", "precisionOffsets"}
                if data.get("schemaVersion") == 2
                else {"schemaVersion", "signature", "accounts"}
            )
            or type(data["schemaVersion"]) is not int
            or data["schemaVersion"] not in (1, 2)
            or not isinstance(data["signature"], str)
            or len(data["signature"]) != 64
            or any(c not in "0123456789abcdef" for c in data["signature"])
            or not isinstance(data["accounts"], dict)
            or set(data["accounts"])
            - {"import", "export", "house", "wallbox", "housewithoutwallbox"}
        ):
            raise ValueError
        if data["schemaVersion"] == 2:
            offsets = data["precisionOffsets"]
            if not isinstance(offsets, dict) or len(offsets) > 64:
                raise ValueError
            for key, value in offsets.items():
                if not isinstance(key, str) or not key or len(key) > 512:
                    raise ValueError
                if value is not None and (
                    not isinstance(value, str)
                    or len(value) > 32
                    or number(value) is None
                    or abs(Decimal(value)) > 1
                ):
                    raise ValueError
        for record in data["accounts"].values():
            if not isinstance(record, dict) or set(record) - {"history"} != ACCOUNT_FIELDS:
                raise ValueError
            date.fromisoformat(record["date"])
            history = record.get("history", {})
            if not isinstance(history, dict) or len(history) > 7:
                raise ValueError
            for day, value in history.items():
                if date.fromisoformat(day) >= date.fromisoformat(record["date"]):
                    raise ValueError
                counter_vector({day: value})
            if utc_time(record["start"]) > utc_time(record["lastTime"]):
                raise ValueError
            if utc_time(record["oldestTime"]) > utc_time(record["lastTime"]):
                raise ValueError
            vectors = [counter_vector(record[k]) for k in ("dailyBase", "totalBase", "last")]
            if any(set(v) != set(vectors[0]) for v in vectors):
                raise ValueError
            if record["dailyStatus"] not in DAY_STATES or record["totalStatus"] not in (
                "ready",
                "reset",
            ):
                raise ValueError
            if (
                not isinstance(record["hardware"], str)
                or len(record["hardware"]) != 64
                or any(c not in "0123456789abcdef" for c in record["hardware"])
            ):
                raise ValueError
            for key in ("dailyValue", "totalValue"):
                if record[key] is not None:
                    counter_vector({key: record[key]})
    except ValueError, TypeError, KeyError, AttributeError, OverflowError, ArithmeticError:
        raise StateError(
            "Energy state is corrupt; restore or reconcile it before startup"
        ) from None
    return data


def reset_energy_baselines(config):
    """Archive only the validated energy ledger under the normal exclusive state lock."""
    with state_lock(config.runtime.state_dir):
        path = Path(config.runtime.state_dir) / "energy-balances.json"
        data = read_state(path, config.runtime.max_state_bytes)
        if data is MISSING:
            return None
        validate_ledger(data)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        backup = path.with_name(f"energy-balances.backup-{stamp}-{uuid4().hex}.json")
        path.rename(backup)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        return backup.name


class EnergyBalances:
    def __init__(self, config, signature, zone, *, precision_inputs=None):
        precision_inputs = (
            configured_precision_inputs(config) if precision_inputs is None else precision_inputs
        )
        self.settings = config.plant
        self.zone = zone
        self.path = Path(config.runtime.state_dir) / "energy-balances.json"
        self.max_bytes = config.runtime.max_state_bytes
        loaded = read_state(self.path, self.max_bytes)
        self.data = (
            {"schemaVersion": 1, "signature": signature, "accounts": {}}
            if loaded is MISSING
            else validate_ledger(loaded)
        )
        self.binding_changed = self.data["signature"] != signature
        self.committed = copy.deepcopy(self.data["accounts"])
        self.dirty = False
        self.force_save = False
        self.last_save = None
        self.precision_backup = None
        if self.data["schemaVersion"] == 2:
            self.binding_changed |= set(self.data["precisionOffsets"]) != set(precision_inputs)
        elif precision_inputs and not self.binding_changed:
            if loaded is not MISSING:
                self.precision_backup = copy.deepcopy(self.data)
            existing = {key for record in self.data["accounts"].values() for key in record["last"]}
            self.data = self.data | {
                "schemaVersion": 2,
                "precisionOffsets": {
                    key: None if key in existing else "0" for key in precision_inputs
                },
            }
            self.dirty = self.force_save = True

    def precise_values(self, values, paired):
        """Align fine increments once to the previous coarse accounting origin."""
        if self.binding_changed or self.data["schemaVersion"] == 1:
            return values
        offsets = dict(self.data["precisionOffsets"])
        for key in values.keys() & offsets.keys():
            if offsets[key] is None:
                coarse = paired.get(key)
                if coarse is None or abs(coarse - values[key]) > 1:
                    return None
                offsets[key] = str(coarse - values[key])
        if offsets != self.data["precisionOffsets"]:
            self.data["precisionOffsets"] = offsets
            self.dirty = self.force_save = True
        return {key: value + Decimal(offsets.get(key) or "0") for key, value in values.items()}

    def persist(self, monotonic, *, force=False):
        if self.binding_changed or not self.dirty:
            return
        if (
            force
            or self.force_save
            or self.last_save is None
            or monotonic - self.last_save >= self.settings.checkpoint_interval_seconds
        ):
            if self.precision_backup is not None:
                backup = self.path.with_name(f"energy-balances.before-fine-{uuid4().hex}.json")
                write_state(backup, self.precision_backup, self.max_bytes)
                self.precision_backup = None
            write_state(self.path, self.data, self.max_bytes)
            self.committed = copy.deepcopy(self.data["accounts"])
            self.dirty = self.force_save = False
            self.last_save = monotonic

    def observe(
        self,
        name,
        values,
        signs,
        hardware,
        wall,
        oldest_wall,
        *,
        sample_wall=None,
        daily_only=False,
    ):
        """Never extrapolate a counter across an unobserved local midnight."""
        if self.binding_changed:
            return None, None, "configuration-changed"
        wall = wall.astimezone(timezone.utc)
        oldest_wall = oldest_wall.astimezone(timezone.utc)
        sample_wall = (sample_wall or wall).astimezone(timezone.utc)
        local_day = wall.astimezone(self.zone).date()
        record = self.data["accounts"].get(name)
        if record is not None:
            if set(record["last"]) != set(values) or record["hardware"] != hardware:
                return None, None, "configuration-changed"
            last_time = utc_time(record["lastTime"])
            # Reject older observations before any reset or baseline mutation.
            if wall < last_time or sample_wall < last_time:
                return None, None, "clock-error"
        offsets = self.data.get("precisionOffsets", {})
        if record is not None and any(
            offsets.get(key) is not None and Decimal(offsets[key]) <= value < 0
            for key, value in values.items()
        ):
            # A real reset can cross the calibrated origin; never persist negative counters.
            record["dailyStatus"] = record["totalStatus"] = "reset"
            self.dirty = self.force_save = True
            return None, None, "reset"
        encoded = {key: str(value) for key, value in values.items()}
        try:
            counter_vector(encoded)
        except ValueError:
            return None, None, "invalid"
        if record is None:
            record = {
                "date": local_day.isoformat(),
                "dailyBase": dict(encoded),
                "totalBase": dict(encoded),
                "last": dict(encoded),
                "lastTime": sample_wall.isoformat(),
                "oldestTime": oldest_wall.isoformat(),
                "start": sample_wall.isoformat(),
                "hardware": hardware,
                "dailyStatus": "partial",
                "totalStatus": "ready",
                "dailyValue": None,
                "totalValue": None,
            }
            self.data["accounts"][name] = record
            self.dirty = self.force_save = True
        last_time = utc_time(record["lastTime"])
        reset = any(values[key] < Decimal(record["last"][key]) for key in values)
        if reset:
            record["dailyStatus"] = record["totalStatus"] = "reset"
            self.dirty = self.force_save = True
        next_boundary = datetime.combine(
            local_day + timedelta(days=1), time(), self.zone
        ).astimezone(timezone.utc)
        before_boundary = next_boundary - timedelta(
            seconds=self.settings.boundary_tolerance_seconds
        )
        if last_time < before_boundary <= sample_wall:
            self.force_save = True
        if local_day.isoformat() != record["date"]:
            previous_day = date.fromisoformat(record["date"])
            boundary = datetime.combine(local_day, time(), self.zone).astimezone(timezone.utc)
            tolerance = timedelta(seconds=self.settings.boundary_tolerance_seconds)
            complete = (
                local_day == previous_day + timedelta(days=1)
                and last_time >= boundary - tolerance
                and boundary <= wall <= boundary + tolerance
                and oldest_wall >= boundary - tolerance
                and not reset
            )
            if name in ("house", "housewithoutwallbox"):
                history = record.setdefault("history", {})
                closed = self.balance(values, signs, record["dailyBase"])
                if (
                    complete
                    and record["dailyStatus"] == "complete"
                    and self.accept(closed, record["dailyValue"])
                ):
                    history[record["date"]] = str(closed)
                record["history"] = {
                    day: value
                    for day, value in history.items()
                    if local_day - timedelta(days=7) <= date.fromisoformat(day) < local_day
                }
            record.update(
                date=local_day.isoformat(),
                dailyBase=dict(encoded),
                dailyStatus="complete" if complete else "gap",
                dailyValue=None,
            )
            self.dirty = self.force_save = True
        previous = dict(record)
        record.update(
            last=encoded, lastTime=sample_wall.isoformat(), oldestTime=oldest_wall.isoformat()
        )
        daily = self.balance(values, signs, record["dailyBase"])
        total = self.balance(values, signs, record["totalBase"])
        if name == "house":
            total += Decimal(str(self.settings.initial_consumption_kwh))
        inconsistent = False
        if record["dailyStatus"] == "complete" or (
            self.settings.publish_partial_day and record["dailyStatus"] == "partial"
        ):
            if self.accept(daily, record["dailyValue"]):
                record["dailyValue"] = str(daily)
            else:
                daily, inconsistent = None, True
        else:
            daily = None
        if not daily_only and record["totalStatus"] == "ready":
            if self.accept(total, record["totalValue"]):
                record["totalValue"] = str(total)
            else:
                total, inconsistent = None, True
        else:
            total = None
        self.dirty |= record != previous
        status = (
            "reset"
            if name == "house" and record["totalStatus"] == "reset"
            else "inconsistent"
            if inconsistent
            else record["dailyStatus"]
        )
        return daily, total, status

    @staticmethod
    def balance(values, signs, baseline):
        return sum(
            (signs[key] * (value - Decimal(baseline[key])) for key, value in values.items()),
            Decimal(0),
        )

    @staticmethod
    def accept(value, previous):
        return value.is_finite() and value >= 0 and (previous is None or value >= Decimal(previous))
