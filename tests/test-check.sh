#!/usr/bin/env bash
# Prepare isolated dependencies and run offline tests without device/broker access.
set -euo pipefail
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd -- "$PROJECT_DIR"
if [[ $# -ne 0 ]]; then
  echo "Usage: ./tests/test-check.sh" >&2
  exit 2
fi
if [[ ! -x "$PROJECT_DIR/.venv/bin/python" ]]; then
  PYTHON_RUNNER=""
  for candidate in python3.15 python3.14 python3; do
    if command -v "$candidate" >/dev/null 2>&1 &&
      "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 14))'; then
      PYTHON_RUNNER="$candidate"
      break
    fi
  done
  if [[ -z "$PYTHON_RUNNER" ]]; then
    echo "Python 3.14+ is required; install Python 3.15 to match CI." >&2
    exit 1
  fi
  echo "Creating isolated test environment..."
  "$PYTHON_RUNNER" -m venv "$PROJECT_DIR/.venv"
fi
PYTHON_RUNNER="$PROJECT_DIR/.venv/bin/python"
"$PYTHON_RUNNER" -c 'import sys; assert sys.version_info >= (3, 14), "Python 3.14+ required"'
if ! "$PYTHON_RUNNER" - <<'PY'
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import sys

failures = []
for line in Path("ressources/requirements.txt").read_text().splitlines():
    if "==" not in line:
        continue
    package, expected = line.split("==", 1)
    try:
        actual = version(package)
    except PackageNotFoundError:
        actual = "not installed"
    if actual != expected:
        failures.append(f"{package}: expected {expected}, found {actual}")
if failures:
    print("Preparing test dependencies:\n" + "\n".join(failures), flush=True)
sys.exit(bool(failures))
PY
then
  "$PYTHON_RUNNER" -m pip install --requirement ressources/requirements.txt
fi
exec "$PYTHON_RUNNER" tests/run_tests.py
