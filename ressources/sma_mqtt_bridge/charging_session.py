"""Historical session display, independent of measurement freshness and charging control."""

import copy
import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .errors import StateError
from .model import Property, SampleValues, SourceState, number
from .storage import MISSING, read_state, write_state

LOG = logging.getLogger(__name__)
ENERGY = "Measurement.ChaSess.WhIn"
VEHICLE = "Measurement.Operation.EVeh.ChaStt"
POWER = "Measurement.Metering.GridMs.TotWIn.ChaSta"
PROPERTIES = (
    Property(
        "session",
        "status",
        "Charging session status",
        "enum",
        format="unknown,waiting,charging,paused,completed",
        channel_group="basic",
    ),
    Property(
        "session",
        "energy",
        "Observed session energy",
        unit="kWh",
        stale_seconds=float("inf"),
        channel_group="basic",
    ),
    Property(
        "session",
        "energy-time",
        "Session energy observation time",
        "string",
        stale_seconds=float("inf"),
        channel_group="basic",
    ),
    Property(
        "session",
        "ended-at",
        "Observed session disconnection time",
        "string",
        stale_seconds=float("inf"),
        channel_group="basic",
    ),
)


def timestamp(value):
    """Reject naive/invalid timestamps instead of assigning a local timezone."""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo is not None else None
    except AttributeError, TypeError, ValueError, OverflowError:
        return None


@dataclass(frozen=True)
class SessionObservation:
    energy: object
    energy_time: datetime | None
    vehicle: object
    vehicle_time: datetime | None
    power: object
    observed_at: float


def observation(raw, stamps, stale_seconds, now, monotonic):
    """Only fresh, nonnegative numeric inputs can advance stored session evidence."""
    values, times, ages = {}, {}, {}
    for channel in (ENERGY, VEHICLE, POWER):
        stamp, value = timestamp(stamps.get(channel)), number(raw.get(channel))
        age = (now - stamp).total_seconds() if stamp is not None else -1
        if value is not None and value >= 0 and 0 <= age <= stale_seconds:
            values[channel], times[channel], ages[channel] = value, stamp, age
    return SessionObservation(
        values.get(ENERGY) / 1000 if ENERGY in values else None,
        times.get(ENERGY),
        values.get(VEHICLE),
        times.get(VEHICLE),
        values.get(POWER),
        monotonic - max((ages.get(VEHICLE, 0), ages.get(POWER, 0))),
    )


