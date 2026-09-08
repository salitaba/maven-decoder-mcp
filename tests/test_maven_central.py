#!/usr/bin/env python3
"""
Tests for online Maven repository support (search, versions, downloads).

Every test here is hermetic: the HTTP session is mocked, so no test touches
the network.
"""

import hashlib
import json
import os
import re
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

from maven_decoder_mcp.config import Config
from maven_decoder_mcp.maven_central import (
    MavenCentralClient,
    MavenRemoteError,
    OfflineError,
)
from maven_decoder_mcp.maven_decoder_server import MavenDecoderServer


def make_response(status_code=200, json_body=None, content=b"", text=None,
                  headers=None):
    """Build a stand-in for a ``requests.Response``."""
    response = Mock()
    response.status_code = status_code
    response.content = content
    response.headers = headers or {}
    response.text = text if text is not None else ""

    if json_body is None:
        response.json.side_effect = ValueError("no json")
    else:
        response.json.return_value = json_body

    response.iter_content.return_value = [content] if content else []
    response.close.return_value = None
    return response


@pytest.fixture
def client(tmp_path):
    """An online client whose HTTP session is fully mocked."""
    return MavenCentralClient(
        search_urls=["https://search.example/solrsearch/select"],
        repositories=["https://repo.example/maven2"],
        cache_dir=tmp_path / "cache",
        offline=False,
        retries=0,
        verify_checksums=False,
    )


class TestBuildSearchQuery:
    """Query construction is what makes search results correct."""

    def test_group_and_artifact_are_quoted_and_anded(self):
        query = MavenCentralClient.build_search_query(
            group_id="org.springframework", artifact_id="spring-core"
        )
        assert query == 'g:"org.springframework" AND a:"spring-core"'

    def test_class_name_uses_c_field(self):
        assert MavenCentralClient.build_search_query(class_name="ObjectMapper") == 'c:"ObjectMapper"'

    def test_fully_qualified_class_uses_fc_field(self):
        query = MavenCentralClient.build_search_query(
            fully_qualified_class="com.fasterxml.jackson.databind.ObjectMapper"
        )
        assert query == 'fc:"com.fasterxml.jackson.databind.ObjectMapper"'

    def test_free_text_is_passed_through(self):
        assert MavenCentralClient.build_search_query(query="jackson databind") == "jackson databind"

    def test_requires_at_least_one_criterion(self):
        with pytest.raises(ValueError):
            MavenCentralClient.build_search_query()


class TestSearch:
    """Search normalization and failover."""

    def test_search_normalizes_documents(self, client):
        payload = {
            "response": {
                "numFound": 2,
                "docs": [
                    {
                        "g": "com.fasterxml.jackson.core",
                        "a": "jackson-databind",
                        "latestVersion": "2.17.0",
                        "p": "jar",
                        "ec": ["-sources.jar", "-javadoc.jar", ".jar", ".pom"],
                        "versionCount": 120,
                    }
                ],
            }
        }

        with patch.object(client, "_get", return_value=make_response(json_body=payload)):
            result = client.search(class_name="ObjectMapper", limit=5)

        assert result["query"] == 'c:"ObjectMapper"'
        assert result["total_found"] == 2
        artifact = result["artifacts"][0]
        assert artifact["coordinates"] == "com.fasterxml.jackson.core:jackson-databind:2.17.0"
        assert artifact["has_sources"] is True
        assert artifact["has_javadoc"] is True
        assert artifact["version_count"] == 120

    def test_all_versions_switches_to_gav_core(self, client):
        payload = {"response": {"numFound": 0, "docs": []}}
        get_mock = Mock(return_value=make_response(json_body=payload))

        with patch.object(client, "_get", get_mock):
            client.search(artifact_id="gson", all_versions=True)

        assert get_mock.call_args.kwargs["params"]["core"] == "gav"

    def test_limit_is_capped_at_200(self, client):
        payload = {"response": {"numFound": 0, "docs": []}}
        get_mock = Mock(return_value=make_response(json_body=payload))

        with patch.object(client, "_get", get_mock):
            client.search(artifact_id="gson", limit=5000)

        assert get_mock.call_args.kwargs["params"]["rows"] == 200

    def test_falls_over_to_second_endpoint(self, tmp_path):
        client = MavenCentralClient(
            search_urls=["https://broken.example/select", "https://good.example/select"],
            cache_dir=tmp_path / "cache",
            offline=False,
            retries=0,
        )
        payload = {"response": {"numFound": 1, "docs": [{"g": "g", "a": "a", "v": "1"}]}}
        responses = [
            make_response(status_code=503),
            make_response(json_body=payload),
        ]

        with patch.object(client, "_get", side_effect=responses):
            result = client.search(artifact_id="a")

        assert result["search_url"] == "https://good.example/select"

    def test_error_when_every_endpoint_fails(self, client):
        with patch.object(client, "_get", return_value=make_response(status_code=500)):
            with pytest.raises(MavenRemoteError):
                client.search(artifact_id="a")

    def test_offline_search_raises(self, tmp_path):
        client = MavenCentralClient(cache_dir=tmp_path, offline=True)
        with pytest.raises(OfflineError):
            client.search(artifact_id="gson")


