#!/bin/sh
# Resolve the checkout version before Docker receives the restricted public context.
set -eu
cd "$(dirname "$0")/.."
smab_python=python3.15
if [ -x .venv/bin/python ]; then smab_python=.venv/bin/python; fi
smab_build_version=$(PYTHONPATH=ressources "$smab_python" -c 'from sma_mqtt_bridge import __version__; print(__version__)')
exec docker build -f Dockerfile-SMAB -t sma-mqtt-bridge:dev \
  --build-arg "SMAB_BUILD_VERSION=$smab_build_version" "$@" .
