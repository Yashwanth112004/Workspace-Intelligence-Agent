"""Unit tests for WorkspaceIndex model."""

from wia.core.index_model import WorkspaceIndex
from wia.core.metadata import FileRecord, IndexingStatus


def test_index_model_serialization():
    """Verify serialization and deserialization of WorkspaceIndex."""
    rec1 = FileRecord(
        relative_path="src/main.py",
        file_size=500,
        modified_time=100.0,
        extension=".py",
        content_hash="hash1",
        language="Python",
    )
    rec2 = FileRecord(
        relative_path="docs/readme.md",
        file_size=200,
        modified_time=100.0,
        extension=".md",
        content_hash="hash2",
        indexing_status=IndexingStatus.IGNORED,
        exclusion_reason="GIT_IGNORED",
    )

    idx = WorkspaceIndex(
        workspace_path="/repo",
        files={"src/main.py": rec1, "docs/readme.md": rec2},
        languages={"Python": 1},
        frameworks=["FastAPI"],
    )

    data = idx.to_dict()
    assert data["index_version"] == "1.0"
    assert data["languages"] == {"Python": 1}
    assert "src/main.py" in data["files"]

    restored = WorkspaceIndex.from_dict(data)
    assert restored.workspace_path == idx.workspace_path
    assert len(restored.get_indexed_files()) == 1
    assert restored.get_files_by_language("python")[0].relative_path == "src/main.py"