class TestGetVersions:
    """Version listing prefers maven-metadata.xml."""

    METADATA = b"""<?xml version="1.0" encoding="UTF-8"?>
    <metadata>
      <groupId>com.google.code.gson</groupId>
      <artifactId>gson</artifactId>
      <versioning>
        <latest>2.11.0</latest>
        <release>2.11.0</release>
        <versions>
          <version>2.9.0</version>
          <version>2.10.1</version>
          <version>2.11.0</version>
        </versions>
        <lastUpdated>20240101000000</lastUpdated>
      </versioning>
    </metadata>"""

    def test_versions_come_from_metadata_newest_first(self, client):
        with patch.object(client, "_get",
                          return_value=make_response(content=self.METADATA)):
            result = client.get_versions("com.google.code.gson", "gson")

        assert result["source"] == "maven-metadata.xml"
        assert result["versions"] == ["2.11.0", "2.10.1", "2.9.0"]
        assert result["release"] == "2.11.0"
        assert result["total_versions"] == 3

    def test_limit_is_applied(self, client):
        with patch.object(client, "_get",
                          return_value=make_response(content=self.METADATA)):
            result = client.get_versions("com.google.code.gson", "gson", limit=2)

        assert result["versions"] == ["2.11.0", "2.10.1"]

    def test_falls_back_to_search_index(self, client):
        payload = {
            "response": {
                "numFound": 1,
                "docs": [{"g": "g", "a": "a", "v": "3.0.0"}],
            }
        }

        def fake_get(url, params=None, stream=False):
            if url.endswith("maven-metadata.xml"):
                return make_response(status_code=404)
            return make_response(json_body=payload)

        with patch.object(client, "_get", side_effect=fake_get):
            result = client.get_versions("g", "a")

        assert result["source"] == "search-index"
        assert result["versions"] == ["3.0.0"]

    def test_get_latest_version_prefers_release(self, client):
        with patch.object(client, "_get",
                          return_value=make_response(content=self.METADATA)):
            assert client.get_latest_version("com.google.code.gson", "gson") == "2.11.0"


