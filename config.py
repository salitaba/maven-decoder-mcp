"""
Configuration module for Maven Decoder MCP Server
"""

import os
from pathlib import Path
from typing import Optional

class Config:
    """Configuration settings for the Maven Decoder MCP Server"""
    
    # Maven repository location
    MAVEN_HOME: Path = Path.home() / ".m2" / "repository"
    
    # Override Maven home from environment variable
    if "M2_HOME" in os.environ:
        MAVEN_HOME = Path(os.environ["M2_HOME"]) / "repository"
    elif "MAVEN_REPO" in os.environ:
        MAVEN_HOME = Path(os.environ["MAVEN_REPO"])
    
    # Server configuration
    SERVER_NAME: str = "maven-decoder"
    SERVER_VERSION: str = "1.0.0"
    
    # Decompiler settings
    DECOMPILER_TIMEOUT: int = 30  # seconds
    DECOMPILER_PRIORITY: list = ["cfr", "procyon", "fernflower", "javap"]
    
    # Search and analysis limits
    DEFAULT_ARTIFACT_LIMIT: int = 50
    DEFAULT_SEARCH_LIMIT: int = 100
    MAX_DEPENDENCY_DEPTH: int = 5
    
    # Cache settings
    ENABLE_CACHE: bool = True
    CACHE_SIZE: int = 1000
    CACHE_TTL: int = 3600  # seconds
    
    # Logging configuration
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Performance settings
    MAX_CONCURRENT_OPERATIONS: int = 10
    JAR_ANALYSIS_TIMEOUT: int = 60  # seconds
    
    # Feature flags
    ENABLE_DECOMPILATION: bool = True
    ENABLE_TRANSITIVE_DEPS: bool = True
    ENABLE_BYTECODE_ANALYSIS: bool = False  # Requires additional libraries
    
    # File size limits (in bytes)
    MAX_JAR_SIZE: int = 100 * 1024 * 1024  # 100MB
    MAX_CLASS_SIZE: int = 1024 * 1024      # 1MB
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration settings"""
        if not cls.MAVEN_HOME.exists():
            print(f"Warning: Maven repository not found at {cls.MAVEN_HOME}")
            return False
        
        if not cls.MAVEN_HOME.is_dir():
            print(f"Error: Maven repository path is not a directory: {cls.MAVEN_HOME}")
            return False
        
        return True
    
    @classmethod
    def get_maven_home(cls) -> Path:
        """Get the Maven repository home directory"""
        return cls.MAVEN_HOME
    
    @classmethod
    def set_maven_home(cls, path: str) -> None:
        """Set a custom Maven repository location"""
        cls.MAVEN_HOME = Path(path)
    
    @classmethod
    def get_decompiler_config(cls) -> dict:
        """Get decompiler configuration"""
        return {
            "timeout": cls.DECOMPILER_TIMEOUT,
            "priority": cls.DECOMPILER_PRIORITY,
            "enabled": cls.ENABLE_DECOMPILATION
        }
    
    @classmethod
    def get_limits(cls) -> dict:
        """Get search and analysis limits"""
        return {
            "artifacts": cls.DEFAULT_ARTIFACT_LIMIT,
            "search": cls.DEFAULT_SEARCH_LIMIT,
            "dependency_depth": cls.MAX_DEPENDENCY_DEPTH,
            "max_jar_size": cls.MAX_JAR_SIZE,
            "max_class_size": cls.MAX_CLASS_SIZE
        }

# Environment-specific configuration overrides
if os.environ.get("MAVEN_DECODER_ENV") == "development":
    Config.LOG_LEVEL = "DEBUG"
    Config.ENABLE_BYTECODE_ANALYSIS = True
    Config.CACHE_TTL = 60  # Shorter cache in development

elif os.environ.get("MAVEN_DECODER_ENV") == "production":
    Config.LOG_LEVEL = "WARNING"
    Config.MAX_CONCURRENT_OPERATIONS = 20
    Config.CACHE_SIZE = 5000
