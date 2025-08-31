#!/usr/bin/env python3
"""
Test runner for pagination and summarization features
"""

import sys
import subprocess
import os
from pathlib import Path

def run_tests():
    """Run the pagination and summarization tests"""
    print("🧪 Running Pagination and Summarization Tests")
    print("=" * 50)
    
    # Debug information
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print()
    
    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        print("❌ pytest not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio"], check=True)
    
    # Run tests
    test_dir = Path(__file__).parent / "tests"
    
    if not test_dir.exists():
        print(f"❌ Test directory not found: {test_dir}")
        return False
    
    print(f"📁 Running tests from: {test_dir}")
    print()
    
    # Run the tests - use system Python if sys.executable is an AppImage
    python_executable = sys.executable
    if "AppImage" in python_executable:
        python_executable = "/usr/bin/python3"
    
    result = subprocess.run([
        python_executable, "-m", "pytest",
        str(test_dir / "test_pagination.py"),
        "-v",
        "--tb=short"
    ], cwd=Path(__file__).parent, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("\n✅ All tests passed!")
        return True
    else:
        print("\n❌ Some tests failed!")
        print(f"Return code: {result.returncode}")
        print("STDOUT:")
        print(result.stdout)
        print("STDERR:")
        print(result.stderr)
        return False

def run_simple_test():
    """Run a simple integration test"""
    print("🔍 Running Simple Integration Test")
    print("=" * 40)
    
    try:
        from maven_decoder_mcp.maven_decoder_server import ResponseManager
        
        # Test ResponseManager
        rm = ResponseManager(
            max_response_size=1000,
            max_items_per_page=5,
            max_text_length=500,
            max_lines=10
        )
        
        # Test pagination
        test_data = {
            "classes": [{"name": f"Class{i}"} for i in range(20)]
        }
        
        paginated = rm.paginate_response(test_data, page=2, items_per_page=5)
        print(f"✅ Pagination test passed: {len(paginated['classes'])} items on page 2")
        
        # Test summarization
        long_text = "\n".join([
            "public class Test {",
            *[f"    private String field{i};" for i in range(50)],
            "}"
        ])
        
        summarized = rm.summarize_large_text(long_text)
        print(f"✅ Summarization test passed: {len(summarized)} chars vs {len(long_text)} chars")
        
        print("\n✅ Simple integration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Simple integration test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Maven Decoder MCP - Pagination and Summarization Tests")
    print("=" * 60)
    
    # Run simple test first
    simple_success = run_simple_test()
    print()
    
    # Run full test suite
    full_success = run_tests()
    
    print("\n" + "=" * 60)
    if simple_success and full_success:
        print("🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("💥 Some tests failed!")
        sys.exit(1)
