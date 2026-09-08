# 🚀 How to Release Maven Decoder MCP Server

**The short version is in [RELEASING.md](RELEASING.md) — follow that checklist.
This page explains the moving parts underneath it.**

Releases are fully automated: push a tag like `v1.3.0` and GitHub Actions
builds and publishes to PyPI, npm, Docker Hub, and GitHub Releases.

## How the tag becomes the release

The tag is the single source of truth. Both the `test` and `build` jobs in
`.github/workflows/release.yml` rewrite the version files from
`${GITHUB_REF_NAME#v}`:

- `pyproject.toml` (`version = "..."`) — what PyPI publishes
- `package.json` (`"version": "..."`) — what npm publishes
- `maven_decoder_mcp/__init__.py` and root `__init__.py` (`__version__`) —
  fallback for source checkouts without installed metadata

So the repo copies only need to be sane, not exact. What the server reports
to MCP clients (`server_version`) is resolved at runtime from the installed
distribution metadata.

## What the workflow does

1. **`test`** — full pytest suite on Python 3.10 / 3.11 / 3.12 with
   `MAVEN_OFFLINE=true`, plus `test_startup.py` and `run_tests.py`.
2. **`build`** — rebuilds with the tag version, uploads to PyPI with twine,
   publishes to npm via OIDC trusted publishing (no token secret), and
   creates the GitHub release with `RELEASE_NOTES.md` as the body plus the
   auto-generated changelog.
3. **`docker`** — builds `linux/amd64,linux/arm64` and pushes
   `ali79taba/maven-decoder-mcp` with the `X.Y.Z`, `X.Y`, `X`, and `latest`
   tags, plus SBOM and provenance attestations.

## Release notes

Notes are **drafted before tagging**, committed, and used as-is:

```bash
python3 scripts/generate_release_notes.py --tag vX.Y.Z
$EDITOR RELEASE_NOTES.md   # always review before committing
```

The generator derives sections from conventional-commit subjects since the
previous tag (`feat:` → Features, `fix:`/`perf:` → Fixes, everything else →
Maintenance) and injects the install snippet with the right version.

If the file is missing at build time, CI regenerates it from git history
rather than shipping a static template — a fixed template is how every
release ended up advertising "pagination and summarization" regardless of
what actually changed.

## Secrets

Settings → Secrets and variables → Actions:

- `PYPI_API_TOKEN` — PyPI account token (`pypi-…`). Missing token fails the
  build job with an explicit error, it no longer leaks secret *presence*
  checks into logs.
- `DOCKER_USERNAME` / `DOCKER_PASSWORD` — Docker Hub. Same explicit failure
  when unset.
- npm needs **no secret**: trusted publishing via OIDC. The trusted
  publisher entry on npmjs.com must point at this repo + workflow.
- GitHub release upload uses the built-in `GITHUB_TOKEN`.

## If it fails

- **Before any publish**: fix, delete the tag (`git tag -d vX.Y.Z &&
  git push origin :vX.Y.Z`), start over.
- **After a partial publish**: never reuse the version. Bump patch and
  release again — npm refuses republished versions outright.

## Legacy helpers (do not use for real releases)

- `scripts/release.py` — hardcodes v1.0.0, calls `python setup.py` (no
  `setup.py` exists), pushes the wrong Docker image name. Reference only.
- `simple_release.sh` — interactive walkthrough from the first release,
  including an unimplemented "full release" option. Reference only.

