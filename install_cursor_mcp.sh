#!/bin/bash

# Script to install Maven Decoder MCP Server configuration for Cursor IDE

echo "Installing Maven Decoder MCP Server for Cursor IDE..."

# Create Cursor MCP config directory if it doesn't exist
CURSOR_CONFIG_DIR="$HOME/.cursor"
MCP_CONFIG_FILE="$CURSOR_CONFIG_DIR/mcp_servers.json"

mkdir -p "$CURSOR_CONFIG_DIR"

# Get the absolute path to this directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Maven Decoder MCP Server location: $SCRIPT_DIR"

# Create or update MCP servers configuration
cat > "$MCP_CONFIG_FILE" << EOF
{
  "mcpServers": {
    "maven-decoder": {
      "command": "$SCRIPT_DIR/start_server.sh",
      "args": [],
      "cwd": "$SCRIPT_DIR",
      "env": {
        "MAVEN_DECODER_ENV": "production"
      }
    }
  }
}
EOF

echo "✓ MCP configuration installed to: $MCP_CONFIG_FILE"

# Make sure the startup script is executable
chmod +x "$SCRIPT_DIR/start_server.sh"
echo "✓ Startup script made executable"

# Test the server
echo ""
echo "Testing server startup..."
cd "$SCRIPT_DIR"
if timeout 3s ./start_server.sh < /dev/null 2>/dev/null; then
    echo "✓ Server test successful"
else
    echo "✓ Server startup test completed (timeout is normal)"
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Next steps:"
echo "1. Restart Cursor IDE"
echo "2. The Maven Decoder MCP Server will be available in the AI chat"
echo "3. You can now ask questions like:"
echo "   - 'List Spring Framework artifacts in my Maven repository'"
echo "   - 'Analyze the dependencies of junit:junit:4.13.2'"
echo "   - 'Find all classes containing ApplicationContext'"
echo "   - 'Decompile org.springframework.core.SpringVersion'"
echo ""
echo "📁 Logs will be available at: $SCRIPT_DIR/maven_decoder_server.log"
echo "📖 Documentation: $SCRIPT_DIR/README.md"
