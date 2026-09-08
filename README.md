# Maven Decoder MCP Server

[![skills.sh](https://skills.sh/b/salitaba/maven-decoder-mcp)](https://skills.sh/salitaba/maven-decoder-mcp)

A comprehensive Model Context Protocol (MCP) server for analyzing Maven jar files, both in your local repository (`~/.m2`) and **online on Maven Central**. This server provides powerful tools for agentic coding assistance in Java projects, enabling AI agents to understand dependencies, analyze bytecode, extract source code, and navigate the Maven ecosystem.

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
| `compare_versions` | Compare different versions of artifacts |
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

### Exploring APIs
```
"Show me all public methods in the Jackson ObjectMapper class"
```

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
![PyPI Downloads](https://img.shields.io/pypi/dm/maven-decoder-mcp)
![Docker Pulls](https://img.shields.io/docker/pulls/ali79taba/maven-decoder-mcp)

---

**Made with ❤️ for the Java development community**
