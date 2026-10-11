"""Resolve immutable image versions or local Git checkout versions without network I/O."""

import re
import subprocess
from pathlib import Path

UNKNOWN = "0.0.0+unknown"
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:-dev\.[0-9]+)?(?:\+[a-z0-9.]+)?")


def resolve_version(package_dir=None):
    package = Path(__file__).resolve().parent if package_dir is None else Path(package_dir)
    try:
        built = (package / "_build_version.txt").read_text(encoding="utf-8").strip()
        if VERSION.fullmatch(built):
            return built
        return UNKNOWN
    except FileNotFoundError:
        pass
    except OSError:
        return UNKNOWN
    root = package.parents[1]
    if not (root / ".git").exists():
        return UNKNOWN
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--match", "v[0-9]*", "--long", "--dirty", "--abbrev=8"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
            timeout=2,
        )
    except OSError, subprocess.SubprocessError:
        return UNKNOWN
    match = re.fullmatch(
        r"v([0-9]+\.[0-9]+\.[0-9]+)-([0-9]+)-g([0-9a-f]+)(-dirty)?", result.stdout.strip()
    )
    if match is None:
        return UNKNOWN
    base, distance, revision, dirty = match.groups()
    if distance == "0" and not dirty:
        return base
    return f"{base}-dev.{distance}+{revision}" + (".dirty" if dirty else "")
