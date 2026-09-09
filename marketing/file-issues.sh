#!/usr/bin/env bash
# NOT IDEMPOTENT. Every run CREATES NEW PUBLIC ISSUES on salitaba/maven-decoder-mcp.
# Running it twice files 15 duplicates. There is no undo; closing them still leaves
# them public and visible. Read marketing/issues-to-file.md before you run this.

set -euo pipefail

# ---------------------------------------------------------------------------
# Safety guard: refuse to do anything unless a human explicitly opts in.
# ---------------------------------------------------------------------------
if [[ "${CONFIRM:-}" != "yes" ]]; then
    cat >&2 <<'EOF'
REFUSING TO RUN.

This script creates 15 real, public GitHub issues on salitaba/maven-decoder-mcp.
It is not idempotent and cannot be undone.

Dry run (prints the titles it would file, touches nothing):

    ./marketing/file-issues.sh --list

To actually file them:

    CONFIRM=yes ./marketing/file-issues.sh

EOF
    if [[ "${1:-}" == "--list" ]]; then
        echo "Would file these issues:" >&2
        grep -E '^\*\*Title:\*\* ' "$(dirname "$0")/issues-to-file.md" \
            | sed 's/^\*\*Title:\*\* /  - /' >&2
    fi
    exit 1
fi

REPO="salitaba/maven-decoder-mcp"
SOURCE_MD="$(cd "$(dirname "$0")" && pwd)/issues-to-file.md"
LABELS="good first issue,help wanted"

if [[ ! -f "$SOURCE_MD" ]]; then
    echo "Cannot find $SOURCE_MD" >&2
    exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
    echo "gh is not installed; see https://cli.github.com/" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Split issues-to-file.md into one body file per issue.
# A section runs from '## Issue N' to the next '---' terminator; the body is
# everything after the '**Body:**' marker.
# ---------------------------------------------------------------------------
BODY_DIR="$(mktemp -d)"
trap 'rm -rf "$BODY_DIR"' EXIT

python3 - "$SOURCE_MD" "$BODY_DIR" <<'PY'
import pathlib
import re
import sys

source = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
outdir = pathlib.Path(sys.argv[2])

# Sections look like:  ## Issue 7\n\n**Title:** ...\n\n**Body:**\n\n<body>\n---
pattern = re.compile(
    r"^## Issue (\d+)\s*\n+\*\*Title:\*\*\s*(.+?)\s*\n+\*\*Body:\*\*\s*\n(.*?)(?=^---\s*$)",
    re.DOTALL | re.MULTILINE,
)

found = 0
for match in pattern.finditer(source):
    number, title, body = match.group(1), match.group(2), match.group(3).strip()
    (outdir / f"issue-{number}.body.md").write_text(body + "\n", encoding="utf-8")
    (outdir / f"issue-{number}.title").write_text(title + "\n", encoding="utf-8")
    found += 1

if found != 15:
    sys.exit(f"Expected 15 issue sections, parsed {found}. Refusing to continue.")
PY

title_for() {
    tr -d '\n' < "$BODY_DIR/issue-$1.title"
}

echo "Filing 15 issues against $REPO ..."

gh issue create --repo "$REPO" --title "$(title_for 1)"  --body-file "$BODY_DIR/issue-1.body.md"  --label "$LABELS"
gh issue create --repo "$REPO" --title "$(title_for 2)"  --body-file "$BODY_DIR/issue-2.body.md"  --label "$LABELS"
gh issue create --repo "$REPO" --title "$(title_for 3)"  --body-file "$BODY_DIR/issue-3.body.md"  --label "$LABELS"
gh issue create --repo "$REPO" --title "$(title_for 4)"  --body-file "$BODY_DIR/issue-4.body.md"  --label "$LABELS"
gh issue create --repo "$REPO" --title "$(title_for 5)"  --body-file "$BODY_DIR/issue-5.body.md"  --label "$LABELS"
gh issue create --repo "$REPO" --title "$(title_for 6)"  --body-file "$BODY_DIR/issue-6.body.md"  --label "$LABELS"
gh issue create --repo "$REPO" --title "$(title_for 7)"  --body-file "$BODY_DIR/issue-7.body.md"  --label "$LABELS"
gh issue create --repo "$REPO" --title "$(title_for 8)"  --body-file "$BODY_DIR/issue-8.body.md"  --label "$LABELS"
gh issue create --repo "$REPO" --title "$(title_for 9)"  --body-file "$BODY_DIR/issue-9.body.md"  --label "$LABELS"
gh issue create --repo "$REPO" --title "$(title_for 10)" --body-file "$BODY_DIR/issue-10.body.md" --label "$LABELS"
gh issue create --repo "$REPO" --title "$(title_for 11)" --body-file "$BODY_DIR/issue-11.body.md" --label "$LABELS"
gh issue create --repo "$REPO" --title "$(title_for 12)" --body-file "$BODY_DIR/issue-12.body.md" --label "$LABELS"
gh issue create --repo "$REPO" --title "$(title_for 13)" --body-file "$BODY_DIR/issue-13.body.md" --label "$LABELS"
gh issue create --repo "$REPO" --title "$(title_for 14)" --body-file "$BODY_DIR/issue-14.body.md" --label "$LABELS"
gh issue create --repo "$REPO" --title "$(title_for 15)" --body-file "$BODY_DIR/issue-15.body.md" --label "$LABELS"

echo "Done. Confirm both labels exist on the repo, then review each issue in the browser."
