---
name: maven-code-search
description: Use the Maven Decoder MCP server to inspect code, APIs, methods, dependencies, versions, and usage examples from Maven artifacts installed in the user's local ~/.m2 repository. Use when working on Java, Maven, Gradle, Spring, Jakarta, Android, or JVM projects and the user asks about dependency internals, installed package code, class/method signatures, decompiled source, dependency trees, version differences, or which local artifact contains a class.
---

# Maven Code Search

## Overview

Use the `maven-decoder` MCP server before guessing about third-party Java dependencies. It can search the user's installed Maven repository, inspect jars, prefer source jars when available, and decompile bytecode when source is missing.

This MCP only sees artifacts already present in the local Maven cache. If the needed artifact is missing, ask the user to build the project or run a dependency resolution command such as `mvn dependency:go-offline`, then retry the MCP search.

## Quick Workflow

1. Identify the target coordinates when possible: `group_id`, `artifact_id`, and `version`. Read `pom.xml`, `build.gradle`, lockfiles, or existing imports if the user did not provide them.
2. Use MCP search tools to confirm what is installed before inspecting code.
3. Prefer narrow queries: a class name, package pattern, artifact coordinates, or method pattern.
4. Use pagination for broad searches and ask for the next page only when the current page is not enough.
5. Report findings with exact coordinates, class names, method names, and whether the result came from sources or decompiled bytecode.

## Tool Selection

Use `list_artifacts` to discover installed artifacts or filter by partial `group_id`, `artifact_id`, or `version`.

Use `get_version_info` when the user asks which versions of an artifact are installed.

Use `search_classes` when the user knows a class name, simple type name, wildcard, or package but not the artifact that contains it.

Use `extract_class_info` when the user needs constructors, fields, annotations, or method signatures for classes in a known artifact. If sources are missing, this tool still returns bytecode-backed fields and methods through the MCP, so do not shell out to `javap` for the same information.

Use `extract_source_code` when the user needs implementation details. Set `prefer_sources` to true unless there is a specific reason to force decompilation.

Use `extract_jar_resource` when the user needs files embedded in the jar, such as `.proto` files, service descriptors, or Maven metadata. Use `analyze_jar` first when you need to discover resource paths. Do not shell out to `jar tf` just to list or read jar entries.

Use `extract_method_info` for targeted method inspection instead of pulling a large class.

Use `get_dependencies` for direct POM dependencies and `get_dependency_tree` for transitive dependency chains.

Use `find_dependents` when the user asks "what installed artifacts depend on X?"

Use `compare_versions` when the user asks what changed between two installed versions of the same artifact.

Use `analyze_jar` or `analyze_jar_structure` when the user asks about jar metadata, manifests, packages, resources, services, or high-level structure.

Use `find_usage_examples` when the user asks how a class or method is used in installed test jars.

## Query Patterns

For "Where is `ObjectMapper` installed?", call `search_classes` with `class_name: "ObjectMapper"` and inspect the returned artifact coordinates.

For "Show me the methods on `RestTemplate`", first resolve the artifact/version if needed, then call `extract_class_info` with the fully qualified class name or a precise class pattern.

For "How does this library implement retry?", search for likely classes by package or class name, then use `extract_method_info` or `extract_source_code` on the most relevant classes.

For generated protobuf classes with no sources jar, call `extract_class_info` on the generated class to recover parsed methods and fields. If the jar includes `.proto` resources or descriptor metadata, use `analyze_jar` and `extract_jar_resource` to inspect those resources through the MCP.

For "Why do I have two versions?", use `get_dependency_tree`, `find_dependents`, and `compare_versions` as needed. Tie the answer back to the project's declared dependencies.

## Answer Guidelines

Keep responses grounded in MCP results. Include:

- Maven coordinates, including version.
- Fully qualified class or method names.
- Whether source came from a source jar or decompilation when that distinction is visible.
- Pagination status when results are incomplete.
- Any local-cache limitation, such as an artifact not being installed.
- For compiled-only classes, say that the class details came from bytecode-backed MCP inspection rather than claiming the source jar was available.

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
