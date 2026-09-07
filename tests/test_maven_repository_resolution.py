#!/usr/bin/env python3
"""Tests for Maven local repository resolution (issue #1)."""

import os
from pathlib import Path
from unittest.mock import patch

from maven_decoder_mcp.config import Config
from maven_decoder_mcp.maven_decoder_server import MavenDecoderServer


class TestResolveMavenRepository:
    def setup_method(self):
        for var in ("MAVEN_REPOSITORY", "MAVEN_REPO", "MAVEN_HOME", "M2_HOME"):
            os.environ.pop(var, None)

    def teardown_method(self):
        for var in ("MAVEN_REPOSITORY", "MAVEN_REPO", "MAVEN_HOME", "M2_HOME"):
            os.environ.pop(var, None)

    def test_direct_repo_vars_win(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        os.environ["MAVEN_HOME"] = str(tmp_path / "ignored-maven")
        os.environ["MAVEN_REPO"] = str(repo)
        assert Config.resolve_maven_repository() == repo.resolve()

        os.environ.pop("MAVEN_REPO")
        os.environ["MAVEN_REPOSITORY"] = str(repo)
        assert Config.resolve_maven_repository() == repo.resolve()

    def test_maven_home_with_nested_repository(self, tmp_path):
        home = tmp_path / "maven"
        (home / "repository").mkdir(parents=True)
        os.environ["MAVEN_HOME"] = str(home)
        assert Config.resolve_maven_repository() == (home / "repository").resolve()

    def test_maven_home_pointing_at_repo_itself(self, tmp_path):
        repo = tmp_path / "repository"
        repo.mkdir()
        os.environ["MAVEN_HOME"] = str(repo)
        assert Config.resolve_maven_repository() == repo.resolve()

    def test_maven_home_settings_local_repo(self, tmp_path):
        home = tmp_path / "maven"
        (home / "conf").mkdir(parents=True)
        custom = tmp_path / "custom-repo"
        custom.mkdir()
        (home / "conf" / "settings.xml").write_text(
            f"<settings><localRepository>{custom}</localRepository></settings>"
        )
        os.environ["MAVEN_HOME"] = str(home)
        assert Config.resolve_maven_repository() == custom.resolve()

    def test_default_settings_local_repo(self, tmp_path):
        custom = tmp_path / "custom-repo"
        custom.mkdir()
        fake_home = tmp_path / "home"
        (fake_home / ".m2").mkdir(parents=True)
        (fake_home / ".m2" / "settings.xml").write_text(
            f"<settings><localRepository>{custom}</localRepository></settings>"
        )
        with patch.object(Path, "home", return_value=fake_home):
            assert Config.resolve_maven_repository() == custom.resolve()

    def test_fallback_default(self, tmp_path):
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        with patch.object(Path, "home", return_value=fake_home):
            assert (
                Config.resolve_maven_repository()
                == (fake_home / ".m2" / "repository").resolve()
            )

    def test_server_uses_resolved_repo(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        with patch.object(
            Config, "resolve_maven_repository", return_value=repo
        ), patch("maven_decoder_mcp.maven_decoder_server.Path.home") as mock_home:
            mock_home.return_value = Path("/mock/home")
            server = MavenDecoderServer()
        assert server.maven_home == repo
        assert server.dependency_analyzer.maven_home == repo

    def test_server_explicit_arg_overrides_env(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        other = tmp_path / "other"
        other.mkdir()
        os.environ["MAVEN_REPO"] = str(other)
        with patch("maven_decoder_mcp.maven_decoder_server.Path.home") as mock_home:
            mock_home.return_value = Path("/mock/home")
            server = MavenDecoderServer(maven_repository=str(repo))
        assert server.maven_home == repo.resolve()
