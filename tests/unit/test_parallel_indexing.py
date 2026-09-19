"""Unit tests for parallel worker indexing, incremental caching, and failure isolation."""

from pathlib import Path
from wia.core.index_model import WorkspaceIndex
from wia.core.metadata import IndexingStatus
from wia.services.indexing_service import IndexingService
from wia.services.init_service import InitService
from wia.storage.repository import IndexRepository


def test_parallel_worker_indexing(tmp_path: Path):
    InitService.initialize_workspace(tmp_path)

    # Create 10 source files
    for i in range(10):
        (tmp_path / f"module_{i}.py").write_text(
            f"def func_{i}():\n    '''Function {i} docstring.'''\n    return {i}\n",
            encoding="utf-8",
        )

    # Index with 4 workers
    res = IndexingService.index_workspace(tmp_path, max_workers=4)
    assert res.success
    data = res.data
    assert data["total_indexed"] == 10
    assert data["workers_used"] == 4

    index = IndexRepository.load_index(tmp_path)
    assert index is not None
    assert len(index.get_indexed_files()) == 10


def test_incremental_indexing_skips_unchanged(tmp_path: Path):
    InitService.initialize_workspace(tmp_path)

    (tmp_path / "file1.py").write_text("def a(): pass\n", encoding="utf-8")
    (tmp_path / "file2.py").write_text("def b(): pass\n", encoding="utf-8")

    # Initial indexing
    res1 = IndexingService.index_workspace(tmp_path, max_workers=2)
    assert res1.success
    assert res1.data["total_indexed"] == 2

    # Second indexing without changes
    res2 = IndexingService.index_workspace(tmp_path, max_workers=2)
    assert res2.success
    assert res2.data["total_skipped_unchanged"] == 2


def test_failure_isolation_on_corrupted_file(tmp_path: Path):
    InitService.initialize_workspace(tmp_path)

    # Valid file A
    (tmp_path / "good.py").write_text("def valid_function(): return 42\n", encoding="utf-8")
    # File B with invalid syntax
    (tmp_path / "bad.py").write_text("def invalid syntax ::: !!!\n", encoding="utf-8")

    # Indexing must NOT crash
    res = IndexingService.index_workspace(tmp_path, max_workers=2)
    assert res.success
    assert res.data["total_indexed"] == 2

    index = IndexRepository.load_index(tmp_path)
    assert index is not None
    good_rec = index.files.get("good.py")
    bad_rec = index.files.get("bad.py")

    assert good_rec is not None
    assert len(good_rec.extra_metadata.get("symbols", [])) == 1

    assert bad_rec is not None
    # Bad file was safely isolated
    assert bad_rec.indexing_status == IndexingStatus.INDEXED
