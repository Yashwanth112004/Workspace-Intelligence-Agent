"""Atomic JSON file serializer."""

import json
import os
from pathlib import Path
from typing import Any
from wia.exceptions import StorageError


class JsonSerializer:
    """Atomic JSON reader and writer for fault-tolerant state persistence."""

    @staticmethod
    def atomic_write_json(file_path: str | Path, data: dict[str, Any]) -> None:
        """Write JSON atomically to disk using a temporary swap file."""
        target = Path(file_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        temp_file = target.with_suffix(target.suffix + ".tmp")

        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())

            # Atomic replace swap operation
            temp_file.replace(target)
        except Exception as err:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass
            raise StorageError(f"Failed to atomically save file '{target}': {err}")

    @staticmethod
    def read_json(file_path: str | Path) -> dict[str, Any]:
        """Read JSON file from disk."""
        target = Path(file_path).resolve()
        if not target.exists():
            raise StorageError(f"File not found: '{target}'")

        try:
            with open(target, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as err:
            raise StorageError(f"Corrupted JSON file '{target}': {err}")
        except Exception as err:
            raise StorageError(f"Failed to read JSON file '{target}': {err}")
