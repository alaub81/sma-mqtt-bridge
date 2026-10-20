"""Keep archived and active documentation file links verifiable without network I/O."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from lint import check_markdown_links


class DocumentationLinkTests(unittest.TestCase):
    def test_local_links_references_images_and_code_examples(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "target file.md").write_text("# Target\n")
            (root / "private").mkdir()
            (root / "private/README.md").write_text("# Public privacy policy\n")
            (root / "private/notes.md").write_text("Private installation evidence\n")
            document = root / "docs/check.md"
            for text, expected in (
                ("[target](../target%20file.md#heading)", True),
                ("![image](</target file.md>)", True),
                ('[ref]: <../target file.md> "Title"', True),
                ("[external](https://example.invalid/missing.md)", True),
                ("[mail](mailto:test@example.invalid)", True),
                ("[anchor](#heading)", True),
                ("[policy](../private/README.md)", True),
                ("[private](../private/notes.md)", False),
                ("[encoded](../private%2Fnotes.md)", False),
                ("[absolute](/private/notes.md)", False),
                ("`[example](missing.md)`", True),
                ("````md\n[example](missing.md)\n```\n[example](missing.md)\n````", True),
                ("~~~md\n[example](missing.md)\n~~~", True),
                ("[missing](missing.md)", False),
                ("![missing](missing.png)", False),
                ("[ref]: missing.md", False),
                ("```md\n[example](missing.md)\n```\n[actual](missing.md)", False),
            ):
                with self.subTest(text=text):
                    document.write_text(text + "\n")
                    output = io.StringIO()
                    with contextlib.redirect_stdout(output):
                        self.assertEqual(check_markdown_links(["docs/check.md"], root), expected)
                    self.assertEqual(bool(output.getvalue()), not expected)
