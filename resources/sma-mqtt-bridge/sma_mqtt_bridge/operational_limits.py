"""Print allowlisted effective operational limits without network requests or secrets."""

import json

from .config import load_config
from .runtime import sources


def summary(config):
    """Resolve reader scheduling and property expiry without polling devices."""
    rows = []
    for state, reader, interval in sources(config):
        settings = getattr(reader, "settings", None)
        rows.append(
            {
                "source": state.id,
                "pollSeconds": interval,
                "requestTimeoutSeconds": getattr(settings, "timeout_seconds", None),
                "sourceStaleSeconds": state.stale_seconds,
                "propertyStaleSeconds": sorted(
                    {p.stale_seconds or state.stale_seconds for p in state.properties}
                ),
                "requiredProperties": list(state.required_keys),
                "pollerSeconds": sorted({reader.interval(p) for p in reader.pollers})
                if hasattr(reader, "pollers")
                else [],
            }
        )
    return {
        "sources": rows,
        "runtime": {
            key: getattr(config.runtime, key)
            for key in (
                "read_cycle_timeout_seconds",
                "reconnect_min_seconds",
                "reconnect_max_seconds",
                "failure_log_interval_seconds",
                "health_interval_seconds",
                "health_stale_seconds",
            )
        },
        "mqtt": {
            "connectTimeoutSeconds": config.mqtt.connect_timeout_seconds,
            "keepaliveSeconds": config.mqtt.keepalive_seconds,
        },
    }


def main():
    try:
        print(json.dumps(summary(load_config()), indent=2))
    except Exception as error:
        # Configuration exceptions can refer to private paths; disclose only the type.
        print(json.dumps({"error": type(error).__name__}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
