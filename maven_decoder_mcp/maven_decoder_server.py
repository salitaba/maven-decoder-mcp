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
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging
import tempfile
import subprocess

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
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

class MavenDecoderServer:
    """MCP Server for Maven jar file analysis"""
    
    def __init__(self):
        logger.info("Initializing Maven Decoder MCP Server...")
        self.server = Server("maven-decoder")
        self.maven_home = Path.home() / ".m2" / "repository"
        logger.info(f"Maven repository location: {self.maven_home}")
        
        if not self.maven_home.exists():
            logger.warning(f"Maven repository not found at {self.maven_home}")
        else:
            # Count artifacts for info
            jar_count = len(list(self.maven_home.rglob("*.jar")))
            pom_count = len(list(self.maven_home.rglob("*.pom")))
            logger.info(f"Found {jar_count} jar files and {pom_count} POM files in repository")
        
        logger.info("Initializing Java decompiler...")
        self.decompiler = JavaDecompiler()
        logger.info(f"Available decompilers: {list(self.decompiler.available_decompilers.keys())}")
        
        logger.info("Initializing Maven dependency analyzer...")
        self.dependency_analyzer = MavenDependencyAnalyzer(self.maven_home)
        
        logger.info("Setting up MCP server handlers...")
        self.setup_handlers()
        logger.info("Maven Decoder MCP Server initialization complete!")
    
    def setup_handlers(self):
        """Setup MCP server handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools for Maven jar analysis"""
            logger.info("MCP client requested tool list")
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
                            "limit": {"type": "integer", "default": 50, "description": "Maximum number of artifacts to return"}
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
                            "include_manifest": {"type": "boolean", "default": True, "description": "Include JAR manifest"}
                        },
                        "required": ["group_id", "artifact_id", "version"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="extract_class_info",
                    description="Extract detailed information about Java classes in a jar",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "group_id": {"type": "string", "description": "Maven group ID"},
                            "artifact_id": {"type": "string", "description": "Maven artifact ID"},
                            "version": {"type": "string", "description": "Maven version"},
                            "class_pattern": {"type": "string", "description": "Pattern to match class names (regex supported)"},
                            "include_methods": {"type": "boolean", "default": True, "description": "Include method signatures"},
                            "include_fields": {"type": "boolean", "default": True, "description": "Include field information"}
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
                            "include_transitive": {"type": "boolean", "default": False, "description": "Include transitive dependencies"}
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
                            "limit": {"type": "integer", "default": 100, "description": "Maximum results to return"}
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
                            "prefer_sources": {"type": "boolean", "default": True, "description": "Prefer source jar over decompilation"}
                        },
                        "required": ["group_id", "artifact_id", "version", "class_name"],
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
                            "version1": {"type": "string", "description": "First version to compare"},
                            "version2": {"type": "string", "description": "Second version to compare"},
                            "compare_api": {"type": "boolean", "default": True, "description": "Compare public API changes"}
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
                            "search_tests": {"type": "boolean", "default": True, "description": "Search in test jars"}
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
                            "version": {"type": "string", "description": "Maven version"}
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
                            "version": {"type": "string", "description": "Specific version to search for (optional)"}
                        },
                        "required": ["group_id", "artifact_id"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="get_version_info",
                    description="Get all available versions of an artifact",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "group_id": {"type": "string", "description": "Maven group ID"},
                            "artifact_id": {"type": "string", "description": "Maven artifact ID"}
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
                            "version": {"type": "string", "description": "Maven version"}
                        },
                        "required": ["group_id", "artifact_id", "version"],
                        "additionalProperties": False
                    }
                )
            ]
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
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Error handling tool {name}: {e}", exc_info=True)
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def _list_artifacts(self, group_id: Optional[str] = None, 
                            artifact_id: Optional[str] = None, 
                            version: Optional[str] = None, 
                            limit: int = 50) -> List[TextContent]:
        """List Maven artifacts with optional filtering"""
        logger.debug(f"Listing artifacts with filters: group_id={group_id}, artifact_id={artifact_id}, version={version}, limit={limit}")
        artifacts = []
        count = 0
        
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
                            artifacts.append({
                                "group_id": self._path_to_group_id(group_path),
                                "artifact_id": artifact_name,
                                "version": version_name,
                                "jar_files": [f.name for f in jar_files],
                                "path": str(version_dir)
                            })
                            count += 1
                            if count >= limit:
                                break
                    
                    if count >= limit:
                        break
                    
                    if count >= limit:
                        break
                if count >= limit:
                    break
            
            result = {
                "total_found": count,
                "artifacts": artifacts[:limit]
            }
            
            logger.info(f"Found {count} artifacts matching criteria")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error listing artifacts: {str(e)}")]
    
    def _path_to_group_id(self, path: Path) -> str:
        """Convert file path to Maven group ID"""
        relative = path.relative_to(self.maven_home)
        return str(relative).replace(os.sep, '.')
    
    async def _analyze_jar(self, group_id: str, artifact_id: str, version: str,
                          include_bytecode: bool = False, include_manifest: bool = True) -> List[TextContent]:
        """Analyze a specific jar file"""
        jar_path = self._get_jar_path(group_id, artifact_id, version)
        if not jar_path or not jar_path.exists():
            return [TextContent(type="text", text=f"Jar file not found: {group_id}:{artifact_id}:{version}")]
        
        try:
            analysis = {
                "artifact": f"{group_id}:{artifact_id}:{version}",
                "jar_path": str(jar_path),
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
            
            return [TextContent(type="text", text=json.dumps(analysis, indent=2))]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error analyzing jar: {str(e)}")]
    
    def _get_jar_path(self, group_id: str, artifact_id: str, version: str) -> Optional[Path]:
        """Get path to jar file"""
        group_path = group_id.replace('.', os.sep)
        jar_dir = self.maven_home / group_path / artifact_id / version
        
        # Look for the main jar file
        main_jar = jar_dir / f"{artifact_id}-{version}.jar"
        if main_jar.exists():
            return main_jar
        
        # Look for any jar file in the directory
        jar_files = list(jar_dir.glob("*.jar"))
        if jar_files:
            return jar_files[0]
        
        return None
    
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
                                 include_fields: bool = True) -> List[TextContent]:
        """Extract detailed class information"""
        jar_path = self._get_jar_path(group_id, artifact_id, version)
        if not jar_path or not jar_path.exists():
            return [TextContent(type="text", text=f"Jar file not found: {group_id}:{artifact_id}:{version}")]
        
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
                    
                    # Basic class info (without bytecode analysis)
                    class_info = {
                        "class_name": class_name,
                        "file_path": class_file,
                        "package": '.'.join(class_name.split('.')[:-1]) if '.' in class_name else '',
                        "simple_name": class_name.split('.')[-1]
                    }
                    
                    # TODO: Add bytecode analysis for methods and fields
                    # This would require additional libraries like javatools or ASM
                    if include_methods:
                        class_info["methods"] = "Bytecode analysis not implemented yet"
                    
                    if include_fields:
                        class_info["fields"] = "Bytecode analysis not implemented yet"
                    
                    classes_info.append(class_info)
            
            result = {
                "artifact": f"{group_id}:{artifact_id}:{version}",
                "total_classes": len(classes_info),
                "classes": classes_info
            }
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error extracting class info: {str(e)}")]
    
    async def _get_dependencies(self, group_id: str, artifact_id: str, version: str,
                              include_transitive: bool = False) -> List[TextContent]:
        """Get Maven dependencies with enhanced analysis"""
        try:
            analysis = self.dependency_analyzer.analyze_dependencies(
                group_id, artifact_id, version, include_transitive, max_depth=3
            )
            
            return [TextContent(type="text", text=json.dumps(analysis, indent=2))]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting dependencies: {str(e)}")]
    
    async def _search_classes(self, class_name: Optional[str] = None,
                            package_pattern: Optional[str] = None,
                            annotation: Optional[str] = None,
                            limit: int = 100) -> List[TextContent]:
        """Search for classes across all jars"""
        import re
        matches = []
        count = 0
        
        try:
            for jar_path in self.maven_home.rglob("*.jar"):
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
                            if class_name and not re.search(class_name.replace('*', '.*'), simple_name):
                                continue
                            
                            if package_pattern and not re.search(package_pattern, package):
                                continue
                            
                            # TODO: Add annotation search (requires bytecode analysis)
                            if annotation:
                                continue  # Skip for now
                            
                            matches.append({
                                "class_name": class_full_name,
                                "simple_name": simple_name,
                                "package": package,
                                "jar_path": str(jar_path),
                                "artifact_info": self._extract_artifact_info_from_path(jar_path)
                            })
                            count += 1
                
                except Exception:
                    continue  # Skip corrupted jars
            
            result = {
                "total_matches": len(matches),
                "matches": matches
            }
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error searching classes: {str(e)}")]
    
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
                                 class_name: str, prefer_sources: bool = True) -> List[TextContent]:
        """Extract source code from jar or decompile"""
        # First try to find sources jar
        if prefer_sources:
            sources_jar = self._get_sources_jar_path(group_id, artifact_id, version)
            if sources_jar and sources_jar.exists():
                source_code = self._extract_from_sources_jar(sources_jar, class_name)
                if source_code:
                    result = {
                        "source": "sources-jar",
                        "class_name": class_name,
                        "artifact": f"{group_id}:{artifact_id}:{version}",
                        "code": source_code
                    }
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        # Fall back to decompilation
        jar_path = self._get_jar_path(group_id, artifact_id, version)
        if not jar_path or not jar_path.exists():
            return [TextContent(type="text", text=f"Jar file not found: {group_id}:{artifact_id}:{version}")]
        
        try:
            decompiled_code = self.decompiler.decompile_class(jar_path, class_name)
            result = {
                "source": "decompiled",
                "class_name": class_name,
                "artifact": f"{group_id}:{artifact_id}:{version}",
                "code": decompiled_code or "Failed to decompile class",
                "available_decompilers": list(self.decompiler.available_decompilers.keys())
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error extracting source code: {str(e)}")]
    
    def _get_sources_jar_path(self, group_id: str, artifact_id: str, version: str) -> Optional[Path]:
        """Get path to sources jar file"""
        group_path = group_id.replace('.', os.sep)
        jar_dir = self.maven_home / group_path / artifact_id / version
        sources_jar = jar_dir / f"{artifact_id}-{version}-sources.jar"
        return sources_jar if sources_jar.exists() else None
    
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
                              compare_api: bool = True) -> List[TextContent]:
        """Compare different versions of the same artifact"""
        # Get both jar paths
        jar1 = self._get_jar_path(group_id, artifact_id, version1)
        jar2 = self._get_jar_path(group_id, artifact_id, version2)
        
        if not jar1 or not jar1.exists():
            return [TextContent(type="text", text=f"Version {version1} not found")]
        
        if not jar2 or not jar2.exists():
            return [TextContent(type="text", text=f"Version {version2} not found")]
        
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
            
            # TODO: Add API comparison (requires bytecode analysis)
            if compare_api:
                comparison["comparison"]["api_changes"] = "API comparison not yet implemented"
            
            return [TextContent(type="text", text=json.dumps(comparison, indent=2))]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error comparing versions: {str(e)}")]
    
    async def _find_usage_examples(self, class_name: str,
                                 method_name: Optional[str] = None,
                                 search_tests: bool = True) -> List[TextContent]:
        """Find usage examples in test jars"""
        # TODO: Implement usage search in test jars and source code
        return [TextContent(type="text", text="Usage example search not yet implemented")]
    
    async def _get_dependency_tree(self, group_id: str, artifact_id: str, version: str) -> List[TextContent]:
        """Get complete dependency tree"""
        try:
            tree = self.dependency_analyzer.find_dependency_tree(group_id, artifact_id, version)
            return [TextContent(type="text", text=json.dumps(tree, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting dependency tree: {str(e)}")]
    
    async def _find_dependents(self, group_id: str, artifact_id: str, 
                             version: Optional[str] = None) -> List[TextContent]:
        """Find artifacts that depend on the target"""
        try:
            dependents = self.dependency_analyzer.find_dependents(group_id, artifact_id, version)
            result = {
                "target_artifact": f"{group_id}:{artifact_id}" + (f":{version}" if version else ""),
                "dependents": dependents,
                "total_dependents": len(dependents)
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error finding dependents: {str(e)}")]
    
    async def _get_version_info(self, group_id: str, artifact_id: str) -> List[TextContent]:
        """Get version information for an artifact"""
        try:
            version_info = self.dependency_analyzer.get_version_info(group_id, artifact_id)
            return [TextContent(type="text", text=json.dumps(version_info, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting version info: {str(e)}")]
    
    async def _analyze_jar_structure(self, group_id: str, artifact_id: str, version: str) -> List[TextContent]:
        """Analyze jar file structure"""
        jar_path = self._get_jar_path(group_id, artifact_id, version)
        if not jar_path or not jar_path.exists():
            return [TextContent(type="text", text=f"Jar file not found: {group_id}:{artifact_id}:{version}")]
        
        try:
            analysis = self.decompiler.analyze_jar_structure(jar_path)
            return [TextContent(type="text", text=json.dumps(analysis, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error analyzing jar structure: {str(e)}")]

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
                        server_version="1.0.0",
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
