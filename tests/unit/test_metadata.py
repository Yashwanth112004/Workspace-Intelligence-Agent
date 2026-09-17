"""Unit tests for FileRecord metadata model."""

from wia.core.metadata import FileRecord, IndexingStatus


def test_file_record_defaults():
    """Verify default attributes of FileRecord."""
    record = FileRecord(
        relative_path="src/app.py",
        file_size=1024,
        modified_time=1700000000.0,
        extension=".py",
        content_hash="abc123sha256",
        language="Python",
    )
    assert record.relative_path == "src/app.py"
    assert record.file_size == 1024
    assert record.extension == ".py"
    assert record.indexing_status == IndexingStatus.INDEXED
    assert record.exclusion_reason is None
    assert record.extra_metadata == {}


def test_file_record_serialization():
    """Verify dictionary serialization and deserialization."""
    record = FileRecord(
        relative_path="src/app.py",
        file_size=1024,
        modified_time=1700000000.0,
        extension=".py",
        content_hash="abc123hash",
        language="Python",
        frameworks=["FastAPI"],
        extra_metadata={"ast_nodes": 42},
    )

    data = record.to_dict()
    assert data["relative_path"] == "src/app.py"
    assert data["frameworks"] == ["FastAPI"]
    assert data["extra_metadata"] == {"ast_nodes": 42}

    restored = FileRecord.from_dict(data)
    assert restored == record
