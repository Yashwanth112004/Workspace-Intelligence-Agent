"""Unit tests for FileDiscovery core engine."""

from pathlib import Path
from wia.core.discovery import FileDiscovery


def test_discover_files_basic(tmp_path: Path):
    """Test recursive discovery of files in a nested directory tree."""
    (tmp_path / "root.py").write_text("print('root')", encoding="utf-8")
    sub_dir = tmp_path / "src" / "utils"
    sub_dir.mkdir(parents=True, exist_ok=True)
    (sub_dir / "helper.py").write_text("def help(): pass", encoding="utf-8")

    discovered = FileDiscovery.discover_files(tmp_path)
    rel_paths = [f.relative_path for f in discovered]

    assert len(discovered) == 2
    assert rel_paths == ["root.py", "src/utils/helper.py"]


def test_discover_files_excludes_generated_artifacts(tmp_path: Path):
    """Verify generated report artifacts and cache dirs are excluded from discovery."""
    (tmp_path / "main.py").write_text("print('main')", encoding="utf-8")
    (tmp_path / "wia-report.html").write_text("<html>Report</html>", encoding="utf-8")
    (tmp_path / "report_data.json").write_text("{}", encoding="utf-8")
    (tmp_path / "app.pyc").write_text("binary", encoding="utf-8")

    wia_dir = tmp_path / ".wia"
    wia_dir.mkdir()
    (wia_dir / "index.json").write_text("{}", encoding="utf-8")

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.html").write_text("<html>Docs</html>", encoding="utf-8")

    discovered = FileDiscovery.discover_files(tmp_path)
    rel_paths = [f.relative_path for f in discovered]

    assert "main.py" in rel_paths
    assert "docs/index.html" in rel_paths
    assert "wia-report.html" not in rel_paths
    assert "report_data.json" not in rel_paths
    assert "app.pyc" not in rel_paths
    assert not any(".wia" in p for p in rel_paths)


def test_discover_files_posix_path_normalization(tmp_path: Path):
    """Verify relative paths use forward slashes on all platforms."""
    sub_dir = tmp_path / "a" / "b"
    sub_dir.mkdir(parents=True)
    (sub_dir / "c.txt").write_text("test", encoding="utf-8")

    discovered = FileDiscovery.discover_files(tmp_path)
    assert discovered[0].relative_path == "a/b/c.txt"


def test_discover_files_deterministic_sorting(tmp_path: Path):
    """Verify discovery results are sorted alphabetically by relative path."""
    (tmp_path / "z.txt").write_text("z", encoding="utf-8")
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "m.txt").write_text("m", encoding="utf-8")

    discovered = FileDiscovery.discover_files(tmp_path)
    rel_paths = [f.relative_path for f in discovered]
    assert rel_paths == ["a.txt", "m.txt", "z.txt"]


def test_discover_empty_directory(tmp_path: Path):
    """Verify discovering an empty directory returns an empty list."""
    discovered = FileDiscovery.discover_files(tmp_path)
    assert discovered == []
