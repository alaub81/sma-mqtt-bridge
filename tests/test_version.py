"""Verify release/development identity and immutable image fallback behavior."""

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sma_mqtt_bridge.version import UNKNOWN, resolve_version


class VersionTests(unittest.TestCase):
    def test_git_tag_distance_and_dirty(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / ".git").mkdir()
            package = root / "ressources" / "sma_mqtt_bridge"
            package.mkdir(parents=True)
            for description, expected in (
                ("v0.3.2-0-gabcdef12", "0.3.2"),
                ("v0.3.2-4-gabcdef12", "0.3.2-dev.4+abcdef12"),
                ("v0.3.2-0-gabcdef12-dirty", "0.3.2-dev.0+abcdef12.dirty"),
                ("v0.3.2-rc1-0-gabcdef12", UNKNOWN),
            ):
                with (
                    self.subTest(description=description),
                    patch(
                        "sma_mqtt_bridge.version.subprocess.run",
                        return_value=subprocess.CompletedProcess([], 0, description + "\n"),
                    ),
                ):
                    self.assertEqual(resolve_version(package), expected)
            with patch("sma_mqtt_bridge.version.subprocess.run", side_effect=OSError):
                self.assertEqual(resolve_version(package), UNKNOWN)

    def test_image_version_without_git_or_environment_override(self):
        with tempfile.TemporaryDirectory() as folder:
            package = Path(folder) / "ressources" / "sma_mqtt_bridge"
            package.mkdir(parents=True)
            self.assertEqual(resolve_version(package), UNKNOWN)
            with patch("sma_mqtt_bridge.version.subprocess.run") as git:
                for value, expected in (("0.3.2", "0.3.2"), ("malformed\nversion", UNKNOWN)):
                    (package / "_build_version.txt").write_text(value, encoding="utf-8")
                    self.assertEqual(resolve_version(package), expected)
                git.assert_not_called()
