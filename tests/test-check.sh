#!/usr/bin/env bash
# Run deterministic Python regression tests without device/broker access.
set -euo pipefail
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd -- "$PROJECT_DIR"
if [[ -x "$PROJECT_DIR/.venv/bin/python" ]]; then
  PYTHON_RUNNER="$PROJECT_DIR/.venv/bin/python"
else
  PYTHON_RUNNER="python3"
fi
"$PYTHON_RUNNER" -c 'import sys; assert sys.version_info >= (3, 14), "Python 3.14+ required"'
exec "$PYTHON_RUNNER" tests/run_tests.py
