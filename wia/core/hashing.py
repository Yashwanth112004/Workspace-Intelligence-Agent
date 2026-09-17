"""Streaming file content hashing engine for change detection."""

import hashlib
from pathlib import Path
from wia.constants import DEFAULT_HASH_ALGORITHM
from wia.exceptions import StorageError


class FileHasher:
    """Computes cryptographic content hashes using streaming chunk processing."""

    DEFAULT_CHUNK_SIZE = 64 * 1024  # 64 KB chunk size

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
            hasher = hashlib.new(algorithm)
            with open(path, "rb") as f:
                while chunk := f.read(chunk_size):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (PermissionError, OSError) as err:
            # Handle unreadable files during hashing
            raise StorageError(f"Failed to read file for hashing '{path}': {err}")

    @classmethod
    def hash_bytes(
        cls, data: bytes, algorithm: str = DEFAULT_HASH_ALGORITHM
    ) -> str:
        """Compute content hash directly for in-memory byte buffer."""
        hasher = hashlib.new(algorithm)
        hasher.update(data)
        return hasher.hexdigest()
