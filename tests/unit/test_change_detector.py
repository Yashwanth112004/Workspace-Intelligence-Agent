"""Unit tests for ChangeDetector core engine."""

from wia.core.change_detector import ChangeDetector
from wia.core.metadata import FileRecord


def test_detect_changes_added_file():
    """Verify new file is classified as ADDED."""
    prev = {}
    curr = {
        "src/new.py": FileRecord(
            relative_path="src/new.py",
            file_size=10,
            modified_time=1.0,
            extension=".py",
            content_hash="hash_new",
        )
    }

    summary = ChangeDetector.detect_changes(prev, curr)
    assert summary.counts == {"added": 1, "modified": 0, "deleted": 0, "unchanged": 0}
    assert summary.added[0].relative_path == "src/new.py"


def test_detect_changes_deleted_file():
    """Verify missing file is classified as DELETED."""
    prev = {
        "old.py": FileRecord(
            relative_path="old.py",
            file_size=10,
            modified_time=1.0,
            extension=".py",
            content_hash="hash_old",
        )
    }
    curr = {}

    summary = ChangeDetector.detect_changes(prev, curr)
    assert summary.counts == {"added": 0, "modified": 0, "deleted": 1, "unchanged": 0}
    assert summary.deleted[0].relative_path == "old.py"


def test_detect_changes_modified_file():
    """Verify file with changed hash is classified as MODIFIED."""
    prev = {
        "app.py": FileRecord(
            relative_path="app.py",
            file_size=10,
            modified_time=1.0,
            extension=".py",
            content_hash="hash_v1",
        )
    }
    curr = {
        "app.py": FileRecord(
            relative_path="app.py",
            file_size=15,
            modified_time=2.0,
            extension=".py",
            content_hash="hash_v2",
        )
    }

    summary = ChangeDetector.detect_changes(prev, curr)
    assert summary.counts == {"added": 0, "modified": 1, "deleted": 0, "unchanged": 0}
    assert summary.modified[0].relative_path == "app.py"


def test_detect_changes_unchanged_file():
    """Verify file with matching hash is classified as UNCHANGED."""
    rec = FileRecord(
        relative_path="app.py",
        file_size=10,
        modified_time=1.0,
        extension=".py",
        content_hash="hash_same",
    )
    prev = {"app.py": rec}
    curr = {"app.py": rec}

    summary = ChangeDetector.detect_changes(prev, curr)
    assert summary.counts == {"added": 0, "modified": 0, "deleted": 0, "unchanged": 1}
    assert summary.unchanged[0].relative_path == "app.py"
