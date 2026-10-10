"""Run all offline regression tests; empty or partially skipped suites fail."""
from pathlib import Path
import sys
import unittest


def main():
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    # Local sources live under ressources; the image places them directly in /app.
    if (root / "ressources/sma_mqtt_bridge").is_dir():
        sys.path.insert(0, str(root / "ressources"))
    suite = unittest.defaultTestLoader.discover(str(root / "tests"))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        print("No regression tests were discovered.", file=sys.stderr)
        return 1
    if result.skipped:
        print("Skipped tests are not allowed in the pre-deployment check.", file=sys.stderr)
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
