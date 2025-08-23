#!/usr/bin/env python3
"""
Release preparation script for Maven Decoder MCP
Automates the release process including building packages, Docker images, and creating release assets
"""

import subprocess
import sys
import os
import json
import shutil
from pathlib import Path

def run_command(cmd, check=True, cwd=None):
    """Run a command and return the result"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd, check=check)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result

def check_prerequisites():
    """Check if all prerequisites are available"""
    print("🔍 Checking prerequisites...")
    
    # Check Python
    try:
        run_command("python --version")
    except:
        print("❌ Python not found")
        return False
    
    # Check Java
    try:
        run_command("java -version")
    except:
        print("❌ Java not found")
        return False
    
    # Check Node.js (optional)
    try:
        run_command("node --version")
        nodejs_available = True
    except:
        print("⚠️  Node.js not found - npm package will be skipped")
        nodejs_available = False
    
    # Check Docker (optional)
    try:
        run_command("docker --version")
        docker_available = True
    except:
        print("⚠️  Docker not found - Docker image will be skipped")
        docker_available = False
    
    print("✅ Prerequisites check complete")
    return True, nodejs_available, docker_available

def build_python_package():
    """Build Python package"""
    print("📦 Building Python package...")
    
    # Clean previous builds
    shutil.rmtree("build", ignore_errors=True)
    shutil.rmtree("dist", ignore_errors=True)
    shutil.rmtree("src/maven_decoder_mcp.egg-info", ignore_errors=True)
    
    # Build package
    run_command("python setup.py sdist bdist_wheel")
    
    print("✅ Python package built successfully")
    return True

def build_npm_package():
    """Build npm package"""
    print("📦 Building npm package...")
    
    # Create npm package
    run_command("npm pack")
    
    print("✅ npm package built successfully")
    return True

def build_docker_image():
    """Build Docker image"""
    print("🐳 Building Docker image...")
    
    # Build image
    run_command("docker build -t maven-decoder/mcp-server:latest .")
    run_command("docker build -t maven-decoder/mcp-server:1.0.0 .")
    
    # Create image archive
    run_command("docker save YOUR_USERNAME/mcp-server:latest | gzip > maven-decoder-mcp-docker.tar.gz")
    
    print("✅ Docker image built successfully")
    return True

def create_release_notes():
    """Create release notes"""
    print("📝 Creating release notes...")
    
    notes = """# Maven Decoder MCP Server v1.0.0

## 🎉 First Release!

This is the initial release of Maven Decoder MCP Server - a comprehensive MCP server for analyzing Maven jar files.

### Features
- 🔍 Comprehensive jar file analysis
- 🛠️ Advanced decompilation with multiple decompilers (CFR, Procyon, javap)
- 📦 Complete Maven integration and dependency analysis  
- 🔗 Cross-reference analysis and usage examples
- 🚀 Multiple installation methods (pip, npm, Docker)
- 🎯 12 powerful tools for Maven repository analysis

### Installation Methods

#### Quick Install
```bash
curl -fsSL https://raw.githubusercontent.com/salitaba/maven-decoder-mcp/main/install.sh | bash
```

#### Python/pip
```bash
pip install maven-decoder-mcp
```

#### Node.js/npm  
```bash
npm install -g maven-decoder-mcp
```

#### Docker
```bash
docker run --rm -it \\
  -v ~/.m2:/home/mcpuser/.m2 \\
  maven-decoder/mcp-server:latest
```

### What's Included
- Python wheel and source distribution
- npm package for Node.js integration
- Docker image for containerized deployment
- Comprehensive documentation
- Installation scripts for all platforms

### Requirements
- Java 8+ (for decompilation)
- Maven repository (~/.m2/repository)
- Python 3.8+ OR Node.js 14+ OR Docker

### Getting Started
1. Install using your preferred method above
2. Configure your IDE (e.g., Cursor) to use the MCP server
3. Start analyzing your Maven projects!

For full documentation, see the [README](README.md).
"""
    
    with open("RELEASE_NOTES.md", "w") as f:
        f.write(notes)
    
    print("✅ Release notes created")
    return True

def create_checksums():
    """Create checksums for release files"""
    print("🔐 Creating checksums...")
    
    files_to_hash = []
    
    # Find distribution files
    dist_dir = Path("dist")
    if dist_dir.exists():
        files_to_hash.extend(dist_dir.glob("*.whl"))
        files_to_hash.extend(dist_dir.glob("*.tar.gz"))
    
    # Find npm package
    npm_packages = list(Path(".").glob("maven-decoder-mcp-*.tgz"))
    files_to_hash.extend(npm_packages)
    
    # Find Docker archive
    docker_archive = Path("maven-decoder-mcp-docker.tar.gz")
    if docker_archive.exists():
        files_to_hash.append(docker_archive)
    
    # Create checksums
    with open("CHECKSUMS.txt", "w") as f:
        f.write("# Maven Decoder MCP Server v1.0.0 - File Checksums\\n")
        f.write("# Verify with: sha256sum -c CHECKSUMS.txt\\n\\n")
        
        for file_path in files_to_hash:
            if file_path.exists():
                result = run_command(f"sha256sum {file_path}")
                f.write(result.stdout)
    
    print("✅ Checksums created")
    return True

def print_release_summary():
    """Print release summary"""
    print("\\n" + "="*60)
    print("🎉 RELEASE PREPARATION COMPLETE!")
    print("="*60)
    
    print("\\n📦 Built Packages:")
    
    # Python packages
    dist_files = list(Path("dist").glob("*")) if Path("dist").exists() else []
    for f in dist_files:
        print(f"  📄 {f}")
    
    # npm packages
    npm_files = list(Path(".").glob("maven-decoder-mcp-*.tgz"))
    for f in npm_files:
        print(f"  📄 {f}")
    
    # Docker
    if Path("maven-decoder-mcp-docker.tar.gz").exists():
        print(f"  🐳 maven-decoder-mcp-docker.tar.gz")
    
    print("\\n📋 Documentation:")
    print("  📖 README.md")
    print("  📝 RELEASE_NOTES.md") 
    print("  🔐 CHECKSUMS.txt")
    
    print("\\n🚀 Next Steps:")
    print("  1. Test the packages in clean environments")
    print("  2. Upload to PyPI: twine upload dist/*")
    print("  3. Publish to npm: npm publish")
    print("  4. Push Docker image: docker push maven-decoder/mcp-server:latest")
    print("  5. Create GitHub release with assets")
    print("  6. Update documentation and announce!")
    
    print("\\n🎯 Installation Commands for Users:")
    print("  pip install maven-decoder-mcp")
    print("  npm install -g maven-decoder-mcp")
    print("  docker pull maven-decoder/mcp-server:latest")

def main():
    """Main release preparation function"""
    print("🏗️  Maven Decoder MCP Server - Release Preparation")
    print("="*60)
    
    # Check prerequisites
    prereq_result = check_prerequisites()
    if not prereq_result[0]:
        print("❌ Prerequisites check failed")
        sys.exit(1)
    
    nodejs_available = prereq_result[1] if len(prereq_result) > 1 else False
    docker_available = prereq_result[2] if len(prereq_result) > 2 else False
    
    try:
        # Build Python package
        build_python_package()
        
        # Build npm package if Node.js is available
        if nodejs_available:
            build_npm_package()
        
        # Build Docker image if Docker is available  
        if docker_available:
            build_docker_image()
        
        # Create documentation
        create_release_notes()
        create_checksums()
        
        # Print summary
        print_release_summary()
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Release preparation failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
