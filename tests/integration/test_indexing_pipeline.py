"""End-to-end integration tests for WIA Indexing Pipeline."""

from pathlib import Path
from wia.services.indexing_service import IndexingService
from wia.storage.repository import IndexRepository


def test_full_indexing_pipeline(tmp_path: Path):
    """Test full indexing pipeline on a mock workspace repository."""
    (tmp_path / "main.py").write_text("print('hello')", encoding="utf-8")
    (tmp_path / "utils.py").write_text("def add(a, b): return a + b", encoding="utf-8")
    (tmp_path / "app.log").write_text("log line", encoding="utf-8")
    (tmp_path / ".gitignore").write_text("*.log\n", encoding="utf-8")

    res = IndexingService.index_workspace(tmp_path)
    assert res.success is True
    data = res.data or {}

    assert data["total_discovered"] == 4  # main.py, utils.py, app.log, .gitignore
    assert data["total_indexed"] == 3    # main.py, utils.py, .gitignore
    assert data["total_ignored"] == 1    # app.log
    assert data["changes"]["added"] == 4
    assert data["languages"].get("Python") == 2

    # Verify index persisted on disk
    loaded_index = IndexRepository.load_index(tmp_path)
    assert loaded_index is not None
    assert len(loaded_index.get_indexed_files()) == 3


def test_incremental_reindexing(tmp_path: Path):
    """Verify second indexing run detects unchanged files."""
    (tmp_path / "main.py").write_text("print('v1')", encoding="utf-8")
    IndexingService.index_workspace(tmp_path)

    # Second run without changes
    res2 = IndexingService.index_workspace(tmp_path)
    data2 = res2.data or {}
    assert data2["changes"]["added"] == 0
    assert data2["changes"]["modified"] == 0
    assert data2["changes"]["unchanged"] == 1

    # Modify file and add new file
    (tmp_path / "main.py").write_text("print('v2')", encoding="utf-8")
    (tmp_path / "new.py").write_text("x = 1", encoding="utf-8")

    res3 = IndexingService.index_workspace(tmp_path)
    data3 = res3.data or {}
    assert data3["changes"]["added"] == 1
    assert data3["changes"]["modified"] == 1
    assert data3["changes"]["unchanged"] == 0
