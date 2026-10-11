"""Run all offline regression tests; empty or partially skipped suites fail."""
from pathlib import Path
import asyncio
import gc
import sys
import unittest
from unittest.mock import patch


def main():
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    # Local sources live under ressources; the image places them directly in /app.
    if (root / "ressources/sma_mqtt_bridge").is_dir():
        sys.path.insert(0, str(root / "ressources"))
    suite = unittest.defaultTestLoader.discover(str(root / "tests"))
    loop_errors = []
    original_new_loop = asyncio.events.new_event_loop

    def new_loop():
        loop = original_new_loop()

        def exception_handler(failed_loop, context):
            loop_errors.append((context.get("message", "Unexpected asyncio failure"),
                                type(context.get("exception")).__name__))
            failed_loop.default_exception_handler(context)

        loop.set_exception_handler(exception_handler)
        return loop

    with patch("asyncio.events.new_event_loop", new_loop):
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        # Collect unreachable client/future cycles before deciding suite success.
        gc.collect()
    if loop_errors:
        for message, error_type in loop_errors:
            print(f"Unhandled asyncio failure: {message} ({error_type})", file=sys.stderr)
        return 1
    if result.testsRun == 0:
        print("No regression tests were discovered.", file=sys.stderr)
        return 1
    if result.skipped:
        print("Skipped tests are not allowed in the pre-deployment check.", file=sys.stderr)
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
