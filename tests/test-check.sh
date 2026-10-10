#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd -- "$PROJECT_DIR"
export PATH="$PROJECT_DIR/.lint-venv/bin:$PROJECT_DIR/.lint-tools/bin:$PATH"

for tool in python3 c++ docker; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "Missing test dependency: $tool" >&2
    exit 1
  fi
done
docker compose version >/dev/null
exec python3 tests/run_tests.py