class TestDownload:
    """Downloading, caching, checksum verification and size limits."""

    def test_downloads_into_maven_layout(self, client):
        payload = b"jar-bytes"
        with patch.object(client, "_get", return_value=make_response(content=payload)):
            path = client.download_artifact("com.example", "demo", "1.0.0")

        expected = client.cache_dir / "com/example/demo/1.0.0/demo-1.0.0.jar"
        assert path == expected
        assert path.read_bytes() == payload

    def test_classifier_is_included_in_filename(self, client):
        with patch.object(client, "_get", return_value=make_response(content=b"x")):
            path = client.download_artifact(
                "com.example", "demo", "1.0.0", classifier="sources"
            )

        assert path.name == "demo-1.0.0-sources.jar"

    def test_cached_file_is_reused_without_network(self, client):
        target = client.cached_path("com.example", "demo", "1.0.0")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"cached")

        get_mock = Mock()
        with patch.object(client, "_get", get_mock):
            path = client.download_artifact("com.example", "demo", "1.0.0")

        get_mock.assert_not_called()
        assert path.read_bytes() == b"cached"

    def test_force_redownloads(self, client):
        target = client.cached_path("com.example", "demo", "1.0.0")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"stale")

        with patch.object(client, "_get", return_value=make_response(content=b"fresh")):
            path = client.download_artifact("com.example", "demo", "1.0.0", force=True)

        assert path.read_bytes() == b"fresh"

    def test_missing_artifact_raises_and_leaves_no_partial_file(self, client):
        with patch.object(client, "_get", return_value=make_response(status_code=404)):
            with pytest.raises(MavenRemoteError):
                client.download_artifact("com.example", "missing", "1.0.0")

        assert not client.cached_path("com.example", "missing", "1.0.0").exists()

    def test_oversized_declared_content_is_rejected(self, client):
        client.max_download_bytes = 10
        response = make_response(content=b"x" * 100, headers={"Content-Length": "100"})

        with patch.object(client, "_get", return_value=response):
            with pytest.raises(MavenRemoteError, match="exceeding"):
                client.download_artifact("com.example", "big", "1.0.0")

    def test_oversized_stream_is_rejected_midflight(self, client):
        client.max_download_bytes = 5
        response = make_response(content=b"x" * 50)

        with patch.object(client, "_get", return_value=response):
            with pytest.raises(MavenRemoteError, match="download limit"):
                client.download_artifact("com.example", "big", "1.0.0")

        assert not client.cached_path("com.example", "big", "1.0.0").exists()

    def test_checksum_mismatch_rejects_the_file(self, tmp_path):
        client = MavenCentralClient(
            repositories=["https://repo.example/maven2"],
            cache_dir=tmp_path / "cache",
            offline=False,
            retries=0,
            verify_checksums=True,
        )

        def fake_get(url, params=None, stream=False):
            if url.endswith(".sha1"):
                return make_response(text="0" * 40)
            return make_response(content=b"payload")

        with patch.object(client, "_get", side_effect=fake_get):
            with pytest.raises(MavenRemoteError, match="Checksum mismatch"):
                client.download_artifact("com.example", "demo", "1.0.0")

        assert not client.cached_path("com.example", "demo", "1.0.0").exists()

    def test_matching_checksum_is_accepted(self, tmp_path):
        client = MavenCentralClient(
            repositories=["https://repo.example/maven2"],
            cache_dir=tmp_path / "cache",
            offline=False,
            retries=0,
            verify_checksums=True,
        )
        payload = b"payload"
        digest = hashlib.sha1(payload).hexdigest()

        def fake_get(url, params=None, stream=False):
            if url.endswith(".sha1"):
                return make_response(text=f"{digest}  demo-1.0.0.jar")
            return make_response(content=payload)

        with patch.object(client, "_get", side_effect=fake_get):
            path = client.download_artifact("com.example", "demo", "1.0.0")

        assert path.read_bytes() == payload

    def test_ensure_artifact_swallows_errors(self, client):
        with patch.object(client, "_get", return_value=make_response(status_code=404)):
            assert client.ensure_artifact("com.example", "missing", "1.0.0") is None

    def test_offline_download_raises(self, tmp_path):
        client = MavenCentralClient(cache_dir=tmp_path, offline=True)
        with pytest.raises(OfflineError):
            client.download_artifact("com.example", "demo", "1.0.0")


