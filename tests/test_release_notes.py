#!/usr/bin/env python3
"""
Tests for scripts/generate_release_notes.py and the release version flow.

The release workflow regenerates RELEASE_NOTES.md from git history when the
committed file does not cover the tag, so these tests pin both the generator
and the guard behaviour that makes stale notes impossible.
"""

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "generate_release_notes.py"


def load_generator(tmp_repo):
    """Load the generator with its REPO_ROOT pointed at a scratch git repo."""
    spec = importlib.util.spec_from_file_location("gen_notes", SCRIPT)
    assert spec is not None and spec.loader is not None, f"cannot load {SCRIPT}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.REPO_ROOT = Path(tmp_repo)
    module.RELEASE_NOTES = Path(tmp_repo) / "RELEASE_NOTES.md"
    return module


@pytest.fixture
def git_repo(tmp_path):
    """A scratch repo with a conventional-commit history and tags."""
    def run(*args):
        subprocess.run(
            ["git", *args], cwd=tmp_path, check=True,
            capture_output=True, text=True,
        )

    run("init")
    run("config", "user.email", "test@example.com")
    run("config", "user.name", "test")
    (tmp_path / "a.txt").write_text("a")
    run("add", ".")
    run("commit", "-m", "fix: repair widget")
    run("tag", "v1.0.0")
    (tmp_path / "b.txt").write_text("b")
    run("add", ".")
    run("commit", "-m", "feat: add sprocket")
    run("commit", "--allow-empty", "-m", "docs: touch up readme")
    return tmp_path


class TestGenerate:
    def test_sections_come_from_commit_subjects(self, git_repo):
        gen = load_generator(git_repo)
        body = gen.generate("v1.1.0")

        assert "# Maven Decoder MCP Server v1.1.0" in body
        assert "- feat: add sprocket" in body
        assert "- fix: repair widget" not in body  # predates v1.0.0
        assert "- docs: touch up readme" in body
        assert "v1.0.0...v1.1.0" in body

    def test_maintenance_section_present_when_needed(self, git_repo):
        gen = load_generator(git_repo)
        assert "### Maintenance" in gen.generate("v1.1.0")

    def test_install_snippet_tracks_tag(self, git_repo):
        gen = load_generator(git_repo)
        assert "ali79taba/maven-decoder-mcp:1.1.0" in gen.generate("v1.1.0")

    def test_works_before_tag_exists(self, git_repo):
        """Notes are drafted before tagging, against HEAD."""
        gen = load_generator(git_repo)
        body = gen.generate("v9.9.9")

        assert "- feat: add sprocket" in body
        assert "v1.0.0...v9.9.9" in body

    def test_rejects_malformed_tags(self, git_repo):
        gen = load_generator(git_repo)
        with pytest.raises(ValueError):
            gen.parse_tag("1.1.0")
        with pytest.raises(ValueError):
            gen.parse_tag("release-1")


class TestCheck:
    def test_missing_notes_fail(self, git_repo):
        gen = load_generator(git_repo)
        assert gen.check("v1.1.0") is False

    def test_notes_for_other_tag_fail(self, git_repo):
        gen = load_generator(git_repo)
        gen.RELEASE_NOTES.write_text("# Maven Decoder MCP Server v1.0.0\n\nnotes\n")
        assert gen.check("v1.1.0") is False

    def test_stub_notes_fail(self, git_repo):
        gen = load_generator(git_repo)
        gen.RELEASE_NOTES.write_text("# Maven Decoder MCP Server v1.1.0\n")
        assert gen.check("v1.1.0") is False

    def test_valid_notes_pass(self, git_repo):
        gen = load_generator(git_repo)
        gen.RELEASE_NOTES.write_text(gen.generate("v1.1.0"))
        assert gen.check("v1.1.0") is True

    def test_notes_headed_for_other_release_fail(self, git_repo):
        """A body whose heading names a different release is stale, even if
        the tag appears somewhere (e.g. inside a compare link)."""
        gen = load_generator(git_repo)
        gen.RELEASE_NOTES.write_text(
            "# Maven Decoder MCP Server v1.0.0\n\n"
            "Some old content that also mentions v1.1.0 in passing.\n"
            "More lines here to pass the length check.\n"
            "Still going.\n"
            "And going.\n"
        )
        assert gen.check("v1.1.0") is False


class TestVersionFlow:
    """The repo's version copies must agree; the workflow rewrites all three
    from the tag, but local builds and the drift regression test read these."""

    @staticmethod
    def _first_group(pattern: str, text: str, label: str) -> str:
        match = re.search(pattern, text, re.M)
        assert match is not None, f"could not find {label}"
        return match.group(1)

    def test_versions_agree(self):
        pyproject = (REPO_ROOT / "pyproject.toml").read_text()
        package = (REPO_ROOT / "package.json").read_text()

        py_version = self._first_group(r'^version = "([^"]+)"', pyproject, "pyproject version")
        js_version = self._first_group(r'"version": "([^"]+)"', package, "package.json version")
        dunder = self._first_group(
            r'__version__ = "([^"]+)"',
            (REPO_ROOT / "maven_decoder_mcp" / "__init__.py").read_text(),
            "package __version__",
        )

        assert py_version == js_version == dunder, (
            f"pyproject={py_version} package.json={js_version} __init__={dunder}"
        )

    def test_workflow_syncs_all_three_copies(self):
        """CI must rewrite pyproject, package.json AND __init__ from the tag,
        or the fixed version drift returns (server reported 1.0.0 for months)."""
        workflow = (REPO_ROOT / ".github" / "workflows" / "release.yml").read_text()
        assert workflow.count("Sync versions from tag") == 2
        for target in ("pyproject.toml", "package.json", "__init__.py"):
            assert target in workflow, f"workflow no longer syncs {target}"

    def test_workflow_has_no_static_release_body(self):
        """A fixed template is how every release shipped v1.0.0-era notes."""
        workflow = (REPO_ROOT / ".github" / "workflows" / "release.yml").read_text()
        assert "Pagination and Summarization" not in workflow
        assert "generate_release_notes.py" in workflow

    def test_skill_and_generator_agree_on_commands(self):
        """SKILL.md must only reference scripts that exist."""
        skill = (REPO_ROOT / "skills" / "project-release" / "SKILL.md").read_text()
        assert "scripts/generate_release_notes.py" in skill
        assert SCRIPT.is_file()
        assert (REPO_ROOT / "RELEASING.md").is_file()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
