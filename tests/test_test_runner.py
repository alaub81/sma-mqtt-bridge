"""The pre-deployment runner must fail on otherwise unhandled event-loop errors."""

import asyncio
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest.mock import patch

from tests.run_tests import main


class StrictRunnerTests(unittest.TestCase):
    def exercise(self, orphan):
        class FixtureTest(unittest.IsolatedAsyncioTestCase):
            async def test_fixture(self):
                if orphan:
                    future = asyncio.get_running_loop().create_future()
                    future.set_exception(RuntimeError("Fixture unhandled future"))
                    del future
                await asyncio.sleep(0)

        suite = unittest.defaultTestLoader.loadTestsFromTestCase(FixtureTest)
        output = StringIO()
        with (
            patch("tests.run_tests.unittest.defaultTestLoader.discover", return_value=suite),
            redirect_stderr(output),
            redirect_stdout(output),
        ):
            status = main()
        return status, output.getvalue()

    def test_unhandled_future_fails_an_otherwise_passing_suite(self):
        status, output = self.exercise(True)
        self.assertEqual(status, 1)
        self.assertIn(
            "Unhandled asyncio failure: Future exception was never retrieved (RuntimeError)", output
        )

    def test_clean_loop_passes_without_false_alarm(self):
        status, output = self.exercise(False)
        self.assertEqual(status, 0)
        self.assertNotIn("Unhandled asyncio failure", output)
