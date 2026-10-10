"""Fail-closed state loading and a process-lifetime lock on the state volume."""

from contextlib import contextmanager
from datetime import datetime
import fcntl
import json
import math
import os
from pathlib import Path
import stat

from .adapters.http import json_data
from .errors import ProtocolError, StateError
from .health import atomic_json

MISSING = object()


def write_state(path, data, max_bytes):
    size = len((json.dumps(data, allow_nan=False, sort_keys=True) + "\n").encode("utf-8"))
    if size > max_bytes:
        raise StateError("Persistent state exceeds the configured size limit")
    atomic_json(path, data)


def read_state(path, max_bytes):
    try:
        # Reject symlinks, directories and FIFOs; a broken symlink is not missing state.
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        if os.path.lexists(path):
            raise StateError("Persistent state is unreadable; manual reconciliation required") from None
        return MISSING
    except OSError:
        raise StateError("Persistent state is unreadable; manual reconciliation required") from None
    try:
        with os.fdopen(fd, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise StateError("Persistent state must be a regular file")
            data = stream.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise StateError("Persistent state exceeds the configured size limit")
        return json_data(data.decode("utf-8"))
    except (OSError, UnicodeError, ProtocolError, RecursionError, OverflowError):
        raise StateError("Persistent state is corrupt; manual reconciliation required") from None


def journal_status(path, max_bytes):
    try:
        data = read_state(path, max_bytes)
        if data is MISSING:
            return None
        if not isinstance(data, dict) or type(data.get("schemaVersion")) is not int or data["schemaVersion"] != 1:
            raise ValueError
        stamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        if stamp.tzinfo is None or not isinstance(data.get("property"), str) or not data["property"]:
            raise ValueError
        if data["property"] == "plan":
            if (set(data) != {"schemaVersion", "property", "targets", "phase", "timestamp"}
                    or data["phase"] not in ("parameters", "mode") or not isinstance(data["targets"], dict)
                    or set(data["targets"]) != {"Parameter.Chrg.Plan.En", "Parameter.Chrg.Plan.StopTm"}
                    or any(not isinstance(v, str) or not v for v in data["targets"].values())):
                raise ValueError
        else:
            if set(data) != {"schemaVersion", "property", "target", "timestamp"}:
                raise ValueError
            if data["property"] == "pv-minimum":
                target = data["target"]
                if (not isinstance(target, dict)
                        or set(target) != {"minPvPercentage", "pvSurplusOnly", "usePriceLimit", "priceLimit"}
                        or type(target["minPvPercentage"]) is not int or not 0 <= target["minPvPercentage"] <= 100
                        or (target["pvSurplusOnly"] is not None and target["pvSurplusOnly"] is not False)
                        or target["usePriceLimit"] is not False
                        or (target["priceLimit"] is not None and (type(target["priceLimit"]) not in (int, float)
                            or not math.isfinite(target["priceLimit"])))):
                    raise ValueError
            elif not isinstance(data["target"], str) or not data["target"]:
                raise ValueError
        return "blocked-uncertain"
    except (StateError, ValueError, KeyError, TypeError, AttributeError, OverflowError):
        return "blocked-corrupt"


@contextmanager
def state_lock(state_dir):
    """Never unlink the lock inode; the kernel releases the lease on process death."""
    path = Path(state_dir)
    try:
        path.mkdir(parents=True, exist_ok=True)
        fd = os.open(path / "bridge.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    except OSError:
        raise StateError("Cannot open the bridge state lock") from None
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise StateError("Bridge state lock must be a regular file")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise StateError("State directory is already in use by another bridge instance") from None
        yield
    finally:
        os.close(fd)
