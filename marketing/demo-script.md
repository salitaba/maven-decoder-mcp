# Demo asset — recording script

One asset, reused in README, every directory listing, the enterprise post, and social.

**Status: built.** `docs/demo.gif` — 87 KB, 30.3 s, 880×246, 11 frames.

```bash
python3 -m venv /tmp/rvenv && /tmp/rvenv/bin/pip install pillow
/tmp/rvenv/bin/python marketing/render_demo.py     # rebuild the GIF
.venv/bin/python marketing/capture_demo.py         # re-verify every number in it
```

Every figure and signature on screen came from `capture_demo.py` running this project's
own tools against real jars. Nothing is illustrative. If you edit `render_demo.py`, run
`capture_demo.py` first and match it — a demo that overstates the tool is worse than no
demo, because the first person to check becomes the loudest voice in the thread.

Target was **≤40 s, ≤5 MB** so it inlines on GitHub and Reddit. Current build is well under.

## Verified numbers (org.jsoup:jsoup 1.17.2 → 1.23.2)

| Metric | Value |
|---|---|
| `breaking_changes` | 45 |
| `members_removed` | 31 |
| `members_added` | 150 |
| `classes_with_api_changes` | 47 of 115 compared |
| `compatible` | false |

The removed members shown include `Document.outerHtml()` and
`Element.nextElementSibling()`, which almost certainly moved to a supertype rather than
disappearing. That is the as-declared caveat, and frame 7 of the GIF states it outright
instead of hiding it. Keep it that way — volunteering the limitation is what makes the
other 45 numbers believable.

## Rules

- No intro card, no logo, no music. Dev audience bounces on branding.
- Terminal + agent pane only. Real output, no mockups.
- Text must be legible at GitHub's ~880 px README width. Font size 16+, dark theme.
- Do not speed up past ~1.5x. Fake-fast output reads as fake.

## Shot 1 — the breaking-change diff (0:00–0:30)

The core script. Chosen because the answer is externally verifiable against the jsoup
changelog, and the stakes are real (upgrade breaks prod).

Prompt, identical in both halves:

```
I'm upgrading org.jsoup:jsoup from 1.17.2 to 1.23.2. What breaks?
```

- **A — MCP off** (`MAVEN_OFFLINE=true` and server detached, or a clean client profile):
  agent answers from memory. Expect plausible prose, no removed-member list, no source read.
- **B — MCP on**: `compare_versions` diffs public and protected members of every class the
  two versions share, and reports removals separately from additions.

On screen, highlight the removed-members count. That number is the whole pitch.

Caveat to keep honest if anyone asks: members are compared **as declared**, so one that
moved to a supertype is reported as removed even though it may still be callable. This is
already stated in the README; do not let the demo imply otherwise.

## Shot 2 — no sources jar (0:30–0:40)

The sharpest technical wedge, and the setup for the enterprise post.

```
The sources jar is missing for this artifact. Show me its fields and methods.
```

`extract_class_info` falls back to `javap` internally and returns parsed fields, methods,
and bytecode version. No IDE, no manual unzip, no sources jar required.

## Production

The GIF is generated, not screen-recorded — `marketing/render_demo.py` draws typed frames
with Pillow. This is deliberate: frames are diffable, rebuildable on any machine, and
free of the cursor jitter and window chrome that make screen captures look amateurish.

To edit: change the `FRAMES` list, rerun the renderer, check the reported size.

If you would rather capture a live terminal session, `asciinema rec` + `agg` produces a
comparable result and neither is installed here.

## Wiring it up

1. `docs/demo.gif` — done, embedded at the top of `README.md`
2. Reuse the same GIF in the enterprise post and every directory submission that renders images

## Reusable copy line

> Your agent guesses at library APIs it has never read. This makes it read them.
