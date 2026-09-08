#!/usr/bin/env python3
"""
Generate release notes for Maven Decoder MCP Server releases.

The notes describe the release being cut, not whatever the static template
happened to say years ago. Two inputs:

1. ``--tag`` (required): the release tag, e.g. ``v1.3.0``. Everything
   (commits, version bumps) is derived from this tag plus its predecessor.
2. ``--out`` (optional): where to write RELEASE_NOTES.md (default: repo root).

Usage:
    python scripts/generate_release_notes.py --tag v1.3.0
    python scripts/generate_release_notes.py --tag v1.4.0 --check   # CI guard

With ``--check`` the script verifies that a prepared RELEASE_NOTES.md exists
and mentions the tag; CI refuses to release without it.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RELEASE_NOTES = REPO_ROOT / "RELEASE_NOTES.md"

INSTALL_SNIPPET = """## Installation

### Python/pip
```bash
pip install maven-decoder-mcp
```

### Node.js/npm
```bash
npm install -g maven-decoder-mcp
```

### Docker
```bash
docker run --rm -it \\
  -v ~/.m2:/home/mcpuser/.m2 \\
  ali79taba/maven-decoder-mcp:{tag}
```
"""


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=True,
    )
    return result.stdout.strip()


def previous_tag(tag: str) -> str | None:
    """Newest version tag older than ``tag`` (by creation date).

    When the release tag does not exist yet (notes are drafted before
    tagging), every existing tag is older.
    """
    tags = _git("tag", "--list", "v*").splitlines() or []
    if tag in tags:
        tags.remove(tag)
    if not tags:
        return None
    tags.sort(key=lambda t: _git("log", "-1", "--format=%ct", t))
    return tags[-1] if tags else None


def _ref_exists(ref: str) -> bool:
    try:
        _git("rev-parse", "--verify", "--quiet", ref)
    except subprocess.CalledProcessError:
        return False
    return True


def commits_since(tag: str, since: str | None) -> list[str]:
    """One-line subjects in ``since..tag``.

    When the release tag does not exist yet (notes are drafted before
    tagging), the range is read against HEAD instead.
    """
    end = tag if _ref_exists(tag) else "HEAD"
    rev_range = f"{since}..{end}" if since else end
    try:
        out = _git("log", "--format=%s", rev_range)
    except subprocess.CalledProcessError:
        return []
    return [line for line in out.splitlines() if line.strip()]


def split_commits(subjects: list[str]) -> tuple[list[str], list[str], list[str]]:
    """Split subjects into (features, fixes, other)."""
    features, fixes, other = [], [], []
    for subject in subjects:
        lowered = subject.lower()
        if lowered.startswith("feat"):
            features.append(subject)
        elif lowered.startswith(("fix", "perf", "revert")):
            fixes.append(subject)
        elif lowered.startswith(("docs", "chore", "ci", "test", "build", "refactor", "style")):
            other.append(subject)
        else:
            other.append(subject)
    return features, fixes, other


def bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- (none this release)"


def generate(tag: str) -> str:
    since = previous_tag(tag)
    subjects = commits_since(tag, since)
    features, fixes, other = split_commits(subjects)

    compare = f"...compare/{since}...{tag}" if since else f"...releases/tag/{tag}"
    notes = [
        f"# Maven Decoder MCP Server {tag}",
        "",
        "## What's Changed",
        "",
        "### Features",
        bullets(features),
        "",
        "### Fixes",
        bullets(fixes),
    ]
    if other:
        notes += ["", "### Maintenance", bullets(other)]
    notes += [
        "",
        INSTALL_SNIPPET.format(tag=tag.lstrip("v")),
        "",
        f"**Full Changelog**: https://github.com/salitaba/maven-decoder-mcp/compare/{since}...{tag}"
        if since
        else f"**Release**: https://github.com/salitaba/maven-decoder-mcp{compare}",
        "",
    ]
    return "\n".join(notes)


def check(tag: str) -> bool:
    """Verify a prepared RELEASE_NOTES.md mentions the tag and is non-trivial."""
    if not RELEASE_NOTES.is_file():
        print(f"FAIL: {RELEASE_NOTES} is missing.")
        print("Run: python scripts/generate_release_notes.py --tag", tag)
        return False

    body = RELEASE_NOTES.read_text()
    if tag not in body:
        print(f"FAIL: {RELEASE_NOTES} does not mention {tag}.")
        print("Run: python scripts/generate_release_notes.py --tag", tag)
        return False

    if len(body.strip().splitlines()) < 5:
        print(f"FAIL: {RELEASE_NOTES} looks like a stub ({len(body)} chars).")
        return False

    # Catch the old failure mode: body copied from an unrelated release, or
    # full of stale compare links to versions that are not part of this one.
    # The Full Changelog link legitimately names the previous tag, so only
    # flag *headed* release bodies for other versions.
    other_tags = set(re.findall(r"^# .*?\b(v\d+\.\d+\.\d+)\b", body, re.M)) - {tag}
    if other_tags:
        print(
            f"FAIL: {RELEASE_NOTES} mentions other releases "
            f"({sorted(other_tags)}); regenerate for {tag}."
        )
        return False

    print(f"OK: {RELEASE_NOTES} covers {tag}.")
    return True


def parse_tag(tag: str) -> str:
    tag = tag.strip()
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise ValueError(f"Tag must look like v1.2.3, got {tag!r}")
    return tag


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help="release tag, e.g. v1.3.0")
    parser.add_argument("--out", default=str(RELEASE_NOTES))
    parser.add_argument("--check", action="store_true",
                        help="only verify prepared notes, do not write")
    args = parser.parse_args()

    try:
        tag = parse_tag(args.tag)
    except ValueError as exc:
        print(f"FAIL: {exc}")
        return 2

    if args.check:
        return 0 if check(tag) else 1

    out = Path(args.out)
    out.write_text(generate(tag))
    print(f"Wrote {out} for {tag}.")
    print("Review and edit the body, then commit it before tagging.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
