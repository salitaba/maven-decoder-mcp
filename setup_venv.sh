#!/bin/bash

# Setup script for Maven Decoder MCP Server virtual environment

set -e

echo "Setting up Maven Decoder MCP Server virtual environment..."

# Remove existing virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Removing existing .venv directory..."
    rm -rf .venv
fi

# Create new virtual environment
echo "Creating Python virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install requirements
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install MCP SDK from GitHub
echo "Installing MCP Python SDK..."
pip install "git+https://github.com/modelcontextprotocol/python-sdk.git"

# Test installation
echo "Testing installation..."
python -c "from mcp.server import Server; print('✓ MCP Server import successful')"
python -c "import xmltodict; print('✓ xmltodict import successful')"
python -c "import pydantic; print('✓ pydantic import successful')"

echo ""
echo "✓ Virtual environment setup complete!"
echo ""
echo "To activate the virtual environment:"
echo "  source .venv/bin/activate"
echo ""
echo "To run the server:"
echo "  source .venv/bin/activate && python maven_decoder_server.py"
echo ""
echo "To test the server:"
echo "  source .venv/bin/activate && python test_server.py"
echo ""
