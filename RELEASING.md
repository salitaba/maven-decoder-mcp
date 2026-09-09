# Releasing maven-decoder-mcp

How a release goes out, in the order it happens. Follow it; CI enforces it.

## Versioning

- Tags look like `vX.Y.Z` (`v1.3.0`). No `latest` tags, no suffixes.
- The **tag is the single source of truth**. CI rewrites
  `pyproject.toml`, `package.json`, and both `__init__.py` files from the
  tag at build time, so the repo copies only need to be sane, not exact.
- **`server.json` is the exception.** CI does not touch it. Its `version`
  and both `packages[].version` fields must be edited by hand to the
  version being released, in the release commit, or the MCP Server Registry
  will point at the wrong npm and PyPI versions.
- Pick the next version by SemVer: bug fixes bump patch, new tools or
  features bump minor, incompatible changes bump major.

## Checklist

```bash
# 0. Start clean on main
git checkout main && git pull

# 1. Run the full gate
MAVEN_OFFLINE=true .venv/bin/python -m pytest tests/ -q --no-cov
.venv/bin/python run_tests.py
.venv/bin/python test_startup.py
.venv/bin/python -m build && .venv/bin/python -m twine check dist/*

# 2. Bump server.json by hand (CI will not do it): 3 occurrences
python3 - <<'PY'
import json, pathlib, sys
v = "X.Y.Z"
p = pathlib.Path("server.json"); d = json.loads(p.read_text())
d["version"] = v
for pkg in d["packages"]:
    pkg["version"] = v
p.write_text(json.dumps(d, indent=2) + "\n")
print("server.json =>", v)
PY

# 3. Draft the notes (edit the result before committing)
python3 scripts/generate_release_notes.py --tag vX.Y.Z
$EDITOR RELEASE_NOTES.md

# 4. Commit, tag, push
git add -A && git commit -m "release: vX.Y.Z"
git tag -a vX.Y.Z -m "Maven Decoder MCP Server vX.Y.Z"
git push origin main && git push origin vX.Y.Z
```

The tag push triggers the `Release` workflow:

1. `test` — pytest on 3.10 / 3.11 / 3.12, offline, plus startup checks.
2. `build` — rebuilds with the tag version, publishes to **PyPI**,
   publishes to **npm** (trusted publishing), creates the **GitHub release**
   with `RELEASE_NOTES.md` as the body.
3. `docker` — builds and pushes `ali79taba/maven-decoder-mcp` with the
   `X.Y.Z`, `X.Y`, `X`, and `latest` tags (plus SBOM and provenance).

## After the run

```bash
# Verify every target before announcing
pip index versions maven-decoder-mcp        # or: pip install maven-decoder-mcp==X.Y.Z
npm view maven-decoder-mcp dist-tags.latest
docker buildx imagetools inspect ali79taba/maven-decoder-mcp:X.Y.Z
gh release view vX.Y.Z
```

## MCP Server Registry

Only after PyPI and npm both show the new version — the registry validates
ownership by reading the published artifacts, not the git repo. It checks
`mcpName` in the npm `package.json` and the `<!-- mcp-name: ... -->` comment
in the PyPI README. Both are committed in this repo; confirm they survived
into the published version before publishing.

```bash
npm view maven-decoder-mcp@X.Y.Z mcpName          # must print the namespace
mcp-publisher login github                        # interactive OAuth as salitaba
mcp-publisher publish                             # reads ./server.json
```

If `server.json` still names an older version, publishing succeeds but points
users at the wrong package version. Fix step 2 and republish.

## If it fails

- **Before any publish**: fix, delete the tag locally and remotely
  (`git tag -d vX.Y.Z && git push origin :vX.Y.Z`), and start over.
- **After a partial publish**: do NOT reuse the version. Bump the patch
  version and release again; twine has `--skip-existing`, but npm refuses
  republished versions outright.
- Missing secrets surface as explicit CI errors now (`PYPI_API_TOKEN`,
  `DOCKER_USERNAME` / `DOCKER_PASSWORD`). Add them under
  Settings → Secrets and variables → Actions.

## What NOT to use

- `scripts/release.py` and `simple_release.sh` are legacy manual helpers.
  They hardcode v1.0.0 and push to the wrong image name; keep them for
  reference but never run them for a real release.
