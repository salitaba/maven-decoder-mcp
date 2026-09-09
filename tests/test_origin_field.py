"""Origin metadata is consistent across jar-inspection tool output."""

import json
import zipfile

import pytest

from maven_decoder_mcp.maven_decoder_server import MavenDecoderServer


@pytest.fixture
def server_with_artifacts(tmp_path, monkeypatch):
    repository = tmp_path / "repository"
    cache = tmp_path / "cache"
    monkeypatch.setenv("MAVEN_REPOSITORY", str(repository))
    monkeypatch.setenv("MAVEN_DECODER_CACHE_DIR", str(cache))
    server = MavenDecoderServer()

    for root, version in ((repository, "1.0.0"), (cache, "2.0.0")):
        artifact_dir = root / "com/example/demo" / version
        artifact_dir.mkdir(parents=True)
        with zipfile.ZipFile(artifact_dir / f"demo-{version}.jar", "w") as jar:
            jar.writestr("com/example/Demo.class", b"\xca\xfe\xba\xbe")
        with zipfile.ZipFile(
            artifact_dir / f"demo-{version}-sources.jar", "w"
        ) as sources:
            sources.writestr("com/example/Demo.java", "class Demo {}")

    return server


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("version", "expected_origin"),
    [("1.0.0", "local-repository"), ("2.0.0", "remote-cache")],
)
async def test_jar_tools_report_artifact_origin(
    server_with_artifacts, version, expected_origin
):
    server = server_with_artifacts
    responses = [
        await server._analyze_jar("com.example", "demo", version),
        await server._extract_source_code(
            "com.example", "demo", version, "com.example.Demo"
        ),
        await server._analyze_jar_structure("com.example", "demo", version),
    ]

    for response in responses:
        payload = json.loads(response[0].text)
        assert payload["origin"] == expected_origin
