"""Regression tests for corrupt or truncated jar handling."""

import json
import logging
import zipfile

import pytest

from maven_decoder_mcp.maven_decoder_server import MavenDecoderServer


@pytest.fixture
def server(tmp_path):
    """Use only temporary Maven roots, never the developer's real ~/.m2."""
    instance = MavenDecoderServer(maven_repository=tmp_path / "m2")
    instance.cache_home = tmp_path / "cache"
    instance.cache_home.mkdir(parents=True, exist_ok=True)
    return instance


def write_corrupt_jar(server, artifact_id="broken"):
    jar_path = (
        server.maven_home
        / "com/example"
        / artifact_id
        / "1.0.0"
        / f"{artifact_id}-1.0.0.jar"
    )
    jar_path.parent.mkdir(parents=True, exist_ok=True)
    jar_path.write_bytes(b"truncated jar")
    return jar_path


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method_name", "extra_args"),
    [
        ("_analyze_jar", ()),
        ("_analyze_jar_structure", ()),
        ("_extract_method_info", ("com.example.Missing",)),
    ],
)
async def test_single_jar_tools_report_corrupt_path(server, method_name, extra_args):
    jar_path = write_corrupt_jar(server)

    method = getattr(server, method_name)
    result = await method("com.example", "broken", "1.0.0", *extra_args)
    message = result[0].text

    assert str(jar_path) in message
    assert "corrupt" in message.lower() or "truncated" in message.lower()
    assert "re-download" in message


@pytest.mark.asyncio
async def test_search_skips_corrupt_jar_and_keeps_valid_results(server, caplog):
    bad_jar = write_corrupt_jar(server)
    good_jar = server.maven_home / "com/example/good/1.0.0/good-1.0.0.jar"
    good_jar.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(good_jar, "w") as jar:
        jar.writestr("com/example/Good.class", b"class bytes")

    with caplog.at_level(logging.WARNING):
        result = await server._search_classes(class_name="Good")

    payload = json.loads(result[0].text)
    assert [match["class_name"] for match in payload["matches"]] == ["com.example.Good"]
    assert any(str(bad_jar) in record.message for record in caplog.records)
