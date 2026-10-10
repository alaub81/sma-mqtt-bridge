#!/usr/bin/env bash
set -euo pipefail
umask 077

# Explicit commands also support development and diagnostics.
# No authentication, device writes or token migration on container startup.
if [[ "${1:-}" == -* ]]; then
  set -- /app/sma_mqtt_bridge "$@"
fi
exec "$@"
