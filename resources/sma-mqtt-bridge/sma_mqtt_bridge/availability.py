"""Secret-free transition logs and bounded summaries for prolonged outages."""

import logging
import time

from .errors import ProtocolTimeout
from .model import utc_timestamp

LOG = logging.getLogger(__name__)


def is_timeout(error):
    return (
        isinstance(error, (TimeoutError, ProtocolTimeout))
        or isinstance(error.__cause__, TimeoutError)
        or isinstance(error.__context__, TimeoutError)
    )


class Availability:
    def __init__(self, label, interval):
        self.label, self.interval = label, interval
        self.previous = None
        self.outage_since = None
        self.last_log = None
        self.failures = 0
        self.consecutive_failures = 0
        self.timeouts = 0
        self.last_success = ""
        self.last_error = ""
        self.last_progress = time.monotonic()
        self.phase = "init"

    def failure(self, timeout=False, reason=""):
        self.failures += 1
        self.consecutive_failures += 1
        self.timeouts += int(timeout)
        self.last_error = reason

    def success(self):
        self.last_success = utc_timestamp()
        self.consecutive_failures = 0

    def progress(self, phase):
        self.phase, self.last_progress = phase, time.monotonic()

    def observe(self, status, now=None):
        now = time.monotonic() if now is None else now
        bad = status in ("error", "stale", "lost")
        if bad and self.outage_since is None:
            self.outage_since = now
        changed = status != self.previous
        if status == "ready" and self.outage_since is not None:
            LOG.info(
                "%s recovered after %.1fs; failures=%d",
                self.label,
                now - self.outage_since,
                self.failures,
            )
            self.outage_since = None
        elif bad and (changed or self.last_log is None or now - self.last_log >= self.interval):
            LOG.warning(
                "%s unavailable (%s); outage=%.1fs failures=%d consecutive=%d timeouts=%d last-error=%s",
                self.label,
                status,
                now - self.outage_since,
                self.failures,
                self.consecutive_failures,
                self.timeouts,
                self.last_error or "none",
            )
            self.last_log = now
        self.previous = status

    def snapshot(self, now=None):
        now = time.monotonic() if now is None else now
        return {
            "failures": self.failures,
            "consecutiveFailures": self.consecutive_failures,
            "timeouts": self.timeouts,
            "outageSeconds": 0 if self.outage_since is None else max(0, now - self.outage_since),
            "lastSuccess": self.last_success,
            "lastError": self.last_error,
            "phase": self.phase,
            "progressAgeSeconds": max(0, now - self.last_progress),
        }