class TestRetries:
    """Transient failures are retried before giving up."""

    def test_retries_then_succeeds(self, tmp_path):
        client = MavenCentralClient(
            cache_dir=tmp_path, offline=False, retries=2, timeout=0.01
        )
        session = Mock()
        session.get.side_effect = [
            requests.Timeout("throttled"),
            make_response(json_body={"response": {"numFound": 0, "docs": []}}),
        ]
        client._session = session

        with patch("maven_decoder_mcp.maven_central.time.sleep"):
            result = client.search(artifact_id="gson")

        assert session.get.call_count == 2
        assert result["total_found"] == 0

    def test_gives_up_after_exhausting_retries(self, tmp_path):
        client = MavenCentralClient(
            cache_dir=tmp_path, offline=False, retries=1, timeout=0.01
        )
        session = Mock()
        session.get.side_effect = requests.Timeout("throttled")
        client._session = session

        with patch("maven_decoder_mcp.maven_central.time.sleep"):
            with pytest.raises(MavenRemoteError):
                client.search(artifact_id="gson")

        assert session.get.call_count == 2


class TestConfigRemoteSettings:
    """Environment-driven remote configuration."""

    def test_offline_flag_accepts_common_spellings(self):
        for value in ("true", "1", "yes", "on"):
            with patch.dict(os.environ, {"MAVEN_OFFLINE": value}):
                assert Config.is_offline() is True

        with patch.dict(os.environ, {"MAVEN_OFFLINE": "false"}):
            assert Config.is_offline() is False

    def test_offline_disables_auto_download(self):
        with patch.dict(os.environ, {"MAVEN_OFFLINE": "true"}):
            assert Config.auto_download_enabled() is False

    def test_auto_download_defaults_on_when_online(self):
        with patch.dict(os.environ, {"MAVEN_OFFLINE": "false"}, clear=False):
            os.environ.pop("MAVEN_AUTO_DOWNLOAD", None)
            assert Config.auto_download_enabled() is True

    def test_remote_repositories_parse_lists(self):
        with patch.dict(os.environ, {"MAVEN_REMOTE_REPOS": "https://a/m2, https://b/m2/"}):
            assert Config.resolve_remote_repositories() == ["https://a/m2", "https://b/m2"]

    def test_search_urls_parse_lists(self):
        with patch.dict(os.environ, {"MAVEN_SEARCH_URL": "https://a/select https://b/select"}):
            assert Config.resolve_search_urls() == ["https://a/select", "https://b/select"]

    def test_cache_dir_override(self, tmp_path):
        with patch.dict(os.environ, {"MAVEN_DECODER_CACHE_DIR": str(tmp_path / "c")}):
            assert Config.resolve_download_cache() == (tmp_path / "c").resolve()

    def test_invalid_timeout_falls_back_to_default(self):
        with patch.dict(os.environ, {"MAVEN_HTTP_TIMEOUT": "not-a-number"}):
            assert Config.http_timeout() == Config.DEFAULT_HTTP_TIMEOUT

    def test_credentials_only_when_username_present(self):
        with patch.dict(os.environ, {"MAVEN_REMOTE_USERNAME": "u", "MAVEN_REMOTE_PASSWORD": "p"}):
            assert Config.remote_credentials() == ("u", "p")

        with patch.dict(os.environ, {"MAVEN_REMOTE_USERNAME": ""}):
            assert Config.remote_credentials() is None


