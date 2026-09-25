"""Streaming file content hashing engine for change detection."""

import hashlib
from pathlib import Path
from wia.constants import DEFAULT_HASH_ALGORITHM
from wia.exceptions import StorageError


class FileHasher:
    """Computes cryptographic content hashes using streaming chunk processing."""

    DEFAULT_CHUNK_SIZE = 64 * 1024  # 64 KB chunk size

    @classmethod
    def _get_hasher(cls, algorithm: str):
        """Return optimized hashlib instance avoiding string lookup overhead for standard algorithms."""
        if algorithm == "sha256":
            return hashlib.sha256()
        elif algorithm == "sha1":
            return hashlib.sha1()
        elif algorithm == "md5":
            return hashlib.md5()
        return hashlib.new(algorithm)

    @classmethod
    def hash_file(
        cls,
        file_path: str | Path,
        algorithm: str = DEFAULT_HASH_ALGORITHM,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> str:
        """Compute content hash for a file by streaming in fixed-size chunks.

        Avoids loading large files entirely into memory.
        Returns hexadecimal digest string.
        """
        path = Path(file_path)

        if not path.exists() or not path.is_file():
            return ""

        try:
            hasher = cls._get_hasher(algorithm)
            with open(path, "rb", buffering=0) as f:
                buf = bytearray(chunk_size)
                while n := f.readinto(buf):
                    hasher.update(memoryview(buf)[:n])
            return hasher.hexdigest()
        except (PermissionError, OSError) as err:
            # Handle unreadable files during hashing
            raise StorageError(f"Failed to read file for hashing '{path}': {err}")

    @classmethod
    def hash_bytes(
        cls, data: bytes, algorithm: str = DEFAULT_HASH_ALGORITHM
    ) -> str:
        """Compute content hash directly for in-memory byte buffer."""
        hasher = cls._get_hasher(algorithm)
        hasher.update(data)
        return hasher.hexdigest()

    @classmethod
    def hash_text(
        cls, text: str, algorithm: str = DEFAULT_HASH_ALGORITHM
    ) -> str:
        """Compute content hash for string by encoding as UTF-8 bytes."""
        return cls.hash_bytes(text.encode("utf-8"), algorithm=algorithm)
