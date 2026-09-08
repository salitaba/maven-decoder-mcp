---
name: project-release
description: Cut a release of this project (maven-decoder-mcp): draft notes, verify the gate, tag, push, watch CI, and confirm packages on PyPI, npm, Docker Hub, and GitHub. Use when the user says "release", "cut a release", "ship it", "tag a version", or asks about the release process, release notes, or publishing.
---

# Project Release

Ship a new version of maven-decoder-mcp end to end. The tag is the single
source of truth — CI rewrites every version file from it — so the release is
mostly ceremony plus verification.

## Rules

- Never reuse a version number. If a publish partially succeeded, bump patch
  and release again (npm refuses republished versions).
- Never retag or force-push a tag after any artifact published. Fix forward.
- Release flow is documented in `RELEASING.md`; the authoritative process
  details live in `RELEASE_GUIDE.md` and `.github/workflows/release.yml`.
- `scripts/release.py` and `simple_release.sh` are legacy and must not be
  used for real releases — they hardcode v1.0.0 and push a wrong image name.

## Workflow

### 1. Decide the version

Inspect commits since the last tag (`git log <last-tag>..HEAD --oneline`).
SemVer: patch for fixes, minor for new tools/features, major for breaking
changes. Confirm with the user when ambiguous — the tag cannot be undone
once artifacts publish.

### 2. Run the gate locally

```bash
MAVEN_OFFLINE=true .venv/bin/python -m pytest tests/ -q --no-cov
.venv/bin/python run_tests.py
.venv/bin/python test_startup.py
.venv/bin/python -m build && .venv/bin/python -m twine check dist/*
```

Do not proceed on failure. All four must pass.

### 3. Draft release notes

```bash
python3 scripts/generate_release_notes.py --tag vX.Y.Z
```

Read the generated `RELEASE_NOTES.md`, fix anything the commit subjects got
wrong (the generator groups by `feat:`/`fix:` prefixes), and keep the focus
on what a user upgrading needs to know: new tools, behavior changes, breaks.
Commit the notes on main before tagging — CI uses the committed file as the
release body and regenerates from history only if it does not cover the tag.

### 4. Commit, tag, push

```bash
git add -A && git commit -m "release: vX.Y.Z"
git tag -a vX.Y.Z -m "Maven Decoder MCP Server vX.Y.Z"
git push origin main && git push origin vX.Y.Z
```

### 5. Watch CI to green

The `Release` workflow runs `test` (3.10/3.11/3.12) → `build`
(PyPI + npm + GitHub release) → `docker` (multi-arch push). Watch all three:

```bash
gh run watch <run-id> --exit-status --interval 20
```

The docker job takes ~8 minutes on arm64; that is normal, not stuck.

### 6. Verify every target

Publishing succeeded is not the same as installable. Check all four:

```bash
pip index versions maven-decoder-mcp
npm view maven-decoder-mcp dist-tags.latest
docker buildx imagetools inspect ali79taba/maven-decoder-mcp:X.Y.Z
gh release view vX.Y.Z
```

Stronger: install the PyPI artifact in a fresh venv and import the server,
confirming tool count and version. Only then report the release as done.

## Failure handling

- CI red before any publish: fix on main, delete the tag locally and
  remotely (`git tag -d vX.Y.Z && git push origin :vX.Y.Z`), restart.
- Partial publish: bump patch, new tag, new release. `twine
  --skip-existing` tolerates re-upload; npm does not.
- Missing-secret errors (`PYPI_API_TOKEN`, `DOCKER_USERNAME` /
  `DOCKER_PASSWORD`) point at repo Settings → Secrets and variables →
  Actions, not at code.