class TestAnalyzerRemotePoms:
    """POM resolution across roots, with a bounded remote fetch budget."""

    def _analyzer(self, tmp_path, resolver, budget=None):
        from maven_decoder_mcp.maven_analyzer import MavenDependencyAnalyzer

        return MavenDependencyAnalyzer(
            tmp_path / "m2",
            extra_roots=[tmp_path / "cache"],
            remote_resolver=resolver,
            remote_pom_budget=budget,
        )

    def test_local_pom_wins_over_remote(self, tmp_path):
        pom = tmp_path / "m2/com/example/demo/1.0.0/demo-1.0.0.pom"
        pom.parent.mkdir(parents=True)
        pom.write_text("<project/>")

        resolver = Mock()
        analyzer = self._analyzer(tmp_path, resolver)

        assert analyzer._get_pom_path("com.example", "demo", "1.0.0") == pom
        resolver.assert_not_called()

    def test_cached_pom_is_found(self, tmp_path):
        pom = tmp_path / "cache/com/example/demo/1.0.0/demo-1.0.0.pom"
        pom.parent.mkdir(parents=True)
        pom.write_text("<project/>")

        resolver = Mock()
        analyzer = self._analyzer(tmp_path, resolver)

        assert analyzer._get_pom_path("com.example", "demo", "1.0.0") == pom
        resolver.assert_not_called()

    def test_remote_resolver_is_used_on_miss(self, tmp_path):
        fetched = tmp_path / "fetched.pom"
        fetched.write_text("<project/>")
        resolver = Mock(return_value=fetched)
        analyzer = self._analyzer(tmp_path, resolver)

        assert analyzer._get_pom_path("com.example", "demo", "1.0.0") == fetched
        resolver.assert_called_once_with("com.example", "demo", "1.0.0")

    def test_failed_lookup_is_not_retried(self, tmp_path):
        resolver = Mock(return_value=None)
        analyzer = self._analyzer(tmp_path, resolver)

        for _ in range(4):
            analyzer._get_pom_path("com.example", "demo", "1.0.0")

        assert resolver.call_count == 1

    def test_resolver_exception_is_contained(self, tmp_path):
        resolver = Mock(side_effect=RuntimeError("network down"))
        analyzer = self._analyzer(tmp_path, resolver)

        assert analyzer._get_pom_path("com.example", "demo", "1.0.0") is None

    def test_remote_budget_is_enforced(self, tmp_path):
        resolver = Mock(return_value=None)
        analyzer = self._analyzer(tmp_path, resolver, budget=2)

        for i in range(6):
            analyzer._get_pom_path("com.example", f"demo{i}", "1.0.0")

        assert resolver.call_count == 2

        analyzer.reset_remote_budget()
        analyzer._get_pom_path("com.example", "another", "1.0.0")
        assert resolver.call_count == 3

    def test_empty_version_is_rejected(self, tmp_path):
        resolver = Mock()
        analyzer = self._analyzer(tmp_path, resolver)

        assert analyzer._get_pom_path("com.example", "demo", "") is None
        resolver.assert_not_called()


class TestVersionReporting:
    """The version reported to MCP clients must track the packaged version."""

    def test_get_version_matches_package_metadata(self):
        from importlib.metadata import version

        from maven_decoder_mcp.maven_decoder_server import get_version

        assert get_version() == version("maven-decoder-mcp")

    def test_get_version_is_not_hardcoded_placeholder(self):
        from maven_decoder_mcp.maven_decoder_server import get_version

        assert get_version() != "0.0.0"

    def test_package_json_matches_pyproject(self):
        """Both packaging manifests must declare the same version.

        The release workflow rewrites them from the git tag, but they should
        agree in the repository too so local builds are not misleading.
        """
        root = Path(__file__).resolve().parent.parent

        package_json = json.loads((root / "package.json").read_text())["version"]

        pyproject = (root / "pyproject.toml").read_text()
        pyproject_version = re.search(
            r'^version = "([^"]+)"', pyproject, re.MULTILINE
        ).group(1)

        assert package_json == pyproject_version

    def test_dunder_version_matches_pyproject(self):
        import maven_decoder_mcp

        root = Path(__file__).resolve().parent.parent
        pyproject_version = re.search(
            r'^version = "([^"]+)"',
            (root / "pyproject.toml").read_text(),
            re.MULTILINE,
        ).group(1)

        assert maven_decoder_mcp.__version__ == pyproject_version


