# Good-first-issue farm — shipped

**Status: done.** All 15 planned issues were filed and 14 are closed. This file is kept
only as the map from the original plan to the issues it became; the drafted issue bodies
that used to live in `issues-to-file.md` are deleted, since every one of them shipped.
Recover them from git history if you ever need the prose.

`CONTRIBUTING.md` exists at the repo root.

## Plan → filed issue

| Plan | Issue | State |
|---|---|---|
| 1 Tool parameter reference table | [#3](https://github.com/salitaba/maven-decoder-mcp/issues/3) | closed |
| 2 `decompiler not found` troubleshooting entry | [#4](https://github.com/salitaba/maven-decoder-mcp/issues/4) | **open — the only one left** |
| 3 Windows setup, `LOCALAPPDATA` cache | [#5](https://github.com/salitaba/maven-decoder-mcp/issues/5) | closed |
| 4 Worked `find_usage_examples` example | [#6](https://github.com/salitaba/maven-decoder-mcp/issues/6) | closed |
| 5 `list_artifacts` sort options | [#7](https://github.com/salitaba/maven-decoder-mcp/issues/7) | closed |
| 6 `get_remote_versions` snapshot filter | [#8](https://github.com/salitaba/maven-decoder-mcp/issues/8) | closed |
| 7 `search_classes` case-insensitive flag | [#9](https://github.com/salitaba/maven-decoder-mcp/issues/9) | closed |
| 8 `compare_versions` moved-to-supertype flag | [#10](https://github.com/salitaba/maven-decoder-mcp/issues/10) | closed |
| 9 `extract_method_info` Javadoc return | [#11](https://github.com/salitaba/maven-decoder-mcp/issues/11) | closed |
| 10 Missing `~/.m2` friendlier error | [#12](https://github.com/salitaba/maven-decoder-mcp/issues/12) | closed |
| 11 Report which endpoint answered | [#13](https://github.com/salitaba/maven-decoder-mcp/issues/13) | closed |
| 12 Corrupt/truncated jar by name | [#14](https://github.com/salitaba/maven-decoder-mcp/issues/14) | closed |
| 13 Test `MAVEN_HTTP_RETRIES` | [#15](https://github.com/salitaba/maven-decoder-mcp/issues/15) | closed |
| 14 Test `MAVEN_MAX_DOWNLOAD_SIZE` | [#16](https://github.com/salitaba/maven-decoder-mcp/issues/16) | closed |
| 15 Test the `origin` field | [#17](https://github.com/salitaba/maven-decoder-mcp/issues/17) | closed |

Filed beyond the plan and also closed: [#21](https://github.com/salitaba/maven-decoder-mcp/issues/21)
(let unexpected `_search_classes` errors propagate) and
[#1](https://github.com/salitaba/maven-decoder-mcp/issues/1) (`MAVEN_HOME` env).

The `pytest-cov` gap that was listed as "issue 0" was fixed directly in `pyproject.toml`
and never filed.

## What this cost

The plan's premise was that an empty tracker converts no contributors, so the issues had
to exist *before* traffic. They now do — but the traffic never came, because
`distribution-sweep.md` is still mostly unfiled. The tracker got drained by the maintainer
rather than by strangers, which is the opposite of the intent. If the sweep ever lands,
the farm will need restocking, and the lesson is to file thin and hold rather than to
draft 1010 lines of issue bodies up front.
