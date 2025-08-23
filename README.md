# Maven Decoder MCP Server

A comprehensive Model Context Protocol (MCP) server for analyzing Maven jar files in your local repository (`~/.m2`). This server provides powerful tools for agentic coding assistance in Java projects, enabling AI agents to understand dependencies, analyze bytecode, extract source code, and navigate the Maven ecosystem.

## 🚀 Features

### Core Functionality
- **Jar File Analysis**: Deep inspection of jar files including metadata, manifests, and structure
- **Dependency Resolution**: Complete dependency tree analysis with transitive dependencies
- **Source Code Extraction**: Extract source code from source jars or decompile bytecode
- **Class Information**: Detailed class signatures, methods, fields, and annotations
- **Search Capabilities**: Find classes, methods, and dependencies across all artifacts
- **Version Management**: Compare versions, find dependents, and track version conflicts

### Advanced Features
- **Decompilation Support**: Integrated support for multiple Java decompilers (CFR, Fernflower, Procyon)
- **Conflict Analysis**: Detect and analyze dependency version conflicts
- **Repository Navigation**: Browse and explore the local Maven repository structure
- **Metadata Parsing**: Extract and parse Maven POM files and metadata
- **Service Discovery**: Find and analyze Java services and SPI implementations

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

#### Method 1: Python/pip (Recommended)
```bash
# Install the package
pip install maven-decoder-mcp

# Install MCP SDK
pip install "git+https://github.com/modelcontextprotocol/python-sdk.git"

# Run the server
maven-decoder-mcp
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
  maven-decoder/mcp-server:latest
```

#### Method 4: From Source (Development)
```bash
# Clone repository
git clone https://github.com/salitaba/maven-decoder-mcp.git
cd maven-decoder-mcp

# Option 4a: Using Virtual Environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install "git+https://github.com/modelcontextprotocol/python-sdk.git"
./setup_decompilers.sh

# Option 4b: System-wide Installation
pip3 install -r requirements.txt
pip3 install "git+https://github.com/modelcontextprotocol/python-sdk.git"
./setup_decompilers.sh
```

## 🔧 Configuration

### For Cursor IDE
Add to your `~/.cursor/mcp_servers.json`:

```json
{
  "maven-decoder": {
    "command": "maven-decoder-mcp",
    "args": []
  }
}
```

### For Other MCP Clients
The server runs as a standard MCP server and can be integrated with any MCP-compatible client.

## 🛠️ Available Tools

| Tool | Description |
|------|-------------|
| `list_artifacts` | List artifacts in Maven repository with filtering |
| `analyze_jar` | Analyze jar file structure and contents |
| `extract_class_info` | Get detailed information about Java classes |
| `get_dependencies` | Retrieve Maven dependencies from POM files |
| `search_classes` | Search for classes across all jars |
| `extract_source_code` | Decompile and extract Java source code |
| `compare_versions` | Compare different versions of artifacts |
| `find_usage_examples` | Find usage examples in test code |
| `get_dependency_tree` | Get complete dependency tree |
| `find_dependents` | Find artifacts that depend on a specific artifact |
| `get_version_info` | Get all available versions of an artifact |
| `analyze_jar_structure` | Analyze overall jar structure and metadata |

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

## 🏗️ Architecture

The server is built with a modular architecture:

- **`MavenDecoderServer`**: Main MCP server implementation
- **`JavaDecompiler`**: Handles multiple decompilation strategies
- **`MavenDependencyAnalyzer`**: Analyzes Maven dependencies and metadata
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
- `MAVEN_HOME`: Custom Maven repository location (default: `~/.m2/repository`)
- `MCP_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

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
# Check Java installation
java -version

# Setup decompilers manually
maven-decoder-setup decompilers
```

**No artifacts found**
```bash
# Verify Maven repository location
ls ~/.m2/repository

# Run a Maven build to populate repository
mvn dependency:resolve
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
![Docker Pulls](https://img.shields.io/docker/pulls/salitaba/mcp-server)

---

**Made with ❤️ for the Java development community**