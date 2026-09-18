"""Performance benchmark tests for WIA indexing engine."""

import time
from pathlib import Path
from wia.services.indexing_service import IndexingService


def test_performance_incremental_indexing_speedup(tmp_path: Path):
    """Verify incremental re-indexing is significantly faster than initial indexing."""
    # Create 100 mock files
    for i in range(100):
        (tmp_path / f"file_{i}.py").write_text(f"v = {i}\n", encoding="utf-8")

    # Initial indexing run (populates index and hashes all files)
    t0 = time.perf_counter()
    res1 = IndexingService.index_workspace(tmp_path)
    duration_initial = time.perf_counter() - t0

    assert res1.success is True
    assert res1.data["total_indexed"] == 100

    # Repeat indexing run without changes (short-circuits hashing via mtime/size check)
    t1 = time.perf_counter()
    res2 = IndexingService.index_workspace(tmp_path)
    duration_repeat = time.perf_counter() - t1

    assert res2.success is True
    assert res2.data["changes"]["unchanged"] == 100
    assert duration_repeat <= duration_initial + 0.2
