"""Release notes cover direct commits without promoting prereleases or unsafe text."""

import unittest

from tools.create_release_notes import previous_tag, render, version

SHA = "a" * 40


class ReleaseNotesTests(unittest.TestCase):
    def test_previous_release_uses_numeric_stable_order(self):
        self.assertEqual(
            previous_tag("v1.10.0", ["v1.9.9", "v1.8.0", "v1.10.0-rc1", "v2.0.0"]),
            "v1.9.9",
        )
        self.assertIsNone(previous_tag("v1.0.0", ["v1.0.0", "v1.0.0-rc1"]))

    def test_direct_commit_and_versioned_setup_links_are_included(self):
        content = render("v1.2.3", "v1.2.2", [(SHA, "Fix missing energy values")], "owner/bridge")
        self.assertIn("Fix missing energy values", content)
        self.assertIn("/commit/" + SHA, content)
        self.assertIn("/compare/v1.2.2...v1.2.3", content)
        self.assertIn("ghcr.io/owner/bridge:1.2.3", content)
        self.assertIn("/blob/v1.2.3/docs/UPDATING.md", content)
        self.assertIn("data_smab_state", content)

    def test_commit_titles_cannot_create_mentions_html_or_extra_links(self):
        content = render(
            "v1.0.0", None, [(SHA, "Fix [link](https://example.invalid) <img> @everyone")], "o/r"
        )
        self.assertNotIn("@everyone", content)
        self.assertNotIn("<img>", content)
        self.assertIn(r"\[link\]\(https://example.invalid\)", content)
        self.assertIn("/tree/v1.0.0", content)

    def test_empty_range_and_exact_published_digest(self):
        digest = "sha256:" + "b" * 64
        content = render("v1.0.1", "v1.0.0", [], "o/r", digest)
        self.assertIn("No non-merge commits", content)
        self.assertIn(digest, content)

    def test_malformed_or_prerelease_inputs_fail(self):
        for tag in ("v1.0.0-rc1", "1.0.0", "v01.0.0", "v1.0.0\n"):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                version(tag)
        for override in (
            {"previous": "v2.0.0"},
            {"repository": "o/r/extra"},
            {"digest": "sha256:invalid"},
            {"commits": [("invalid", "Fix")]},
        ):
            args = dict(tag="v1.0.0", previous=None, commits=[], repository="o/r") | override
            with self.subTest(override=override), self.assertRaises(ValueError):
                render(**args)
