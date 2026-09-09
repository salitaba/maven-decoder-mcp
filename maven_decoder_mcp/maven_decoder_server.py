#!/usr/bin/env python3
"""
Maven Decoder MCP Server

An MCP server for analyzing Maven jar files in the local repository (~/.m2).
Provides comprehensive tools for agentic coding assistance in Java projects.
"""

import asyncio
import json
import os
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging
import tempfile
import subprocess
import re

try:
    from mcp.server.lowlevel import Server
except ImportError:
    from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    ListToolsResult,
    CallToolResult,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel,
    ServerCapabilities,
    ToolsCapability
)
from pydantic import BaseModel
import xmltodict

# Import our custom modules
from .decompiler import JavaDecompiler
from .maven_analyzer import MavenDependencyAnalyzer
from .maven_central import MavenCentralClient, MavenRemoteError

# Configure logging
import os
log_file = os.path.join(os.path.dirname(__file__), "maven_decoder_server.log")
logging.basicConfig(
    level=logging.INFO,  # Back to INFO level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()  # Also log to console when not running as MCP server
    ]
)
logger = logging.getLogger(__name__)


def get_version() -> str:
    """Resolve the running package version.

    Read from the installed distribution metadata so the version reported to
    MCP clients cannot drift from what was actually packaged; the release
    workflow rewrites ``pyproject.toml`` from the git tag at build time.
    """
    try:
        from importlib.metadata import version

        return version("maven-decoder-mcp")
    except Exception:
        # Running from a source checkout without an installed distribution.
        try:
            from . import __version__

            return __version__
        except Exception:
            return "0.0.0"


class ResponseManager:
    """Manages large responses with pagination and summarization"""
    
    def __init__(self, max_response_size: Optional[int] = None, max_items_per_page: Optional[int] = None, 
                 max_text_length: Optional[int] = None, max_lines: Optional[int] = None):
        self.max_response_size = max_response_size or int(os.getenv('MCP_MAX_RESPONSE_SIZE', '50000'))
        self.max_items_per_page = max_items_per_page or int(os.getenv('MCP_MAX_ITEMS_PER_PAGE', '20'))
        self.max_text_length = max_text_length or int(os.getenv('MCP_MAX_TEXT_LENGTH', '10000'))
        self.max_lines = max_lines or int(os.getenv('MCP_MAX_LINES', '500'))
    
    def paginate_response(self, data: Dict[str, Any], page: int = 1, 
                         items_per_page: Optional[int] = None) -> Dict[str, Any]:
        """Paginate a response with items"""
        if items_per_page is None:
            items_per_page = self.max_items_per_page
        
        # Handle different data structures
        if 'classes' in data:
            items = data['classes']
            key = 'classes'
        elif 'matches' in data:
            items = data['matches']
            key = 'matches'
        elif 'dependencies' in data:
            items = data['dependencies']
            key = 'dependencies'
        else:
            # If no known structure, return as is
            return data
        
        total_items = len(items)
        total_pages = (total_items + items_per_page - 1) // items_per_page
        
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        
        paginated_items = items[start_idx:end_idx]
        
        result = data.copy()
        result[key] = paginated_items
        result['pagination'] = {
            'page': page,
            'total_pages': total_pages,
            'items_per_page': items_per_page,
            'total_items': total_items,
            'showing_items': f"{start_idx + 1}-{min(end_idx, total_items)}"
        }
        
        return result
    
    def summarize_large_text(self, text: str, max_length: Optional[int] = None) -> str:
        """Summarize large text content"""
        if max_length is None:
            max_length = min(self.max_text_length, self.max_response_size)
            
        # For Java code, try to keep important parts
        lines = text.split('\n')
        if len(text) <= max_length and len(lines) <= self.max_lines:
            return text
        
        # Keep first 20 lines (usually package, imports, class declaration)
        # Keep last 10 lines (usually closing braces)
        # Keep method signatures in between
        head_count = min(20, len(lines))
        tail_count = min(10, max(0, len(lines) - head_count))
        summary_lines = []
        
        # Add header
        summary_lines.append("// SUMMARY: Large class content (showing key parts)")
        summary_lines.append(f"// Total lines: {len(lines)}")
        summary_lines.append("// Showing: package/imports, method signatures, and closing braces")
        summary_lines.append("")
        
        # Add first lines
        summary_lines.extend(lines[:head_count])
        
        # Find method signatures (lines with public/private/protected + method name)
        method_lines = []
        for i, line in enumerate(lines[head_count:len(lines) - tail_count]):
            stripped = line.strip()
            if (re.match(r'^\s*(public|private|protected|static|final)\s+', stripped) and 
                '(' in stripped and ')' in stripped and 
                not stripped.startswith('//') and not stripped.startswith('/*')):
                method_lines.append((i + head_count, line))
        
        # Add some method signatures (up to 10)
        if method_lines:
            summary_lines.append("")
            summary_lines.append("// ... key method signatures ...")
            for idx, line in method_lines[:10]:
                summary_lines.append(f"// Line {idx + 1}: {line.strip()}")
        
        # Add closing braces
        if tail_count:
            summary_lines.append("")
            summary_lines.append("// ... closing braces ...")
            summary_lines.extend(lines[-tail_count:])
        
        summary_lines.append("")
        summary_lines.append(f"// Use pagination or specific method extraction for full content")
        
        return '\n'.join(summary_lines)
    
    def should_paginate(self, data: Dict[str, Any]) -> bool:
        """Check if response should be paginated"""
        response_str = json.dumps(data, indent=2)
        return len(response_str) > self.max_response_size
    
    def should_summarize(self, text: str) -> bool:
        """Check if text should be summarized"""
        return len(text) > min(self.max_text_length, self.max_response_size)

