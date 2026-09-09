# Maven Decoder MCP Server v1.3.2

A packaging and documentation release. No runtime behavior changes — the
server's tools and their outputs are identical to v1.3.1.

## What's Changed

### Fixes
- A clean `pip install -e ".[dev]"` could not run the test suite. `pytest.ini`
  passes `--cov`, but `pytest-cov` was missing from the `dev` extra, so
  `pytest` failed on a fresh checkout. It is now declared.

### Packaging
- Published to the [MCP Server Registry](https://github.com/modelcontextprotocol/registry).
  Adds a root `server.json`, `mcpName` in `package.json`, and an `mcp-name`
  marker in `README.md` so the registry can verify namespace ownership from
  the published npm and PyPI artifacts.

### Documentation
- Rewritten README intro with a demo GIF showing a real `compare_versions`
  run against `org.jsoup:jsoup` 1.17.2 → 1.23.2.
- Added `CONTRIBUTING.md`.
- `RELEASING.md` now documents that `server.json` is not rewritten from the
  git tag by CI and must be bumped by hand.

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
  ali79taba/maven-decoder-mcp:1.3.2
```


**Full Changelog**: https://github.com/salitaba/maven-decoder-mcp/compare/v1.3.1...v1.3.2
