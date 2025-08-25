#!/bin/bash

# Maven Decoder MCP Server - Easy Installation Script
# Supports multiple installation methods

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
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

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Show banner
show_banner() {
    echo "================================================="
    echo "   Maven Decoder MCP Server - Easy Install"
    echo "================================================="
    echo ""
}

# Show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --method=METHOD    Installation method (pip|uvx|npm|docker|auto)"
    echo "  --python=PATH      Path to Python executable"
    echo "  --global           Install globally (for pip/npm)"
    echo "  --help             Show this help message"
    echo ""
    echo "Methods:"
    echo "  uvx      Install via uvx (recommended, handles PEP 668 environments)"
    echo "  pip      Install via Python pip"
    echo "  npm      Install via Node.js npm"
    echo "  docker   Run via Docker container"
    echo "  auto     Auto-detect best method (default)"
}

# Parse command line arguments
METHOD="auto"
PYTHON_CMD=""
GLOBAL_INSTALL=""

for arg in "$@"; do
    case $arg in
        --method=*)
            METHOD="${arg#*=}"
            shift
            ;;
        --python=*)
            PYTHON_CMD="${arg#*=}"
            shift
            ;;
        --global)
            GLOBAL_INSTALL="--global"
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $arg"
            show_usage
            exit 1
            ;;
    esac
done

# Find Python
find_python() {
    if [ -n "$PYTHON_CMD" ]; then
        if command_exists "$PYTHON_CMD"; then
            echo "$PYTHON_CMD"
            return 0
        else
            print_error "Specified Python command not found: $PYTHON_CMD"
            exit 1
        fi
    fi
    
    for cmd in python3 python; do
        if command_exists "$cmd"; then
            echo "$cmd"
            return 0
        fi
    done
    
    return 1
}

# Install via pip
install_pip() {
    print_status "Installing Maven Decoder MCP via pip..."
    
    local python_cmd
    if ! python_cmd=$(find_python); then
        print_error "Python not found. Please install Python 3.8+ first."
        exit 1
    fi
    
    print_status "Using Python: $python_cmd"
    
    # Check Python version
    local python_version
    python_version=$($python_cmd --version 2>&1 | cut -d' ' -f2)
    print_status "Python version: $python_version"
    
    # Try pip installation first
    if [ "$GLOBAL_INSTALL" = "--global" ]; then
        print_status "Installing globally..."
        if ! $python_cmd -m pip install maven-decoder-mcp 2>&1; then
            print_warning "Pip installation failed (likely PEP 668 externally-managed-environment)"
            print_status "Falling back to uvx installation..."
            METHOD="uvx"
            install_uvx
            return
        fi
    else
        print_status "Installing for current user..."
        if ! $python_cmd -m pip install --user maven-decoder-mcp 2>&1; then
            print_warning "Pip installation failed (likely PEP 668 externally-managed-environment)"
            print_status "Falling back to uvx installation..."
            METHOD="uvx"
            install_uvx
            return
        fi
    fi
    
    # Install MCP SDK
    print_status "Installing MCP SDK..."
    if [ "$GLOBAL_INSTALL" = "--global" ]; then
        $python_cmd -m pip install "git+https://github.com/modelcontextprotocol/python-sdk.git"
    else
        $python_cmd -m pip install --user "git+https://github.com/modelcontextprotocol/python-sdk.git"
    fi
    
    print_success "Pip installation complete!"
    print_status "You can now run: maven-decoder-mcp"
}

