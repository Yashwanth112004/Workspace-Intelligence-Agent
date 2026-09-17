"""Unit tests for FileFilter core engine."""

from pathlib import Path
from wia.core.config import WorkspaceConfig
from wia.core.discovery import DiscoveredFile
from wia.core.filter import FileFilter, FilterReason
from wia.core.gitignore import GitignoreProcessor


def test_filter_valid_text_file(tmp_path: Path):
    """Verify standard text/code file passes filter."""
    config = WorkspaceConfig(workspace_path=str(tmp_path))
    file_filter = FileFilter(config)

    file = DiscoveredFile(
        relative_path="src/main.py",
        absolute_path=tmp_path / "src" / "main.py",
        is_symlink=False,
        file_size=100,
        modified_time=0.0,
    )
    res = file_filter.evaluate(file)
    assert res.should_index is True
    assert res.reason is None


def test_filter_legitimate_html_file(tmp_path: Path):
    """Verify legitimate source HTML files pass filter."""
    config = WorkspaceConfig(workspace_path=str(tmp_path))
    file_filter = FileFilter(config)

    file = DiscoveredFile(
        relative_path="docs/index.html",
        absolute_path=tmp_path / "docs" / "index.html",
        is_symlink=False,
        file_size=500,
        modified_time=0.0,
    )
    res = file_filter.evaluate(file)
    assert res.should_index is True


def test_filter_generated_report_artifacts(tmp_path: Path):
    """Verify generated WIA report artifacts are excluded."""
    config = WorkspaceConfig(workspace_path=str(tmp_path))
    file_filter = FileFilter(config)

    report_file = DiscoveredFile(
        relative_path="wia-report.html",
        absolute_path=tmp_path / "wia-report.html",
        is_symlink=False,
        file_size=5000,
        modified_time=0.0,
    )
    res_report = file_filter.evaluate(report_file)
    assert res_report.should_index is False
    assert res_report.reason == FilterReason.BUILD_ARTIFACT

    wia_dir_file = DiscoveredFile(
        relative_path=".wia/index.json",
        absolute_path=tmp_path / ".wia" / "index.json",
        is_symlink=False,
        file_size=5000,
        modified_time=0.0,
    )
    res_wia = file_filter.evaluate(wia_dir_file)
    assert res_wia.should_index is False

    pyc_file = DiscoveredFile(
        relative_path="app.pyc",
        absolute_path=tmp_path / "app.pyc",
        is_symlink=False,
        file_size=500,
        modified_time=0.0,
    )
    res_pyc = file_filter.evaluate(pyc_file)
    assert res_pyc.should_index is False


def test_filter_binary_extension(tmp_path: Path):
    """Verify binary extension files are excluded."""
    config = WorkspaceConfig(workspace_path=str(tmp_path))
    file_filter = FileFilter(config)

    file = DiscoveredFile(
        relative_path="assets/logo.png",
        absolute_path=tmp_path / "assets" / "logo.png",
        is_symlink=False,
        file_size=5000,
        modified_time=0.0,
    )
    res = file_filter.evaluate(file)
    assert res.should_index is False
    assert res.reason == FilterReason.BINARY_FILE


def test_filter_vendor_directory(tmp_path: Path):
    """Verify vendor directory files are excluded."""
    config = WorkspaceConfig(workspace_path=str(tmp_path))
    file_filter = FileFilter(config)

    file = DiscoveredFile(
        relative_path="node_modules/react/index.js",
        absolute_path=tmp_path / "node_modules" / "react" / "index.js",
        is_symlink=False,
        file_size=100,
        modified_time=0.0,
    )
    res = file_filter.evaluate(file)
    assert res.should_index is False
    assert res.reason == FilterReason.VENDOR_DEPENDENCY


def test_filter_exceeds_max_file_size(tmp_path: Path):
    """Verify files exceeding max_file_size_bytes are excluded."""
    config = WorkspaceConfig(
        workspace_path=str(tmp_path), max_file_size_bytes=1000
    )
    file_filter = FileFilter(config)

    file = DiscoveredFile(
        relative_path="data/huge_file.csv",
        absolute_path=tmp_path / "data" / "huge_file.csv",
        is_symlink=False,
        file_size=5000,
        modified_time=0.0,
    )
    res = file_filter.evaluate(file)
    assert res.should_index is False
    assert res.reason == FilterReason.EXCEEDS_MAX_SIZE


def test_filter_gitignore_integration(tmp_path: Path):
    """Verify Gitignore rules integration."""
    (tmp_path / ".gitignore").write_text("*.log", encoding="utf-8")
    config = WorkspaceConfig(workspace_path=str(tmp_path))
    gi = GitignoreProcessor(tmp_path)
    file_filter = FileFilter(config, gitignore_processor=gi)

    file = DiscoveredFile(
        relative_path="app.log",
        absolute_path=tmp_path / "app.log",
        is_symlink=False,
        file_size=10,
        modified_time=0.0,
    )
    res = file_filter.evaluate(file)
    assert res.should_index is False
    assert res.reason == FilterReason.GIT_IGNORED
