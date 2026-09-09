# Good-first-issue farm

File these **before** traffic arrives, not after. A visitor who wants to contribute
decides in about ninety seconds; an empty issue tracker converts nobody.

Target: 15 open issues labeled `good first issue`, each scoped small enough that a
stranger can finish it in one sitting without asking a design question.

`CONTRIBUTING.md` now exists at the repo root. Every issue below assumes the reader has
followed its setup section, so no issue needs to repeat install instructions — link to it
instead.

## Rules for each issue

- Name the exact file and function to change
- State the acceptance test, or the test file to add to
- No open design questions — if it needs a decision, decide it in the issue body first
- Add `help wanted` alongside `good first issue`; GitHub surfaces both

## Verified anchors

Checked against the working tree on 2026-09-09. Re-check line numbers before filing;
the function names are the stable reference.

| Symbol | Location |
|---|---|
| `_list_artifacts` | `maven_decoder_mcp/maven_decoder_server.py:689` |
| `_path_origin` | `maven_decoder_mcp/maven_decoder_server.py:915` |
| `_search_classes` | `maven_decoder_mcp/maven_decoder_server.py:1092` |
| `_compare_versions` | `maven_decoder_mcp/maven_decoder_server.py:1337` |
| `_find_usage_examples` | `maven_decoder_mcp/maven_decoder_server.py:1513` |
| `_get_remote_versions` | `maven_decoder_mcp/maven_decoder_server.py:1766` |
| `_extract_method_info` | `maven_decoder_mcp/maven_decoder_server.py:1856` |
| `Config.http_retries` | `maven_decoder_mcp/config.py:151` |
| `Config.max_download_bytes` | `maven_decoder_mcp/config.py:220` |
| `Config.resolve_download_cache` | `maven_decoder_mcp/config.py:182` |
| `MavenCentralClient._verify_checksum` | `maven_decoder_mcp/maven_central.py:480` |

Tool declarations live in the `name=` list starting around
`maven_decoder_server.py:344`; each has an `async def _handler` further down.

## Issue 0 — file this one first

**`pytest-cov` is missing from the `dev` extra.** `pytest.ini` sets `--cov=maven_decoder_mcp`
in `addopts`, but `pyproject.toml`'s `[project.optional-dependencies] dev` list omits
`pytest-cov` (it is in `requirements.txt` and installed explicitly in both CI workflows).
So `pip install -e ".[dev]" && pytest` fails for a new contributor on the very first
command they run.

Fix: add `"pytest-cov>=4.0.0"` to the `dev` list in `pyproject.toml`, then drop the
workaround note from `CONTRIBUTING.md`.

This is the highest-value issue on the list because it breaks the onboarding path
described in the file that points people at these issues. File it first, or just fix it
yourself before publishing any of the others.

## Candidate issues

Verified against the current code — the notes below say what was actually found.

**Docs and onboarding**

1. Document each MCP tool's full parameter set in one reference table. Source of truth is
   the `name=`/`inputSchema` block from `maven_decoder_server.py:344` onward.
2. Add a troubleshooting section for "decompiler not found" (`setup_decompilers.sh` paths,
   and `MAVEN_DECODER_DECOMPILER_DIR`).
3. Windows setup walkthrough — `MAVEN_REPOSITORY` with a drive-letter path is supported
   and undocumented outside a single example. Note that the cache falls back to
   `LOCALAPPDATA` on Windows (`config.py:193`), which is documented nowhere.
4. Add a worked example for `find_usage_examples`, currently the thinnest-documented tool.

**Small features**

5. `_list_artifacts`: sort options (name, size, last modified).
6. `_get_remote_versions`: filter out snapshot versions via a flag.
7. `_search_classes`: case-insensitive matching flag.
8. `_compare_versions`: opt-in flag to treat a member moved to a supertype as non-breaking.
   Currently reported as removed — this is the documented as-declared limitation, and it
   is the caveat quoted in the README, so the flag must default to today's behavior.
9. `_extract_method_info`: return surrounding Javadoc when a sources jar is present.

**Robustness**

10. Friendlier error when `~/.m2/repository` does not exist at all. `config.py` has no
    "missing repository" message today, so a fresh machine gets an empty result rather
    than an explanation.
11. Retry/backoff surface: log which search endpoint was used on fallback.
    `MavenCentralClient` reads `Config.http_retries()` at `maven_central.py:59` but never
    reports which attempt or endpoint succeeded.
12. Handle a corrupt or truncated jar without a stack trace. **Confirmed missing** —
    `zipfile.BadZipFile` is not caught anywhere in `maven_decoder_mcp/`. A truncated jar
    in `~/.m2` currently raises through to the agent.

**Tests**

13. Test coverage for `MAVEN_HTTP_TIMEOUT` and `MAVEN_HTTP_RETRIES` handling.
    `tests/test_maven_central.py:412` covers a non-numeric `MAVEN_HTTP_TIMEOUT` only;
    `MAVEN_HTTP_RETRIES` has no test at all. Scope this to `Config.http_retries`.
14. Test `MAVEN_MAX_DOWNLOAD_SIZE` enforcement. No test references it today; the size
    ceiling is enforced at `maven_central.py:446` and `:465`.
15. Test that the `origin` field is present and correct on every tool response.
    `tests/test_maven_central.py:1094` asserts `_path_origin` returns `remote-cache` in
    isolation, but no test checks the field is actually attached to tool output
    (`maven_decoder_server.py:1207`, `:1227`, `:1848`).

Issues 12, 13, 14, and 15 are the strongest of the set: each is a genuine gap confirmed
by reading the code, each is one file, and each has an obvious acceptance test.

## CONTRIBUTING.md

Written — see `CONTRIBUTING.md` at the repo root. It covers setup, the offline test
command (`MAVEN_OFFLINE=true pytest tests/ -q --no-cov`, verified: 135 pass, no network),
a module map, and the five merge criteria. The `~/.m2`-stays-untouched rule is stated as
non-negotiable there, which issues 5-12 all depend on.
