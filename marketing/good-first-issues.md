# Good-first-issue farm

File these **before** traffic arrives, not after. A visitor who wants to contribute
decides in about ninety seconds; an empty issue tracker converts nobody.

Target: 15 open issues labeled `good first issue`, each scoped small enough that a
stranger can finish it in one sitting without asking a design question.

## Rules for each issue

- Name the exact file and function to change
- State the acceptance test, or the test file to add to
- No open design questions — if it needs a decision, decide it in the issue body first
- Add `help wanted` alongside `good first issue`; GitHub surfaces both

## Candidate issues

Verify each against the current code before filing — several may already be done.

**Docs and onboarding**
1. Document each MCP tool's full parameter set in one reference table
2. Add a troubleshooting section for "decompiler not found" (`setup_decompilers.sh` paths)
3. Windows setup walkthrough — `MAVEN_REPOSITORY` with a drive-letter path is already
   supported and undocumented outside a single example
4. Add a worked example for `find_usage_examples`, currently the thinnest-documented tool

**Small features**
5. `list_artifacts`: sort options (name, size, last modified)
6. `get_remote_versions`: filter out snapshot versions via a flag
7. `search_classes`: case-insensitive matching flag
8. `compare_versions`: opt-in flag to treat a member moved to a supertype as non-breaking
   (currently reported as removed — the documented limitation)
9. `extract_method_info`: return surrounding Javadoc when a sources jar is present

**Robustness**
10. Friendlier error when `~/.m2/repository` does not exist at all
11. Retry/backoff surface: log which search endpoint was used on fallback
12. Handle a corrupt or truncated jar without a stack trace

**Tests**
13. Test coverage for `MAVEN_HTTP_TIMEOUT` and `MAVEN_HTTP_RETRIES` handling
14. Test `MAVEN_MAX_DOWNLOAD_SIZE` enforcement
15. Test the `origin` field is present and correct on every tool response

## CONTRIBUTING.md

Does not exist yet. Write one before filing the issues. It needs exactly four things:

1. Five-minute setup, copy-pasteable:
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -e ".[dev]"
   ./setup_decompilers.sh
   ```
2. How to run tests offline (this is the important one — tests must not need network):
   ```bash
   MAVEN_OFFLINE=true .venv/bin/python -m pytest tests/ -q --no-cov
   ```
3. Where the code lives — the module list already in the README's Architecture section
4. What gets a PR merged: a test, and no new network calls in the test suite
