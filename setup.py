#!/usr/bin/env python3
"""
Setup script for maven-decoder-mcp
Provides backward compatibility and additional setup functionality
"""

from setuptools import setup, find_packages
from pathlib import Path
import subprocess
import sys
import os

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

def download_decompilers():
    """Download Java decompilers during installation"""
    print("Setting up Java decompilers...")
    
    # Create decompilers directory
    decompilers_dir = this_directory / "decompilers"
    decompilers_dir.mkdir(exist_ok=True)
    
    # Try to run the setup script if it exists
    setup_script = this_directory / "setup_decompilers.sh"
    if setup_script.exists():
        try:
            subprocess.run([str(setup_script)], check=True, cwd=this_directory)
            print("✓ Decompilers setup complete!")
        except subprocess.CalledProcessError:
            print("⚠ Warning: Could not automatically download decompilers")
            print("  You can manually run: ./setup_decompilers.sh")
    else:
        print("⚠ Warning: setup_decompilers.sh not found")

# Custom install command
class PostInstallCommand:
    """Post-installation for installation mode."""
    def run(self):
        download_decompilers()

if __name__ == "__main__":
    # Check if we're in development mode
    if "develop" in sys.argv or "egg_info" in sys.argv:
        # Skip decompiler download in development mode
        pass
    else:
        try:
            download_decompilers()
        except Exception as e:
            print(f"Warning: Could not setup decompilers: {e}")
    
    setup(
        name="maven-decoder-mcp",
        use_scm_version=False,
        version="1.0.0",
        description="MCP server for reading and decompiling Maven .m2 jar files",
        long_description=long_description,
        long_description_content_type="text/markdown",
        author="Ali Tabatabaei",
        author_email="ali79taba@gmail.com",
        url="https://github.com/salitaba/maven-decoder-mcp",
        packages=find_packages(),
        python_requires=">=3.8",
        install_requires=[
            "mcp>=1.0.0",
            "pydantic>=2.0.0", 
            "xmltodict>=0.13.0",
            "requests>=2.25.0",
        ],
        extras_require={
            "dev": [
                "pytest>=7.0.0",
                "pytest-asyncio>=0.21.0",
                "black>=23.0.0",
                "isort>=5.12.0",
                "mypy>=1.0.0",
                "flake8>=6.0.0",
            ],
        },
        entry_points={
            "console_scripts": [
                "maven-decoder-mcp=maven_decoder_server:main",
                "maven-decoder-setup=setup:main",
            ],
        },
        include_package_data=True,
        package_data={
            "": ["decompilers/*.jar", "*.md"],
        },
        classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Topic :: Software Development :: Build Tools",
        ],
        zip_safe=False,
    )