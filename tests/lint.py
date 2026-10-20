#!/usr/bin/env python3
"""Lint all existing tracked and non-ignored untracked files without modifying them."""

import json
import re
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def check_linter_versions():
    """Require the same pinned Python linter environment as CI."""
    failures = []
    for line in (ROOT / "tests/requirements-lint.txt").read_text().splitlines():
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
        print("Lint environment differs from CI:\n" + "\n".join(failures), flush=True)
        print(
            "Update with: .lint-venv/bin/python -m pip install "
            "--requirement tests/requirements-lint.txt",
            flush=True,
        )
    return not failures


def project_files():
    """Deduplicate staged/untracked paths and omit staged deletions and ignored data."""
    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return sorted(
        {
            name.decode("utf-8")
            for name in result.stdout.split(b"\0")
            if name and (ROOT / name.decode("utf-8")).is_file()
        }
    )


def check_text(files):
    failures = []
    for name in files:
        try:
            text = (ROOT / name).read_bytes().decode("utf-8")
        except UnicodeError:
            failures.append(f"{name}: not valid UTF-8")
            continue
        if "\r" in text:
            failures.append(f"{name}: use LF line endings")
        if text and not text.endswith("\n"):
            failures.append(f"{name}: missing final newline")
        for number, line in enumerate(text.splitlines(), 1):
            if re.match(r"^(<{7}|={7}|>{7})(?: |$)", line):
                failures.append(f"{name}:{number}: unresolved merge marker")
            # Markdown permits hard line breaks.
            if not name.endswith(".md") and line.rstrip() != line:
                failures.append(f"{name}:{number}: trailing whitespace")
    if failures:
        print("\n".join(failures), flush=True)
    return not failures


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def check_json(files):
    passed = True
    for name in files:
        try:
            json.loads((ROOT / name).read_text(), object_pairs_hook=reject_duplicate_keys)
        except (ValueError, UnicodeError) as error:
            print(f"{name}: {error}", flush=True)
            passed = False
    return passed


def check_dotenv(files):
    passed = True
    for name in files:
        keys = set()
        for number, line in enumerate((ROOT / name).read_text().splitlines(), 1):
            if line.startswith("# SMAB_"):
                line = line.removeprefix("# ")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", line)
            if not match or not match[1].startswith("SMAB_") or match[1] in keys:
                print(f"{name}:{number}: expected a unique KEY=value assignment", flush=True)
                passed = False
            else:
                keys.add(match[1])
    return passed


def check_markdown_links(files, root=ROOT):
    """Check local file targets in inline links/images and reference definitions.

    Ignore examples inside fenced/inline code, external URLs and same-page anchors.
    Heading anchors are deliberately outside this file-existence check.
    """
    passed = True
    for name in files:
        fence = None
        for number, line in enumerate((root / name).read_text().splitlines(), 1):
            marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
            if fence:
                if (
                    marker
                    and marker[1][0] == fence[0]
                    and len(marker[1]) >= len(fence)
                    and not marker[2].strip()
                ):
                    fence = None
                continue
            if marker:
                fence = marker[1]
                continue
            line = re.sub(r"(`+).*?\1", "", line)
            targets = re.findall(r"\]\(\s*(<[^>]*>|[^\s)]+)", line)
            reference = re.match(r"^ {0,3}\[[^]]+\]:\s*(<[^>]*>|\S+)", line)
            if reference:
                targets.append(reference[1])
            for target in targets:
                target = target.removeprefix("<").removesuffix(">")
                url = urlsplit(target)
                if url.scheme or url.netloc or not url.path:
                    continue
                path = unquote(url.path)
                destination = (
                    root / path.lstrip("/") if path.startswith("/") else root / name / ".." / path
                )
                if not destination.resolve().exists():
                    print(f"{name}:{number}: missing Markdown file target: {target}", flush=True)
                    passed = False
    return passed


def check_widget_export(_files):
    return (
        subprocess.run(
            [sys.executable, "tools/export_openhab_widget.py", "--check"],
            cwd=ROOT,
            check=False,
        ).returncode
        == 0
    )


def main():
    if len(sys.argv) != 1:
        print("Usage: ./tests/linter-check.sh (read-only; no arguments)", file=sys.stderr)
        return 2
    if not check_linter_versions():
        return 1
    try:
        files = project_files()
    except subprocess.CalledProcessError as error:
        print(f"Cannot list project files: {error}", file=sys.stderr)
        return 1
    if not files:
        print("No project files found.", file=sys.stderr)
        return 1
    results = []

    def check(label, paths, command=None, function=None, timeout=None):
        if not paths:
            return
        print(f"\n==> {label} ({len(paths)} files)", flush=True)
        if command:
            if not shutil.which(command[0]):
                print(f"Missing tool: {command[0]}. See README.md (Lint checks).", flush=True)
                passed = False
            else:
                try:
                    passed = (
                        subprocess.run(command + paths, cwd=ROOT, timeout=timeout).returncode == 0
                    )
                except subprocess.TimeoutExpired:
                    print(f"{label}: timed out after {timeout} seconds; check failed.", flush=True)
                    passed = False
        else:
            passed = function(paths)
        results.append((label, passed))

    check("Text hygiene / file coverage", files, function=check_text)
    check(
        "Markdown local file links",
        [p for p in files if p.endswith(".md")],
        function=check_markdown_links,
    )
    check(
        "JSON syntax and duplicate keys",
        [p for p in files if p.endswith(".json")],
        function=check_json,
    )
    check(
        "Dotenv examples",
        [p for p in files if Path(p).name == "smab.example.env"],
        function=check_dotenv,
    )
    check(
        "openHAB widget export",
        [p for p in files if p == "openHAB/yaml/widgets/echarger-comfort.yml"],
        function=check_widget_export,
    )
    check("ShellCheck", [p for p in files if p.endswith(".sh")], command=["shellcheck"])
    check(
        "Hadolint",
        [p for p in files if Path(p).name.startswith("Dockerfile")],
        command=["hadolint", "--config", ".hadolint.yaml"],
    )
    check(
        "YAML",
        [p for p in files if p.endswith((".yml", ".yaml"))],
        command=["yamllint", "--strict", "--config-file", ".yamllint.yaml"],
    )
    check(
        "GitHub Actions",
        [p for p in files if p.startswith(".github/workflows/") and p.endswith((".yml", ".yaml"))],
        command=["actionlint", "-pyflakes="],
    )
    check(
        "Python / Ruff",
        [p for p in files if p.endswith(".py")],
        command=["ruff", "check", "--config", "ruff.toml"],
    )
    check(
        "Python / formatting",
        [p for p in files if p.endswith(".py")],
        command=["ruff", "format", "--check", "--config", "ruff.toml"],
    )
    check(
        "Python / Pylint",
        [p for p in files if p.endswith(".py")],
        command=["pylint", "--rcfile", ".pylintrc", "--errors-only"],
        timeout=180,
    )
    check(
        "Markdown",
        [p for p in files if p.endswith(".md")],
        command=["pymarkdown", "--config", ".pymarkdown.yaml", "--strict-config", "scan"],
    )
    print("\n================ Summary ================", flush=True)
    print(f"All {len(files)} project files received the text hygiene check.", flush=True)
    for label, passed in results:
        print(f"{'PASS' if passed else 'FAIL'}  {label}", flush=True)
    return 0 if all(passed for _, passed in results) else 1


def cli():
    try:
        return main()
    except KeyboardInterrupt:
        print("\nLint checks interrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(cli())
