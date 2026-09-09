# Issues to file

Ready-to-file bodies for the 15 candidates in `good-first-issues.md`. Issue 0 is skipped
(already fixed). Every body below was checked against the working tree before drafting.

Labels for all: `good first issue`, `help wanted`.

Line numbers are **hints only** — the function name is the stable reference.

Test command referenced throughout:

```bash
MAVEN_OFFLINE=true pytest tests/ -q
```

(`CONTRIBUTING.md` uses `MAVEN_OFFLINE=true .venv/bin/python -m pytest tests/ -q --no-cov`;
add `--no-cov` if you have not installed the `dev` extra.)

Anchor re-verification notes are in `## Anchor drift` at the bottom.

---

## Issue 1

**Title:** Document every MCP tool's parameters in one reference table

**Body:**

### What's wrong / where

`README.md` has two tool tables (`### Local Analysis` around line 164 and
`### Online (Maven Central)` around line 183). Both list only a tool name and a one-line
description. Neither lists parameters, types, or defaults.

The real parameter set lives in `maven_decoder_mcp/maven_decoder_server.py`, in the
`tools = [ ... ]` list inside `_setup_handlers` — the first entry is
`Tool(name="list_artifacts", ...)` around line 344, and there are 17 `Tool(...)` entries
through `name="download_artifact"` around line 617. Each carries an `inputSchema` with the
authoritative `properties`, `default`, and `required` values.

A user today has to read Python source to learn that `list_artifacts` accepts
`page` and `items_per_page`, or that `download_artifact` accepts `include_javadoc`.

### What to change

Add a `### Tool parameters` section to `README.md`, after the existing two tool tables.
One row per parameter:

| Tool | Parameter | Type | Default | Description |

