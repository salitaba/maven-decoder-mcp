<!-- mcp-name: io.github.salitaba/maven-decoder-mcp -->

# Maven Decoder MCP Server

[![skills.sh](https://skills.sh/b/salitaba/maven-decoder-mcp)](https://skills.sh/salitaba/maven-decoder-mcp)

**Your agent guesses at library APIs it has never read. This makes it read them.**

Lets AI agents read the actual source of any Maven dependency — decompiles jars from
`~/.m2` or Maven Central, and diffs versions for breaking changes.

![Demo: comparing jsoup 1.17.2 with 1.23.2](docs/demo.gif)

Ask an agent *"I'm upgrading `org.jsoup:jsoup` from 1.17.2 to 1.23.2 — what breaks?"* and
without a way to read the jars it will answer from memory. With this server,
`compare_versions` reads both jars and reports what actually changed:

| | 1.17.2 → 1.23.2 |
|---|---|
| Breaking changes | **45** |
| Members removed | 31 |
| Members added | 150 |
| Classes with API changes | 47 of 115 compared |

Members are compared **as declared**, so one that moved to a supertype is reported as
removed even though it may still be callable. The tool states this in its own output.

It works on artifacts that have **no sources jar** too: `extract_class_info` falls back
to `javap` and returns parsed fields, methods, and bytecode version — which is exactly
the case for the internal artifacts in a corporate Nexus.

### Try it in one command

```bash
npx skills add https://github.com/salitaba/maven-decoder-mcp --skill maven-code-search
```

That installs the `maven-code-search` agent skill, which tells your agent when to reach
for these tools. For a raw MCP server setup instead, see [Installation](#-installation).

## 🚀 Features

### Core Functionality
- **Jar File Analysis**: Deep inspection of jar files including metadata, manifests, and structure
- **Dependency Resolution**: Complete dependency tree analysis with transitive dependencies
- **Source Code Extraction**: Extract source code from source jars or decompile bytecode
- **Class Information**: Detailed class signatures, methods, fields, and annotations
- **Search Capabilities**: Find classes, methods, and dependencies across all artifacts
- **Version Management**: Compare versions, find dependents, and track version conflicts

### Online Maven Support
- **Maven Central Search**: Find artifacts and classes that are **not installed locally**
- **Remote Version Listing**: See every published version, not just the ones you have
- **On-Demand Download**: Fetch any artifact (jar, sources, POM) into a local cache
- **Transparent Fallback**: Every analysis tool automatically downloads a missing artifact, so decompiling a dependency you never installed just works
- **Mirror Friendly**: Point it at a corporate Nexus/Artifactory, with optional credentials
- **Offline Mode**: A single env var restores fully local, network-free behavior

### Advanced Features
- **Decompilation Support**: Integrated support for multiple Java decompilers (CFR, Fernflower, Procyon)
- **Conflict Analysis**: Detect and analyze dependency version conflicts
- **Repository Navigation**: Browse and explore the local Maven repository structure
- **Metadata Parsing**: Extract and parse Maven POM files and metadata
- **Service Discovery**: Find and analyze Java services and SPI implementations
- **Response Management**: Intelligent pagination and summarization for large responses
- **Method Extraction**: Extract specific methods from large Java classes
- **Integrity Checking**: Downloads are verified against the repository's SHA-1 checksums

## 📦 Installation

### Prerequisites
- Java 8+ (for decompilation features)
- Maven local repository (`~/.m2/repository`)
- One of: **Python 3.8+**, **Node.js 14+**, or **Docker**

### 🚀 Quick Install

#### One-Line Install (Recommended)
```bash
curl -fsSL https://raw.githubusercontent.com/salitaba/maven-decoder-mcp/main/install.sh | bash
```

### 📋 Installation Methods

#### Method 1: uvx (Recommended)
```bash
# Install uv (if not installed)
curl -Ls https://astral.sh/uv/install.sh | sh
# Ensure your shell PATH is updated (restart shell or eval as printed by installer)

# Run the server via uvx (isolated, fast, no venv needed)
uvx maven-decoder-mcp

# Optional: pick a specific Python
# uvx --python 3.12 maven-decoder-mcp
```

#### Method 2: Node.js/npm
```bash
# Install globally
npm install -g maven-decoder-mcp

# Or install locally
npm install maven-decoder-mcp

# Run the server
maven-decoder-mcp
# or if installed locally: npx maven-decoder-mcp
```

#### Method 3: Docker
```bash
# Pull and run
docker run --rm -it \
  -v ~/.m2:/home/mcpuser/.m2 \
  -v $(pwd):/workspace \
  ali79taba/maven-decoder-mcp:latest
```

#### Method 4: From Source (Development)
```bash
# Clone repository
git clone https://github.com/salitaba/maven-decoder-mcp.git
cd maven-decoder-mcp

# Option A: Using Virtual Environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install "git+https://github.com/modelcontextprotocol/python-sdk.git"
./setup_decompilers.sh

# Option B: System-wide Installation (not recommended)
./setup_decompilers.sh
```

### Windows

For a source checkout, use Python 3.10 or newer and a JDK on `PATH`. From the
repository root, create and activate a virtual environment in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"

# Point to your existing local Maven repository (drive-letter paths are supported)
$env:MAVEN_REPOSITORY = 'F:\data\repository'
maven-decoder-mcp
```

In Command Prompt (`cmd.exe`), activate with `.venv\Scripts\activate.bat` and set
the repository with `set "MAVEN_REPOSITORY=F:\data\repository"` instead. These
environment settings apply to programs launched from that terminal; set them in
your MCP client's environment when it launches the server separately.

Remote downloads use a separate cache, resolved in this order (empty values are
skipped):

1. `MAVEN_DECODER_CACHE_DIR`: the complete cache directory; no subdirectory is appended.
2. `XDG_CACHE_HOME`: append `maven-decoder-mcp\repository`.
3. `LOCALAPPDATA`: append `maven-decoder-mcp\repository`.
4. Otherwise, `~/.cache/maven-decoder-mcp/repository` under your home directory.

On Windows, this usually means `%LOCALAPPDATA%\maven-decoder-mcp\repository`;
`XDG_CACHE_HOME` still takes precedence if set. The cache uses Maven's directory
layout but stays separate from the real local repository so downloads do not
interfere with Maven builds. Setting `MAVEN_REPOSITORY` does not change the cache
location.

## 🔧 Configuration

### For Cursor IDE
Add to your `~/.cursor/mcp_servers.json`:

```json
{
  "maven-decoder": {
    "command": "uvx",
    "args": ["maven-decoder-mcp"]
  }
}
```

### For Other MCP Clients
The server runs as a standard MCP server and can be integrated with any MCP-compatible client.

## 🧠 AI Agent Skill

This repository includes a `maven-code-search` agent skill that tells AI coding agents when and how to use this MCP for searching installed Maven package code.

```bash
npx skills add https://github.com/salitaba/maven-decoder-mcp --skill maven-code-search
```

The skill is located at `skills/maven-code-search` and is ready for skills.sh indexing after the repository is pushed.

## 🛠️ Available Tools

### Local Analysis

| Tool | Description |
|------|-------------|
| `list_artifacts` | List artifacts in Maven repository with filtering |
| `analyze_jar` | Analyze jar file structure and contents |
| `extract_class_info` | Get detailed information about Java classes |
| `get_dependencies` | Retrieve Maven dependencies from POM files |
| `search_classes` | Search for classes across all jars, optionally filtered by annotation |
| `extract_source_code` | Decompile and extract Java source code |
| `extract_jar_resource` | Extract text resources such as `.proto` files, services, and metadata |
| `compare_versions` | Compare two versions, including a public API diff and breaking changes |
| `find_usage_examples` | Find classes that reference a given class or method |
| `get_dependency_tree` | Get complete dependency tree |
| `find_dependents` | Find artifacts that depend on a specific artifact |
| `get_version_info` | Get installed versions of an artifact (set `include_remote` to add published ones) |
| `analyze_jar_structure` | Analyze overall jar structure and metadata |
| `extract_method_info` | Extract specific method information from Java classes |

### Online (Maven Central)

| Tool | Description |
|------|-------------|
| `search_maven_central` | Search Maven Central for artifacts by name, coordinates, or contained class |
| `get_remote_versions` | List every version published remotely, flagging which are installed |
| `download_artifact` | Download an artifact (jar/sources/POM) into the local cache; accepts `latest` |

### Tool parameters
| Tool | Parameter | Type | Default | Description |
|------|-----------|------|---------|-------------|
| `list_artifacts` | `group_id` | string | — | Filter by group ID (e.g., 'org.springframework') |
| `list_artifacts` | `artifact_id` | string | — | Filter by artifact ID (e.g., 'spring-core') |
| `list_artifacts` | `version` | string | — | Filter by version (e.g., '5.3.21') |
| `list_artifacts` | `sort_by` | string | name | Order results by: 'name' (group/artifact/version ascending, default), 'size' (largest jars first), or 'modified' (most recently modified first). Unknown values fall back to 'name'. |
| `list_artifacts` | `limit` | integer | 50 | Maximum number of artifacts to return |
| `list_artifacts` | `page` | integer | 1 | Page number for pagination |
| `list_artifacts` | `items_per_page` | integer | 20 | Items per page |
| `analyze_jar` | `group_id`* | string | — | Maven group ID |
| `analyze_jar` | `artifact_id`* | string | — | Maven artifact ID |
| `analyze_jar` | `version`* | string | — | Maven version |
| `analyze_jar` | `include_bytecode` | boolean | False | Include bytecode analysis |
| `analyze_jar` | `include_manifest` | boolean | True | Include JAR manifest |
| `analyze_jar` | `summarize_large_content` | boolean | True | Summarize large content automatically |
| `extract_class_info` | `group_id`* | string | — | Maven group ID |
| `extract_class_info` | `artifact_id`* | string | — | Maven artifact ID |
| `extract_class_info` | `version`* | string | — | Maven version |
| `extract_class_info` | `class_pattern` | string | — | Pattern to match class names (regex supported) |
| `extract_class_info` | `include_methods` | boolean | True | Include method signatures |
| `extract_class_info` | `include_fields` | boolean | True | Include field information |
| `extract_class_info` | `include_bytecode` | boolean | False | Include verbose javap bytecode output for matched classes |
| `extract_class_info` | `page` | integer | 1 | Page number for pagination |
| `extract_class_info` | `items_per_page` | integer | 20 | Items per page |
| `extract_class_info` | `summarize_large_content` | boolean | True | Summarize large content automatically |
| `get_dependencies` | `group_id`* | string | — | Maven group ID |
| `get_dependencies` | `artifact_id`* | string | — | Maven artifact ID |
| `get_dependencies` | `version`* | string | — | Maven version |
| `get_dependencies` | `include_transitive` | boolean | False | Include transitive dependencies |
| `get_dependencies` | `page` | integer | 1 | Page number for pagination |
| `get_dependencies` | `items_per_page` | integer | 20 | Items per page |
| `search_classes` | `class_name` | string | — | Class name to search for (supports wildcards) |
| `search_classes` | `package_pattern` | string | — | Package pattern to filter by |
| `search_classes` | `annotation` | string | — | Search for classes with specific annotation |
| `search_classes` | `case_sensitive` | boolean | True | Match class_name and package_pattern case-sensitively. Set false for a case-insensitive search (e.g. 'arraylist' matches 'ArrayList'). |
| `search_classes` | `limit` | integer | 100 | Maximum results to return |
| `search_classes` | `page` | integer | 1 | Page number for pagination |
| `search_classes` | `items_per_page` | integer | 20 | Items per page |
| `extract_source_code` | `group_id`* | string | — | Maven group ID |
| `extract_source_code` | `artifact_id`* | string | — | Maven artifact ID |
| `extract_source_code` | `version`* | string | — | Maven version |
| `extract_source_code` | `class_name`* | string | — | Fully qualified class name |
| `extract_source_code` | `prefer_sources` | boolean | True | Prefer source jar over decompilation |
| `extract_source_code` | `summarize_large_content` | boolean | True | Summarize large content automatically |
| `extract_source_code` | `max_lines` | integer | 500 | Maximum lines to return (0 for all) |
| `extract_jar_resource` | `group_id`* | string | — | Maven group ID |
| `extract_jar_resource` | `artifact_id`* | string | — | Maven artifact ID |
| `extract_jar_resource` | `version`* | string | — | Maven version |
| `extract_jar_resource` | `resource_path` | string | — | Exact resource path inside the jar |
| `extract_jar_resource` | `resource_pattern` | string | — | Regex pattern to match resource paths |
| `extract_jar_resource` | `max_bytes` | integer | 65536 | Maximum bytes to read per resource |
| `extract_jar_resource` | `limit` | integer | 20 | Maximum matching resources to return |
| `compare_versions` | `group_id`* | string | — | Maven group ID |
| `compare_versions` | `artifact_id`* | string | — | Maven artifact ID |
| `compare_versions` | `version1`* | string | — | First (older) version to compare |
| `compare_versions` | `version2`* | string | — | Second (newer) version to compare |
| `compare_versions` | `compare_api` | boolean | True | Diff the public API: added/removed public and protected methods and fields, and breaking changes |
| `compare_versions` | `resolve_inherited` | boolean | False | Reclassify members that disappeared from a class but are still declared on a supertype within the new jar into a 'moved to supertype' bucket instead of counting them as breaking removals. Defaults to false (byte-identical to the as-declared diff). |
| `compare_versions` | `summarize_large_content` | boolean | True | Summarize large content automatically |
| `find_usage_examples` | `class_name`* | string | — | Class name to find usage for |
| `find_usage_examples` | `method_name` | string | — | Method name to find usage for |
| `find_usage_examples` | `search_tests` | boolean | True | Search in test jars |
| `find_usage_examples` | `limit` | integer | 50 | Maximum results to return |
| `find_usage_examples` | `page` | integer | 1 | Page number for pagination |
| `find_usage_examples` | `items_per_page` | integer | 20 | Items per page |
| `get_dependency_tree` | `group_id`* | string | — | Maven group ID |
| `get_dependency_tree` | `artifact_id`* | string | — | Maven artifact ID |
| `get_dependency_tree` | `version`* | string | — | Maven version |
| `get_dependency_tree` | `max_depth` | integer | 3 | Maximum depth to show |
| `get_dependency_tree` | `summarize_large_content` | boolean | True | Summarize large content automatically |
| `find_dependents` | `group_id`* | string | — | Target group ID |
| `find_dependents` | `artifact_id`* | string | — | Target artifact ID |
| `find_dependents` | `version` | string | — | Specific version to search for (optional) |
| `find_dependents` | `limit` | integer | 100 | Maximum results to return |
| `find_dependents` | `page` | integer | 1 | Page number for pagination |
| `find_dependents` | `items_per_page` | integer | 20 | Items per page |
| `get_version_info` | `group_id`* | string | — | Maven group ID |
| `get_version_info` | `artifact_id`* | string | — | Maven artifact ID |
| `get_version_info` | `include_remote` | boolean | False | Also list versions published on the remote repository (not just installed ones) |
| `get_version_info` | `limit` | integer | 50 | Maximum versions to return |
| `get_version_info` | `page` | integer | 1 | Page number for pagination |
| `get_version_info` | `items_per_page` | integer | 20 | Items per page |
| `analyze_jar_structure` | `group_id`* | string | — | Maven group ID |
| `analyze_jar_structure` | `artifact_id`* | string | — | Maven artifact ID |
| `analyze_jar_structure` | `version`* | string | — | Maven version |
| `analyze_jar_structure` | `summarize_large_content` | boolean | True | Summarize large content automatically |
| `extract_method_info` | `group_id`* | string | — | Maven group ID |
| `extract_method_info` | `artifact_id`* | string | — | Maven artifact ID |
| `extract_method_info` | `version`* | string | — | Maven version |
| `extract_method_info` | `class_name`* | string | — | Fully qualified class name |
| `extract_method_info` | `method_pattern` | string | — | Pattern to match method names (regex supported) |
| `extract_method_info` | `include_bytecode` | boolean | False | Include bytecode analysis |
| `extract_method_info` | `max_methods` | integer | 10 | Maximum number of methods to return |
| `search_maven_central` | `query` | string | — | Free-text search term (e.g. 'jackson databind') |
| `search_maven_central` | `group_id` | string | — | Exact group ID filter (e.g. 'org.springframework') |
| `search_maven_central` | `artifact_id` | string | — | Exact artifact ID filter (e.g. 'spring-core') |
| `search_maven_central` | `class_name` | string | — | Simple class name to find the containing artifact (e.g. 'ObjectMapper') |
| `search_maven_central` | `fully_qualified_class` | string | — | Fully qualified class name (e.g. 'com.fasterxml.jackson.databind.ObjectMapper') |
| `search_maven_central` | `packaging` | string | — | Packaging filter (e.g. 'jar', 'pom') |
| `search_maven_central` | `all_versions` | boolean | False | Return every published version instead of only the latest per artifact |
| `search_maven_central` | `limit` | integer | 20 | Maximum results to return (max 200) |
| `search_maven_central` | `page` | integer | 1 | Page number for pagination |
| `get_remote_versions` | `group_id`* | string | — | Maven group ID |
| `get_remote_versions` | `artifact_id`* | string | — | Maven artifact ID |
| `get_remote_versions` | `include_snapshots` | boolean | True | Include -SNAPSHOT versions. Set false to list only released versions. |
| `get_remote_versions` | `limit` | integer | 100 | Maximum versions to return |
| `download_artifact` | `group_id`* | string | — | Maven group ID |
| `download_artifact` | `artifact_id`* | string | — | Maven artifact ID |
| `download_artifact` | `version`* | string | — | Version to download, or 'latest' for the newest release |
| `download_artifact` | `include_sources` | boolean | True | Also download the sources jar when published |
| `download_artifact` | `include_javadoc` | boolean | False | Also download the javadoc jar when published |
| `download_artifact` | `classifier` | string | — | Download a specific classified jar instead of the main one |
| `download_artifact` | `force` | boolean | False | Re-download even when the file is already cached |

\* Required — the parameter appears in the tool's `inputSchema` `required` array. Parameters without a `*` are optional and may be omitted.

## 💡 Usage Examples

### Finding Dependencies
```
"Show me all dependencies of org.springframework:spring-core:5.3.21"
```

### Decompiling Classes
```
"Decompile the class com.example.MyService from my Maven repository"
```

### Analyzing Conflicts
```
"Find all version conflicts in my Maven repository"
```

### Checking an Upgrade for Breaking Changes
```
"Compare org.jsoup:jsoup 1.17.2 with 1.23.2 and tell me what would break"
```
`compare_versions` diffs the public and protected members of every class the
two versions share, and reports removals separately from additions. Removed
members and removed classes are counted as breaking changes. Members are
compared as *declared*, so one that moved to a supertype is reported as
removed even though it may still be callable.

### Exploring APIs
```
"Show me all public methods in the Jackson ObjectMapper class"
```

### Finding Real Callers
```
"Find classes that call ObjectMapper.readValue, including examples from test jars"
```
`find_usage_examples` scans compiled class constant pools, so it finds real callers
rather than simple name matches. Pass `method_name` (such as `readValue`) to narrow
the results to callers of a specific method. Test jars are included by default and
ranked first because they often contain the clearest examples; set `search_tests` to
`false` to exclude them. The scan stops after `MCP_USAGE_SCAN_LIMIT` classes (default:
200000) to stay responsive on large repositories.

### Inspecting Compiled-Only Artifacts
```
"The sources jar is missing. Use extract_class_info for bytecode-backed fields and methods."
"Find and read .proto resources from com.example:protobuf-lib:1.0.0"
```

When a dependency has no sources jar, `extract_class_info` uses `javap` internally and returns parsed fields, methods, bytecode version, and optional verbose bytecode output. Agents should use `analyze_jar`, `extract_class_info`, `extract_source_code`, and `extract_jar_resource` through this MCP instead of running `jar` or `javap` directly.

### Working with Large Responses
```
"List all Spring classes with pagination (page 2, 10 items per page)"
"Extract source code for a large class with summarization"
"Get method information for specific patterns in a class"
```

### Searching Maven Central (Online)
```
"Which Maven artifact contains the class HikariDataSource?"
"Search Maven Central for retrofit"
"What is the newest published version of org.apache.commons:commons-lang3?"
"Download com.google.code.gson:gson:latest and show me the JsonParser class"
```

## 🌐 Online Maven Support

The server works against the local repository **and** remote repositories. Online
access is enabled by default.

### How it works

1. Every tool first looks in your local repository (`~/.m2/repository`).
2. On a miss, the artifact is downloaded from Maven Central into a cache
   (`~/.cache/maven-decoder-mcp/repository`) that uses the standard Maven layout.
3. All existing analysis (decompilation, class info, dependencies) then runs on
   the cached artifact exactly as it would on an installed one.

The cache is deliberately **separate from `~/.m2`** so downloads never interfere
with your Maven or Gradle builds. Responses include an `origin` field
(`local-repository` or `remote-cache`) so you always know where a result came from.

### Going offline

```bash
MAVEN_OFFLINE=true   # no network access at all; original local-only behavior
MAVEN_AUTO_DOWNLOAD=false   # keep online search, but never auto-download
```

### Using a private mirror

```bash
MAVEN_REMOTE_REPOS="https://nexus.corp/repository/maven-public"
MAVEN_REMOTE_USERNAME=builder
MAVEN_REMOTE_PASSWORD=secret
```

### A note on the search index

Artifact **downloads** use `repo1.maven.org`, which is fast and reliable.
Artifact **search** uses `search.maven.org`, the only public index that answers
class-level (`c:` / `fc:`) queries correctly. That index rate-limits bursts, so
requests are retried with backoff; a busy period can still surface as a timeout.
Downloads and version listing are unaffected, because they read
`maven-metadata.xml` directly from the repository.

## 🔄 Response Management

### Pagination Support
The server automatically handles large responses through intelligent pagination:

- **Automatic Detection**: Responses exceeding 50KB are automatically paginated
- **Configurable Page Size**: Default 20 items per page, customizable per request
- **Pagination Metadata**: Each response includes pagination information
- **Supported Tools**: `list_artifacts`, `extract_class_info`, `search_classes`, `get_dependencies`, `find_dependents`, `get_version_info`

### Summarization Features
Large text content is automatically summarized to improve readability:

- **Smart Summarization**: Preserves important parts (package declarations, method signatures, closing braces)
- **Configurable Limits**: Default 10KB text limit, customizable
- **Java-Specific**: Optimized for Java source code structure
- **Metadata Preservation**: Original structure and metadata are maintained

### Method Extraction
New tool for targeted access to specific methods:

- **Pattern Matching**: Use regex patterns to find specific methods
- **Limited Results**: Control the number of methods returned
- **Full Context**: Includes method signatures, bodies, and line numbers
- **Efficient Processing**: Only extracts requested methods, not entire classes

## 🏗️ Architecture

The server is built with a modular architecture:

- **`MavenDecoderServer`**: Main MCP server implementation
- **`ResponseManager`**: Handles pagination and summarization
- **`JavaDecompiler`**: Handles multiple decompilation strategies
- **`MavenDependencyAnalyzer`**: Analyzes Maven dependencies and metadata
- **`MavenCentralClient`**: Remote search, version listing, and artifact downloads
- **Decompilers**: CFR, Procyon, Fernflower, and javap integration

## 🧪 Development

### Running Tests
```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run specific test
python test_startup.py
```

### Building Package
```bash
# Build distribution
python setup.py sdist bdist_wheel

# Install locally
pip install dist/maven_decoder_mcp-*.whl
```

### Docker Development
```bash
# Build Docker image
docker build -t maven-decoder-mcp .

# Run container
docker run --rm -it maven-decoder-mcp
```

## 📝 Configuration Options

### Environment Variables

#### Local repository
- `MAVEN_REPOSITORY` / `MAVEN_REPO`: direct path to local Maven repository (e.g. `F:\data\repository`). Highest precedence.
- `MAVEN_HOME` / `M2_HOME`: Maven install dir or repository dir. A nested `repository/` subdir wins when it exists; `conf/settings.xml` `<localRepository>` honored.
- `~/.m2/settings.xml` `<localRepository>` honored when no env var set. Fallback: `~/.m2/repository`.

#### Online access
- `MAVEN_OFFLINE`: set to `true` to disable all network access (default: `false`)
- `MAVEN_AUTO_DOWNLOAD`: auto-fetch artifacts missing locally (default: `true`)
- `MAVEN_REMOTE_REPOS` / `MAVEN_REMOTE_REPO`: comma/space separated repository base URLs (default: `https://repo1.maven.org/maven2`)
- `MAVEN_SEARCH_URL`: comma/space separated Solr search endpoints (default: `https://search.maven.org/solrsearch/select`)
- `MAVEN_DECODER_CACHE_DIR`: where downloaded artifacts are cached (default: `~/.cache/maven-decoder-mcp/repository`)
- `MAVEN_REMOTE_USERNAME` / `MAVEN_REMOTE_PASSWORD`: basic-auth credentials for a private mirror
- `MAVEN_HTTP_TIMEOUT`: per-request timeout in seconds (default: 30)
- `MAVEN_HTTP_RETRIES`: retries for transient network failures (default: 3)
- `MAVEN_MAX_DOWNLOAD_SIZE`: maximum download size in bytes (default: 104857600)
- `MAVEN_VERIFY_CHECKSUM`: verify downloads against published SHA-1 (default: `true`)

#### Responses
- `MCP_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `MCP_MAX_RESPONSE_SIZE`: Maximum response size in bytes (default: 50000)
- `MCP_MAX_ITEMS_PER_PAGE`: Default items per page (default: 20)
- `MCP_MAX_TEXT_LENGTH`: Maximum text length before summarization (default: 10000)
- `MCP_MAX_LINES`: Maximum lines before summarization (default: 500)
- `MCP_USAGE_SCAN_LIMIT`: Max classes scanned by `find_usage_examples` (default: 200000)
- `MCP_API_DIFF_LIMIT`: Max classes compared by `compare_versions` (default: 2000)
- `MAVEN_DECODER_DECOMPILER_DIR`: Directory holding `cfr.jar` / `procyon-decompiler.jar`

### Advanced Configuration
The server automatically detects and configures:
- Maven repository location
- Available Java decompilers
- System capabilities

## 🔍 Troubleshooting

### Common Issues

**Server won't start**
```bash
# Check Python installation
python --version

# Check Maven repository
ls ~/.m2/repository

# Check logs
maven-decoder-mcp --debug
```



**Decompilation fails**
```bash
# Check the environment: Java, repository, cache and available decompilers
maven-decoder-setup status

# Install the optional CFR and Procyon decompilers
maven-decoder-setup decompilers
```
Without CFR or Procyon the server still works, falling back to `javap` from
the JDK for signatures, fields and methods.

**No artifacts found**
```bash
# Verify Maven repository location
ls ~/.m2/repository

# Run a Maven build to populate repository
mvn dependency:resolve
```

**Maven Central search times out**

The public search index rate-limits bursts of requests. Retries with backoff are
built in, but during heavy throttling a search can still fail. Workarounds:

```bash
# Wait a moment and retry, or raise the retry budget
MAVEN_HTTP_RETRIES=5

# Downloads and version listing do not use the search index, so these keep
# working even while search is throttled:
#   get_remote_versions, download_artifact
```

**Downloads fail behind a proxy or firewall**
```bash
# requests honors the standard proxy variables
export HTTPS_PROXY=http://proxy.corp:8080

# Or point at an internal mirror
export MAVEN_REMOTE_REPOS="https://nexus.corp/repository/maven-public"

# Or turn the network off entirely
export MAVEN_OFFLINE=true
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Model Context Protocol](https://github.com/modelcontextprotocol) - The protocol that powers this server
- [CFR](https://github.com/leibnitz27/cfr) - Java decompiler
- [Procyon](https://github.com/mstrobel/procyon) - Java decompiler
- [Maven](https://maven.apache.org/) - Dependency management

## 📊 Stats

![GitHub Stars](https://img.shields.io/github/stars/salitaba/maven-decoder-mcp)
![GitHub Forks](https://img.shields.io/github/forks/salitaba/maven-decoder-mcp)
![PyPI Downloads](https://img.shields.io/pypi/dm/maven-decoder-mcp)
![npm Downloads](https://img.shields.io/npm/dm/maven-decoder-mcp)
![Docker Pulls](https://img.shields.io/docker/pulls/ali79taba/maven-decoder-mcp)

---

**Made with ❤️ for the Java development community**
