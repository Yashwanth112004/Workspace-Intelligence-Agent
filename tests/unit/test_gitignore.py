"""Unit tests for GitignoreProcessor engine."""

from pathlib import Path
from wia.core.gitignore import GitignoreProcessor


def test_gitignore_root_rules(tmp_path: Path):
    """Test matching against root .gitignore file rules."""
    (tmp_path / ".gitignore").write_text("*.log\nbuild/\nnode_modules/", encoding="utf-8")

    processor = GitignoreProcessor(tmp_path)

    assert processor.is_ignored("app.log") is True
    assert processor.is_ignored("src/debug.log") is True
    assert processor.is_ignored("build/output.js") is True
    assert processor.is_ignored("node_modules/express/index.js") is True
    assert processor.is_ignored("main.py") is False


def test_gitignore_negation_rules(tmp_path: Path):
    """Test gitignore negation (!) unignore rules."""
    (tmp_path / ".gitignore").write_text("*.log\n!important.log", encoding="utf-8")

    processor = GitignoreProcessor(tmp_path)

    assert processor.is_ignored("regular.log") is True
    assert processor.is_ignored("important.log") is False


def test_gitignore_nested_rules(tmp_path: Path):
    """Test matching against nested .gitignore file rules."""
    sub_dir = tmp_path / "src"
    sub_dir.mkdir()
    (sub_dir / ".gitignore").write_text("*.tmp", encoding="utf-8")

    processor = GitignoreProcessor(tmp_path)

    assert processor.is_ignored("src/temp.tmp") is True
    assert processor.is_ignored("other/temp.tmp") is False


def test_default_metadata_dir_ignored(tmp_path: Path):
    """Verify .git and .wia are ignored by default."""
    processor = GitignoreProcessor(tmp_path)

    assert processor.is_ignored(".git/config") is True
    assert processor.is_ignored(".wia/index.json") is True