Transcribe from each `inputSchema` in `maven_decoder_server.py`. Do not invent
descriptions — copy the `description` string already in the schema. Mark required
parameters (those in the schema's `required` list, or those without a `default`) with a
`*` and add one footnote explaining the marker.

### How to verify

Docs-only change; no test needed. Before opening the PR, confirm every `Tool(name=...)`
entry in `maven_decoder_server.py` has a matching block in your table:

```bash
grep -n 'name="' maven_decoder_mcp/maven_decoder_server.py | head -20
```

Then run the suite once to confirm nothing else broke:
`MAVEN_OFFLINE=true pytest tests/ -q`

### Decisions already made

- One combined table for all 17 tools, sorted in the same order as the `tools` list — not
  one table per tool, and not alphabetical.
- Goes in `README.md`, not a new `docs/` page.
- Copy schema `description` strings verbatim rather than rewriting them, so the table stays
  diffable against source.

Setup: see [`CONTRIBUTING.md`](../CONTRIBUTING.md).

---

## Issue 2

**Title:** Add a "decompiler not found" troubleshooting entry naming MAVEN_DECODER_DECOMPILER_DIR

**Body:**

### What's wrong / where

`README.md` has a `## 🔍 Troubleshooting` section around line 393 with a
**Decompilation fails** entry, but it only tells you to run `maven-decoder-setup status`
and `maven-decoder-setup decompilers`. It never mentions:

- `setup_decompilers.sh` (the script referenced at `README.md:129` and `CONTRIBUTING.md:17`)
- `MAVEN_DECODER_DECOMPILER_DIR`, which is documented once as a bare bullet at
  `README.md:385` and is the actual escape hatch when the jars live somewhere non-default.

Someone who put `cfr.jar` in a custom directory has no way to find that env var from the
troubleshooting section.

### What to change

In `README.md`, extend the **Decompilation fails** entry under `## 🔍 Troubleshooting`:

1. Note that `./setup_decompilers.sh` downloads CFR and Procyon, and say where it puts them
   (read the script to get the exact path — do not guess it).
2. Document `MAVEN_DECODER_DECOMPILER_DIR` as the override for a custom location, with a
   one-line export example.
3. Keep the existing note that without CFR/Procyon the server falls back to `javap`.

Discovery logic lives in `maven_decoder_mcp/decompiler_paths.py`; read it to confirm the
lookup order before writing the prose.

### How to verify

Docs-only. Confirm the env var name is spelled exactly as in the code:

```bash
grep -rn "MAVEN_DECODER_DECOMPILER_DIR" maven_decoder_mcp/
```

Then: `MAVEN_OFFLINE=true pytest tests/ -q`

### Decisions already made

- Extend the existing **Decompilation fails** entry; do not create a new top-level section.
- Do not repeat install steps — link to `CONTRIBUTING.md`.

Setup: see [`CONTRIBUTING.md`](../CONTRIBUTING.md).

---

## Issue 3

**Title:** Document Windows setup, including the LOCALAPPDATA cache fallback

**Body:**

### What's wrong / where

Windows appears in `README.md` exactly once, as an inline comment at line 126
(`source .venv/bin/activate  # On Windows: .venv\Scripts\activate`). Two Windows-relevant
behaviors are documented nowhere:

1. **Cache location.** `Config.resolve_download_cache` in `maven_decoder_mcp/config.py`
   (around line 182) checks `MAVEN_DECODER_CACHE_DIR` first, then loops over
   `("XDG_CACHE_HOME", "LOCALAPPDATA")` at line 193, and only then falls back to
   `~/.cache/maven-decoder-mcp/repository`. On Windows the cache therefore lands under
   `%LOCALAPPDATA%\maven-decoder-mcp\repository` — stated in no doc.
2. **Drive-letter `MAVEN_REPOSITORY` paths** work, but only appear in a passing example.

### What to change

Add a `### Windows` subsection to `README.md` under `## 📦 Installation`, covering:

- Activating the venv with `.venv\Scripts\activate`
- Setting `MAVEN_REPOSITORY` to a drive-letter path
- The resolved cache path, derived from `Config.resolve_download_cache` — state the
  `MAVEN_DECODER_CACHE_DIR` → `XDG_CACHE_HOME` → `LOCALAPPDATA` → `~/.cache` order exactly
  as the code implements it
- That the download cache is deliberately separate from the real local repository (the
  docstring on `resolve_download_cache` says why)

### How to verify

Docs-only; a Windows machine is **not** required — read
`maven_decoder_mcp/config.py::resolve_download_cache` and describe what it does.

`tests/test_maven_repository_resolution.py` already exercises repository resolution; run
the suite to confirm you changed no behavior:
`MAVEN_OFFLINE=true pytest tests/ -q`

### Decisions already made

- Docs only. Do **not** change `resolve_download_cache` — the `XDG_CACHE_HOME` before
  `LOCALAPPDATA` ordering is intentional and stays.
- New `### Windows` subsection under `## 📦 Installation`, not a separate file.

Setup: see [`CONTRIBUTING.md`](../CONTRIBUTING.md).

---

## Issue 4

**Title:** Add a worked example for find_usage_examples to the README

**Body:**

### What's wrong / where

`find_usage_examples` is the thinnest-documented tool in `README.md`. It has:

- one table row at line 176 (`Find classes that reference a given class or method`)
- one env-var bullet at line 383 (`MCP_USAGE_SCAN_LIMIT`)

and no entry in the `## 💡 Usage Examples` section (around line 191), which does have
worked examples for dependencies, decompiling, conflicts and API exploring.

The implementation is `_find_usage_examples` in
`maven_decoder_mcp/maven_decoder_server.py` (around line 1513). Its signature is
`(self, class_name, method_name=None, search_tests=True, limit=50, page=1, items_per_page=20)`
and its docstring explains the constant-pool scan. Results are sorted test-jars-first
(`matches.sort(...)` around line 1610) — behavior a user cannot discover from the docs.

### What to change

Add an `### Finding Real Callers` subsection to `## 💡 Usage Examples` in `README.md`,
matching the style of the neighboring examples (a natural-language prompt plus a note on
what comes back). Cover:

- narrowing with `method_name`
- that test jars are ranked first, and `search_tests` controls whether they are included
- that the scan reads the constant pool, so it finds real callers rather than name matches
- that `MCP_USAGE_SCAN_LIMIT` (default 200000) caps how many classes are scanned

`skills/maven-code-search/SKILL.md:60` already describes this tool well — reuse that phrasing.

### How to verify

Docs-only. `tests/test_maven_central.py` has a `TestUsageExamples` class (around line 879);
read it to confirm the behavior you describe matches what is asserted. Then:
`MAVEN_OFFLINE=true pytest tests/ -q`

### Decisions already made

- Prose example in the existing `## 💡 Usage Examples` section — no new page, no code change.
- Describe `search_tests` and `MCP_USAGE_SCAN_LIMIT` in the same example rather than
  scattering them.

Setup: see [`CONTRIBUTING.md`](../CONTRIBUTING.md).

---

## Issue 5

**Title:** Add a sort_by option to list_artifacts

**Body:**

### What's wrong / where

`_list_artifacts` in `maven_decoder_mcp/maven_decoder_server.py` (around line 689) returns
artifacts in raw filesystem-iteration order — whatever `Path.iterdir()` yields. Its result
dict (around line 748) is:

```python
result = {
    "total_found": count,
    "artifacts": artifacts[:limit]
}
```

and each entry has `group_id`, `artifact_id`, `version`, `jar_files`, `path`. There is no
sort anywhere in the function, so paginated output is effectively arbitrary and unstable
across machines.

### What to change

Add a `sort_by: str = "name"` parameter to `_list_artifacts`, and the matching
`"sort_by"` property to the `Tool(name="list_artifacts", ...)` `inputSchema` around
`maven_decoder_server.py:344`.

Accepted values and their meaning:

- `"name"` (default) — sort by `(group_id, artifact_id, version)` ascending
- `"size"` — sort by total bytes of the jars in the version directory, descending
- `"modified"` — sort by the newest jar's mtime in the version directory, descending

Sort the accumulated `artifacts` list **after** the collection loop and **before**
the `artifacts[:limit]` slice, so the slice reflects the sort.

For `"size"` and `"modified"` you need values the current entry dict does not carry. Add
them while building the entry (the block that appends `group_id`/`artifact_id`/... around
line 729), using the `jar_files` list already computed there via
`list(version_dir.glob("*.jar"))`. Add both as real response fields — `size_bytes` and
`last_modified` (ISO 8601 string) — so the sort key is visible in the output.

An unknown `sort_by` value should fall back to `"name"` rather than raise.

### How to verify

Add tests to `tests/test_pagination.py` (it already exercises `_list_artifacts` paging).
Cover: default is `"name"`; `"size"` orders largest first; `"modified"` orders newest
first; an unknown value falls back to `"name"` without raising. Build the fixture jars
under a `tmp_path` repository — **never** touch the real `~/.m2`.

```bash
MAVEN_OFFLINE=true pytest tests/test_pagination.py -q
```

### Decisions already made

- Parameter is named `sort_by`, a string, with default `"name"` — so existing callers see
  a *stable* order where they previously saw an arbitrary one. That is the intended change.
- No separate `sort_order`/`descending` parameter. Direction is fixed per key as listed above.
- Size means summed jar bytes in the version directory, not directory size on disk.
- New `size_bytes` and `last_modified` fields are always present, not gated behind `sort_by`.

Setup: see [`CONTRIBUTING.md`](../CONTRIBUTING.md).

---

## Issue 6

**Title:** Add an include_snapshots flag to get_remote_versions

**Body:**

### What's wrong / where

`_get_remote_versions` in `maven_decoder_mcp/maven_decoder_server.py` (around line 1766)
has the signature `(self, group_id, artifact_id, limit=100)` and returns every version the
remote index reports. There is no snapshot filtering anywhere: `grep -n "SNAPSHOT"` matches
nothing in `maven_decoder_mcp/maven_central.py` and nothing in
`maven_decoder_mcp/maven_decoder_server.py`.

For an artifact publishing snapshots, the version list is padded with `-SNAPSHOT` entries
that are almost never what the caller wants.

### What to change

Add `include_snapshots: bool = True` to `_get_remote_versions`, and the matching
`"include_snapshots"` boolean property (with `"default": true`) to the
`Tool(name="get_remote_versions", ...)` `inputSchema` around
`maven_decoder_server.py:603`.

When `include_snapshots` is `False`, drop versions whose string ends with `-SNAPSHOT`
(case-insensitive) from the `versions` list before it is returned. Filter in
`_get_remote_versions` — do **not** change `MavenCentralClient.get_versions` in
`maven_central.py`, which stays a faithful view of the remote index.

Apply the same filter to the `installed_versions` set the function builds (around line 1774)
so the two lists stay consistent.

### How to verify

Add a test to the `TestGetVersions` class in `tests/test_maven_central.py` (around line 165).
Mock the remote payload to contain both a release and a `-SNAPSHOT` version, then assert:
default keeps both; `include_snapshots=False` keeps only the release; `installed_versions`
is filtered identically.

```bash
MAVEN_OFFLINE=true pytest tests/test_maven_central.py -q
```

### Decisions already made

- Flag name `include_snapshots`, default `True` — current behavior is unchanged unless
  the caller opts out.
- Detection is a case-insensitive `-SNAPSHOT` suffix check. Do not parse version semantics.
- Filtering lives in the server handler, not in `MavenCentralClient`.

Setup: see [`CONTRIBUTING.md`](../CONTRIBUTING.md).

---

## Issue 7

**Title:** Add a case_sensitive flag to search_classes

**Body:**

### What's wrong / where

`_search_classes` in `maven_decoder_mcp/maven_decoder_server.py` (around line 1092) matches
class and package names case-sensitively. The filters are, around lines 1119 and 1122:

```python
if class_name and not re.search(class_name.replace('*', '.*'), simple_name):
    continue

if package_pattern and not re.search(package_pattern, package):
    continue
```

Neither passes `re.IGNORECASE`. Searching for `arraylist` returns nothing, which reads as
a broken tool rather than a case mismatch.

Note the inconsistency this creates: `_matching_annotations` (around line 899) already
compiles its pattern with `re.IGNORECASE`, so annotation search is case-insensitive while
class search is not.

### What to change

Add `case_sensitive: bool = True` to `_search_classes`, and the matching
`"case_sensitive"` boolean property (with `"default": true`) to the
`Tool(name="search_classes", ...)` `inputSchema` around `maven_decoder_server.py:415`.

When `case_sensitive` is `False`, pass `flags=re.IGNORECASE` to both `re.search` calls
above. `re` is imported locally at the top of `_search_classes` (`import re`), so no new
import is needed.

Prefer compiling each pattern once before the jar loop instead of re-running `re.search`
with a raw string per class — this function scans every class in every local jar, so the
compile cost matters.

### How to verify

Add a test to `tests/test_maven_central.py`. The `TestAnnotationSearch` class (around line
821) already builds jar fixtures for `_search_classes`; follow its fixture pattern. Assert
that a lowercase query misses by default and hits with `case_sensitive=False`, and that
`package_pattern` behaves the same way.

```bash
MAVEN_OFFLINE=true pytest tests/test_maven_central.py -q
```

### Decisions already made

- Flag name `case_sensitive`, default `True` — today's behavior is preserved by default.
  Do **not** name it `ignore_case`; the positive form matches the rest of the schema.
- One flag governs both `class_name` and `package_pattern`. No per-field flags.
- Annotation matching keeps its existing always-insensitive behavior; do not change it in
  this issue.

Setup: see [`CONTRIBUTING.md`](../CONTRIBUTING.md).

---

## Issue 8

**Title:** Add an opt-in compare_versions flag treating members moved to a supertype as non-breaking

**Body:**

### What's wrong / where

`_compare_versions` in `maven_decoder_mcp/maven_decoder_server.py` (around line 1337) has
the signature
`(self, group_id, artifact_id, version1, version2, compare_api=True, summarize_large_content=True)`
and compares members **as declared on each class**. A member that moved from a class to its
supertype between versions is therefore reported as removed, even though source compiled
against the new version still resolves it.

This is a documented, deliberate limitation, stated in three places:

- `README.md:23` — "Members are compared **as declared**, so one that moved to a supertype is reported as..."
- `README.md:215` — the same caveat in the breaking-changes example
- `maven_decoder_server.py:1495-1497` — the caveat string emitted in the tool's own output:
  `"Members are compared as declared on each class. A member ... supertype, but code compiled against the old declaration ..."`

### What to change

Add `resolve_inherited: bool = False` to `_compare_versions`, plus the matching
`"resolve_inherited"` boolean property (with `"default": false`) to the
`Tool(name="compare_versions", ...)` `inputSchema` around `maven_decoder_server.py:467`.

When `resolve_inherited` is `True`, a member missing from a class in version 2 but present
on one of that class's supertypes **within the same jar** must not be reported as removed.
Reclassify it into a distinct `moved_to_supertype` bucket in the result so the information
is not simply dropped. The API diff is produced by `_compare_public_api` (around line 1393),
which already receives both open `zipfile.ZipFile` handles — resolve supertypes from those.

When `resolve_inherited` is `False`, output must be **byte-identical** to today, including
the caveat text at lines 1495-1497. When it is `True`, the caveat string should say that
inherited members were resolved instead.

### Decisions already made — read this before writing code

- **The flag defaults to `False`, i.e. exactly today's behavior.** The as-declared caveat is
  quoted verbatim in `README.md` and must not change meaning for anyone who does not pass
  the flag. Do not flip the default, and do not "fix" the default in a follow-up.
- Flag name is `resolve_inherited`.
- Scope: supertypes resolvable **inside the same jar** only. Do not walk the classpath, do
  not download parent artifacts, do not resolve `java.*` types. A member whose supertype is
  not in the jar stays reported as removed.
- Moved members go into a separate `moved_to_supertype` list — they are not silently merged
  into the "unchanged" set.

### How to verify

Add a test to the `TestApiComparison` class in `tests/test_maven_central.py` (around line
655), which already builds two-version jar fixtures. Assert:

1. With the flag unset, a member moved to a supertype is still reported as removed, and the
   caveat text is unchanged.
2. With `resolve_inherited=True`, the same member appears under `moved_to_supertype` and
   not under removed.

```bash
MAVEN_OFFLINE=true pytest tests/test_maven_central.py -q
```

The unchanged-default assertion in (1) is the acceptance criterion — a PR that changes
default output will not be merged.

Setup: see [`CONTRIBUTING.md`](../CONTRIBUTING.md).

---

## Issue 9

**Title:** Return Javadoc comments from extract_method_info when a sources jar is present

**Body:**

### What's wrong / where

`_extract_method_info` in `maven_decoder_mcp/maven_decoder_server.py` (around line 1856)
builds each result entry via `_extract_methods_from_source` (around line 1886), whose regex
(`method_pattern_regex`) matches only the method declaration line — modifiers, return type,
name, parameter list. Preceding `/** ... */` blocks are discarded.

The result dict (around line 1873) is `class_name`, `artifact`, `total_methods_found`,
`methods`, `method_pattern`. No documentation field exists.

The server already knows how to find a sources jar: `_resolve_sources_jar_path` (around line
1307) and `_extract_from_sources_jar` (used at line 1200 inside the source-extraction path).
`_extract_method_info` does not use them — it calls `_extract_source_code_internal`.

### What to change

In `_extract_methods_from_source`, when a method declaration is matched, look backwards
through the preceding lines for a `/** ... */` block that ends immediately above the
declaration (blank lines and annotation lines may sit between). Attach it as a `javadoc`
key on the method dict.

Add `"javadoc": null` for methods with no doc comment, so the response shape is stable.

Strip the comment markers before returning: drop the opening `/**`, the closing `*/`, and
the leading `* ` on each line. Return the remaining text as-is — do **not** parse `@param`
or `@return` into structured fields.

Because decompiler output rarely carries comments, also make `_extract_method_info` prefer
sources-jar text when it is available: call `_resolve_sources_jar_path`, and if it returns
an existing path use `_extract_from_sources_jar` for the source text, falling back to
`_extract_source_code_internal` otherwise. Add a `"source"` field to the result recording
which path was used.

### How to verify

Add a test to `tests/test_maven_central.py`. Build a `-sources.jar` fixture under `tmp_path`
containing a class with one documented and one undocumented method. Assert the documented
method's `javadoc` contains the comment text with markers stripped, the undocumented one is
`None`, and the `source` field reports the sources jar. Then assert the fallback path still
works when no sources jar exists.

```bash
MAVEN_OFFLINE=true pytest tests/test_maven_central.py -q
```

### Decisions already made

- Field name is `javadoc`, raw text, always present (`None` when absent). No `@param`/`@return`
  parsing — that is a separate issue.
- No new tool parameter. Javadoc is included whenever it is available; there is no flag.
- Sources jar is preferred over decompiled output when present, and the choice is reported
  in a `source` field.
- Only `/** */` blocks count. `//` and `/* */` comments are ignored.

Setup: see [`CONTRIBUTING.md`](../CONTRIBUTING.md).

---

## Issue 10

**Title:** Explain a missing ~/.m2/repository instead of returning an empty artifact list

**Body:**

### What's wrong / where

**Premise correction from the original candidate note:** a message *does* exist —
`Config.validate` in `maven_decoder_mcp/config.py` (around line 286) prints
`f"Warning: Maven repository not found at {cls.MAVEN_HOME}"` and returns `False`. But
`grep -rn "validate" ` across the package returns only that one definition line: **nothing
ever calls it.** It is dead code, and it `print`s to stdout, which is the wrong channel for
an MCP server anyway.

Meanwhile `_list_artifacts` in `maven_decoder_mcp/maven_decoder_server.py` (around line 689)
starts with `group_dirs = [p for p in self.maven_home.iterdir() if p.is_dir()]` inside a
`try`. On a machine with no `~/.m2/repository`, `iterdir()` raises `FileNotFoundError`, and
the bare handler at the end of the function returns
`f"Error listing artifacts: {str(e)}"` — a raw `FileNotFoundError` string. A new user sees
a stack-trace-flavored error instead of "you have no local repository yet".

### What to change

In `_list_artifacts`, check `self.maven_home.exists()` (and `is_dir()`) **before** the
`iterdir()` call, and return a `TextContent` with an actionable message naming:

- the path that was checked (`self.maven_home`)
- that `MAVEN_REPOSITORY` overrides it
- that running any Maven build creates the directory
- that remote tools (`search_maven_central`, `download_artifact`) still work without it

Follow the tone of the existing `_jar_not_found_message` helper (around line 923), which
already writes explanatory misses with the relevant env var named. Adding a sibling helper
next to it — e.g. `_missing_repository_message` — keeps the two consistent.

Leave `Config.validate` alone in this issue; removing dead code is a separate change.

### How to verify

Add a test to `tests/test_maven_repository_resolution.py`. Point the server at a `tmp_path`
subdirectory that does not exist, call `_list_artifacts`, and assert the returned text
mentions both the missing path and `MAVEN_REPOSITORY`, and does **not** contain
`FileNotFoundError`.

```bash
MAVEN_OFFLINE=true pytest tests/test_maven_repository_resolution.py -q
```

### Decisions already made

- The tool returns an explanatory `TextContent`; it does **not** raise, and it does **not**
  create the directory.
- Message is produced by a helper next to `_jar_not_found_message`, not inlined.
- Scope is `_list_artifacts` only. Other tools already route misses through
  `_jar_not_found_message`.
- `Config.validate` stays as-is.

Setup: see [`CONTRIBUTING.md`](../CONTRIBUTING.md).

---

## Issue 11

**Title:** Report the search endpoint that actually answered, not the first configured one

**Body:**

### What's wrong / where

**Premise correction from the original candidate note:** the search path *does* already
report its endpoint. `MavenCentralClient.search` in `maven_decoder_mcp/maven_central.py`
loops `for search_url in self.search_urls:` (around line 200) and includes
`"search_url": search_url` in its result (around line 212) — the endpoint that actually
succeeded.

The real defect is one layer up. `get_versions` builds its result around line 302 with:

```python
"repository": self.search_url,
```

`search_url` is a property (around line 100) that returns `self.search_urls[0]` — always the
*first configured* endpoint, regardless of which one answered. When the first endpoint fails
and the second succeeds, `get_versions` reports the wrong repository. The correct value is
sitting unused in `search_result["search_url"]`.

Separately, fallback and retry are invisible in practice:

- `_get` (around line 104) logs its retry with `logger.debug` at line 122 only
- `search` accumulates failures into a local `errors` list and only surfaces them if
  *every* endpoint fails, in the `MavenRemoteError` at the end of the loop

So a partial outage — first endpoint down, second working — leaves no trace at default log
level.

### What to change

1. In `get_versions`, replace `"repository": self.search_url` with the endpoint that
   answered: `search_result["search_url"]`.
2. In `search`, when an endpoint fails and another will be tried, log at `logger.warning`
   naming the failed endpoint and the one being tried next. `logger` is already defined at
   `maven_central.py:29`.
3. In `_get`, promote the existing retry log from `logger.debug` to `logger.info` and
   include the attempt number (`attempt + 1`) and `self.retries + 1` as the total.

Do not change the returned data shape beyond fixing the `repository` value, and do not add
new fields.

### How to verify

Add a test to the `TestRetries` class in `tests/test_maven_central.py` (around line 344).
Configure two search URLs, make the first raise and the second succeed, then assert that
`get_versions` reports the **second** URL in `repository`. Use `caplog` to assert a warning
naming the failed endpoint was emitted.

```bash
MAVEN_OFFLINE=true pytest tests/test_maven_central.py -q
```

### Decisions already made

- `repository` reporting the first configured URL is a **bug**, not a contract. Fixing it to
  the answering endpoint is the intended change.
- Fallback logs at `warning`; retry logs at `info`. Nothing new is added to the response.
- The `search_url` property keeps returning `search_urls[0]` — it is the "preferred
  endpoint" accessor. Do not redefine it.

Setup: see [`CONTRIBUTING.md`](../CONTRIBUTING.md).

---

## Issue 12

**Title:** Report a corrupt or truncated jar by name instead of a generic error

**Body:**

### What's wrong / where

**Re-confirmed before filing:** `zipfile.BadZipFile` appears **nowhere** in the repository.

```bash
$ grep -rn "BadZipFile\|LargeZipFile" maven_decoder_mcp/ tests/
(no matches)
```

There are 12 `zipfile.ZipFile(...)` call sites — 8 in
`maven_decoder_mcp/maven_decoder_server.py` (lines ~780, 1005, 1107, 1256, 1330, 1366, and
the `_compare_public_api` signature at 1393, 1551) and 4 in
`maven_decoder_mcp/decompiler.py` (~137, 174, 566, 641). None distinguishes a corrupt
archive.

The current outcomes are both bad, in different ways:

- `_search_classes` swallows it — `except Exception: continue  # Skip corrupted jars`
  (around line 1145). The jar vanishes from results with no indication it was skipped.
- `_analyze_jar` and `_extract_method_info` fall into their generic
  `except Exception as e:` handlers and return `f"Error analyzing jar: {str(e)}"` /
  `f"Error extracting method info: {str(e)}"`, which surfaces a bare zipfile message
  with no path and no remediation.

Either way the agent cannot tell the user "the jar at *this path* is truncated; re-download it".

### What to change

Add an explicit `except zipfile.BadZipFile:` ahead of the existing generic handlers at the
tool-entry functions in `maven_decoder_mcp/maven_decoder_server.py` — start with
`_analyze_jar` (around line 763), `_analyze_jar_structure` (around line 1840), and
`_extract_method_info` (around line 1856).

The message must name the offending path and say the file is likely truncated or corrupt,
and that deleting it and re-downloading (or re-running the Maven build that produced it)
fixes it. Do **not** delete the file — see decisions below.

In `_search_classes`, keep skipping corrupt jars (scanning must not abort on one bad file),
but narrow `except Exception` to `except zipfile.BadZipFile` and `logger.warning` the path
so the skip is visible. Leave any other exception type to propagate.

`zipfile` is already imported in `maven_decoder_server.py`.

### How to verify

Add a new test file `tests/test_corrupt_jars.py`. Write a truncated/garbage file with a
`.jar` extension into a `tmp_path` repository layout, then assert:

1. `_analyze_jar` returns text naming the path and the words "corrupt" or "truncated", and
   does not raise.
2. `_search_classes` completes and still returns matches from a valid sibling jar, and logs
   a warning naming the bad jar (use `caplog`).

Build all fixtures under `tmp_path`. **Never** write into the real `~/.m2` — that rule is
non-negotiable per `CONTRIBUTING.md`.

```bash
MAVEN_OFFLINE=true pytest tests/test_corrupt_jars.py -q
```

### Decisions already made

- The server **never deletes** a jar it thinks is corrupt. `~/.m2` stays untouched; the
  message tells the user what to remove.
- Single-artifact tools return an explanatory message. Multi-jar scans skip and warn. That
  asymmetry is intentional.
- Catch `zipfile.BadZipFile` specifically. Do not broaden to `except Exception`.
- Scope is the three tool-entry functions listed above plus `_search_classes`. Leave
  `decompiler.py` for a follow-up.

Setup: see [`CONTRIBUTING.md`](../CONTRIBUTING.md).

---

## Issue 13

**Title:** Test MAVEN_HTTP_RETRIES parsing in Config.http_retries

**Body:**

### What's wrong / where

`Config.http_retries` in `maven_decoder_mcp/config.py` (around line 151) is untested:

```python
raw = os.environ.get("MAVEN_HTTP_RETRIES", "").strip()
try:
    retries = int(raw)
except ValueError:
    return cls.DEFAULT_HTTP_RETRIES
return max(0, retries)
```

`grep -rn "MAVEN_HTTP_RETRIES" tests/` returns nothing.

Its sibling `Config.http_timeout` has exactly one test —
`test_invalid_timeout_falls_back_to_default` at `tests/test_maven_central.py:412`, in the
`TestConfigRemoteSettings` class (starting around line 379) — which covers only the
non-numeric case.

Three behaviors are unverified: the `DEFAULT_HTTP_RETRIES` fallback (`3`, defined at
`config.py:33`), the empty-string case, and the `max(0, retries)` clamp that turns a
negative value into `0`.

### What to change

Add tests to `TestConfigRemoteSettings` in `tests/test_maven_central.py`, alongside
`test_invalid_timeout_falls_back_to_default`. Use the same `patch.dict(os.environ, {...})`
style already used throughout that class. Cover:

- `MAVEN_HTTP_RETRIES` unset → `Config.DEFAULT_HTTP_RETRIES`
- `"not-a-number"` → `Config.DEFAULT_HTTP_RETRIES`
- `""` → `Config.DEFAULT_HTTP_RETRIES` (the empty string hits the same `ValueError` path)
- `"5"` → `5`
- `"-1"` → `0` (the clamp)
- `"0"` → `0` (zero is valid and means no retries — distinct from unset)

Also add the missing timeout cases while you are in the same class: whitespace-only, and a
valid numeric value.

Assert against `Config.DEFAULT_HTTP_RETRIES`, never a hardcoded `3`.

### How to verify

```bash
MAVEN_OFFLINE=true pytest tests/test_maven_central.py -q -k ConfigRemoteSettings
```

Then the full suite: `MAVEN_OFFLINE=true pytest tests/ -q`

### Decisions already made

- Tests only. `Config.http_retries` behavior is correct as written — do **not** change it.
  In particular, `"0"` meaning zero retries is intended, not a bug.
- Tests go in the existing `TestConfigRemoteSettings` class. Do not create a new file.
- Scope is `Config.http_retries`. `MavenCentralClient` retry *behavior* is issue 11's
  territory.

Setup: see [`CONTRIBUTING.md`](../CONTRIBUTING.md).

---

## Issue 14

**Title:** Test MAVEN_MAX_DOWNLOAD_SIZE enforcement in MavenCentralClient

**Body:**

### What's wrong / where

`grep -rn "MAVEN_MAX_DOWNLOAD_SIZE" tests/` returns nothing. The size ceiling has two
independent enforcement points in `maven_decoder_mcp/maven_central.py`, neither tested:

1. **Declared size, pre-download** (around line 442):
   `if declared and declared.isdigit() and int(declared) > self.max_download_bytes:` —
   rejects on the `Content-Length` header, raising with a message that ends
   `"byte limit (set MAVEN_MAX_DOWNLOAD_SIZE)"` (line ~446).
2. **Streamed size, mid-download** (around line 462):
   `if written > self.max_download_bytes:` — catches a server that lies about or omits
   `Content-Length`.

The parsing side is `Config.max_download_bytes` in `maven_decoder_mcp/config.py` (around
line 220), which falls back to `Config.MAX_JAR_SIZE` (`100 * 1024 * 1024`, defined at
`config.py:63`) on a non-numeric value, and also when the parsed value is `<= 0`.

`MavenCentralClient.__init__` takes `max_download_bytes` directly (around line 55) and
defaults to `Config.max_download_bytes()` (around line 68), so tests can inject a tiny
limit without touching the environment.

### What to change

Add tests to the `TestDownload` class in `tests/test_maven_central.py` (around line 226),
which already mocks HTTP responses for downloads. Cover:

- **Config parsing:** `MAVEN_MAX_DOWNLOAD_SIZE` unset → `Config.MAX_JAR_SIZE`; non-numeric
  → `Config.MAX_JAR_SIZE`; `"0"` and a negative value → `Config.MAX_JAR_SIZE`; a valid
  positive value → that value. These belong in `TestConfigRemoteSettings` (around line 379)
  rather than `TestDownload`.
- **Declared-size rejection:** construct the client with a small `max_download_bytes`, mock
  a response whose `Content-Length` exceeds it, assert the raise and that the message names
  `MAVEN_MAX_DOWNLOAD_SIZE`.
- **Streamed-size rejection:** mock a response with **no** `Content-Length` that streams
  more bytes than the limit, assert the raise.
- **Partial file cleanup:** after a streamed rejection, assert no partial file is left in
  the cache directory.

Use `tmp_path` for the cache via `MAVEN_DECODER_CACHE_DIR`. Never write to the real cache
or to `~/.m2`.

### How to verify

```bash
MAVEN_OFFLINE=true pytest tests/test_maven_central.py -q -k "Download or ConfigRemoteSettings"
```

Then: `MAVEN_OFFLINE=true pytest tests/ -q`

### Decisions already made

- Tests only. If the partial-cleanup test fails, **report it in a comment** rather than
  fixing it here — a cleanup fix is a separate issue with its own review.
- Inject the limit via the `max_download_bytes` constructor argument for the two
  enforcement tests, and via the environment only for the `Config` parsing tests.
- Assert against `Config.MAX_JAR_SIZE`, never a hardcoded `104857600`.

Setup: see [`CONTRIBUTING.md`](../CONTRIBUTING.md).

---

## Issue 15

**Title:** Test that tool responses carry the origin field, and fix the analyze_jar key mismatch

**Body:**

### What's wrong / where

`_path_origin` in `maven_decoder_mcp/maven_decoder_server.py` (around line 915) returns
`"remote-cache"` or `"local-repository"` depending on whether the path sits under
`self.cache_home`. It has exactly one test — `tests/test_maven_central.py:1094`:

```python
assert self.server._path_origin(resolved) == "remote-cache"
```

in the `TestServerRemoteIntegration` class (starting around line 1064). That tests the
helper in isolation. **No test asserts the value reaches tool output.**

While checking the call sites, a real inconsistency turned up. `_path_origin` is called at
four places, and one uses a different key:

| Line | Function | Key |
|---|---|---|
| ~776 | `_analyze_jar` | `"source"` |
| ~1207 | source extraction (sources jar) | `"origin"` |
| ~1227 | source extraction (jar) | `"origin"` |
| ~1848 | `_analyze_jar_structure` | `"origin"` |

`_analyze_jar` emits `"source": self._path_origin(jar_path)` while the other three emit
`"origin"`. A consumer keying on `origin` silently gets nothing back from `analyze_jar`.

### What to change

1. Change the key at `_analyze_jar` (~line 776) from `"source"` to `"origin"`, so all four
   call sites agree.
2. Add a new test file `tests/test_origin_field.py` asserting the field is present **and
   correct** on real tool output — not just from the helper. For each of `analyze_jar`,
   `extract_source_code`, and `analyze_jar_structure`:
   - a jar resolved from the local repository yields `origin == "local-repository"`
   - a jar resolved from the download cache yields `origin == "remote-cache"`

Parse the `TextContent` JSON the handler returns and assert on the parsed dict — do not
substring-match the text.

Build a fake local repository and a fake cache under `tmp_path`, pointing at them with
`MAVEN_REPOSITORY` and `MAVEN_DECODER_CACHE_DIR`. `tests/conftest.py` already holds shared
fixtures and environment isolation; reuse them rather than re-rolling the setup.

### How to verify

```bash
MAVEN_OFFLINE=true pytest tests/test_origin_field.py -q
```

Then the full suite, which must stay green:
`MAVEN_OFFLINE=true pytest tests/ -q`

### Decisions already made

- `"origin"` is the canonical key; `"source"` in `_analyze_jar` is the outlier and gets
  renamed. Do not add a duplicate `"source"` alias for compatibility — this project is
  pre-1.0 and the field is undocumented in `README.md`.
- New file `tests/test_origin_field.py`, because this spans several handlers and does not
  belong under `test_maven_central.py`'s remote-client theme.
- Tests must run offline. No network, no real `~/.m2`.
- Scope is the four existing `_path_origin` call sites. Do not add `origin` to tools that
  do not emit it today.

Setup: see [`CONTRIBUTING.md`](../CONTRIBUTING.md).

---

## Anchor drift

Re-checked against the working tree before drafting.

| Symbol | Claimed | Actual | Status |
|---|---|---|---|
| `_list_artifacts` | `maven_decoder_server.py:689` | 689 | exact |
| `_path_origin` | `maven_decoder_server.py:915` | 915 | exact |
| `_search_classes` | `maven_decoder_server.py:1092` | 1092 | exact |
| `_compare_versions` | `maven_decoder_server.py:1337` | 1337 | exact |
| `_find_usage_examples` | `maven_decoder_server.py:1513` | 1513 | exact |
| `_get_remote_versions` | `maven_decoder_server.py:1766` | 1766 | exact |
| `_extract_method_info` | `maven_decoder_server.py:1856` | 1856 | exact |
| `Config.http_retries` | `config.py:151` | 151 | exact |
| `Config.max_download_bytes` | `config.py:220` | 220 | exact |
| `Config.resolve_download_cache` | `config.py:182` | 182 | exact |
| `MavenCentralClient._verify_checksum` | `maven_central.py:480` | 480 | exact |
| Tool declarations | `maven_decoder_server.py:344` | 344 (`name="list_artifacts"`) | exact |
| `LOCALAPPDATA` fallback | `config.py:193` | 193 | exact |
| Download size ceiling | `maven_central.py:446` and `:465` | 442/446 and 462/464 | **drifted** (off by up to 3) |
| `Config.http_retries` read | `maven_central.py:59` | 59 | exact |
| `MAVEN_HTTP_TIMEOUT` test | `tests/test_maven_central.py:412` | 412 | exact |
| `_path_origin` test | `tests/test_maven_central.py:1094` | 1094 | exact |
| `origin` emitted | `maven_decoder_server.py:1207`, `:1227`, `:1848` | all three exact | exact, but **incomplete** — a fourth call site at ~776 uses key `"source"`, not `"origin"` |

### Premise corrections

- **Issue 10** — candidate said "`config.py` has no 'missing repository' message today".
  Wrong: `Config.validate` (`config.py:286`) prints one. It is never called from anywhere
  in the package. Issue rewritten around the dead-code fact.
- **Issue 11** — candidate said `MavenCentralClient` "never reports which attempt or
  endpoint succeeded". Partly wrong: `search` already returns `search_url` for the endpoint
  that answered (`maven_central.py:212`). The genuine defect is `get_versions` reporting
  `self.search_url` (= `search_urls[0]`) at line 305 instead of the answering endpoint.
- **Issue 12** — re-confirmed as claimed: `BadZipFile` is caught nowhere. Nuance added:
  `_search_classes` swallows it under a bare `except Exception: continue` at ~1145, and the
  single-artifact tools surface it through generic handlers rather than raising raw to the
  agent.
