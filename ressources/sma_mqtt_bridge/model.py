"""Protocol-neutral property metadata and independently expiring samples."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
import math
import time

from .errors import ProtocolError


@dataclass(frozen=True)
class Property:
    node: str
    id: str
    name: str
    datatype: str = "float"
    unit: str = ""
    format: str = ""

    @property
    def key(self):
        return self.node + "/" + self.id


def payload(value, prop):
    if value is None:
        return None
    if prop.datatype == "boolean":
        return str(value).lower() if type(value) is bool else None
    if prop.datatype in ("integer", "float"):
        if isinstance(value, bool):
            return None
        try:
            number = Decimal(str(value))
            if not number.is_finite():
                return None
            if prop.datatype == "integer" and number != number.to_integral_value():
                return None
            return format(number, "f")
        except (ValueError, ArithmeticError):
            return None
    if prop.datatype == "enum" and str(value) not in prop.format.split(","):
        return None
    return str(value) if isinstance(value, (str, int)) else None


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

    @property
    def diagnostic_keys(self):
        if self.id == "portal":
            return "portal/status", "portal/last-success"
        return "diagnostics/" + self.id + "-status", "diagnostics/" + self.id + "-last-success"

    def update(self, values, now=None, timestamp=None):
        now = time.monotonic() if now is None else now
        by_key = {p.key: p for p in self.properties}
        if set(values) - set(by_key):
            raise ProtocolError("Adapter returned an undeclared property")
        usable = False
        for key, value in values.items():
            encoded = payload(value, by_key[key])
            if encoded is None:
                self.values.pop(key, None)
            else:
                self.values[key] = (encoded, now)
                usable = True
        if usable:
            self.last_success = now
            self.last_timestamp = timestamp or utc_timestamp()
            self.error = False

    def fresh_values(self, now=None):
        now = time.monotonic() if now is None else now
        return {k: value for k, (value, received) in self.values.items()
                if math.isfinite(received) and 0 <= now - received <= self.stale_seconds}

    def status(self, now=None):
        if self.error:
            return "error"
        if self.last_success is None:
            return "init"
        return "ready" if self.fresh_values(now) else "stale"
