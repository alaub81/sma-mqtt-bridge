"""Resource accounting boundaries, partial reads and bounded restart-aware sampling."""

import ast
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests import resource_soak


class ResourceSoakTests(unittest.TestCase):
    def test_cpu_delta_uses_one_core_and_rejects_missing_reset_or_bad_time(self):
        self.assertEqual(resource_soak.cpu_percent(100000, 700000, 60), 1)
        for old, new, elapsed in ((None, 1, 60), (1, None, 60), (2, 1, 60), (0, 1, 0)):
            self.assertIsNone(resource_soak.cpu_percent(old, new, elapsed))

    def test_process_memory_marks_partial_and_missing_reads(self):
        def read(path):
            if str(path) == "/proc/1/status":
                return "VmRSS:\t100 kB\nVmHWM:\t120 kB\nThreads:\t2\n"
            raise FileNotFoundError

        with patch.object(Path, "read_text", autospec=True, side_effect=read):
            values = resource_soak.process_memory(["1", "2"])
            self.assertEqual(values["processRssSumBytes"], 102400)
            self.assertEqual(values["processPeakRssSumBytes"], 122880)
            self.assertEqual((values["processesExpected"], values["processesRead"]), (2, 1))
            self.assertIsNone(resource_soak.process_memory(["2"])["processRssSumBytes"])

    def test_cgroup_root_and_missing_controller_do_not_substitute_host_memory(self):
        with patch.object(Path, "read_text", return_value="0::/\n"):
            self.assertEqual(
                resource_soak.cgroup_metrics("1"),
                {"cgroupCpuUsec": None, "cgroupMemoryBytes": None},
            )

        def read(path):
            if str(path) == "/proc/1/cgroup":
                return "0::/system.slice/fixture.scope\n"
            if path.name == "cpu.stat":
                return "usage_usec 12345\nuser_usec 10000\nsystem_usec 2345\n"
            raise FileNotFoundError

        with patch.object(Path, "read_text", autospec=True, side_effect=read):
            self.assertEqual(
                resource_soak.cgroup_metrics("1"),
                {"cgroupCpuUsec": 12345, "cgroupMemoryBytes": None},
            )

    def test_bounded_collection_marks_restart_gaps_and_does_not_save_container_identity(self):
        now = 0

        def sleep(seconds):
            nonlocal now
            now += seconds

        observations = [
            ({"cgroupCpuUsec": 100000}, ("private-container", "first-start")),
            ({"cgroupCpuUsec": 700000}, ("private-container", "first-start")),
            ({"status": "unavailable"}, None),
            ({"cgroupCpuUsec": 10000}, ("private-container", "new-start")),
            ({"cgroupCpuUsec": 610000}, ("private-container", "new-start")),
        ]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "samples.jsonl"
            with (
                patch(
                    "sys.argv",
                    ["resource_soak", "--duration-seconds", "240", "--output", str(output)],
                ),
                patch.object(resource_soak, "sample", side_effect=observations) as sample,
                patch.object(resource_soak.time, "monotonic", side_effect=lambda: now),
                patch.object(resource_soak.time, "sleep", side_effect=sleep),
            ):
                self.assertEqual(resource_soak.main(), 0)
            rows = [json.loads(line) for line in output.read_text().splitlines()]
            self.assertEqual(sample.call_count, 5)
            self.assertEqual([r["elapsedSeconds"] for r in rows], [0, 60, 120, 180, 240])
            self.assertEqual([r["cpuPercentOneCore"] for r in rows], [None, 1, None, None, 1])
            self.assertEqual([r["generation"] for r in rows], [1, 1, 2, 3, 3])
            self.assertNotIn("private-container", output.read_text())
            with patch("sys.argv", ["resource_soak", "--output", str(output)]):
                with self.assertRaises(FileExistsError):
                    resource_soak.main()

    def test_host_collector_syntax_remains_python_39_compatible(self):
        ast.parse(Path(resource_soak.__file__).read_text(), feature_version=(3, 9))