class TestServerRemoteIntegration:
    """The server wires the remote client into its tools."""

    def setup_method(self):
        self.server = MavenDecoderServer()

    def test_remote_tools_are_registered(self):
        names = {tool.name for tool in self.server.server._tools}
        assert {"search_maven_central", "get_remote_versions", "download_artifact"} <= names

    def test_cache_is_searched_after_local_repository(self):
        assert self.server.repository_roots[0] == self.server.maven_home
        assert self.server.repository_roots[1] == self.server.cache_home

    def test_analyzer_sees_the_cache(self):
        assert self.server.cache_home in self.server.dependency_analyzer.repository_roots

    @pytest.mark.asyncio
    async def test_jar_is_resolved_from_the_cache(self, tmp_path):
        """A jar present only in the cache is found without any download."""
        jar_path = (
            self.server.cache_home / "com/example/demo/1.0.0/demo-1.0.0.jar"
        )
        jar_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(jar_path, "w") as jar:
            jar.writestr("com/example/Demo.class", b"\xca\xfe\xba\xbe")

        resolved = await self.server._resolve_jar_path("com.example", "demo", "1.0.0")

        assert resolved == jar_path
        assert self.server._path_origin(resolved) == "remote-cache"

    @pytest.mark.asyncio
    async def test_offline_miss_explains_why(self):
        """Offline misses tell the user how to enable downloads."""
        result = await self.server._analyze_jar("com.nope", "nope", "1.0.0")
        text = result[0].text

        assert "Jar file not found" in text
        assert "MAVEN_OFFLINE" in text

    @pytest.mark.asyncio
    async def test_search_reports_offline_instead_of_hanging(self):
        result = await self.server._search_maven_central(class_name="ObjectMapper")
        assert "offline" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_search_surfaces_local_availability(self):
        """Results flag which hits are already installed, to avoid downloads."""
        payload = {
            "search_url": "https://search.example/select",
            "query": 'c:"Demo"',
            "total_found": 1,
            "start": 0,
            "returned": 1,
            "artifacts": [{
                "group_id": "com.example",
                "artifact_id": "demo",
                "version": "1.0.0",
                "coordinates": "com.example:demo:1.0.0",
                "has_sources": False,
                "has_javadoc": False,
                "available_files": [],
                "packaging": "jar",
            }],
        }

        jar_path = self.server.cache_home / "com/example/demo/1.0.0/demo-1.0.0.jar"
        jar_path.parent.mkdir(parents=True, exist_ok=True)
        jar_path.write_bytes(b"jar")

        with patch.object(self.server.central, "search", return_value=payload):
            result = await self.server._search_maven_central(class_name="Demo")

        data = json.loads(result[0].text)
        assert data["artifacts"][0]["installed_locally"] is True

    @pytest.mark.asyncio
    async def test_download_resolves_latest_keyword(self):
        with patch.object(self.server.central, "get_latest_version", return_value="9.9.9") as latest, \
             patch.object(self.server.central, "download_bundle",
                          return_value={"artifact": "g:a:9.9.9", "downloaded": {}}) as bundle:
            result = await self.server._download_artifact("g", "a", "latest")

        latest.assert_called_once_with("g", "a")
        assert bundle.call_args[0][2] == "9.9.9"

        data = json.loads(result[0].text)
        assert data["requested_version"] == "latest"
        assert data["resolved_version"] == "9.9.9"

    @pytest.mark.asyncio
    async def test_version_info_can_include_remote_versions(self):
        remote = {"source": "maven-metadata.xml", "versions": ["2.0.0", "1.0.0"]}

        with patch.object(self.server.central, "get_versions", return_value=remote), \
             patch.object(self.server.central, "offline", False):
            result = await self.server._get_version_info(
                "com.example", "demo", include_remote=True
            )

        data = json.loads(result[0].text)
        assert data["remote"]["versions"] == ["2.0.0", "1.0.0"]

    @pytest.mark.asyncio
    async def test_version_info_stays_local_by_default(self):
        result = await self.server._get_version_info("com.example", "demo")
        assert "remote" not in json.loads(result[0].text)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
