#!/usr/bin/env python3
"""
Tests asserting that tool responses carry the 'origin' field.

Verifies that analyze_jar, extract_source_code, and analyze_jar_structure
correctly report whether an artifact was resolved from 'local-repository'
or 'remote-cache'.
"""

import json
import os
import zipfile
from pathlib import Path
from unittest.mock import patch
import pytest

from maven_decoder_mcp.maven_decoder_server import MavenDecoderServer


def _create_jar(path: Path, entries: dict) -> Path:
    """Create a jar file containing specified file entries."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as zf:
        for name, content in entries.items():
            zf.writestr(name, content)
    return path


def _populate_artifact(base_dir: Path, group_id: str, artifact_id: str, version: str):
    """Populate main and sources jars in standard Maven repository layout."""
    rel_dir = base_dir / Path(*group_id.split(".")) / artifact_id / version

    # Main jar with manifest, dummy class, and java source
    main_jar = rel_dir / f"{artifact_id}-{version}.jar"
    _create_jar(main_jar, {
        "META-INF/MANIFEST.MF": "Manifest-Version: 1.0\nCreated-By: Maven\n",
        "com/example/Demo.class": b"\xca\xfe\xba\xbe\x00\x00\x00\x3d\x00\x01\x00\x00",
        "com/example/Demo.java": "package com.example;\npublic class Demo {}\n",
    })

    # Sources jar
    sources_jar = rel_dir / f"{artifact_id}-{version}-sources.jar"
    _create_jar(sources_jar, {
        "com/example/Demo.java": "package com.example;\npublic class Demo {}\n",
    })


@pytest.fixture
def repo_and_cache(tmp_path):
    """Isolated environment pointing MAVEN_REPOSITORY and MAVEN_DECODER_CACHE_DIR to tmp_path."""
    local_repo = tmp_path / "m2" / "repository"
    cache_dir = tmp_path / "cache"
    local_repo.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    with patch.dict(os.environ, {
        "MAVEN_REPOSITORY": str(local_repo),
        "MAVEN_DECODER_CACHE_DIR": str(cache_dir),
        "MAVEN_OFFLINE": "true",
    }):
        server = MavenDecoderServer()
        yield server, local_repo, cache_dir


@pytest.mark.asyncio
async def test_analyze_jar_origin_local_repository(repo_and_cache):
    server, local_repo, _ = repo_and_cache
    _populate_artifact(local_repo, "com.example", "local-demo", "1.0.0")

    result = await server._analyze_jar("com.example", "local-demo", "1.0.0")
    data = json.loads(result[0].text)

    assert "origin" in data
    assert data["origin"] == "local-repository"


@pytest.mark.asyncio
async def test_analyze_jar_origin_remote_cache(repo_and_cache):
    server, _, cache_dir = repo_and_cache
    _populate_artifact(cache_dir, "com.example", "remote-demo", "1.0.0")

    result = await server._analyze_jar("com.example", "remote-demo", "1.0.0")
    data = json.loads(result[0].text)

    assert "origin" in data
    assert data["origin"] == "remote-cache"


@pytest.mark.asyncio
async def test_extract_source_code_origin_local_repository(repo_and_cache):
    server, local_repo, _ = repo_and_cache
    _populate_artifact(local_repo, "com.example", "local-demo", "1.0.0")

    result = await server._extract_source_code(
        "com.example", "local-demo", "1.0.0", "com.example.Demo"
    )
    data = json.loads(result[0].text)

    assert "origin" in data
    assert data["origin"] == "local-repository"


@pytest.mark.asyncio
async def test_extract_source_code_origin_remote_cache(repo_and_cache):
    server, _, cache_dir = repo_and_cache
    _populate_artifact(cache_dir, "com.example", "remote-demo", "1.0.0")

    result = await server._extract_source_code(
        "com.example", "remote-demo", "1.0.0", "com.example.Demo"
    )
    data = json.loads(result[0].text)

    assert "origin" in data
    assert data["origin"] == "remote-cache"


@pytest.mark.asyncio
async def test_analyze_jar_structure_origin_local_repository(repo_and_cache):
    server, local_repo, _ = repo_and_cache
    _populate_artifact(local_repo, "com.example", "local-demo", "1.0.0")

    result = await server._analyze_jar_structure("com.example", "local-demo", "1.0.0")
    data = json.loads(result[0].text)

    assert "origin" in data
    assert data["origin"] == "local-repository"


@pytest.mark.asyncio
async def test_analyze_jar_structure_origin_remote_cache(repo_and_cache):
    server, _, cache_dir = repo_and_cache
    _populate_artifact(cache_dir, "com.example", "remote-demo", "1.0.0")

    result = await server._analyze_jar_structure("com.example", "remote-demo", "1.0.0")
    data = json.loads(result[0].text)

    assert "origin" in data
    assert data["origin"] == "remote-cache"