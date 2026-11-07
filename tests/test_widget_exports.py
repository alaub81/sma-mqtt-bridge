"""Native MainUI exports preserve every widget and reject ambiguous source wrappers."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import export_openhab_widget as exporter

SINGLE = "version: 1\nwidgets:\n  example:\n    component: oh-label-card\n"
MULTIPLE = (
    "version: 1\nwidgets:\n  PlanCard:\n"
    "    component: oh-label-card\n"
    "    config:\n      title: \"=props.title || 'Plan'\"\n"
    "      stylesheet: |-\n        .card { color: red; }\n"
    "  PlanOpener:\n    component: oh-list-item\n"
    "    config:\n      actionModal: widget:PlanCard\n"
)


class WidgetExportTests(unittest.TestCase):
    def test_multiple_widgets_preserve_expressions_styles_and_dependency(self):
        widgets = exporter.render(MULTIPLE)
        self.assertEqual(set(widgets), {"PlanCard", "PlanOpener"})
        self.assertTrue(widgets["PlanCard"].startswith(exporter.HEADER + "uid: PlanCard\n"))
        self.assertIn("  title: \"=props.title || 'Plan'\"\n", widgets["PlanCard"])
        self.assertIn("    .card { color: red; }\n", widgets["PlanCard"])
        self.assertIn("  actionModal: widget:PlanCard\n", widgets["PlanOpener"])
        self.assertNotIn("version: 1", widgets["PlanOpener"])

    def test_invalid_empty_duplicate_and_misindented_sources_fail(self):
        for source in (
            "widgets:\n  example:\n    component: div\n",
            "version: 1\nwidgets:\n",
            "version: 1\nwidgets:\n  example:\n",
            "version: 1\nwidgets:\n  example:\n component: div\n",
            SINGLE + "  example:\n    component: div\n",
        ):
            with self.subTest(source=source), self.assertRaises(ValueError):
                exporter.render(source)

    def test_duplicate_uid_across_source_files_fails_before_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.yml").write_text(SINGLE)
            (root / "b.yaml").write_text(SINGLE)
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                exporter.exports(root)

    def test_generate_and_check_all_files_without_rewriting_or_deleting(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / "source", root / "output"
            source.mkdir()
            (source / "first.yml").write_text(SINGLE)
            (source / "second.yaml").write_text(MULTIPLE)
            with (
                patch.object(exporter, "ROOT", root),
                patch.object(exporter, "SOURCE_DIR", source),
                patch.object(exporter, "OUTPUT_DIR", output),
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                with patch("sys.argv", ["exporter"]):
                    self.assertEqual(exporter.main(), 0)
                self.assertEqual(
                    {p.name for p in output.iterdir()},
                    {"example.yaml", "PlanCard.yaml", "PlanOpener.yaml"},
                )
                with patch("sys.argv", ["exporter", "--check"]):
                    self.assertEqual(exporter.main(), 0)
                    (output / "example.yaml").write_text("edited fixture\n")
                    self.assertEqual(exporter.main(), 1)
                    self.assertEqual((output / "example.yaml").read_text(), "edited fixture\n")
                    (output / "example.yaml").write_text(exporter.render(SINGLE)["example"])
                    (output / "obsolete.yaml").write_text("uid: obsolete\n")
                    self.assertEqual(exporter.main(), 1)
                    self.assertTrue((output / "obsolete.yaml").exists())