# Install via uvx (handles PEP 668 environments)
install_uvx() {
    print_status "Installing Maven Decoder MCP via uvx..."
    
    # Check if uvx is available
    if ! command_exists uvx; then
        print_status "uvx not found. Installing uv..."
        if ! curl -Ls https://astral.sh/uv/install.sh | sh; then
            print_error "Failed to install uv. Please install manually: https://astral.sh/uv/install.sh"
            exit 1
        fi
        # Add to PATH for current session
        export PATH="$HOME/.local/bin:$PATH"
    fi
    
    print_status "uvx version: $(uvx --version)"
    
    # Test that the package can be run via uvx
    print_status "Testing uvx installation..."
    if uvx maven-decoder-mcp --help >/dev/null 2>&1 & sleep 2 && kill $! 2>/dev/null; then
        print_success "uvx installation test successful!"
    else
        print_error "uvx installation test failed"
        exit 1
    fi
    
    print_success "uvx installation complete!"
    print_status "You can now run: uvx maven-decoder-mcp"
    print_status "For IDE integration, use command: uvx"
    print_status "With args: [maven-decoder-mcp]"
}

# Install via npm
install_npm() {
    print_status "Installing Maven Decoder MCP via npm..."
    
    if ! command_exists npm; then
        print_error "npm not found. Please install Node.js first."
        exit 1
    fi
    
    local npm_version
    npm_version=$(npm --version)
    print_status "npm version: $npm_version"
    
    if [ "$GLOBAL_INSTALL" = "--global" ]; then
        print_status "Installing globally..."
        npm install -g maven-decoder-mcp
    else
        print_status "Installing locally..."
        npm install maven-decoder-mcp
    fi
    
    print_success "npm installation complete!"
    if [ "$GLOBAL_INSTALL" = "--global" ]; then
        print_status "You can now run: maven-decoder-mcp"
    else
        print_status "You can now run: npx maven-decoder-mcp"
    fi
}

# Install via Docker
install_docker() {
    print_status "Setting up Maven Decoder MCP via Docker..."
    
    if ! command_exists docker; then
        print_error "Docker not found. Please install Docker first."
        exit 1
    fi
    
    print_status "Pulling Docker image..."
    docker pull maven-decoder/mcp-server:latest
    
    print_status "Creating wrapper script..."
    cat > ~/.local/bin/maven-decoder-mcp << 'EOF'
#!/bin/bash
docker run --rm -it \
    -v ~/.m2:/home/mcpuser/.m2 \
    -v $(pwd):/workspace \
    maven-decoder/mcp-server:latest "$@"
EOF
    chmod +x ~/.local/bin/maven-decoder-mcp
    
    print_success "Docker installation complete!"
    print_status "You can now run: maven-decoder-mcp"
}

# Auto-detect best method
auto_install() {
    print_status "Auto-detecting best installation method..."
    
    if command_exists uvx; then
        print_status "uvx found - using uvx installation (recommended)"
        METHOD="uvx"
        install_uvx
    elif find_python >/dev/null 2>&1; then
        print_status "Python found - using pip installation"
        METHOD="pip"
        install_pip
    elif command_exists npm; then
        print_status "Node.js found - using npm installation"
        METHOD="npm"
        install_npm
    elif command_exists docker; then
        print_status "Docker found - using docker installation"
        METHOD="docker"
        install_docker
    else
        print_error "No suitable package manager found!"
        print_error "Please install one of: uvx, Python (pip), Node.js (npm), or Docker"
        exit 1
    fi
}

# Main installation logic
main() {
    show_banner
    
    case $METHOD in
        pip)
            install_pip
            ;;
        uvx)
            install_uvx
            ;;
        npm)
            install_npm
            ;;
        docker)
            install_docker
            ;;
        auto)
            auto_install
            ;;
        *)
            print_error "Unknown installation method: $METHOD"
            show_usage
            exit 1
            ;;
    esac
    
    echo ""
    print_success "Installation complete! 🎉"
    echo ""
    print_status "Next steps:"
    print_status "1. Configure your IDE (e.g., Cursor) to use the MCP server"
    if [ "$METHOD" = "uvx" ]; then
        print_status "2. Run 'uvx maven-decoder-mcp' to start the server"
        print_status "3. For IDE config, use command: uvx, args: [maven-decoder-mcp]"
    else
        print_status "2. Run 'maven-decoder-mcp' to start the server"
    fi
    print_status "4. Visit https://github.com/YOUR_USERNAME/maven-decoder-mcp for documentation"
}

# Run main function
main
