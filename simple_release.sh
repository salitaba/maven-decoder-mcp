#!/bin/bash

# Simple Release Script for Maven Decoder MCP Server
# This script guides you through releasing your MCP server step by step

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

ask_yes_no() {
    while true; do
        read -p "$1 (y/n): " yn
        case $yn in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) echo "Please answer yes or no.";;
        esac
    done
}

echo "🚀 Maven Decoder MCP Server - Simple Release Guide"
echo "=================================================="
echo ""

# Check if packages exist
if [ ! -d "dist" ] || [ -z "$(ls -A dist)" ]; then
    print_error "No packages found in dist/ directory"
    echo "Run this first: python setup.py sdist bdist_wheel"
    exit 1
fi

print_success "Found built packages:"
ls -la dist/

echo ""
print_step "What would you like to do?"
echo "1. Release to PyPI (Python users can 'pip install')"
echo "2. Release to npm (Node.js users can 'npm install')"  
echo "3. Create GitHub repository and release"
echo "4. All of the above (full release)"
echo "5. Just show me what I have (no release)"

read -p "Choose option (1-5): " choice

case $choice in
    1)
        echo ""
        print_step "Releasing to PyPI..."
        
        if ! command -v twine &> /dev/null; then
            print_warning "Installing twine (PyPI upload tool)..."
            pip install twine
        fi
        
        echo ""
        print_warning "You need a PyPI account and API token:"
        echo "1. Go to https://pypi.org and create account"
        echo "2. Go to Account Settings → API tokens → Add API token"
        echo "3. Copy the token (starts with 'pypi-')"
        echo ""
        
        if ask_yes_no "Do you have a PyPI account and token ready?"; then
            print_step "Uploading to PyPI..."
            twine upload dist/*
            print_success "Uploaded to PyPI! Users can now run: pip install maven-decoder-mcp"
        else
            print_warning "Skipping PyPI upload. Create account at https://pypi.org first."
        fi
        ;;
    
    2)
        echo ""
        print_step "Releasing to npm..."
        
        if ! command -v npm &> /dev/null; then
            print_error "npm not found. Please install Node.js first."
            exit 1
        fi
        
        # Build npm package if not exists
        if [ ! -f "maven-decoder-mcp-1.0.0.tgz" ]; then
            print_step "Building npm package..."
            npm pack
        fi
        
        echo ""
        print_warning "You need an npm account:"
        echo "1. Go to https://npmjs.com and create account"
        echo "2. Run 'npm login' to login"
        echo ""
        
        if ask_yes_no "Do you have an npm account and are logged in?"; then
            print_step "Publishing to npm..."
            npm publish maven-decoder-mcp-*.tgz
            print_success "Published to npm! Users can now run: npm install -g maven-decoder-mcp"
        else
            print_warning "Skipping npm publish. Create account at https://npmjs.com and run 'npm login' first."
        fi
        ;;
    
    3)
        echo ""
        print_step "Setting up GitHub repository..."
        
        if [ ! -d ".git" ]; then
            print_step "Initializing git repository..."
            git init
            git add .
            git commit -m "Initial release v1.0.0"
        fi
        
        echo ""
        print_warning "You need to create a GitHub repository:"
        echo "1. Go to https://github.com and create a new repository"
        echo "2. Copy the repository URL (e.g., https://github.com/username/maven-decoder-mcp.git)"
        echo ""
        
        read -p "Enter your GitHub repository URL: " repo_url
        
        if [ -n "$repo_url" ]; then
            print_step "Setting up remote and pushing..."
            git remote add origin "$repo_url" 2>/dev/null || git remote set-url origin "$repo_url"
            git push -u origin main
            
            print_step "Creating release tag..."
            git tag v1.0.0
            git push origin v1.0.0
            
            print_success "Code pushed to GitHub!"
            echo ""
            print_step "Now create a GitHub release:"
            echo "1. Go to your repository on GitHub"
            echo "2. Click 'Releases' → 'Create a new release'"
            echo "3. Tag: v1.0.0"
            echo "4. Upload files from dist/ folder"
            echo "5. Publish release"
        else
            print_warning "Skipping GitHub setup."
        fi
        ;;
    
    4)
        echo ""
        print_step "Full release process..."
        
        # Run all the above steps
        print_warning "This will release to PyPI, npm, and GitHub."
        print_warning "Make sure you have accounts on all platforms!"
        
        if ask_yes_no "Continue with full release?"; then
            # Run steps 1, 2, 3
            ./simple_release.sh # This will cause recursion, let's avoid it
            print_error "Full release not implemented yet. Run steps 1-3 individually."
        else
            print_warning "Full release cancelled."
        fi
        ;;
    
    5)
        echo ""
        print_step "Current status:"
        echo ""
        print_success "Built packages:"
        ls -la dist/
        
        if [ -f "maven-decoder-mcp-1.0.0.tgz" ]; then
            print_success "npm package: maven-decoder-mcp-1.0.0.tgz"
        else
            print_warning "npm package not built. Run: npm pack"
        fi
        
        if [ -d ".git" ]; then
            print_success "Git repository initialized"
        else
            print_warning "Git repository not initialized. Run: git init"
        fi
        
        echo ""
        print_step "Next steps:"
        echo "1. Create accounts on PyPI (pypi.org), npm (npmjs.com), GitHub (github.com)"
        echo "2. Run this script again and choose release options"
        echo "3. Users will be able to install with:"
        echo "   - pip install maven-decoder-mcp"
        echo "   - npm install -g maven-decoder-mcp"
        ;;
    
    *)
        print_error "Invalid option. Please choose 1-5."
        exit 1
        ;;
esac

echo ""
print_success "Release process complete! 🎉"

if [ "$choice" != "5" ]; then
    echo ""
    print_step "What users can do now:"
    echo "- Install with pip: pip install maven-decoder-mcp"
    echo "- Install with npm: npm install -g maven-decoder-mcp"
    echo "- Use in Cursor IDE by adding to ~/.cursor/mcp_servers.json:"
    echo '  {"maven-decoder": {"command": "maven-decoder-mcp", "args": []}}'
fi
