"""Shared eCharger device-time classification with bounded clock-skew tolerance."""

from datetime import datetime, timezone

DEFAULT_FUTURE_TOLERANCE_SECONDS = 0.01


def sample_timestamp(
    timestamp, now, stale_seconds, future_tolerance_seconds=DEFAULT_FUTURE_TOLERANCE_SECONDS
):
    """Keep raw age for evidence; only a tiny future lead may count as fresh."""
    try:
        measured = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        age = (now - measured).total_seconds()
        stamp = measured.astimezone(timezone.utc).isoformat()
    except AttributeError, TypeError, ValueError, OverflowError:
        return None, None, "invalid"
    quality = (
        "future"
        if age < -future_tolerance_seconds
        else "fresh"
        if age <= stale_seconds
        else "stale"
    )
    return stamp, age, quality
