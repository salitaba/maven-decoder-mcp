# 🚀 How to Release Maven Decoder MCP Server

This guide walks you through releasing your MCP server so developers can easily install it.

## 📋 Quick Overview

We've prepared **4 ways** for people to install your server:
1. **pip install maven-decoder-mcp** (Python users)
2. **npm install -g maven-decoder-mcp** (Node.js users)  
3. **docker run maven-decoder/mcp-server** (Docker users)
4. **One-line install script** (everyone else)

## 🎯 Option A: Manual Release (Easiest to Start)

### Step 1: Create GitHub Repository
```bash
# In your project directory
git init
git add .
git commit -m "Initial release v1.0.0"

# Create repository on GitHub, then:
git remote add origin https://github.com/salitaba/maven-decoder-mcp.git
git push -u origin main
```

### Step 2: Publish to PyPI (Python Package)
```bash
# Install publishing tools
pip install twine

# Upload to PyPI (you'll need a PyPI account)
twine upload dist/*
```
**Result**: People can now run `pip install maven-decoder-mcp`

### Step 3: Publish to npm (Node.js Package) 
```bash
# Build npm package
npm pack

# Publish (you'll need an npm account)
npm publish maven-decoder-mcp-1.0.0.tgz
```
**Result**: People can now run `npm install -g maven-decoder-mcp`

### Step 4: Create GitHub Release
1. Go to your GitHub repository
2. Click "Releases" → "Create a new release"
3. Tag: `v1.0.0`
4. Upload files from `dist/` folder
5. Publish release

**Result**: People can download and install manually

## 🤖 Option B: Automated Release (Professional)

### Step 1: Setup Repository (same as above)
```bash
git init
git add .
git commit -m "Initial release v1.0.0"
git remote add origin https://github.com/salitaba/maven-decoder-mcp.git
git push -u origin main
```

### Step 2: Add Secrets to GitHub
1. Go to your repository → Settings → Secrets and variables → Actions
2. Add these secrets:
   - `PYPI_API_TOKEN`: Get from pypi.org → Account settings → API tokens
   - `NPM_TOKEN`: Get from npmjs.com → Access Tokens
   - `DOCKER_USERNAME`: Your Docker Hub username
   - `DOCKER_PASSWORD`: Your Docker Hub password

### Step 3: Create Release Tag
```bash
git tag v1.0.0
git push origin v1.0.0
```

**Result**: GitHub Actions automatically:
- ✅ Builds all packages
- ✅ Publishes to PyPI, npm, Docker Hub
- ✅ Creates GitHub release

## 📦 What Users Will Be Able to Do

After release, developers can install your server with:

### Python Users
```bash
pip install maven-decoder-mcp
maven-decoder-mcp
```

### Node.js Users
```bash
npm install -g maven-decoder-mcp
maven-decoder-mcp
```

### Docker Users
```bash
docker run --rm -it \
  -v ~/.m2:/home/mcpuser/.m2 \
  maven-decoder/mcp-server:latest
```

### Everyone Else
```bash
curl -fsSL https://raw.githubusercontent.com/salitaba/maven-decoder-mcp/main/install.sh | bash
```

## 🔍 Step-by-Step: First Time Release

### 1. Create Accounts (if you don't have them)
- **GitHub**: github.com (for code hosting)
- **PyPI**: pypi.org (for Python packages)
- **npm**: npmjs.com (for Node.js packages)
- **Docker Hub**: hub.docker.com (for Docker images)

### 2. Test Everything Works
```bash
# Test the built package locally
pip install dist/maven_decoder_mcp-1.0.0-py3-none-any.whl
maven-decoder-mcp --help
```

### 3. Upload to PyPI
```bash
# Create PyPI account at pypi.org
# Get API token from Account Settings → API tokens

# Install upload tool
pip install twine

# Upload (will ask for username and password/token)
twine upload dist/*
```

### 4. Upload to npm
```bash
# Create npm account at npmjs.com
# Login to npm
npm login

# Publish package
npm publish maven-decoder-mcp-1.0.0.tgz
```

### 5. Create GitHub Release
1. Push your code to GitHub
2. Go to repository → Releases → "Create a new release"
3. Tag version: `v1.0.0`
4. Release title: `Maven Decoder MCP Server v1.0.0`
5. Upload files from `dist/` folder
6. Click "Publish release"

## ✅ Verification

After release, verify everything works:

```bash
# Test Python install
pip install maven-decoder-mcp
maven-decoder-mcp

# Test npm install  
npm install -g maven-decoder-mcp
maven-decoder-mcp

# Check GitHub release page has files
```

## 🆘 If You Get Stuck

### Common Issues:

**"Package already exists on PyPI"**
- Update version in `pyproject.toml` (e.g., `1.0.1`)
- Rebuild: `python setup.py sdist bdist_wheel`
- Upload again

**"npm publish fails"**
- Update version in `package.json`
- Run `npm pack` again
- Publish the new `.tgz` file

**"Don't want to deal with accounts"**
- Just push to GitHub
- People can install from source:
  ```bash
  pip install git+https://github.com/salitaba/maven-decoder-mcp.git
  ```

## 🎉 Success!

Once released, your users can install with just:
```bash
pip install maven-decoder-mcp
```

And start using it immediately in their IDEs like Cursor!

---

**Need help?** The packages are already built and ready to upload. You just need to create the accounts and run the upload commands above.
