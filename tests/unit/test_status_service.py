"""Unit tests for StatusService states, change detection, and read-only preservation."""

from pathlib import Path
from wia.core.metadata import WorkspaceStatusState
from wia.services.indexing_service import IndexingService
from wia.services.init_service import InitService
from wia.services.status_service import StatusService


def test_status_uninitialized_workspace(tmp_path: Path):
    """Verify StatusService detects NOT_INITIALIZED workspace."""
    res = StatusService.get_status(tmp_path)
    assert res.success is True
    assert res.data["status_code"] == WorkspaceStatusState.NOT_INITIALIZED
    assert res.data["status_label"] == "Not Initialized"
    assert res.data["is_initialized"] is False


def test_status_initialized_unindexed_workspace(tmp_path: Path):
    """Verify StatusService detects NO_INDEX workspace."""
    InitService.initialize_workspace(tmp_path)
    res = StatusService.get_status(tmp_path)
    assert res.success is True
    assert res.data["status_code"] == WorkspaceStatusState.NO_INDEX
    assert res.data["status_label"] == "Initialized — Not Indexed"
    assert res.data["is_initialized"] is True
    assert res.data["is_indexed"] is False


def test_status_up_to_date_workspace(tmp_path: Path):
    """Verify StatusService detects UP_TO_DATE indexed workspace."""
    (tmp_path / "main.py").write_text("print('hello')", encoding="utf-8")
    IndexingService.index_workspace(tmp_path)

    res = StatusService.get_status(tmp_path)
    assert res.success is True
    assert res.data["status_code"] == WorkspaceStatusState.UP_TO_DATE
    assert res.data["status_label"] == "Up to Date"
    assert res.data["indexed_files_count"] == 1
    assert res.data["changes"]["unchanged"] == 1
    assert res.data["changes"]["added"] == 0
    assert res.data["changes"]["modified"] == 0
    assert res.data["changes"]["deleted"] == 0


def test_status_changes_detected_modified(tmp_path: Path):
    """Verify StatusService detects modified file change."""
    main_file = tmp_path / "main.py"
    main_file.write_text("print('hello')", encoding="utf-8")
    IndexingService.index_workspace(tmp_path)

    # Modify file after index
    main_file.write_text("print('hello world')", encoding="utf-8")

    res = StatusService.get_status(tmp_path)
    assert res.success is True
    assert res.data["status_code"] == WorkspaceStatusState.CHANGES_DETECTED
    assert res.data["status_label"] == "Changes Detected"
    assert res.data["changes"]["modified"] == 1


def test_status_changes_detected_added_and_deleted(tmp_path: Path):
    """Verify StatusService detects added and deleted file changes."""
    f1 = tmp_path / "f1.py"
    f2 = tmp_path / "f2.py"
    f1.write_text("a = 1", encoding="utf-8")
    f2.write_text("b = 2", encoding="utf-8")
    IndexingService.index_workspace(tmp_path)

    # Delete f2 and add f3
    f2.unlink()
    (tmp_path / "f3.py").write_text("c = 3", encoding="utf-8")

    res = StatusService.get_status(tmp_path)
    assert res.success is True
    assert res.data["status_code"] == WorkspaceStatusState.CHANGES_DETECTED
    assert res.data["changes"]["added"] == 1
    assert res.data["changes"]["deleted"] == 1
    assert res.data["changes"]["unchanged"] == 1


def test_status_read_only_preserves_timestamp(tmp_path: Path):
    """Verify executing status does not mutate last indexed timestamp or index records."""
    (tmp_path / "app.py").write_text("v = 1", encoding="utf-8")
    IndexingService.index_workspace(tmp_path)

    initial_res = StatusService.get_status(tmp_path)
    ts1 = initial_res.data["indexed_at"]

    # Execute status multiple times
    res2 = StatusService.get_status(tmp_path)
    res3 = StatusService.get_status(tmp_path)

    assert res2.data["indexed_at"] == ts1
    assert res3.data["indexed_at"] == ts1
