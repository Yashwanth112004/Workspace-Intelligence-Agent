"""Unit tests for SQLiteStore database persistence."""

from pathlib import Path
from wia.core.index_model import WorkspaceIndex
from wia.core.metadata import FileRecord, IndexingStatus
from wia.storage.sqlite_store import SQLiteStore


def test_sqlite_store_roundtrip(tmp_path: Path):
    db_path = tmp_path / "test_workspace.db"

    index = WorkspaceIndex(
        workspace_path=str(tmp_path),
        files={
            "main.py": FileRecord(
                relative_path="main.py",
                file_size=150,
                modified_time=123456789.0,
                extension=".py",
                content_hash="abc123hash",
                language="Python",
                indexing_status=IndexingStatus.INDEXED,
                extra_metadata={
                    "symbols": [
                        {"name": "main_func", "symbol_type": "function", "line_number": 1}
                    ]
                },
            )
        },
        languages={"Python": 1},
        frameworks=["Django"],
        stats={"total_discovered": 1, "total_indexed": 1},
    )

    # Save to SQLite
    SQLiteStore.save_index(db_path, index)
    assert db_path.exists()

    # Load from SQLite
    loaded_index = SQLiteStore.load_index(db_path)
    assert loaded_index is not None
    assert loaded_index.workspace_path == str(tmp_path)
    assert "main.py" in loaded_index.files
    rec = loaded_index.files["main.py"]
    assert rec.content_hash == "abc123hash"
    assert rec.language == "Python"
    assert rec.extra_metadata["symbols"][0]["name"] == "main_func"
