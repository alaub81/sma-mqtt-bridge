#!/usr/bin/env bash
set -euo pipefail
cd /build/src

# Retain the BMW project's C++17, libcurl and libmosquitto toolchain.
# pkg-config emits separate compiler/linker flags.
# shellcheck disable=SC2046
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -pthread \
  sma_mqtt_bridge.cpp -o sma_mqtt_bridge \
  $(pkg-config --cflags --libs libmosquitto) -lcurl
