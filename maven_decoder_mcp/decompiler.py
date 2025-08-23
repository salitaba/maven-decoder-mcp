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
