# Maven Decoder MCP Server v1.3.1

## What's Changed

### Fixes
- Install from PyPI without git URL: `bin/maven-decoder-mcp.js`, `install.sh`, and `scripts/install.js` now run plain `pip install maven-decoder-mcp` (SDK comes from PyPI)
- Fix Docker image name to `ali79taba/maven-decoder-mcp` in `install.sh`
- `simple_release.sh`: use `python -m build` and generic `maven-decoder-mcp-*.tgz` instead of hardcoded v1.0.0 paths
- `DISTRIBUTION.md`: generic `<version>` placeholders instead of stale 1.0.0 filenames

### Maintenance
- Release workflow syncs all three version copies from tag (`pyproject.toml`, `package.json`, both `__init__.py`)
- Release notes generated from git history via `scripts/generate_release_notes.py`; stale static template removed so notes describe this release
- Add `RELEASING.md` checklist, rewrite `RELEASE_GUIDE.md` around tag-as-source-of-truth, add `skills/project-release/`
- Docker publish gains SBOM + provenance attestations and explicit errors for missing `PYPI_API_TOKEN` / `DOCKER_*` secrets
- Add `tests/test_release_notes.py` pinning generator, guard, and version-sync behavior

## Installation

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
docker run --rm -it \
  -v ~/.m2:/home/mcpuser/.m2 \
  ali79taba/maven-decoder-mcp:1.3.1
```


**Full Changelog**: https://github.com/salitaba/maven-decoder-mcp/compare/v1.3.0...v1.3.1
