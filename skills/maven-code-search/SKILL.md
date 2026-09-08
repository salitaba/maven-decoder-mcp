---
name: maven-code-search
description: Use the Maven Decoder MCP server to inspect code, APIs, methods, dependencies, versions, and usage examples from Maven artifacts, both those installed in the user's local ~/.m2 repository and those published on Maven Central. Use when working on Java, Maven, Gradle, Spring, Jakarta, Android, or JVM projects and the user asks about dependency internals, package code, class/method signatures, decompiled source, dependency trees, version differences, which artifact contains a class, or what versions of a library exist.
---

# Maven Code Search

## Overview

Use the `maven-decoder` MCP server before guessing about third-party Java dependencies. It can search the user's installed Maven repository, search Maven Central online, inspect jars, prefer source jars when available, and decompile bytecode when source is missing.

The MCP sees both local and remote artifacts. Artifacts already in the local Maven repository are used directly; anything else is downloaded from Maven Central into a separate cache on demand, so you can inspect a library the user has never installed. Local copies always take precedence.

If a remote lookup fails, check whether offline mode is enabled (`MAVEN_OFFLINE`) before telling the user an artifact does not exist.

## Quick Workflow

1. Identify the target coordinates when possible: `group_id`, `artifact_id`, and `version`. Read `pom.xml`, `build.gradle`, lockfiles, or existing imports if the user did not provide them.
2. Use MCP search tools to confirm what is available before inspecting code. Search locally first; go online when the artifact is not installed.
3. Prefer narrow queries: a class name, package pattern, artifact coordinates, or method pattern.
4. Use pagination for broad searches and ask for the next page only when the current page is not enough.
5. Report findings with exact coordinates, class names, method names, whether the result came from sources or decompiled bytecode, and whether it came from the local repository or was downloaded.

## Tool Selection

### Local first

Use `list_artifacts` to discover installed artifacts or filter by partial `group_id`, `artifact_id`, or `version`.

Use `get_version_info` when the user asks which versions of an artifact are installed. Set `include_remote: true` to also show versions published on Maven Central.

Use `search_classes` when the user knows a class name, simple type name, wildcard, or package but not the artifact that contains it. This scans installed jars only.

### Going online

Use `search_maven_central` when the artifact is not installed, when the user asks what exists on Maven Central, or when `search_classes` finds nothing. Search by `class_name` or `fully_qualified_class` to discover which published artifact contains a type.

Use `get_remote_versions` when the user asks what versions exist, which is the newest, or whether an upgrade is available. This reads `maven-metadata.xml` and keeps working even when the search index is throttled.

Use `download_artifact` to pull an artifact into the cache before a deep inspection. Pass `latest` as the version to get the newest release. This is usually optional: the analysis tools download automatically when an artifact is missing.

### Inspecting code (local or downloaded)

Use `extract_class_info` when the user needs constructors, fields, annotations, or method signatures for classes in a known artifact. If sources are missing, this tool still returns bytecode-backed fields and methods through the MCP, so do not shell out to `javap` for the same information.

Use `extract_source_code` when the user needs implementation details. Set `prefer_sources` to true unless there is a specific reason to force decompilation.

Use `extract_jar_resource` when the user needs files embedded in the jar, such as `.proto` files, service descriptors, or Maven metadata. Use `analyze_jar` first when you need to discover resource paths. Do not shell out to `jar tf` just to list or read jar entries.

Use `extract_method_info` for targeted method inspection instead of pulling a large class.

Use `get_dependencies` for direct POM dependencies and `get_dependency_tree` for transitive dependency chains.

Use `find_dependents` when the user asks "what installed artifacts depend on X?"

Use `compare_versions` when the user asks what changed between two versions, or whether an upgrade is safe. With `compare_api` (default true) it returns added and removed public/protected members per class, a `breaking_changes` count, and a `compatible` flag. Report removals as the risk, and mention that a member which moved to a supertype still shows as removed.

Use `analyze_jar` or `analyze_jar_structure` when the user asks about jar metadata, manifests, packages, resources, services, or high-level structure.

Use `find_usage_examples` when the user asks how a class or method is used, or which installed artifacts call it. It scans bytecode references, so it finds real callers rather than guesses, and ranks test jars first. Pass `method_name` to narrow to a specific call.

Use `search_classes` with `annotation` to find classes carrying an annotation, such as `Deprecated` or a Spring stereotype. The annotation may be a simple name, a fully qualified name, or a pattern.

## Query Patterns

For "Where is `ObjectMapper` installed?", call `search_classes` with `class_name: "ObjectMapper"` and inspect the returned artifact coordinates. If nothing is installed, call `search_maven_central` with the same class name to find the published artifact.

For "What library provides X?" when nothing is installed, call `search_maven_central` with `class_name` or `fully_qualified_class`, then inspect the best match directly; it will be downloaded automatically.

For "Is there a newer version of X?", call `get_remote_versions` and compare against the version in the project's build file.

For "Show me the methods on `RestTemplate`", first resolve the artifact/version if needed, then call `extract_class_info` with the fully qualified class name or a precise class pattern.

For "How does this library implement retry?", search for likely classes by package or class name, then use `extract_method_info` or `extract_source_code` on the most relevant classes.

For generated protobuf classes with no sources jar, call `extract_class_info` on the generated class to recover parsed methods and fields. If the jar includes `.proto` resources or descriptor metadata, use `analyze_jar` and `extract_jar_resource` to inspect those resources through the MCP.

For "Why do I have two versions?", use `get_dependency_tree`, `find_dependents`, and `compare_versions` as needed. Tie the answer back to the project's declared dependencies.

## Answer Guidelines

Keep responses grounded in MCP results. Include:

- Maven coordinates, including version.
- Fully qualified class or method names.
- Whether source came from a source jar or decompilation when that distinction is visible.
- Whether the artifact was already installed locally or was downloaded from Maven Central. The `origin` field in responses reports this as `local-repository` or `remote-cache`.
- Pagination status when results are incomplete.
- For compiled-only classes, say that the class details came from bytecode-backed MCP inspection rather than claiming the source jar was available.

Do not claim an artifact or version does not exist based only on a local search. Confirm with `search_maven_central` or `get_remote_versions` first, unless offline mode is enabled.

Do not paste huge decompiled files into chat. Summarize the relevant behavior and include only small snippets when they are necessary to explain the answer.

## Missing MCP Server

If the `maven-decoder` MCP tools are not available, tell the user the skill requires the Maven Decoder MCP server to be installed and configured in their MCP-capable client. A common stdio setup is:

```json
{
  "maven-decoder": {
    "command": "uvx",
    "args": ["maven-decoder-mcp"]
  }
}
```
