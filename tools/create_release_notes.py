"""Generate public release notes locally from reachable stable Git tags and commits."""

import argparse
import html
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STABLE = re.compile(r"v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")


def version(tag):
    match = STABLE.fullmatch(tag)
    if not match:
        raise ValueError("A stable vMAJOR.MINOR.PATCH tag is required")
    return tuple(map(int, match.groups()))


def previous_tag(tag, reachable_tags):
    current = version(tag)
    older = [t for t in reachable_tags if STABLE.fullmatch(t) and version(t) < current]
    return max(older, key=version) if older else None


def markdown_text(value):
    value = html.escape(" ".join(value.split()), quote=False).replace("@", "&#64;")
    return re.sub(r"([\\`*_{}\[\]()#!|])", r"\\\1", value)


def render(tag, previous, commits, repository, digest=None):
    version(tag)
    if previous is not None and version(previous) >= version(tag):
        raise ValueError("Previous release must precede the target version")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Expected repository owner/name")
    if digest is not None and not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise ValueError("Expected a SHA-256 image digest")
    base = "https://github.com/" + repository
    image = "ghcr.io/" + repository.lower() + ":" + tag[1:]
    lines = ["## Changes", ""]
    for sha, subject in commits:
        if not re.fullmatch(r"[0-9a-f]{40,64}", sha) or not subject.strip():
            raise ValueError("Invalid Git commit metadata")
        lines.append(f"- {markdown_text(subject)} ([{sha[:7]}]({base}/commit/{sha}))")
    if not commits:
        lines.append("No non-merge commits in this release range; see the full comparison below.")
    lines += [
        "",
        "## Install or update",
        "",
        f"Container image: `{image}` (Linux amd64 and arm64).",
        "",
        f"- [Quick start]({base}/blob/{tag}/README.md#quick-start)",
        f"- [Supported devices and firmware]({base}/blob/{tag}/README.md#supported-devices)",
        f"- [Backup and update instructions]({base}/blob/{tag}/docs/UPDATING.md)",
        "",
        "Back up configuration and the persistent state volume before updating. "
        "Preserve `data_smab_state`, custom profiles and command journals.",
        "",
        "Release publication follows successful CI, container checks, security gates "
        "and multi-architecture image publication. These checks do not establish "
        "compatibility with unlisted hardware or installation-specific live acceptance.",
    ]
    if digest:
        lines += ["", f"Published image digest: `{digest}`."]
    target = f"compare/{previous}...{tag}" if previous else f"tree/{tag}"
    lines += ["", f"[Full {'comparison' if previous else 'source'}]({base}/{target})", ""]
    return "\n".join(lines)


def git(*args):
    return subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, check=True, timeout=30
    ).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--repository", default="alaub81/sma-mqtt-bridge")
    parser.add_argument("--image-digest")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        version(args.tag)
        ref = "refs/tags/" + args.tag
        git("rev-parse", "--verify", ref + "^{commit}")
        previous = previous_tag(args.tag, git("tag", "--merged", ref).splitlines())
        selection = f"refs/tags/{previous}..{ref}" if previous else ref
        commits = [
            tuple(line.split("\t", 1))
            for line in git("log", "--no-merges", "--format=%H%x09%s", selection).splitlines()
        ]
        content = render(args.tag, previous, commits, args.repository, args.image_digest)
        args.output.write_text(content, encoding="utf-8")
    except OSError, ValueError, subprocess.SubprocessError:
        parser.exit(2, "Release note generation failed; no release was published\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
