# Maven Decoder MCP Server - Distribution Guide

This document outlines how the Maven Decoder MCP Server is packaged and distributed for easy installation by developers.

## 🎯 Distribution Methods

### 1. Python Package (PyPI) - **Recommended**
**Installation**: `pip install maven-decoder-mcp`

- **Files**: `dist/maven_decoder_mcp-1.0.0-py3-none-any.whl`, `dist/maven-decoder-mcp-1.0.0.tar.gz`
- **Benefits**: Standard Python packaging, automatic dependency management
- **Target Users**: Python developers, data scientists, most users

### 2. Node.js Package (npm)
**Installation**: `npm install -g maven-decoder-mcp`

- **Files**: `maven-decoder-mcp-1.0.0.tgz`
- **Benefits**: Easy for Node.js developers, automatic Python setup
- **Target Users**: JavaScript/TypeScript developers, full-stack developers

### 3. Docker Container
**Installation**: `docker run maven-decoder/mcp-server:latest`

- **Benefits**: No local dependencies, consistent environment
- **Target Users**: DevOps teams, containerized environments

### 4. One-Line Install Script
**Installation**: `curl -fsSL https://raw.githubusercontent.com/.../install.sh | bash`

- **File**: `install.sh`
- **Benefits**: Auto-detects best method, works everywhere
- **Target Users**: All users who want simplicity

## 📦 Package Contents

### Python Package Structure
```
src/maven_decoder_mcp/
├── __init__.py                 # Package entry point
├── maven_decoder_server.py     # Main MCP server
├── decompiler.py              # Java decompilation
├── dependency_analyzer.py     # Maven analysis  
├── decompilers/               # Bundled decompilers
│   ├── cfr.jar               # CFR decompiler
│   └── procyon-decompiler.jar # Procyon decompiler
└── setup.py                  # Setup utilities
```

### Console Scripts
- `maven-decoder-mcp` - Start the MCP server
- `maven-decoder-setup` - Setup decompilers and configuration

### Included Dependencies
- **CFR 0.152** - Java decompiler
- **Procyon 0.6.0** - Java decompiler  
- **MCP SDK** - Model Context Protocol implementation

## 🚀 Installation Workflows

### For End Users

#### Simplest (Recommended)
```bash
curl -fsSL https://raw.githubusercontent.com/salitaba/maven-decoder-mcp/main/install.sh | bash
```

#### Python Users
```bash
pip install maven-decoder-mcp
maven-decoder-mcp
```

#### Node.js Users  
```bash
npm install -g maven-decoder-mcp
maven-decoder-mcp
```

#### Docker Users
```bash
docker run --rm -it \
  -v ~/.m2:/home/mcpuser/.m2 \
  maven-decoder/mcp-server:latest
```

### For Cursor IDE Integration
Add to `~/.cursor/mcp_servers.json`:
```json
{
  "maven-decoder": {
    "command": "maven-decoder-mcp",
    "args": []
  }
}
```

## 🔧 Build Process

### Local Development Build
```bash
# Clone and setup
git clone https://github.com/salitaba/maven-decoder-mcp.git
cd maven-decoder-mcp

# Build all packages
python scripts/release.py
```

### Automated Release (GitHub Actions)
- **Trigger**: Push tag `v*` (e.g., `v1.0.0`)
- **Builds**: Python wheel, npm package, Docker image
- **Publishes**: PyPI, npm registry, Docker Hub, GitHub Releases

## 📋 Requirements by Method

### Python/pip Installation
- Python 3.8+
- Java 8+ (for decompilation)
- Maven repository (~/.m2/repository)

### npm Installation  
- Node.js 14+
- Python 3.8+ (auto-installed if missing)
- Java 8+ (for decompilation)
- Maven repository (~/.m2/repository)

### Docker Installation
- Docker
- Maven repository (mounted as volume)

## 🎯 Target Platforms

### Supported Operating Systems
- **Linux** (Ubuntu, CentOS, Alpine, etc.)
- **macOS** (Intel and Apple Silicon)
- **Windows** (WSL recommended)

### Supported Architectures  
- **x86_64 (AMD64)** - Primary
- **ARM64** - Docker images only

## 📊 Distribution Stats

Once published, track adoption via:
- **PyPI Downloads**: `pip download` statistics
- **npm Downloads**: npm registry analytics  
- **Docker Pulls**: Docker Hub pull counts
- **GitHub**: Stars, forks, releases downloads

## 🔒 Security & Verification

### Package Integrity
- **Checksums**: SHA256 hashes provided for all packages
- **Signatures**: GPG signatures for release assets
- **Reproducible**: All builds are reproducible

### Verification Commands
```bash
# Verify Python package
pip download maven-decoder-mcp --no-deps
sha256sum maven_decoder_mcp-*.whl

# Verify npm package  
npm pack maven-decoder-mcp
sha256sum maven-decoder-mcp-*.tgz

# Verify Docker image
docker pull maven-decoder/mcp-server:latest
docker inspect maven-decoder/mcp-server:latest
```

## 🚀 Release Checklist

- [ ] Update version in `pyproject.toml` and `package.json`
- [ ] Update `CHANGELOG.md` with new features
- [ ] Test all installation methods locally
- [ ] Create release tag: `git tag v1.0.0 && git push origin v1.0.0`
- [ ] Monitor automated release workflow
- [ ] Verify packages on PyPI, npm, Docker Hub
- [ ] Update documentation with new version
- [ ] Announce release in community channels

## 🎉 Success Metrics

A successful distribution achieves:
- **Easy Installation**: One command install for all platforms
- **No Dependencies**: Everything needed is included or auto-installed
- **Universal Compatibility**: Works on all major platforms
- **Fast Setup**: From install to working in under 2 minutes
- **Great Documentation**: Clear instructions for all skill levels

---

**The goal**: Any developer should be able to install and use Maven Decoder MCP Server in less than 2 minutes, regardless of their platform or preferred package manager.**
