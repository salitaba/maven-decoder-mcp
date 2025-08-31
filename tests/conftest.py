"""
Pytest configuration for Maven Decoder MCP tests
"""

import pytest
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test configuration
pytest_plugins = []

# Environment variables for testing
@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    test_env = {
        'MCP_MAX_RESPONSE_SIZE': '1000',
        'MCP_MAX_ITEMS_PER_PAGE': '5',
        'MCP_MAX_TEXT_LENGTH': '500',
        'MCP_MAX_LINES': '10',
        'MCP_LOG_LEVEL': 'ERROR'  # Reduce log noise during tests
    }
    
    # Store original environment
    original_env = {}
    for key in test_env:
        if key in os.environ:
            original_env[key] = os.environ[key]
    
    # Set test environment
    for key, value in test_env.items():
        os.environ[key] = value
    
    yield
    
    # Restore original environment
    for key in test_env:
        if key in original_env:
            os.environ[key] = original_env[key]
        else:
            os.environ.pop(key, None)

# Mock Maven repository for testing
@pytest.fixture
def mock_maven_repo(tmp_path):
    """Create a mock Maven repository for testing"""
    repo_path = tmp_path / "repository"
    repo_path.mkdir()
    
    # Create some mock jar files
    group_path = repo_path / "com" / "example"
    group_path.mkdir(parents=True)
    
    artifact_path = group_path / "test-artifact"
    artifact_path.mkdir()
    
    version_path = artifact_path / "1.0.0"
    version_path.mkdir()
    
    # Create a mock jar file
    jar_file = version_path / "test-artifact-1.0.0.jar"
    jar_file.write_bytes(b"mock jar content")
    
    return repo_path

# Async test support
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
