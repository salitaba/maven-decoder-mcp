#!/bin/bash

# Startup script for Maven Decoder MCP Server

echo "Starting Maven Decoder MCP Server..."

# Check if we're in a virtual environment or should use one
if [ -d ".venv" ] && [ -f ".venv/bin/python" ]; then
    echo "Using virtual environment..."
    source .venv/bin/activate
    python maven_decoder_server.py
elif [ -n "$VIRTUAL_ENV" ]; then
    echo "Using active virtual environment: $VIRTUAL_ENV"
    python maven_decoder_server.py
else
    echo "Using system Python..."
    python3 maven_decoder_server.py
fi
