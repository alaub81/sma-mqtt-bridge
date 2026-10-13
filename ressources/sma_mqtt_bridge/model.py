"""Protocol-neutral property metadata and independently expiring samples."""

import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from .errors import ConfigError, ProtocolError


@dataclass(frozen=True)
class Property:
    node: str
    id: str
    name: str
    datatype: str = "float"
    unit: str = ""
    format: str = ""
    stale_seconds: float | None = None
    settable: bool = False
    required_for_ready: bool = False

    @property
    def key(self):
        return self.node + "/" + self.id


def bounded_payload(text, max_bytes):
    try:
        return text if len(text.encode("utf-8")) <= max_bytes else None
    except UnicodeError:
        return None


def payload(value, prop, max_bytes=4096):
    if value is None:
        return None
    if prop.datatype == "boolean":
        return bounded_payload(str(value).lower(), max_bytes) if type(value) is bool else None
    if prop.datatype in ("integer", "float"):
        if isinstance(value, bool):
            return None
        try:
            number = Decimal(str(value))
            if not number.is_finite():
                return None
            if prop.datatype == "integer":
                if number != number.to_integral_value() or not -(2**63) <= number < 2**63:
                    return None
                return bounded_payload(str(int(number)), max_bytes)
            sign, digits, exponent = number.as_tuple()
            if exponent >= 0:
                length = sign + (len(digits) + exponent if number else 1)
            else:
                length = sign + max(len(digits) + 1, 2 - exponent)
            # Fixed-point expansion must be bounded before allocating its string.
            return format(number, "f") if length <= max_bytes else None
        except ValueError, ArithmeticError:
            return None
    if prop.datatype == "enum" and str(value) not in prop.format.split(","):
        return None
    return bounded_payload(str(value), max_bytes) if isinstance(value, (str, int)) else None


def number(value):
    if value is None or isinstance(value, bool) or not str(value).strip():
        return None
    try:
        n = Decimal(str(value))
        return n if n.is_finite() else None
    except ArithmeticError:
        return None


def utc_timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class SampleValues(dict):
    """Decoded values with optional monotonic observation times per property."""

    def __init__(self, values, observed_at):
        super().__init__(values)
        self.observed_at = observed_at


@dataclass
class SourceState:
    id: str
    device: str
    properties: tuple
    stale_seconds: float
    values: dict = field(default_factory=dict)
    last_success: float | None = None
    last_timestamp: str = ""
    error: bool = False
    diagnostics_enabled: bool = True
    ready_properties: tuple = ()
    monitor: object = None
    contributes_availability: bool = True
    initialization_deadline: float | None = None
    max_payload_bytes: int = 4096
    _indexed_properties: tuple | None = field(default=None, init=False, repr=False, compare=False)
    _by_key: dict = field(default_factory=dict, init=False, repr=False, compare=False)
    _default_required_keys: tuple = field(default=(), init=False, repr=False, compare=False)

    def property_index(self):
        """Cache immutable descriptions, rebuilding when the inventory tuple changes."""
        if self._indexed_properties is not self.properties:
            self._by_key = {p.key: p for p in self.properties}
            self._default_required_keys = tuple(
                p.key for p in self.properties if p.required_for_ready
            ) or tuple(p.key for p in self.properties if p.node == "measurements")
            self._indexed_properties = self.properties
        return self._by_key

    def __post_init__(self):
        if set(self.ready_properties) - self.property_index().keys():
            raise ConfigError("Readiness references an unavailable property")

    @property
    def required_keys(self):
        self.property_index()
        return self.ready_properties or self._default_required_keys

    def missing_critical(self, now=None):
        return sorted(set(self.required_keys) - set(self.fresh_values(now)))

    @property
    def diagnostic_keys(self):
        if self.id == "portal":
            return "portal/status", "portal/last-success"
        return "diagnostics/" + self.id + "-status", "diagnostics/" + self.id + "-last-success"

    def update(self, values, now=None, timestamp=None):
        now = time.monotonic() if now is None else now
        observed_at = values.observed_at if isinstance(values, SampleValues) else {}
        by_key = self.property_index()
        if set(values) - by_key.keys():
            raise ProtocolError("Adapter returned an undeclared property")
        usable = False
        for key, value in values.items():
            encoded = payload(value, by_key[key], self.max_payload_bytes)
            if encoded is None:
                self.values.pop(key, None)
            else:
                self.values[key] = (encoded, observed_at.get(key, now))
                usable = True
        if usable:
            self.last_success = now
            self.last_timestamp = timestamp or utc_timestamp()
            self.error = False
        if (
            self.initialization_deadline is not None
            and self.fresh_values(now)
            and not self.missing_critical(now)
        ):
            self.initialization_deadline = None

    def fresh_values(self, now=None):
        now = time.monotonic() if now is None else now
        by_key = self.property_index()
        return {
            k: value
            for k, (value, received) in self.values.items()
            if math.isfinite(received)
            and 0
            <= now - received
            <= (
                by_key[k].stale_seconds
                if by_key[k].stale_seconds is not None
                else self.stale_seconds
            )
        }

    def status(self, now=None):
        if self.error:
            return "error"
        if self.initialization_deadline is not None:
            now = time.monotonic() if now is None else now
            return "init" if now < self.initialization_deadline else "stale"
        if self.last_success is None:
            return "init"
        fresh = self.fresh_values(now)
        return "ready" if fresh and not self.missing_critical(now) else "stale"
