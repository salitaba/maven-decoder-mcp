"""
Java Decompiler Integration for Maven Decoder MCP Server

Provides integration with various Java decompilers and bytecode analysis tools.
"""

import subprocess
import tempfile
import os
import zipfile
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class JavaDecompiler:
    """Java bytecode decompiler and analyzer"""
    
    def __init__(self):
        self.available_decompilers = self._detect_decompilers()
    
    def _detect_decompilers(self) -> Dict[str, str]:
        """Detect available decompilers on the system"""
        decompilers = {}
        
        # Check for CFR (free Java decompiler)
        try:
            cfr_paths = ['cfr.jar', 'decompilers/cfr.jar']
            for cfr_path in cfr_paths:
                if Path(cfr_path).exists():
                    result = subprocess.run(['java', '-jar', cfr_path, '--help'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        decompilers['cfr'] = cfr_path
                        break
        except Exception:
            pass
        
        # Check for Fernflower (IntelliJ's decompiler)
        try:
            if Path('fernflower.jar').exists():
                result = subprocess.run(['java', '-jar', 'fernflower.jar'], 
                                      capture_output=True, text=True, timeout=5)
                decompilers['fernflower'] = 'fernflower.jar'
        except Exception:
            pass
        
        # Check for Procyon
        try:
            procyon_paths = ['procyon-decompiler.jar', 'decompilers/procyon-decompiler.jar']
            for procyon_path in procyon_paths:
                if Path(procyon_path).exists():
                    result = subprocess.run(['java', '-jar', procyon_path, '--help'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        decompilers['procyon'] = procyon_path
                        break
        except Exception:
            pass
        
        # Check for javap (built-in with JDK)
        try:
            result = subprocess.run(['javap', '-help'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                decompilers['javap'] = 'javap'
        except Exception:
            pass
        
        return decompilers
    
    def decompile_class(self, jar_path: Path, class_name: str, 
                       decompiler: Optional[str] = None) -> Optional[str]:
        """Decompile a specific class from a jar file"""
        logger.info(f"Attempting to decompile {class_name} from {jar_path}")
        
        if not self.available_decompilers:
            logger.warning("No decompilers available, using fallback")
            return self._fallback_class_info(jar_path, class_name)
        
        # Choose decompiler
        if not decompiler:
            decompiler = next(iter(self.available_decompilers.keys()))
        
        if decompiler not in self.available_decompilers:
            logger.warning(f"Decompiler {decompiler} not available")
            return self._fallback_class_info(jar_path, class_name)
        
        logger.info(f"Using decompiler: {decompiler}")
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Extract class file
                class_file_path = class_name.replace('.', '/') + '.class'
                logger.debug(f"Looking for class file: {class_file_path}")
                
                with zipfile.ZipFile(jar_path, 'r') as jar:
                    if class_file_path not in jar.namelist():
                        logger.error(f"Class file not found in jar: {class_file_path}")
                        return self._fallback_class_info(jar_path, class_name)
                    
                    # Extract the class file
                    extracted_class = temp_path / 'extracted.class'
                    logger.debug(f"Extracting to: {extracted_class}")
                    with open(extracted_class, 'wb') as f:
                        f.write(jar.read(class_file_path))
                    
                    # Decompile
                    result = self._run_decompiler(decompiler, extracted_class, temp_path)
                    if result:
                        logger.info(f"Decompilation successful with {decompiler}")
                        return result
                    else:
                        logger.warning(f"Decompilation failed with {decompiler}, trying fallback")
                        return self._fallback_class_info(jar_path, class_name)
        
        except Exception as e:
            logger.error(f"Decompilation failed: {e}")
            return self._fallback_class_info(jar_path, class_name)

    def analyze_class(self, jar_path: Path, class_name: str,
                      include_bytecode: bool = False) -> Dict[str, Any]:
        """Analyze a class file and return parsed javap fields/methods."""
        class_file_path = class_name.replace('.', '/') + '.class'
        analysis: Dict[str, Any] = {
            "class_name": class_name,
            "class_file": class_file_path,
            "fields": [],
            "methods": [],
            "javap_available": "javap" in self.available_decompilers,
        }

        try:
            with zipfile.ZipFile(jar_path, 'r') as jar:
                if class_file_path not in jar.namelist():
                    analysis["error"] = f"Class file not found in jar: {class_file_path}"
                    return analysis

                class_data = jar.read(class_file_path)
                analysis["size_bytes"] = len(class_data)

                if class_data[:4] == b'\xca\xfe\xba\xbe':
                    minor_version = int.from_bytes(class_data[4:6], 'big')
                    major_version = int.from_bytes(class_data[6:8], 'big')
                    analysis["bytecode"] = {
                        "major_version": major_version,
                        "minor_version": minor_version,
                        "java_version": self._map_bytecode_version(major_version),
                    }
        except Exception as e:
            analysis["error"] = f"Error reading class file: {e}"
            return analysis

        javap_output = self._run_javap_on_classpath(jar_path, class_name, include_bytecode)
        if not javap_output:
            analysis["javap_error"] = "javap did not return class details"
            return analysis

        parsed = self._parse_javap_output(javap_output, class_name)
        analysis.update(parsed)

        if include_bytecode:
            analysis["javap_output"] = javap_output

        return analysis

    def _run_javap_on_classpath(self, jar_path: Path, class_name: str,
                                include_bytecode: bool = False) -> Optional[str]:
        """Run javap against a class using the jar as the classpath."""
        if "javap" not in self.available_decompilers:
            return None

        args = ['javap', '-classpath', str(jar_path), '-p', '-s', '-constants']
        if include_bytecode:
            args.extend(['-c', '-v'])
        args.append(class_name)

        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return result.stdout
            logger.warning(f"javap classpath analysis failed: {result.stderr}")
        except Exception as e:
            logger.error(f"javap classpath analysis failed: {e}")

        return None

    def _parse_javap_output(self, output: str, class_name: str) -> Dict[str, Any]:
        """Parse javap output into class signature, fields, and methods."""
        fields: List[Dict[str, str]] = []
        methods: List[Dict[str, str]] = []
        class_signature = ""
        current_member: Optional[Dict[str, str]] = None
        current_collection: Optional[List[Dict[str, str]]] = None

        for line in output.splitlines():
            stripped = line.strip()
            if not stripped or stripped in {"{", "}"}:
                continue

            if stripped.startswith("Compiled from "):
                continue

            if stripped.endswith("{") and not class_signature:
                class_signature = stripped[:-1].strip()
                continue

            if stripped.startswith("descriptor:") and current_member is not None:
                current_member["descriptor"] = stripped.split(":", 1)[1].strip()
                continue

            if stripped.startswith("flags:") and current_member is not None:
                current_member["flags"] = stripped.split(":", 1)[1].strip()
                continue

            if not stripped.endswith(";"):
                continue

            signature = stripped[:-1].strip()
            if not signature or signature.startswith(("descriptor:", "flags:", "Code:")):
                continue

            member: Dict[str, str] = {"signature": signature}
            if "(" in signature and ")" in signature:
                member["name"] = self._extract_method_name(signature, class_name)
                methods.append(member)
                current_collection = methods
            else:
                member["name"] = self._extract_field_name(signature)
                fields.append(member)
                current_collection = fields

            current_member = current_collection[-1]

        return {
            "class_signature": class_signature,
            "fields": fields,
            "methods": methods,
        }

    def _extract_method_name(self, signature: str, class_name: str) -> str:
        """Extract a method or constructor name from a javap member signature."""
        before_args = signature.split("(", 1)[0].strip()
        method_token = before_args.split()[-1] if before_args.split() else before_args
        simple_class_name = class_name.split(".")[-1]

        if method_token == class_name or method_token.endswith("." + simple_class_name):
            return simple_class_name

        return method_token.split(".")[-1]

    def _extract_field_name(self, signature: str) -> str:
        """Extract a field name from a javap field signature."""
        left_side = signature.split("=", 1)[0].strip()
        return left_side.split()[-1] if left_side.split() else left_side
    
    def _run_decompiler(self, decompiler: str, class_file: Path, temp_dir: Path) -> Optional[str]:
        """Run the specified decompiler"""
        logger.debug(f"Running decompiler {decompiler} on {class_file}")
        
        try:
            if decompiler == 'javap':
                # Use javap for disassembly
                logger.debug("Using javap for disassembly")
                result = subprocess.run([
                    'javap', '-v', '-p', '-c', str(class_file)
                ], capture_output=True, text=True, timeout=30)
                
                logger.debug(f"javap return code: {result.returncode}")
                if result.stderr:
                    logger.warning(f"javap stderr: {result.stderr}")
                
                if result.returncode == 0:
                    return result.stdout
                else:
                    logger.error(f"javap failed with return code {result.returncode}: {result.stderr}")
            
            elif decompiler == 'cfr':
                # Use CFR decompiler
                output_dir = temp_dir / 'output'
                output_dir.mkdir()
                
                result = subprocess.run([
                    'java', '-jar', self.available_decompilers[decompiler],
                    str(class_file), '--outputdir', str(output_dir)
                ], capture_output=True, text=True, timeout=30)
                
                # Look for generated .java file
                java_files = list(output_dir.rglob('*.java'))
                if java_files:
                    with open(java_files[0], 'r', encoding='utf-8') as f:
                        return f.read()
            
            elif decompiler == 'procyon':
                # Use Procyon decompiler
                result = subprocess.run([
                    'java', '-jar', self.available_decompilers[decompiler],
                    str(class_file)
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    return result.stdout
            
            elif decompiler == 'fernflower':
                # Use Fernflower decompiler
                output_dir = temp_dir / 'output'
                output_dir.mkdir()
                
                result = subprocess.run([
                    'java', '-jar', self.available_decompilers[decompiler],
                    str(class_file), str(output_dir)
                ], capture_output=True, text=True, timeout=30)
                
                # Look for generated .java file
                java_files = list(output_dir.rglob('*.java'))
                if java_files:
                    with open(java_files[0], 'r', encoding='utf-8') as f:
                        return f.read()
        
        except Exception as e:
            logger.error(f"Decompiler {decompiler} failed: {e}")
        
        return None
    
    def _fallback_class_info(self, jar_path: Path, class_name: str) -> str:
        """Fallback to basic class information when decompilation fails"""
        try:
            class_file_path = class_name.replace('.', '/') + '.class'
            
            with zipfile.ZipFile(jar_path, 'r') as jar:
                if class_file_path in jar.namelist():
                    class_data = jar.read(class_file_path)
                    
                    # Basic bytecode analysis
                    info = f"// Decompilation not available\n"
                    info += f"// Class: {class_name}\n"
                    info += f"// Size: {len(class_data)} bytes\n"
                    info += f"// Location: {jar_path}\n\n"
                    
                    # Try to extract some basic info from bytecode
                    magic = class_data[:4]
                    if magic == b'\xca\xfe\xba\xbe':
                        minor_version = int.from_bytes(class_data[4:6], 'big')
                        major_version = int.from_bytes(class_data[6:8], 'big')
                        info += f"// Java bytecode version: {major_version}.{minor_version}\n"
                        
                        # Map major version to Java version
                        java_version = self._map_bytecode_version(major_version)
                        if java_version:
                            info += f"// Compiled for Java: {java_version}\n"
                    
                    info += f"\npublic class {class_name.split('.')[-1]} {{\n"
                    info += "    // Decompilation requires external tools\n"
                    info += "    // Install CFR, Procyon, or Fernflower for full decompilation\n"
                    info += "}\n"
                    
                    return info
        
        except Exception as e:
            return f"// Error reading class file: {e}"
        
        return f"// Class not found: {class_name}"
    
    def _map_bytecode_version(self, major_version: int) -> Optional[str]:
        """Map bytecode major version to Java version"""
        version_map = {
            45: "1.1",
            46: "1.2",
            47: "1.3",
            48: "1.4",
            49: "5",
            50: "6",
            51: "7",
            52: "8",
            53: "9",
            54: "10",
            55: "11",
            56: "12",
            57: "13",
            58: "14",
            59: "15",
            60: "16",
            61: "17",
            62: "18",
            63: "19",
            64: "20",
            65: "21"
        }
        return version_map.get(major_version)
    
    def analyze_jar_structure(self, jar_path: Path) -> Dict[str, Any]:
        """Analyze the overall structure of a jar file"""
        analysis = {
            "jar_path": str(jar_path),
            "total_size": jar_path.stat().st_size,
            "packages": {},
            "class_count": 0,
            "resource_count": 0,
            "manifest": {},
            "services": [],
            "annotations": []
        }
        
        try:
            with zipfile.ZipFile(jar_path, 'r') as jar:
                entries = jar.namelist()
                
                # Analyze entries
                for entry in entries:
                    if entry.endswith('.class'):
                        analysis["class_count"] += 1
                        
                        # Extract package info
                        if '/' in entry:
                            package = '/'.join(entry.split('/')[:-1]).replace('/', '.')
                            if package not in analysis["packages"]:
                                analysis["packages"][package] = 0
                            analysis["packages"][package] += 1
                    
                    elif not entry.endswith('/'):
                        analysis["resource_count"] += 1
                
                # Read manifest
                if "META-INF/MANIFEST.MF" in entries:
                    manifest_content = jar.read("META-INF/MANIFEST.MF").decode('utf-8', errors='ignore')
                    analysis["manifest"] = self._parse_manifest(manifest_content)
                
                # Look for services
                service_entries = [e for e in entries if e.startswith("META-INF/services/")]
                for service_entry in service_entries:
                    service_name = service_entry.replace("META-INF/services/", "")
                    try:
                        service_content = jar.read(service_entry).decode('utf-8', errors='ignore')
                        analysis["services"].append({
                            "interface": service_name,
                            "implementations": [line.strip() for line in service_content.split('\n') if line.strip()]
                        })
                    except Exception:
                        pass
        
        except Exception as e:
            analysis["error"] = str(e)
        
        return analysis
    
    def _parse_manifest(self, manifest_content: str) -> Dict[str, str]:
        """Parse JAR manifest file"""
        manifest = {}
        current_key = None
        
        for line in manifest_content.split('\n'):
            line = line.rstrip('\r')
            
            if line.startswith(' ') and current_key:
                # Continuation line
                manifest[current_key] += line[1:]
            elif ':' in line:
                key, value = line.split(':', 1)
                current_key = key.strip()
                manifest[current_key] = value.strip()
        
        return manifest
