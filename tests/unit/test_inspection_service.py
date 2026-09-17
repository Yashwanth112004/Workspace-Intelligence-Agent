"""Unit tests for InspectionService."""

from pathlib import Path
from wia.services.indexing_service import IndexingService
from wia.services.inspection_service import InspectionService


def test_inspection_unindexed_workspace(tmp_path: Path):
    """Verify InspectionService fails gracefully when workspace is not indexed."""
    res = InspectionService.list_files(tmp_path)
    assert res.success is False
    assert "not indexed" in res.message


def test_inspection_list_files(tmp_path: Path):
    """Verify InspectionService lists indexed files."""
    (tmp_path / "main.py").write_text("print('hello')", encoding="utf-8")
    (tmp_path / "index.ts").write_text("console.log('hi')", encoding="utf-8")
    IndexingService.index_workspace(tmp_path)

    res = InspectionService.list_files(tmp_path)
    assert res.success is True
    assert res.data["total_count"] == 2

    res_py = InspectionService.list_files(tmp_path, language="Python")
    assert res_py.success is True
    assert res_py.data["total_count"] == 1
    assert res_py.data["files"][0]["relative_path"] == "main.py"


def test_inspection_get_info(tmp_path: Path):
    """Verify InspectionService.get_info calculates metrics and language percentages."""
    (tmp_path / "app.py").write_text("print('py')", encoding="utf-8")
    (tmp_path / "script.py").write_text("print('py2')", encoding="utf-8")
    (tmp_path / "style.css").write_text("body {}", encoding="utf-8")
    IndexingService.index_workspace(tmp_path)

    res = InspectionService.get_info(tmp_path)
    assert res.success is True
    data = res.data or {}

    assert data["stats"]["total_indexed"] == 3
    langs = {item["language"]: item["percentage"] for item in data["languages"]}
    assert langs["Python"] == 66.7
    assert langs["CSS"] == 33.3
