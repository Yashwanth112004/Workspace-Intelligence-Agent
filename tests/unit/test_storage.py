"""Unit tests for JsonSerializer and IndexRepository storage engine."""

import pytest
from pathlib import Path
from wia.core.index_model import WorkspaceIndex
from wia.exceptions import StorageError, IncompatibleIndexError
from wia.storage.repository import IndexRepository
from wia.storage.serializer import JsonSerializer


def test_atomic_write_and_read(tmp_path: Path):
    """Verify atomic writing and reading of JSON files."""
    json_path = tmp_path / "test.json"
    data = {"status": "ok", "value": 42}

    JsonSerializer.atomic_write_json(json_path, data)
    assert json_path.exists()

    read_data = JsonSerializer.read_json(json_path)
    assert read_data == data


def test_read_corrupted_json(tmp_path: Path):
    """Verify loading corrupted JSON file raises StorageError."""
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{ incomplete json string...", encoding="utf-8")

    with pytest.raises(StorageError):
        JsonSerializer.read_json(bad_json)


def test_index_repository_save_and_load(tmp_path: Path):
    """Verify saving and reloading WorkspaceIndex via IndexRepository."""
    idx = WorkspaceIndex(workspace_path=str(tmp_path))
    IndexRepository.save_index(tmp_path, idx)

    assert IndexRepository.index_exists(tmp_path) is True

    reloaded = IndexRepository.load_index(tmp_path)
    assert reloaded is not None
    assert reloaded.workspace_path == str(tmp_path)


def test_index_repository_incompatible_version(tmp_path: Path):
    """Verify loading an index with incompatible version raises IncompatibleIndexError."""
    idx = WorkspaceIndex(workspace_path=str(tmp_path), index_version="99.0")
    IndexRepository.save_index(tmp_path, idx)

    with pytest.raises(IncompatibleIndexError):
        IndexRepository.load_index(tmp_path)
