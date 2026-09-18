"""Unit tests for FileHasher streaming content hashing engine."""

from pathlib import Path
from wia.core.hashing import FileHasher


def test_hash_file_deterministic(tmp_path: Path):
    """Verify hashing the same content yields identical hash digests."""
    file1 = tmp_path / "a.txt"
    file2 = tmp_path / "b.txt"

    content = "def hello(): return 'world'\n"
    file1.write_text(content, encoding="utf-8")
    file2.write_text(content, encoding="utf-8")

    h1 = FileHasher.hash_file(file1)
    h2 = FileHasher.hash_file(file2)

    assert len(h1) == 64  # SHA-256 hex string length
    assert h1 == h2


def test_hash_file_content_change(tmp_path: Path):
    """Verify changing file content produces a different hash digest."""
    file = tmp_path / "code.py"
    file.write_text("v1 = 100\n", encoding="utf-8")
    h1 = FileHasher.hash_file(file)

    file.write_text("v1 = 200\n", encoding="utf-8")
    h2 = FileHasher.hash_file(file)

    assert h1 != h2


def test_hash_large_file_streaming(tmp_path: Path):
    """Verify streaming chunk hashing works on large files (> 64 KB)."""
    large_file = tmp_path / "large.dat"
    data = b"X" * (128 * 1024)  # 128 KB
    large_file.write_bytes(data)

    digest = FileHasher.hash_file(large_file, chunk_size=1024)
    expected_digest = FileHasher.hash_bytes(data)

    assert digest == expected_digest


def test_hash_nonexistent_file(tmp_path: Path):
    """Verify hashing nonexistent file returns empty string."""
    digest = FileHasher.hash_file(tmp_path / "ghost.txt")
    assert digest == ""
