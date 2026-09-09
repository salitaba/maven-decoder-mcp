# Contributing

Thanks for looking. This project reads Maven artifacts and hands the real source to an
AI agent, so most contributions are small, testable, and local — a good shape for a first
pull request.

Issues labeled [`good first issue`](https://github.com/salitaba/maven-decoder-mcp/labels/good%20first%20issue)
name the exact file and function to change and the test to add. Start there.

## Setup, five minutes

```bash
git clone https://github.com/salitaba/maven-decoder-mcp.git
cd maven-decoder-mcp
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
./setup_decompilers.sh
```

Python 3.10 or newer, and a JDK on `PATH` — `javap` is what makes artifacts without a
sources jar readable.

`setup_decompilers.sh` downloads CFR and Procyon. It is optional; without them you get
`javap` output instead of decompiled source, and most tests still pass.

## Running tests

Tests must never touch the network. Run them the way CI does:

```bash
MAVEN_OFFLINE=true .venv/bin/python -m pytest tests/ -q --no-cov
```

135 tests, about 35 seconds. While iterating, run only what you touched:

```bash
MAVEN_OFFLINE=true .venv/bin/python -m pytest tests/test_maven_central.py -q --no-cov
```

Drop `--no-cov` when you want the coverage report.

## Where the code lives

| Path | What it does |
|---|---|
| `maven_decoder_mcp/maven_decoder_server.py` | MCP tool definitions and their handlers. Every tool is declared here (`name=` in the tool list) with a `_handler` below it. |
| `maven_decoder_mcp/maven_central.py` | Remote search, download, checksum verification, retry. |
| `maven_decoder_mcp/config.py` | Every environment variable and its default. Read this before adding a setting. |
| `tests/` | pytest. `conftest.py` holds shared fixtures and environment isolation. |
| `skills/maven-code-search/` | The agent skill shipped via `npx skills add`. |

Adding a tool means two edits in `maven_decoder_server.py`: the declaration in the tool
list, and the `async def _your_tool` handler.

## What gets a PR merged

1. **A test.** Any behavior change needs one. Bug fixes need a test that fails before
   your change.
2. **No new network calls in the test suite.** Mock the HTTP layer; see the existing
   `patch` usage in `tests/test_maven_central.py`. A test that only passes with internet
   access will be asked for changes.
3. **`~/.m2` stays untouched.** Downloads belong in the separate cache resolved by
   `MavenConfig.resolve_download_cache()`. Interfering with a user's local repository
   would break their Maven and Gradle builds, so this one is not negotiable.
4. **New settings are documented.** If you add an environment variable, it goes in
   `config.py` with a docstring and in the README's configuration table.
5. **Errors stay legible.** Return a clear message rather than letting a stack trace
   reach the agent — the agent is the one reading it.

Formatting is `black` and `isort`, both in the `dev` extra. Run them before pushing;
there is no enforcing hook yet.

## Opening the PR

One change per PR. Describe what broke or what was missing, not just what you did — the
reasoning is what gets reviewed. If a change needs a design decision, open an issue first
so you do not write code that gets rejected on direction.

Questions are welcome in an issue. A question is cheaper than a rewrite.
