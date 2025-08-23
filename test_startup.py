#!/usr/bin/env python3
"""
Basic startup test for Maven Decoder MCP Server

This script performs basic validation to ensure the server can be imported
and initialized correctly.
"""

import sys
import asyncio

def test_import():
    """Test that the main module can be imported"""
    try:
        from maven_decoder_mcp import MavenDecoderServer
        print("✅ Successfully imported MavenDecoderServer")
        return True
    except ImportError as e:
        print(f"❌ Failed to import MavenDecoderServer: {e}")
        return False

def test_server_initialization():
    """Test that the server can be initialized"""
    try:
        from maven_decoder_mcp import MavenDecoderServer
        server = MavenDecoderServer()
        print("✅ Successfully initialized MavenDecoderServer")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize MavenDecoderServer: {e}")
        return False

async def test_basic_functionality():
    """Test basic functionality without external dependencies"""
    try:
        from maven_decoder_mcp import MavenDecoderServer
        server = MavenDecoderServer()
        
        # Test that the server has the expected tools
        expected_tools = [
            'list_artifacts',
            'analyze_jar',
            'get_dependencies',
            'search_classes',
            'extract_source_code',
            'get_version_info',
            'analyze_jar_structure'
        ]
        
        for tool_name in expected_tools:
            if hasattr(server, f'_{tool_name}'):
                print(f"✅ Found tool: {tool_name}")
            else:
                print(f"❌ Missing tool: {tool_name}")
                return False
        
        print("✅ All expected tools are present")
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Maven Decoder MCP Server - Startup Test")
    print("=" * 40)
    
    # Test 1: Import
    if not test_import():
        sys.exit(1)
    
    # Test 2: Initialization
    if not test_server_initialization():
        sys.exit(1)
    
    # Test 3: Basic functionality
    try:
        result = asyncio.run(test_basic_functionality())
        if not result:
            sys.exit(1)
    except Exception as e:
        print(f"❌ Async test failed: {e}")
        sys.exit(1)
    
    print("\n🎉 All startup tests passed!")
    print("The Maven Decoder MCP Server is ready to use.")

if __name__ == "__main__":
    main()