class MavenDecoderServer:
    """MCP Server for Maven jar file analysis"""
    
    def __init__(self, maven_repository: Optional[Union[str, Path]] = None):
        logger.info("Initializing Maven Decoder MCP Server...")
        self.server = Server("maven-decoder")
        self._ensure_server_decorators()
        self.maven_home = (
            Path(os.path.expandvars(os.path.expanduser(str(maven_repository)))).resolve()
            if maven_repository
            else self._resolve_maven_repository()
        )
        self.response_manager = ResponseManager()
        logger.info(f"Maven repository location: {self.maven_home}")
        
        if not self.maven_home.exists():
            logger.warning(f"Maven repository not found at {self.maven_home}")
        else:
            # Count artifacts for info
            jar_count = len(list(self.maven_home.rglob("*.jar")))
            pom_count = len(list(self.maven_home.rglob("*.pom")))
            logger.info(f"Found {jar_count} jar files and {pom_count} POM files in repository")

        logger.info("Initializing remote Maven repository client...")
        self.central = MavenCentralClient()
        self.cache_home = self.central.cache_dir
        self.auto_download = self._resolve_auto_download()
        if self.central.offline:
            logger.info("Offline mode enabled: remote Maven lookups are disabled")
        else:
            logger.info(
                "Online mode: search=%s, repositories=%s, cache=%s, auto_download=%s",
                ", ".join(self.central.search_urls),
                ", ".join(self.central.repositories),
                self.cache_home,
                self.auto_download,
            )

        logger.info("Initializing Java decompiler...")
        self.decompiler = JavaDecompiler()
        logger.info(f"Available decompilers: {list(self.decompiler.available_decompilers.keys())}")
        
        logger.info("Initializing Maven dependency analyzer...")
        self.dependency_analyzer = MavenDependencyAnalyzer(
            self.maven_home,
            extra_roots=[self.cache_home],
            remote_resolver=self._resolve_remote_pom,
        )
        
        logger.info("Setting up MCP server handlers...")
        self.setup_handlers()
        logger.info("Maven Decoder MCP Server initialization complete!")

    @staticmethod
    def _resolve_maven_repository() -> Path:
        """Resolve repo dir; import Config lazily to keep startup light."""
        from .config import Config

        return Config.resolve_maven_repository()

    @staticmethod
    def _resolve_auto_download() -> bool:
        """Whether missing artifacts may be fetched from a remote repository."""
        from .config import Config

        return Config.auto_download_enabled()

    def _resolve_remote_pom(self, group_id: str, artifact_id: str,
                            version: str) -> Optional[Path]:
        """Fetch a POM from a remote repository into the cache."""
        if not self.auto_download:
            return None
        return self.central.ensure_artifact(
            group_id, artifact_id, version, extension="pom"
        )

    def _ensure_server_decorators(self):
        """Provide decorator registration for newer MCP SDK request handlers."""
        if hasattr(self.server, "list_tools") and hasattr(self.server, "call_tool"):
            return

        if hasattr(self.server, "add_request_handler"):
            # MCP SDK >= 2.0: decorators were removed in favor of explicit
            # handler registration via add_request_handler(method, params_type, handler)
            from mcp.types import CallToolRequestParams, PaginatedRequestParams

            def list_tools():
                def decorator(func):
                    async def handler(ctx, params):
                        return ListToolsResult(tools=await func())

                    self.server.add_request_handler("tools/list", PaginatedRequestParams, handler)
                    return func

                return decorator

            def call_tool():
                def decorator(func):
                    async def handler(ctx, params):
                        content = await func(params.name, params.arguments or {})
                        if isinstance(content, CallToolResult):
                            return content
                        return CallToolResult(content=content)

                    self.server.add_request_handler("tools/call", CallToolRequestParams, handler)
                    return func

                return decorator

            self.server.list_tools = list_tools
            self.server.call_tool = call_tool
            return

        if not hasattr(self.server, "_add_request_handler"):
            raise RuntimeError("Unsupported MCP Server API: missing tool registration handlers")

        if not hasattr(self.server, "list_tools"):
            def list_tools():
                def decorator(func):
                    async def handler(ctx, params):
                        return ListToolsResult(tools=await func())

                    self.server._add_request_handler("tools/list", handler)
                    return func

                return decorator

            self.server.list_tools = list_tools

        if not hasattr(self.server, "call_tool"):
            def call_tool():
                def decorator(func):
                    async def handler(ctx, params):
                        content = await func(params.name, params.arguments or {})
                        if isinstance(content, CallToolResult):
                            return content
                        return CallToolResult(content=content)

                    self.server._add_request_handler("tools/call", handler)
                    return func

                return decorator

            self.server.call_tool = call_tool
    
    def setup_handlers(self):
        """Setup MCP server handlers"""
        
        tools = [
                Tool(
                    name="list_artifacts",
                    description="List all Maven artifacts in the local repository with optional filtering",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "group_id": {"type": "string", "description": "Filter by group ID (e.g., 'org.springframework')"},
                            "artifact_id": {"type": "string", "description": "Filter by artifact ID (e.g., 'spring-core')"},
                            "version": {"type": "string", "description": "Filter by version (e.g., '5.3.21')"},
                            "sort_by": {"type": "string", "default": "name", "description": "Order results by: 'name' (group/artifact/version ascending, default), 'size' (largest jars first), or 'modified' (most recently modified first). Unknown values fall back to 'name'."},
                            "limit": {"type": "integer", "default": 50, "description": "Maximum number of artifacts to return"},
                            "page": {"type": "integer", "default": 1, "description": "Page number for pagination"},
                            "items_per_page": {"type": "integer", "default": 20, "description": "Items per page"}
                        },
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="analyze_jar",
                    description="Analyze a specific jar file and extract detailed information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "group_id": {"type": "string", "description": "Maven group ID"},
                            "artifact_id": {"type": "string", "description": "Maven artifact ID"},
                            "version": {"type": "string", "description": "Maven version"},
                            "include_bytecode": {"type": "boolean", "default": False, "description": "Include bytecode analysis"},
                            "include_manifest": {"type": "boolean", "default": True, "description": "Include JAR manifest"},
                            "summarize_large_content": {"type": "boolean", "default": True, "description": "Summarize large content automatically"}
                        },
                        "required": ["group_id", "artifact_id", "version"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="extract_class_info",
                    description="Get detailed information about Java classes in a jar",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "group_id": {"type": "string", "description": "Maven group ID"},
                            "artifact_id": {"type": "string", "description": "Maven artifact ID"},
                            "version": {"type": "string", "description": "Maven version"},
                            "class_pattern": {"type": "string", "description": "Pattern to match class names (regex supported)"},
                            "include_methods": {"type": "boolean", "default": True, "description": "Include method signatures"},
                            "include_fields": {"type": "boolean", "default": True, "description": "Include field information"},
                            "include_bytecode": {"type": "boolean", "default": False, "description": "Include verbose javap bytecode output for matched classes"},
                            "page": {"type": "integer", "default": 1, "description": "Page number for pagination"},
                            "items_per_page": {"type": "integer", "default": 20, "description": "Items per page"},
                            "summarize_large_content": {"type": "boolean", "default": True, "description": "Summarize large content automatically"}
                        },
                        "required": ["group_id", "artifact_id", "version"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="get_dependencies",
                    description="Get Maven dependencies from POM files",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "group_id": {"type": "string", "description": "Maven group ID"},
                            "artifact_id": {"type": "string", "description": "Maven artifact ID"},
                            "version": {"type": "string", "description": "Maven version"},
                            "include_transitive": {"type": "boolean", "default": False, "description": "Include transitive dependencies"},
                            "page": {"type": "integer", "default": 1, "description": "Page number for pagination"},
                            "items_per_page": {"type": "integer", "default": 20, "description": "Items per page"}
                        },
                        "required": ["group_id", "artifact_id", "version"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="search_classes",
                    description="Search for Java classes across all jars in the repository",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "class_name": {"type": "string", "description": "Class name to search for (supports wildcards)"},
                            "package_pattern": {"type": "string", "description": "Package pattern to filter by"},
                            "annotation": {"type": "string", "description": "Search for classes with specific annotation"},
                            "case_sensitive": {"type": "boolean", "default": True, "description": "Match class_name and package_pattern case-sensitively. Set false for a case-insensitive search (e.g. 'arraylist' matches 'ArrayList')."},
                            "limit": {"type": "integer", "default": 100, "description": "Maximum results to return"},
                            "page": {"type": "integer", "default": 1, "description": "Page number for pagination"},
                            "items_per_page": {"type": "integer", "default": 20, "description": "Items per page"}
                        },
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="extract_source_code",
                    description="Extract source code from jar (if available) or decompile bytecode",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "group_id": {"type": "string", "description": "Maven group ID"},
                            "artifact_id": {"type": "string", "description": "Maven artifact ID"},
                            "version": {"type": "string", "description": "Maven version"},
                            "class_name": {"type": "string", "description": "Fully qualified class name"},
                            "prefer_sources": {"type": "boolean", "default": True, "description": "Prefer source jar over decompilation"},
                            "summarize_large_content": {"type": "boolean", "default": True, "description": "Summarize large content automatically"},
                            "max_lines": {"type": "integer", "default": 500, "description": "Maximum lines to return (0 for all)"}
                        },
                        "required": ["group_id", "artifact_id", "version", "class_name"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="extract_jar_resource",
                    description="Extract text resources from a jar, such as .proto files, service descriptors, or metadata",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "group_id": {"type": "string", "description": "Maven group ID"},
                            "artifact_id": {"type": "string", "description": "Maven artifact ID"},
                            "version": {"type": "string", "description": "Maven version"},
                            "resource_path": {"type": "string", "description": "Exact resource path inside the jar"},
                            "resource_pattern": {"type": "string", "description": "Regex pattern to match resource paths"},
                            "max_bytes": {"type": "integer", "default": 65536, "description": "Maximum bytes to read per resource"},
                            "limit": {"type": "integer", "default": 20, "description": "Maximum matching resources to return"}
                        },
                        "required": ["group_id", "artifact_id", "version"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="compare_versions",
                    description="Compare different versions of the same Maven artifact",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "group_id": {"type": "string", "description": "Maven group ID"},
                            "artifact_id": {"type": "string", "description": "Maven artifact ID"},
                            "version1": {"type": "string", "description": "First (older) version to compare"},
                            "version2": {"type": "string", "description": "Second (newer) version to compare"},
                            "compare_api": {"type": "boolean", "default": True, "description": "Diff the public API: added/removed public and protected methods and fields, and breaking changes"},
                            "summarize_large_content": {"type": "boolean", "default": True, "description": "Summarize large content automatically"}
                        },
                        "required": ["group_id", "artifact_id", "version1", "version2"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="find_usage_examples",
                    description="Find usage examples of classes/methods in test jars",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "class_name": {"type": "string", "description": "Class name to find usage for"},
                            "method_name": {"type": "string", "description": "Method name to find usage for"},
                            "search_tests": {"type": "boolean", "default": True, "description": "Search in test jars"},
                            "limit": {"type": "integer", "default": 50, "description": "Maximum results to return"},
                            "page": {"type": "integer", "default": 1, "description": "Page number for pagination"},
                            "items_per_page": {"type": "integer", "default": 20, "description": "Items per page"}
                        },
                        "required": ["class_name"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="get_dependency_tree",
                    description="Get complete dependency tree for an artifact",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "group_id": {"type": "string", "description": "Maven group ID"},
                            "artifact_id": {"type": "string", "description": "Maven artifact ID"},
                            "version": {"type": "string", "description": "Maven version"},
                            "max_depth": {"type": "integer", "default": 3, "description": "Maximum depth to show"},
                            "summarize_large_content": {"type": "boolean", "default": True, "description": "Summarize large content automatically"}
                        },
                        "required": ["group_id", "artifact_id", "version"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="find_dependents",
                    description="Find artifacts that depend on a specific artifact",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "group_id": {"type": "string", "description": "Target group ID"},
                            "artifact_id": {"type": "string", "description": "Target artifact ID"},
                            "version": {"type": "string", "description": "Specific version to search for (optional)"},
                            "limit": {"type": "integer", "default": 100, "description": "Maximum results to return"},
                            "page": {"type": "integer", "default": 1, "description": "Page number for pagination"},
                            "items_per_page": {"type": "integer", "default": 20, "description": "Items per page"}
                        },
                        "required": ["group_id", "artifact_id"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="get_version_info",
                    description="Get all available versions of an artifact, optionally including versions published remotely",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "group_id": {"type": "string", "description": "Maven group ID"},
                            "artifact_id": {"type": "string", "description": "Maven artifact ID"},
                            "include_remote": {"type": "boolean", "default": False, "description": "Also list versions published on the remote repository (not just installed ones)"},
                            "limit": {"type": "integer", "default": 50, "description": "Maximum versions to return"},
                            "page": {"type": "integer", "default": 1, "description": "Page number for pagination"},
                            "items_per_page": {"type": "integer", "default": 20, "description": "Items per page"}
                        },
                        "required": ["group_id", "artifact_id"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="analyze_jar_structure",
                    description="Analyze the overall structure and metadata of a jar file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "group_id": {"type": "string", "description": "Maven group ID"},
                            "artifact_id": {"type": "string", "description": "Maven artifact ID"},
                            "version": {"type": "string", "description": "Maven version"},
                            "summarize_large_content": {"type": "boolean", "default": True, "description": "Summarize large content automatically"}
                        },
                        "required": ["group_id", "artifact_id", "version"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="extract_method_info",
                    description="Extract specific method information from a Java class",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "group_id": {"type": "string", "description": "Maven group ID"},
                            "artifact_id": {"type": "string", "description": "Maven artifact ID"},
                            "version": {"type": "string", "description": "Maven version"},
                            "class_name": {"type": "string", "description": "Fully qualified class name"},
                            "method_pattern": {"type": "string", "description": "Pattern to match method names (regex supported)"},
                            "include_bytecode": {"type": "boolean", "default": False, "description": "Include bytecode analysis"},
                            "max_methods": {"type": "integer", "default": 10, "description": "Maximum number of methods to return"}
                        },
                        "required": ["group_id", "artifact_id", "version", "class_name"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="search_maven_central",
                    description="Search Maven Central (or the configured mirror) online for artifacts, including ones not installed locally. Use this to discover coordinates or find which published artifact contains a class.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Free-text search term (e.g. 'jackson databind')"},
                            "group_id": {"type": "string", "description": "Exact group ID filter (e.g. 'org.springframework')"},
                            "artifact_id": {"type": "string", "description": "Exact artifact ID filter (e.g. 'spring-core')"},
                            "class_name": {"type": "string", "description": "Simple class name to find the containing artifact (e.g. 'ObjectMapper')"},
                            "fully_qualified_class": {"type": "string", "description": "Fully qualified class name (e.g. 'com.fasterxml.jackson.databind.ObjectMapper')"},
                            "packaging": {"type": "string", "description": "Packaging filter (e.g. 'jar', 'pom')"},
                            "all_versions": {"type": "boolean", "default": False, "description": "Return every published version instead of only the latest per artifact"},
                            "limit": {"type": "integer", "default": 20, "description": "Maximum results to return (max 200)"},
                            "page": {"type": "integer", "default": 1, "description": "Page number for pagination"}
                        },
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="get_remote_versions",
                    description="List all versions of an artifact published on the remote repository, including versions that are not installed locally",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "group_id": {"type": "string", "description": "Maven group ID"},
                            "artifact_id": {"type": "string", "description": "Maven artifact ID"},
                            "include_snapshots": {"type": "boolean", "default": True, "description": "Include -SNAPSHOT versions. Set false to list only released versions."},
                            "limit": {"type": "integer", "default": 100, "description": "Maximum versions to return"}
                        },
                        "required": ["group_id", "artifact_id"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="download_artifact",
                    description="Download an artifact from the remote repository into the local analysis cache so every other tool can inspect it. Use 'latest' as the version to fetch the newest release.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "group_id": {"type": "string", "description": "Maven group ID"},
                            "artifact_id": {"type": "string", "description": "Maven artifact ID"},
                            "version": {"type": "string", "description": "Version to download, or 'latest' for the newest release"},
                            "include_sources": {"type": "boolean", "default": True, "description": "Also download the sources jar when published"},
                            "include_javadoc": {"type": "boolean", "default": False, "description": "Also download the javadoc jar when published"},
                            "classifier": {"type": "string", "description": "Download a specific classified jar instead of the main one"},
                            "force": {"type": "boolean", "default": False, "description": "Re-download even when the file is already cached"}
                        },
                        "required": ["group_id", "artifact_id", "version"],
                        "additionalProperties": False
                    }
                )
            ]
        self.server._tools = tools

        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools for Maven jar analysis"""
            logger.info("MCP client requested tool list")
            logger.info(f"Registered {len(tools)} tools: {[tool.name for tool in tools]}")
            return tools
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            logger.info(f"Tool called: {name} with arguments: {arguments}")
            try:
                if name == "list_artifacts":
                    return await self._list_artifacts(**arguments)
                elif name == "analyze_jar":
                    return await self._analyze_jar(**arguments)
                elif name == "extract_class_info":
                    return await self._extract_class_info(**arguments)
                elif name == "get_dependencies":
                    return await self._get_dependencies(**arguments)
                elif name == "search_classes":
                    return await self._search_classes(**arguments)
                elif name == "extract_source_code":
                    return await self._extract_source_code(**arguments)
                elif name == "extract_jar_resource":
                    return await self._extract_jar_resource(**arguments)
                elif name == "compare_versions":
                    return await self._compare_versions(**arguments)
                elif name == "find_usage_examples":
                    return await self._find_usage_examples(**arguments)
                elif name == "get_dependency_tree":
                    return await self._get_dependency_tree(**arguments)
                elif name == "find_dependents":
                    return await self._find_dependents(**arguments)
                elif name == "get_version_info":
                    return await self._get_version_info(**arguments)
                elif name == "analyze_jar_structure":
                    return await self._analyze_jar_structure(**arguments)
                elif name == "extract_method_info":
                    return await self._extract_method_info(**arguments)
                elif name == "search_maven_central":
                    return await self._search_maven_central(**arguments)
                elif name == "get_remote_versions":
                    return await self._get_remote_versions(**arguments)
                elif name == "download_artifact":
                    return await self._download_artifact(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Error handling tool {name}: {e}", exc_info=True)
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def _list_artifacts(self, group_id: Optional[str] = None,
                            artifact_id: Optional[str] = None,
                            version: Optional[str] = None,
                            sort_by: str = "name",
                            limit: int = 50, page: int = 1, items_per_page: int = 20) -> List[TextContent]:
        """List Maven artifacts with optional filtering"""
        logger.debug(f"Listing artifacts with filters: group_id={group_id}, artifact_id={artifact_id}, version={version}, sort_by={sort_by}, limit={limit}, page={page}, items_per_page={items_per_page}")
        artifacts = []
        if not self.maven_home.exists() or not self.maven_home.is_dir():
            return [TextContent(type="text", text=self._missing_repository_message())]

        try:
            logger.debug(f"Scanning Maven repository: {self.maven_home}")
            group_dirs = [p for p in self.maven_home.iterdir() if p.is_dir()]
            logger.debug(f"Found {len(group_dirs)} top-level directories")
            
            for group_path in group_dirs:
                group_name = group_path.name
                if group_id and group_id not in group_name:
                    continue
                
                # Look for artifact directories within this group
                for artifact_dir in group_path.iterdir():
                    if not artifact_dir.is_dir():
                        continue
                    
                    artifact_name = artifact_dir.name
                    if artifact_id and artifact_id not in artifact_name:
                        continue
                    
                    # Look for version directories within this artifact
                    for version_dir in artifact_dir.iterdir():
                        if not version_dir.is_dir():
                            continue
                        
                        version_name = version_dir.name
                        if version and version not in version_name:
                            continue
                        
                        # Check if this version directory contains jar files
                        jar_files = list(version_dir.glob("*.jar"))
                        if jar_files:
                            stats = [f.stat() for f in jar_files]
                            size_bytes = sum(s.st_size for s in stats)
                            mtime = max(s.st_mtime for s in stats)
                            artifacts.append({
                                "group_id": self._path_to_group_id(group_path),
                                "artifact_id": artifact_name,
                                "version": version_name,
                                "jar_files": [f.name for f in jar_files],
                                "size_bytes": size_bytes,
                                "last_modified": datetime.fromtimestamp(mtime).isoformat(),
                                "path": str(version_dir),
                                # Sort key only; the ISO string above is for
                                # display and is not ordered reliably across
                                # differing UTC offsets. Removed before output.
                                "_mtime": mtime,
                            })

            # Sort the full result set before slicing so the returned page
            # reflects the requested order. Filesystem iteration order is
            # otherwise arbitrary and unstable across machines. An unknown
            # sort_by falls back to "name" rather than raising.
            if sort_by == "size":
                artifacts.sort(key=lambda a: a["size_bytes"], reverse=True)
            elif sort_by == "modified":
                artifacts.sort(key=lambda a: a["_mtime"], reverse=True)
            else:
                artifacts.sort(
                    key=lambda a: (a["group_id"], a["artifact_id"], a["version"])
                )

            page_items = [
                {k: v for k, v in a.items() if k != "_mtime"}
                for a in artifacts[:limit]
            ]

            result = {
                "total_found": len(artifacts),
                "artifacts": page_items
            }

            logger.info(f"Found {len(artifacts)} artifacts matching criteria")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error listing artifacts: {str(e)}")]
    
    def _path_to_group_id(self, path: Path) -> str:
        """Convert file path to Maven group ID"""
        relative = path.relative_to(self.maven_home)
        return str(relative).replace(os.sep, '.')
    
    async def _analyze_jar(self, group_id: str, artifact_id: str, version: str,
                          include_bytecode: bool = False, include_manifest: bool = True,
                          summarize_large_content: bool = True) -> List[TextContent]:
        """Analyze a specific jar file"""
        jar_path = await self._resolve_jar_path(group_id, artifact_id, version)
        if not jar_path or not jar_path.exists():
            return [TextContent(type="text", text=self._jar_not_found_message(group_id, artifact_id, version))]
        
        try:
            analysis = {
                "artifact": f"{group_id}:{artifact_id}:{version}",
                "jar_path": str(jar_path),
                "origin": self._path_origin(jar_path),
                "size_bytes": jar_path.stat().st_size
            }
            
            with zipfile.ZipFile(jar_path, 'r') as jar:
                entries = jar.namelist()
                analysis["total_entries"] = len(entries)
                
                # Categorize entries
                classes = [e for e in entries if e.endswith('.class')]
                resources = [e for e in entries if not e.endswith('.class') and not e.endswith('/')]
                
                analysis["classes"] = {
                    "count": len(classes),
                    "packages": self._extract_packages(classes),
                    "class_list": classes[:100] if not include_bytecode else classes
                }
                
                analysis["resources"] = {
                    "count": len(resources),
                    "types": self._categorize_resources(resources),
                    "resource_list": resources[:50]
                }
                
                # Extract manifest
                if include_manifest and "META-INF/MANIFEST.MF" in entries:
                    manifest_content = jar.read("META-INF/MANIFEST.MF").decode('utf-8', errors='ignore')
                    analysis["manifest"] = self._parse_manifest(manifest_content)
                
                # Extract Maven metadata
                pom_entries = [e for e in entries if e.endswith('pom.xml')]
                if pom_entries:
                    pom_content = jar.read(pom_entries[0]).decode('utf-8', errors='ignore')
                    analysis["maven_metadata"] = self._parse_pom(pom_content)
            
            if summarize_large_content and self.response_manager.should_summarize(json.dumps(analysis, indent=2)):
                analysis["content"] = self.response_manager.summarize_large_text(json.dumps(analysis, indent=2))
                analysis["summarized"] = True
            
            return [TextContent(type="text", text=json.dumps(analysis, indent=2))]
            
        except zipfile.BadZipFile:
            return [TextContent(type="text", text=self._corrupt_jar_message(jar_path))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error analyzing jar: {str(e)}")]
    
    @property
    def repository_roots(self) -> List[Path]:
        """Maven-layout roots to search: local repository first, then cache."""
        return [self.maven_home, self.cache_home]

    def _get_jar_path(self, group_id: str, artifact_id: str, version: str) -> Optional[Path]:
        """Get path to a locally available jar (local repository or cache)"""
        group_path = group_id.replace('.', os.sep)

        for root in self.repository_roots:
            jar_dir = root / group_path / artifact_id / version

            # Look for the main jar file
            main_jar = jar_dir / f"{artifact_id}-{version}.jar"
            if main_jar.exists():
                return main_jar

            # Look for any non-classified jar file in the directory
            jar_files = [
                path for path in sorted(jar_dir.glob("*.jar"))
                if not path.name.endswith(("-sources.jar", "-javadoc.jar"))
            ]
            if jar_files:
                return jar_files[0]

        return None

    async def _resolve_jar_path(self, group_id: str, artifact_id: str,
                                version: str) -> Optional[Path]:
        """Resolve a jar locally, downloading it from a remote repo if needed."""
        jar_path = self._get_jar_path(group_id, artifact_id, version)
        if jar_path and jar_path.exists():
            return jar_path

        if not self.auto_download:
            return None

        logger.info(
            "Jar %s:%s:%s not found locally, fetching from remote repository",
            group_id, artifact_id, version,
        )
        downloaded = await asyncio.to_thread(
            self.central.ensure_artifact, group_id, artifact_id, version
        )
        return downloaded

    def _iter_local_jars(self):
        """Yield every analyzable jar across all roots, deduplicated.

        Sources and javadoc jars are skipped: they hold no bytecode, so they
        only add scan time to class searches.
        """
        seen = set()
        for root in self.repository_roots:
            if not root.exists():
                continue
            for jar_path in root.rglob("*.jar"):
                if jar_path.name.endswith(("-sources.jar", "-javadoc.jar")):
                    continue
                if jar_path in seen:
                    continue
                seen.add(jar_path)
                yield jar_path

    def _matching_annotations(self, class_data: bytes, annotation: str) -> List[str]:
        """Return annotations on a class matching a name or pattern.

        Accepts a simple name (``Deprecated``), a fully qualified name, or a
        regex. Matching is case-insensitive on the simple name so agents can
        ask for what they remember.
        """
        import re

        info = self.decompiler.read_class_strings(class_data)
        if not info.get("parsed"):
            return []

        needle = annotation.lstrip('@')
        try:
            pattern = re.compile(needle.replace('*', '.*'), re.IGNORECASE)
        except re.error:
            pattern = None

        found = []
        for candidate in info["annotations"]:
            simple = candidate.split('.')[-1]
            if (
                candidate == needle
                or simple.lower() == needle.lower()
                or (pattern is not None and pattern.search(candidate))
            ):
                found.append(candidate)

        return found

    def _path_origin(self, path: Path) -> str:
        """Report whether a file came from the local repository or the cache."""
        try:
            path.relative_to(self.cache_home)
            return "remote-cache"
        except ValueError:
            return "local-repository"

    def _jar_not_found_message(self, group_id: str, artifact_id: str,
                               version: str) -> str:
        """Explain a miss, including why the remote lookup did not help."""
        base = f"Jar file not found: {group_id}:{artifact_id}:{version}"
        if self.central.offline:
            return (
                f"{base}. Offline mode is enabled, so Maven Central was not "
                "queried. Unset MAVEN_OFFLINE to allow remote downloads."
            )
        if not self.auto_download:
            return (
                f"{base}. Auto-download is disabled; call download_artifact "
                "first or set MAVEN_AUTO_DOWNLOAD=true."
            )
        return (
            f"{base}. It is not in the local repository or cache and could not "
            "be downloaded from any configured remote repository. Use "
            "search_maven_central to confirm the coordinates."
        )

    def _missing_repository_message(self) -> str:
        """Actionable message when the local Maven repository directory does not exist."""
        return (
            f"Maven repository not found at '{self.maven_home}'.\n\n"
            f"- Set the MAVEN_REPOSITORY environment variable to point to your repository.\n"
            f"- Running any Maven build (e.g. 'mvn compile') will create the directory.\n"
            f"- Remote tools (search_maven_central, download_artifact) still work without a local repository."
        )
    
    @staticmethod
    def _corrupt_jar_message(jar_path: Path) -> str:
        """Explain how to recover from a corrupt or truncated jar."""
        return (
            f"Jar file is likely truncated or corrupt: {jar_path}. Delete it and "
            "re-download the artifact, or re-run the Maven build that produced it."
        )

    def _extract_packages(self, classes: List[str]) -> Dict[str, int]:
        """Extract package information from class list"""
        packages = {}
        for class_file in classes:
            if '/' in class_file:
                package = '/'.join(class_file.split('/')[:-1]).replace('/', '.')
                packages[package] = packages.get(package, 0) + 1
        return packages
    
    def _categorize_resources(self, resources: List[str]) -> Dict[str, int]:
        """Categorize resource files by type"""
        types = {}
        for resource in resources:
            if '.' in resource:
                ext = resource.split('.')[-1].lower()
                types[ext] = types.get(ext, 0) + 1
            else:
                types['no_extension'] = types.get('no_extension', 0) + 1
        return types
    
    def _parse_manifest(self, manifest_content: str) -> Dict[str, str]:
        """Parse JAR manifest file"""
        manifest = {}
        for line in manifest_content.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                manifest[key.strip()] = value.strip()
        return manifest
    
    def _parse_pom(self, pom_content: str) -> Dict[str, Any]:
        """Parse POM XML content"""
        try:
            pom_dict = xmltodict.parse(pom_content)
            project = pom_dict.get('project', {})
            
            return {
                "group_id": project.get('groupId', ''),
                "artifact_id": project.get('artifactId', ''),
                "version": project.get('version', ''),
                "name": project.get('name', ''),
                "description": project.get('description', ''),
                "dependencies": project.get('dependencies', {})
            }
        except Exception:
            return {"error": "Failed to parse POM"}
    
    async def _extract_class_info(self, group_id: str, artifact_id: str, version: str,
                                 class_pattern: Optional[str] = None,
                                 include_methods: bool = True,
                                 include_fields: bool = True,
                                 include_bytecode: bool = False,
                                 page: int = 1, items_per_page: int = 20,
                                 summarize_large_content: bool = True) -> List[TextContent]:
        """Extract detailed class information"""
        jar_path = await self._resolve_jar_path(group_id, artifact_id, version)
        if not jar_path or not jar_path.exists():
            return [TextContent(type="text", text=self._jar_not_found_message(group_id, artifact_id, version))]
        
        try:
            import re
            classes_info = []
            
            with zipfile.ZipFile(jar_path, 'r') as jar:
                class_files = [e for e in jar.namelist() if e.endswith('.class')]
                
                for class_file in class_files:
                    class_name = class_file.replace('/', '.').replace('.class', '')
                    
                    # Apply pattern filter if provided
                    if class_pattern:
                        if not re.search(class_pattern, class_name):
                            continue
                    
                    class_info = {
                        "class_name": class_name,
                        "file_path": class_file,
                        "package": '.'.join(class_name.split('.')[:-1]) if '.' in class_name else '',
                        "simple_name": class_name.split('.')[-1]
                    }
                    classes_info.append(class_info)
            
            result = {
                "artifact": f"{group_id}:{artifact_id}:{version}",
                "total_classes": len(classes_info),
                "classes": classes_info
            }
            
            # Apply pagination before bytecode analysis so broad queries stay bounded.
            needs_bytecode_analysis = include_methods or include_fields or include_bytecode
            if self.response_manager.should_paginate(result) or (
                needs_bytecode_analysis and len(classes_info) > items_per_page
            ):
                result = self.response_manager.paginate_response(result, page, items_per_page)

            if needs_bytecode_analysis:
                for class_info in result["classes"]:
                    bytecode_info = self.decompiler.analyze_class(
                        jar_path,
                        class_info["class_name"],
                        include_bytecode=include_bytecode
                    )

                    if include_methods:
                        class_info["methods"] = bytecode_info.get("methods", [])

                    if include_fields:
                        class_info["fields"] = bytecode_info.get("fields", [])

                    for key in ("class_signature", "bytecode", "javap_available", "javap_error", "error"):
                        if key in bytecode_info:
                            class_info[key] = bytecode_info[key]

                    if include_bytecode and "javap_output" in bytecode_info:
                        class_info["javap_output"] = bytecode_info["javap_output"]
            
            # Apply summarization if needed
            if summarize_large_content and self.response_manager.should_summarize(json.dumps(result, indent=2)):
                result["content"] = self.response_manager.summarize_large_text(json.dumps(result, indent=2))
                result["summarized"] = True
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error extracting class info: {str(e)}")]
    
    async def _get_dependencies(self, group_id: str, artifact_id: str, version: str,
                              include_transitive: bool = False,
                              page: int = 1, items_per_page: int = 20) -> List[TextContent]:
        """Get Maven dependencies with enhanced analysis"""
        try:
            self.dependency_analyzer.reset_remote_budget()
            analysis = self.dependency_analyzer.analyze_dependencies(
                group_id, artifact_id, version, include_transitive, max_depth=3
            )
            
            # Apply pagination if needed
            if self.response_manager.should_paginate(analysis):
                analysis = self.response_manager.paginate_response(analysis, page, items_per_page)
            
            # Apply summarization if needed
            if self.response_manager.should_summarize(json.dumps(analysis, indent=2)):
                analysis["content"] = self.response_manager.summarize_large_text(json.dumps(analysis, indent=2))
                analysis["summarized"] = True
            
            return [TextContent(type="text", text=json.dumps(analysis, indent=2))]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting dependencies: {str(e)}")]
    
    async def _search_classes(self, class_name: Optional[str] = None,
                            package_pattern: Optional[str] = None,
                            annotation: Optional[str] = None,
                            case_sensitive: bool = True,
                            limit: int = 100, page: int = 1, items_per_page: int = 20) -> List[TextContent]:
        """Search for classes across all jars in every local root"""
        import re
        matches = []
        count = 0

        # Compile the name/package patterns once up front rather than re-running
        # re.search with a raw string for every class in every jar. When
        # case_sensitive is False, matching is case-insensitive (e.g. a query of
        # "arraylist" matches "ArrayList"). Annotation matching keeps its own
        # always-insensitive behavior in _matching_annotations.
        flags = 0 if case_sensitive else re.IGNORECASE
        class_re = (
            re.compile(class_name.replace('*', '.*'), flags) if class_name else None
        )
        package_re = re.compile(package_pattern, flags) if package_pattern else None

        try:
            for jar_path in self._iter_local_jars():
                if count >= limit:
                    break
                
                try:
                    with zipfile.ZipFile(jar_path, 'r') as jar:
                        class_files = [e for e in jar.namelist() if e.endswith('.class')]
                        
                        for class_file in class_files:
                            if count >= limit:
                                break
                            
                            class_full_name = class_file.replace('/', '.').replace('.class', '')
                            simple_name = class_full_name.split('.')[-1]
                            package = '.'.join(class_full_name.split('.')[:-1])
                            
                            # Apply filters
                            if class_re and not class_re.search(simple_name):
                                continue

                            if package_re and not package_re.search(package):
                                continue
                            
                            match_info = {
                                "class_name": class_full_name,
                                "simple_name": simple_name,
                                "package": package,
                                "jar_path": str(jar_path),
                                "artifact_info": self._extract_artifact_info_from_path(jar_path)
                            }

                            # Annotation filtering needs the constant pool, so
                            # only pay that cost for classes that already match
                            # the cheaper name/package filters.
                            if annotation:
                                found = self._matching_annotations(
                                    jar.read(class_file), annotation
                                )
                                if not found:
                                    continue
                                match_info["matched_annotations"] = found

                            matches.append(match_info)
                            count += 1
                
                except zipfile.BadZipFile:
                    logger.warning("Skipping corrupt or truncated jar: %s", jar_path)
                    continue
            
            result = {
                "total_matches": len(matches),
                "matches": matches
            }
            if annotation:
                result["annotation_filter"] = annotation
            
            # Apply pagination if needed
            if self.response_manager.should_paginate(result):
                result = self.response_manager.paginate_response(result, page, items_per_page)
            
            # Apply summarization if needed
            if self.response_manager.should_summarize(json.dumps(result, indent=2)):
                result["content"] = self.response_manager.summarize_large_text(json.dumps(result, indent=2))
                result["summarized"] = True
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
        except Exception:
            # Only zipfile.BadZipFile is an expected, per-jar condition and is
            # handled inside the scan loop above. Anything reaching here is
            # unexpected (a permissions error on the repository root, an OSError
            # mid-walk, a decode bug, ...) and must not be flattened into an
            # ordinary text response, where it is indistinguishable from an
            # empty result. Log it with a traceback and re-raise so the tool
            # handler surfaces it as a clear error. See issue #21.
            logger.error("Unexpected error while searching classes", exc_info=True)
            raise

    def _extract_artifact_info_from_path(self, jar_path: Path) -> Dict[str, str]:
        """Extract Maven artifact info from jar path"""
        try:
            relative_path = jar_path.relative_to(self.maven_home)
            parts = relative_path.parts
            
            if len(parts) >= 3:
                version = parts[-2]
                artifact_id = parts[-3]
                group_id = '.'.join(parts[:-3])
                
                return {
                    "group_id": group_id,
                    "artifact_id": artifact_id,
                    "version": version
                }
        except Exception:
            pass
        
        return {"group_id": "unknown", "artifact_id": "unknown", "version": "unknown"}
    
    async def _extract_source_code(self, group_id: str, artifact_id: str, version: str,
                                 class_name: str, prefer_sources: bool = True,
                                 summarize_large_content: bool = True, max_lines: int = 500) -> List[TextContent]:
        """Extract source code from jar or decompile"""
        # First try to find sources jar
        if prefer_sources:
            sources_jar = await self._resolve_sources_jar_path(group_id, artifact_id, version)
            if sources_jar and sources_jar.exists():
                source_code = self._extract_from_sources_jar(sources_jar, class_name)
                if source_code:
                    result = {
                        "source": "sources-jar",
                        "class_name": class_name,
                        "artifact": f"{group_id}:{artifact_id}:{version}",
                        "sources_jar_path": str(sources_jar),
                        "origin": self._path_origin(sources_jar),
                        "code": source_code
                    }
                    if summarize_large_content and self.response_manager.should_summarize(result["code"]):
                        result["code"] = self.response_manager.summarize_large_text(result["code"])
                        result["summarized"] = True
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        # Fall back to decompilation
        jar_path = await self._resolve_jar_path(group_id, artifact_id, version)
        if not jar_path or not jar_path.exists():
            return [TextContent(type="text", text=self._jar_not_found_message(group_id, artifact_id, version))]
        
        try:
            decompiled_code = self.decompiler.decompile_class(jar_path, class_name)
            result = {
                "source": "decompiled",
                "class_name": class_name,
                "artifact": f"{group_id}:{artifact_id}:{version}",
                "jar_path": str(jar_path),
                "origin": self._path_origin(jar_path),
                "code": decompiled_code or "Failed to decompile class",
                "available_decompilers": list(self.decompiler.available_decompilers.keys())
            }
            if summarize_large_content and self.response_manager.should_summarize(result["code"]):
                result["code"] = self.response_manager.summarize_large_text(result["code"])
                result["summarized"] = True
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error extracting source code: {str(e)}")]

    async def _extract_jar_resource(self, group_id: str, artifact_id: str, version: str,
                                    resource_path: Optional[str] = None,
                                    resource_pattern: Optional[str] = None,
                                    max_bytes: int = 65536,
                                    limit: int = 20) -> List[TextContent]:
        """Extract text resources from a jar by exact path or regex pattern."""
        jar_path = await self._resolve_jar_path(group_id, artifact_id, version)
        if not jar_path or not jar_path.exists():
            return [TextContent(type="text", text=self._jar_not_found_message(group_id, artifact_id, version))]

        if not resource_path and not resource_pattern:
            return [TextContent(type="text", text="Either resource_path or resource_pattern is required")]

        try:
            resources = []
            pattern = re.compile(resource_pattern) if resource_pattern else None

            with zipfile.ZipFile(jar_path, 'r') as jar:
                entries = [
                    entry for entry in jar.namelist()
                    if not entry.endswith('/') and not entry.endswith('.class')
                ]

                if resource_path:
                    matches = [resource_path] if resource_path in entries else []
                else:
                    matches = [entry for entry in entries if pattern and pattern.search(entry)]

                for entry in matches[:limit]:
                    data = jar.read(entry)
                    truncated = len(data) > max_bytes
                    preview = data[:max_bytes]
                    text = preview.decode('utf-8', errors='replace')

                    resources.append({
                        "path": entry,
                        "size_bytes": len(data),
                        "truncated": truncated,
                        "content": text
                    })

            result = {
                "artifact": f"{group_id}:{artifact_id}:{version}",
                "jar_path": str(jar_path),
                "total_matches": len(matches),
                "returned": len(resources),
                "resources": resources
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            return [TextContent(type="text", text=f"Error extracting jar resource: {str(e)}")]
    
    def _get_sources_jar_path(self, group_id: str, artifact_id: str, version: str) -> Optional[Path]:
        """Get path to a locally available sources jar"""
        group_path = group_id.replace('.', os.sep)

        for root in self.repository_roots:
            sources_jar = (
                root / group_path / artifact_id / version
                / f"{artifact_id}-{version}-sources.jar"
            )
            if sources_jar.exists():
                return sources_jar

        return None

    async def _resolve_sources_jar_path(self, group_id: str, artifact_id: str,
                                        version: str) -> Optional[Path]:
        """Resolve a sources jar, downloading it when available remotely.

        Many artifacts publish no sources jar at all, so a miss here is normal
        and simply falls through to decompilation.
        """
        sources_jar = self._get_sources_jar_path(group_id, artifact_id, version)
        if sources_jar and sources_jar.exists():
            return sources_jar

        if not self.auto_download:
            return None

        return await asyncio.to_thread(
            self.central.ensure_artifact,
            group_id, artifact_id, version, "sources", "jar",
        )
    
    def _extract_from_sources_jar(self, sources_jar: Path, class_name: str) -> Optional[str]:
        """Extract source code from sources jar"""
        try:
            java_file = class_name.replace('.', '/') + '.java'
            with zipfile.ZipFile(sources_jar, 'r') as jar:
                if java_file in jar.namelist():
                    return jar.read(java_file).decode('utf-8', errors='ignore')
        except Exception:
            pass
        return None
    
    async def _compare_versions(self, group_id: str, artifact_id: str,
                              version1: str, version2: str,
                              compare_api: bool = True,
                              summarize_large_content: bool = True) -> List[TextContent]:
        """Compare different versions of the same artifact"""
        # Get both jar paths, downloading either side when it is missing
        jar1 = await self._resolve_jar_path(group_id, artifact_id, version1)
        jar2 = await self._resolve_jar_path(group_id, artifact_id, version2)
        
        if not jar1 or not jar1.exists():
            return [TextContent(type="text", text=self._jar_not_found_message(group_id, artifact_id, version1))]
        
        if not jar2 or not jar2.exists():
            return [TextContent(type="text", text=self._jar_not_found_message(group_id, artifact_id, version2))]
        
        try:
            comparison = {
                "artifact": f"{group_id}:{artifact_id}",
                "version1": version1,
                "version2": version2,
                "comparison": {}
            }
            
            # Compare jar sizes
            comparison["comparison"]["size_v1"] = jar1.stat().st_size
            comparison["comparison"]["size_v2"] = jar2.stat().st_size
            comparison["comparison"]["size_diff"] = jar2.stat().st_size - jar1.stat().st_size
            
            # Compare class lists
            with zipfile.ZipFile(jar1, 'r') as z1, zipfile.ZipFile(jar2, 'r') as z2:
                classes1 = set(e for e in z1.namelist() if e.endswith('.class'))
                classes2 = set(e for e in z2.namelist() if e.endswith('.class'))
                
                comparison["comparison"]["classes_added"] = sorted(list(classes2 - classes1))
                comparison["comparison"]["classes_removed"] = sorted(list(classes1 - classes2))
                comparison["comparison"]["classes_common"] = len(classes1 & classes2)

                if compare_api:
                    comparison["comparison"]["api_changes"] = self._compare_public_api(
                        z1, z2, classes1, classes2
                    )
            
            if summarize_large_content and self.response_manager.should_summarize(json.dumps(comparison, indent=2)):
                comparison["content"] = self.response_manager.summarize_large_text(json.dumps(comparison, indent=2))
                comparison["summarized"] = True
            
            return [TextContent(type="text", text=json.dumps(comparison, indent=2))]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error comparing versions: {str(e)}")]
    
    @staticmethod
    def _describe_member(name: str, descriptor: str) -> str:
        """Render a member as ``name descriptor`` for readable diffs."""
        return f"{name}{descriptor}"

    def _compare_public_api(self, z1: zipfile.ZipFile, z2: zipfile.ZipFile,
                            classes1: set, classes2: set) -> Dict[str, Any]:
        """Diff the public API of two jars.

        Only classes present in both versions are compared member by member;
        wholly added or removed classes are already reported separately.
        Members are keyed by name plus descriptor, so an overload change
        reads as one removal and one addition rather than a false "same".
        """
        api_limit = int(os.getenv('MCP_API_DIFF_LIMIT', '2000'))

        removed_members = []
        added_members = []
        changed_classes = []
        unparseable = 0
        compared = 0

        for entry in sorted(classes1 & classes2):
            if compared >= api_limit:
                break

            # Only the public surface matters, and nested/synthetic classes
            # would add noise without changing the contract.
            class_name = entry.replace('/', '.').replace('.class', '')

            try:
                api1 = self.decompiler.read_class_api(z1.read(entry))
                api2 = self.decompiler.read_class_api(z2.read(entry))
            except Exception:
                unparseable += 1
                continue

            if api1 is None or api2 is None:
                unparseable += 1
                continue

            # A class that is not public in either version is not API.
            if not api1.get("public") and not api2.get("public"):
                continue

            compared += 1

            class_changes: Dict[str, Any] = {}

            if api1.get("public") and not api2.get("public"):
                class_changes["visibility"] = "public -> non-public (breaking)"
            elif not api1.get("public") and api2.get("public"):
                class_changes["visibility"] = "non-public -> public"

            if not api1.get("final") and api2.get("final"):
                class_changes["final"] = "became final (breaking for subclasses)"

            if not api1.get("abstract") and api2.get("abstract"):
                class_changes["abstract"] = "became abstract (breaking)"

            for kind in ("methods", "fields"):
                old = {
                    self._describe_member(m["name"], m["descriptor"]): m
                    for m in api1[kind]
                }
                new = {
                    self._describe_member(m["name"], m["descriptor"]): m
                    for m in api2[kind]
                }

                gone = sorted(set(old) - set(new))
                fresh = sorted(set(new) - set(old))

                if gone:
                    class_changes[f"{kind}_removed"] = gone
                    for signature in gone:
                        removed_members.append(f"{class_name}#{signature}")
                if fresh:
                    class_changes[f"{kind}_added"] = fresh
                    for signature in fresh:
                        added_members.append(f"{class_name}#{signature}")

            if class_changes:
                changed_classes.append({
                    "class_name": class_name,
                    **class_changes,
                })

        # Removing a public class or member is what breaks downstream code.
        breaking = len(removed_members) + len(classes1 - classes2)

        result: Dict[str, Any] = {
            "classes_compared": compared,
            "classes_with_api_changes": len(changed_classes),
            "members_added": len(added_members),
            "members_removed": len(removed_members),
            "breaking_changes": breaking,
            "compatible": breaking == 0,
            "summary": (
                f"{len(added_members)} member(s) added, "
                f"{len(removed_members)} removed across "
                f"{len(changed_classes)} class(es); "
                f"{len(classes2 - classes1)} class(es) added, "
                f"{len(classes1 - classes2)} removed"
            ),
            "changes": changed_classes,
            "note": (
                "Members are compared as declared on each class. A member "
                "listed as removed may still be callable if it moved to a "
                "supertype, but code compiled against the old declaration "
                "can still break, so treat removals as suspect rather than "
                "certain breakage."
            ),
        }

        if unparseable:
            result["unparseable_classes"] = unparseable
        if compared >= api_limit:
            result["truncated"] = (
                f"Stopped after comparing {api_limit} classes "
                "(raise MCP_API_DIFF_LIMIT for a full diff)"
            )

        return result

    async def _find_usage_examples(self, class_name: str,
                                 method_name: Optional[str] = None,
                                 search_tests: bool = True,
                                 limit: int = 50, page: int = 1, items_per_page: int = 20) -> List[TextContent]:
        """Find classes that reference a given class, and optionally a method.

        A class that uses another class carries that type (and any method it
        calls) in its constant pool, so scanning the pool finds real callers
        without decompiling every candidate.
        """
        try:
            target = class_name.strip()
            if not target:
                return [TextContent(type="text", text="class_name is required")]

            simple_target = target.split('.')[-1]
            # Constant pool stores internal form: com/example/Foo
            internal = target.replace('.', '/')
            internal_bytes = internal.encode('utf-8')

            matches = []
            scanned = 0
            seen_classes = set()
            # A full repository can hold hundreds of thousands of classes;
            # cap the scan so the tool stays responsive.
            scan_budget = int(os.getenv('MCP_USAGE_SCAN_LIMIT', '200000'))
            budget_exhausted = False

            for jar_path in self._iter_local_jars():
                if len(matches) >= limit or budget_exhausted:
                    break

                # Test jars are the best usage examples, but most local
                # repositories hold very few, so other jars are still scanned
                # and simply ranked lower.
                is_test_jar = 'test' in jar_path.name.lower()
                if is_test_jar and not search_tests:
                    continue

                try:
                    with zipfile.ZipFile(jar_path, 'r') as jar:
                        for entry in jar.namelist():
                            if len(matches) >= limit:
                                break
                            if scanned >= scan_budget:
                                budget_exhausted = True
                                break
                            if not entry.endswith('.class'):
                                continue

                            user_class = entry.replace('/', '.').replace('.class', '')
                            # A class always references itself.
                            if user_class == target:
                                continue
                            # The same class appears in many artifact versions;
                            # report each distinct class once.
                            if user_class in seen_classes:
                                continue

                            raw = jar.read(entry)
                            scanned += 1

                            # Cheap pre-filter: if the internal name does not
                            # appear anywhere in the raw bytes, the class
                            # cannot reference it, so skip the pool parse.
                            if internal_bytes not in raw:
                                continue

                            info = self.decompiler.read_class_strings(raw)
                            if not info.get("parsed"):
                                continue

                            strings = set(info["strings"])

                            references_class = (
                                internal in strings
                                or target in strings
                                or any(internal in s for s in strings)
                            )
                            if not references_class:
                                continue

                            if method_name and method_name not in strings:
                                continue

                            seen_classes.add(user_class)
                            matches.append({
                                "using_class": user_class,
                                "jar_path": str(jar_path),
                                "is_test_jar": is_test_jar,
                                "artifact_info": self._extract_artifact_info_from_path(jar_path),
                                "references": target,
                                "method": method_name,
                            })

                except Exception:
                    continue  # Skip corrupted jars

            # Surface test-jar usages first: they are the best examples.
            matches.sort(key=lambda m: (not m["is_test_jar"], m["using_class"]))

            result = {
                "target_class": target,
                "target_simple_name": simple_target,
                "method_name": method_name,
                "classes_scanned": scanned,
                "total_matches": len(matches),
                "matches": matches,
            }
            if budget_exhausted:
                result["truncated"] = (
                    f"Stopped after scanning {scanned} classes "
                    "(raise MCP_USAGE_SCAN_LIMIT to search further)"
                )

            if not matches:
                result["hint"] = (
                    "No local artifact references this class. It may not be "
                    "used by anything installed; try search_maven_central to "
                    "find published artifacts instead."
                )

            if self.response_manager.should_paginate(result):
                result = self.response_manager.paginate_response(result, page, items_per_page)

            if self.response_manager.should_summarize(json.dumps(result, indent=2)):
                result["content"] = self.response_manager.summarize_large_text(
                    json.dumps(result, indent=2)
                )
                result["summarized"] = True

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            return [TextContent(type="text", text=f"Error finding usage examples: {str(e)}")]
    
    async def _get_dependency_tree(self, group_id: str, artifact_id: str, version: str,
                                  max_depth: int = 3, summarize_large_content: bool = True) -> List[TextContent]:
        """Get complete dependency tree"""
        try:
            self.dependency_analyzer.reset_remote_budget()
            tree = self.dependency_analyzer.find_dependency_tree(group_id, artifact_id, version)
            if summarize_large_content and self.response_manager.should_summarize(json.dumps(tree, indent=2)):
                tree = self.response_manager.summarize_large_text(json.dumps(tree, indent=2))
            return [TextContent(type="text", text=json.dumps(tree, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting dependency tree: {str(e)}")]
    
    async def _find_dependents(self, group_id: str, artifact_id: str, 
                             version: Optional[str] = None,
                             limit: int = 100, page: int = 1, items_per_page: int = 20) -> List[TextContent]:
        """Find artifacts that depend on the target"""
        try:
            dependents = self.dependency_analyzer.find_dependents(group_id, artifact_id, version)
            result = {
                "target_artifact": f"{group_id}:{artifact_id}" + (f":{version}" if version else ""),
                "dependents": dependents,
                "total_dependents": len(dependents)
            }
            # Apply pagination if needed
            if self.response_manager.should_paginate(result):
                result = self.response_manager.paginate_response(result, page, items_per_page)
            
            # Apply summarization if needed
            if self.response_manager.should_summarize(json.dumps(result, indent=2)):
                result["content"] = self.response_manager.summarize_large_text(json.dumps(result, indent=2))
                result["summarized"] = True
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error finding dependents: {str(e)}")]
    
    async def _get_version_info(self, group_id: str, artifact_id: str,
                                include_remote: bool = False,
                                limit: int = 50, page: int = 1, items_per_page: int = 20) -> List[TextContent]:
        """Get version information for an artifact"""
        try:
            version_info = self.dependency_analyzer.get_version_info(group_id, artifact_id)

            if include_remote:
                version_info["remote"] = await self._collect_remote_versions(
                    group_id, artifact_id, limit
                )

            # Apply pagination if needed
            if self.response_manager.should_paginate(version_info):
                version_info = self.response_manager.paginate_response(version_info, page, items_per_page)
            
            # Apply summarization if needed
            if self.response_manager.should_summarize(json.dumps(version_info, indent=2)):
                version_info["content"] = self.response_manager.summarize_large_text(json.dumps(version_info, indent=2))
                version_info["summarized"] = True
            return [TextContent(type="text", text=json.dumps(version_info, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting version info: {str(e)}")]

    async def _collect_remote_versions(self, group_id: str, artifact_id: str,
                                       limit: int) -> Dict[str, Any]:
        """Fetch remote version info, reporting errors instead of raising."""
        if self.central.offline:
            return {"available": False, "reason": "offline mode is enabled"}

        try:
            return await asyncio.to_thread(
                self.central.get_versions, group_id, artifact_id, limit
            )
        except MavenRemoteError as exc:
            return {"available": False, "reason": str(exc)}

    async def _search_maven_central(self, query: Optional[str] = None,
                                    group_id: Optional[str] = None,
                                    artifact_id: Optional[str] = None,
                                    class_name: Optional[str] = None,
                                    fully_qualified_class: Optional[str] = None,
                                    packaging: Optional[str] = None,
                                    all_versions: bool = False,
                                    limit: int = 20,
                                    page: int = 1) -> List[TextContent]:
        """Search a remote Maven repository index for artifacts."""
        try:
            page = max(1, int(page))
            limit = max(1, int(limit))
            start = (page - 1) * limit

            result = await asyncio.to_thread(
                self.central.search,
                query, group_id, artifact_id, class_name,
                fully_qualified_class, packaging, limit, start, all_versions,
            )

            # Tell the agent which hits can be analyzed without a download.
            for artifact in result["artifacts"]:
                if artifact.get("version"):
                    local = self._get_jar_path(
                        artifact["group_id"], artifact["artifact_id"], artifact["version"]
                    )
                    artifact["installed_locally"] = local is not None

            result["page"] = page
            result["items_per_page"] = limit

            if self.response_manager.should_summarize(json.dumps(result, indent=2)):
                result["content"] = self.response_manager.summarize_large_text(
                    json.dumps(result, indent=2)
                )
                result["summarized"] = True

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except ValueError as e:
            return [TextContent(type="text", text=f"Invalid search request: {str(e)}")]
        except MavenRemoteError as e:
            return [TextContent(type="text", text=f"Remote search failed: {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error searching Maven Central: {str(e)}")]

    async def _get_remote_versions(self, group_id: str, artifact_id: str,
                                   include_snapshots: bool = True,
                                   limit: int = 100) -> List[TextContent]:
        """List versions published on the remote repository."""
        try:
            result = await asyncio.to_thread(
                self.central.get_versions, group_id, artifact_id, limit
            )

            # Snapshot filtering lives here, not in MavenCentralClient, which
            # stays a faithful view of the remote index. Detection is a simple
            # case-insensitive "-SNAPSHOT" suffix check (no version parsing).
            def _is_snapshot(version: str) -> bool:
                return str(version).upper().endswith("-SNAPSHOT")

            if not include_snapshots and isinstance(result.get("versions"), list):
                result["versions"] = [
                    v for v in result["versions"] if not _is_snapshot(v)
                ]

            installed = {
                entry["version"]
                for entry in self.dependency_analyzer.get_version_info(
                    group_id, artifact_id
                ).get("versions", [])
            }
            if not include_snapshots:
                installed = {v for v in installed if not _is_snapshot(v)}
            result["installed_versions"] = sorted(installed)

            if self.response_manager.should_summarize(json.dumps(result, indent=2)):
                result["content"] = self.response_manager.summarize_large_text(
                    json.dumps(result, indent=2)
                )
                result["summarized"] = True

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except MavenRemoteError as e:
            return [TextContent(type="text", text=f"Could not list remote versions: {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting remote versions: {str(e)}")]

    async def _download_artifact(self, group_id: str, artifact_id: str, version: str,
                                 include_sources: bool = True,
                                 include_javadoc: bool = False,
                                 classifier: Optional[str] = None,
                                 force: bool = False) -> List[TextContent]:
        """Download an artifact into the cache so other tools can analyze it."""
        try:
            resolved_version = version
            if version.strip().lower() in ("latest", "release"):
                resolved_version = await asyncio.to_thread(
                    self.central.get_latest_version, group_id, artifact_id
                )
                if not resolved_version:
                    return [TextContent(
                        type="text",
                        text=(
                            f"Could not resolve the latest version of "
                            f"{group_id}:{artifact_id} from any remote repository"
                        ),
                    )]

            result = await asyncio.to_thread(
                self.central.download_bundle,
                group_id, artifact_id, resolved_version,
                include_sources, include_javadoc, classifier, force,
            )

            if resolved_version != version:
                result["requested_version"] = version
                result["resolved_version"] = resolved_version

            result["next_steps"] = (
                "The artifact is now cached; analyze it with extract_class_info, "
                "extract_source_code, get_dependencies, or analyze_jar using "
                f"version '{resolved_version}'."
            )

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except MavenRemoteError as e:
            return [TextContent(type="text", text=f"Download failed: {str(e)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error downloading artifact: {str(e)}")]

    async def _analyze_jar_structure(self, group_id: str, artifact_id: str, version: str,
                                   summarize_large_content: bool = True) -> List[TextContent]:
        """Analyze jar file structure"""
        jar_path = await self._resolve_jar_path(group_id, artifact_id, version)
        if not jar_path or not jar_path.exists():
            return [TextContent(type="text", text=self._jar_not_found_message(group_id, artifact_id, version))]
        
        try:
            # JavaDecompiler currently turns archive errors into a generic result,
            # so validate here to keep the tool-facing error actionable.
            if jar_path.is_file():
                with zipfile.ZipFile(jar_path, "r"):
                    pass
            analysis = self.decompiler.analyze_jar_structure(jar_path)
            analysis["origin"] = self._path_origin(jar_path)
            if summarize_large_content and self.response_manager.should_summarize(json.dumps(analysis, indent=2)):
                analysis["content"] = self.response_manager.summarize_large_text(json.dumps(analysis, indent=2))
                analysis["summarized"] = True
            return [TextContent(type="text", text=json.dumps(analysis, indent=2))]
        except zipfile.BadZipFile:
            return [TextContent(type="text", text=self._corrupt_jar_message(jar_path))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error analyzing jar structure: {str(e)}")]
    
    async def _extract_method_info(self, group_id: str, artifact_id: str, version: str,
                                 class_name: str, method_pattern: Optional[str] = None,
                                 include_bytecode: bool = False, max_methods: int = 10) -> List[TextContent]:
        """Extract specific method information from a Java class"""
        jar_path = await self._resolve_jar_path(group_id, artifact_id, version)
        if not jar_path or not jar_path.exists():
            return [TextContent(type="text", text=self._jar_not_found_message(group_id, artifact_id, version))]
        
        try:
            # Fail before the decompiler's generic fallback hides BadZipFile.
            if jar_path.is_file():
                with zipfile.ZipFile(jar_path, "r"):
                    pass
            # Prefer real source from a sources jar: it carries Javadoc, which
            # decompiled output almost never does. Fall back to decompilation.
            source_code = None
            source = None
            sources_jar = await self._resolve_sources_jar_path(
                group_id, artifact_id, version
            )
            if sources_jar and sources_jar.exists():
                source_code = self._extract_from_sources_jar(sources_jar, class_name)
                if source_code:
                    source = "sources-jar"
            if not source_code:
                source_code = await self._extract_source_code_internal(jar_path, class_name)
                source = "decompiled"
            if not source_code:
                return [TextContent(type="text", text=f"Could not extract source code for class: {class_name}")]

            # Parse methods from source code
            methods = self._extract_methods_from_source(source_code, method_pattern, max_methods)

            result = {
                "class_name": class_name,
                "artifact": f"{group_id}:{artifact_id}:{version}",
                "source": source,
                "total_methods_found": len(methods),
                "methods": methods,
                "method_pattern": method_pattern or "all methods"
            }
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
        except zipfile.BadZipFile:
            return [TextContent(type="text", text=self._corrupt_jar_message(jar_path))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error extracting method info: {str(e)}")]
    
    def _extract_methods_from_source(self, source_code: str, method_pattern: Optional[str] = None, 
                                   max_methods: int = 10) -> List[Dict[str, Any]]:
        """Extract method information from Java source code"""
        import re
        
        methods = []
        lines = source_code.split('\n')
        
        # Pattern to match method declarations
        method_pattern_regex = re.compile(
            r'^\s*(public|private|protected|static|final)?\s*'
            r'(?:<[^>]+>\s+)?'  # Generic type parameters
            r'(\w+(?:<[^>]+>)?)\s+'  # Return type
            r'(\w+)\s*'  # Method name
            r'\([^)]*\)'  # Parameters
        )
        
        current_method = None
        brace_count = 0
        method_start_line = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Skip comments and empty lines
            if stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*') or not stripped:
                continue
            
            # Check if this line starts a method
            match = method_pattern_regex.match(stripped)
            if match and not current_method:
                method_name = match.group(3)
                
                # Apply pattern filter if provided
                if method_pattern and not re.search(method_pattern, method_name):
                    continue
                
                current_method = {
                    "name": method_name,
                    "return_type": match.group(2),
                    "modifiers": match.group(1) or "",
                    "javadoc": self._javadoc_above(lines, i),
                    "signature": stripped,
                    "start_line": i + 1,
                    "body": []
                }
                method_start_line = i + 1
                brace_count = 0
                continue
            
            # If we're in a method, collect the body
            if current_method:
                current_method["body"].append(line)
                
                # Count braces to find method end
                brace_count += line.count('{') - line.count('}')
                
                if brace_count <= 0 and line.strip().endswith('}'):
                    # Method ended
                    current_method["end_line"] = i + 1
                    current_method["body"] = '\n'.join(current_method["body"])
                    
                    methods.append(current_method)
                    current_method = None
                    
                    if len(methods) >= max_methods:
                        break

        return methods

    def _javadoc_above(self, lines: List[str], decl_index: int) -> Optional[str]:
        """Return the Javadoc block ending immediately above a declaration.

        Only ``/** ... */`` blocks count; ``//`` and ``/* */`` comments are
        ignored. Blank lines and annotation lines are allowed between the block
        and the declaration. The comment markers (opening ``/**``, closing
        ``*/`` and each line's leading ``*``) are stripped; the remaining text
        is returned as-is. Returns None when there is no doc comment.
        """
        # Walk up past blank and annotation lines to the line that would end
        # the doc block.
        j = decl_index - 1
        while j >= 0:
            s = lines[j].strip()
            if s == "" or s.startswith("@"):
                j -= 1
                continue
            break

        if j < 0 or not lines[j].strip().endswith("*/"):
            return None

        end = j
        start = None
        k = end
        while k >= 0:
            s = lines[k].strip()
            if "/**" in s:
                start = k
                break
            # Interior lines of a Javadoc block are conventionally "*"-led;
            # anything else means this is not a contiguous /** */ block.
            if k != end and not s.startswith("*"):
                break
            k -= 1

        if start is None:
            return None

        cleaned = []
        for raw in lines[start:end + 1]:
            s = raw.strip()
            if s.startswith("/**"):
                s = s[3:]
            if s.endswith("*/"):
                s = s[:-2]
            s = s.strip()
            if s.startswith("*"):
                s = s[1:].strip()
            cleaned.append(s)

        text = "\n".join(cleaned).strip()
        return text or None

    async def _extract_source_code_internal(self, jar_path: Path, class_name: str) -> Optional[str]:
        """Internal method to extract source code without response formatting"""
        try:
            # First try to find sources jar
            sources_jar = self._get_sources_jar_path_from_jar(jar_path)
            if sources_jar and sources_jar.exists():
                source_code = self._extract_from_sources_jar(sources_jar, class_name)
                if source_code:
                    return source_code
            
            # Fall back to decompilation
            return self.decompiler.decompile_class(jar_path, class_name)
            
        except Exception:
            return None
    
    def _get_sources_jar_path_from_jar(self, jar_path: Path) -> Optional[Path]:
        """Get path to sources jar file from main jar path"""
        jar_dir = jar_path.parent
        jar_name = jar_path.stem
        
        # Remove version suffix to get artifact name
        if '-' in jar_name:
            artifact_name = jar_name.rsplit('-', 1)[0]
            version = jar_name.rsplit('-', 1)[1]
            sources_jar = jar_dir / f"{artifact_name}-{version}-sources.jar"
            return sources_jar if sources_jar.exists() else None
        
        return None

    async def run(self):
        """Run the MCP server"""
        logger.info("Starting Maven Decoder MCP Server...")
        try:
            async with stdio_server() as (read_stream, write_stream):
                logger.info("Connected to stdio streams")
                logger.info("Server capabilities: tools support enabled")
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="maven-decoder",
                        server_version=get_version(),
                        capabilities=ServerCapabilities(
                            tools=ToolsCapability(listChanged=False)
                        )
                    )
                )
        except Exception as e:
            logger.error(f"Error running MCP server: {e}", exc_info=True)
            raise

def main():
    """Main entry point for the maven-decoder-mcp command"""
    logger.info("="*60)
    logger.info("Maven Decoder MCP Server - Starting up...")
    logger.info("="*60)
    
    try:
        server = MavenDecoderServer()
        logger.info("Server instance created successfully")
        logger.info("Running async server loop...")
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Server startup failed: {e}", exc_info=True)
        raise
    finally:
        logger.info("Maven Decoder MCP Server shutdown complete")

if __name__ == "__main__":
    main()