class ChargingSession:
    """Persist evidence before publication; a disconnect closes a sampled session."""

    def __init__(self, config):
        ec = config.echarger
        self.path = Path(config.runtime.state_dir) / "echarger-session.json"
        self.max_bytes = config.runtime.max_state_bytes
        self.latest_status_time = None
        # Store an installation fingerprint, never addresses, identities or credentials.
        identity = hashlib.sha256(
            "\0".join((ec.host, ec.expected_serial, ec.semp_device_id)).encode()
        ).hexdigest()
        self.data = {
            "schemaVersion": 1,
            "identity": identity,
            "connected": None,
            "boundary": None,
            "resetTime": None,
            "current": None,
            "last": None,
        }
        saved = read_state(self.path, self.max_bytes)
        if saved is not MISSING:
            self.validate(saved, identity)
            self.data = saved
        self.state = SourceState(
            "charging-session",
            ec.homie_id,
            PROPERTIES,
            ec.stale_seconds,
            diagnostics_enabled=False,
            contributes_availability=False,
        )
        self.state.max_payload_bytes = config.runtime.max_payload_bytes
        self.publish("unknown")

    @staticmethod
    def validate(data, identity):
        try:
            if (
                not isinstance(data, dict)
                or set(data)
                != {
                    "schemaVersion",
                    "identity",
                    "connected",
                    "boundary",
                    "resetTime",
                    "current",
                    "last",
                }
                or type(data["schemaVersion"]) is not int
                or data["schemaVersion"] != 1
                or data["identity"] != identity
                or (data["connected"] is not None and type(data["connected"]) is not bool)
                or (data["boundary"] is not None and timestamp(data["boundary"]) is None)
                or (data["resetTime"] is not None and timestamp(data["resetTime"]) is None)
            ):
                raise ValueError
            for key in ("current", "last"):
                entry = data[key]
                fields = {"energy", "time"} | ({"ended"} if key == "last" else set())
                if entry is None:
                    continue
                energy = number(entry.get("energy")) if isinstance(entry, dict) else None
                if (
                    not isinstance(entry, dict)
                    or set(entry) != fields
                    or not isinstance(entry["energy"], str)
                    or energy is None
                    or energy <= 0
                    or any(timestamp(entry[field]) is None for field in fields - {"energy"})
                    or (key == "last" and timestamp(entry["ended"]) < timestamp(entry["time"]))
                ):
                    raise ValueError
            if data["connected"] is False and data["current"] is not None:
                raise ValueError
            if data["resetTime"] is not None and (
                data["current"] is None
                or data["connected"] is not True
                or timestamp(data["resetTime"]) < timestamp(data["current"]["time"])
            ):
                raise ValueError
        except KeyError, TypeError, ValueError, ArithmeticError:
            raise StateError(
                "Invalid charging-session state; manual reconciliation required"
            ) from None

    def publish(self, status, observed_at=None, now=None):
        entry = self.data["current"] or self.data["last"]
        values = {
            "session/status": status,
            "session/energy": entry["energy"] if entry else None,
            "session/energy-time": entry["time"] if entry else "",
            "session/ended-at": entry.get("ended", "") if entry else "",
        }
        self.state.update(
            SampleValues(
                values, {"session/status": observed_at} if observed_at is not None else {}
            ),
            now=now,
        )

    def update(self, sample, now=None):
        if sample is None:
            self.publish("unknown", now=now)
            return
        candidate = copy.deepcopy(self.data)
        current = candidate["current"]
        vehicle, stamp = sample.vehicle, sample.vehicle_time
        boundary = timestamp(candidate["boundary"])
        if (
            vehicle is None
            or stamp is None
            or sample.power is None
            or (boundary is not None and stamp < boundary)
            or (self.latest_status_time is not None and stamp < self.latest_status_time)
        ):
            self.publish("unknown", sample.observed_at, now)
            return
        self.latest_status_time = stamp
        status = "unknown"
        if vehicle == 200111 and sample.power == 0:
            if (current is not None and stamp < timestamp(current["time"])) or (
                candidate["resetTime"] is not None and stamp < timestamp(candidate["resetTime"])
            ):
                self.publish("unknown", sample.observed_at, now)
                return
            if current is not None and stamp >= timestamp(current["time"]):
                candidate["last"] = current | {"ended": stamp.isoformat()}
                candidate["current"] = None
            if candidate["connected"] is not False:
                candidate["boundary"] = stamp.isoformat()
            candidate["connected"] = False
            candidate["resetTime"] = None
            status = "completed" if candidate["last"] else "waiting"
        elif vehicle in (200112, 200113, 5169):
            candidate["connected"] = True
            if (
                sample.energy is not None
                and sample.energy_time is not None
                and (boundary is None or sample.energy_time > boundary)
                and (current is None or sample.energy_time > timestamp(current["time"]))
                and (
                    candidate["resetTime"] is None
                    or sample.energy_time > timestamp(candidate["resetTime"])
                )
            ):
                if sample.energy > 0:
                    # A newer decreased counter is not proof of completion.
                    candidate["current"] = {
                        "energy": str(sample.energy),
                        "time": sample.energy_time.isoformat(),
                    }
                    candidate["resetTime"] = None
                elif current is not None:
                    # Reset and disconnected status may arrive in different frames.
                    # Preserve the positive evidence until the boundary is known.
                    candidate["resetTime"] = sample.energy_time.isoformat()
            if candidate["resetTime"] is not None:
                status = "unknown"
            elif vehicle == 200113 and sample.power > 0:
                status = "charging" if candidate["current"] else "unknown"
            elif vehicle in (200112, 5169) and sample.power == 0:
                status = (
                    "paused"
                    if candidate["current"]
                    else "completed"
                    if candidate["last"]
                    else "waiting"
                )
        if candidate != self.data:
            try:
                write_state(self.path, candidate, self.max_bytes)
            except OSError, StateError, ValueError:
                # Failed durability must not publish a new, uncommitted historical value.
                self.publish("unknown", sample.observed_at, now)
                self.state.error = True
                LOG.warning("Charging-session persistence unavailable")
                return
            self.data = candidate
        self.publish(status, sample.observed_at, now)
