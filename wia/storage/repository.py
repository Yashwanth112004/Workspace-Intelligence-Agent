"""Index repository for loading and saving WorkspaceIndex state."""

from pathlib import Path
from wia.constants import WIA_DIR_NAME, WIA_INDEX_FILE, CURRENT_INDEX_SCHEMA_VERSION
from wia.core.index_model import WorkspaceIndex
from wia.exceptions import StorageError, IncompatibleIndexError
from wia.storage.serializer import JsonSerializer


class IndexRepository:
    """Storage repository interface managing `.wia/index.json` operations."""

    @staticmethod
    def get_index_path(workspace_path: str | Path) -> Path:
        """Return canonical path to `.wia/index.json` file."""
        return Path(workspace_path).resolve() / WIA_DIR_NAME / WIA_INDEX_FILE

    @classmethod
    def index_exists(cls, workspace_path: str | Path) -> bool:
        """Check if workspace index file exists."""
        return cls.get_index_path(workspace_path).exists()

    @classmethod
    def load_index(cls, workspace_path: str | Path) -> WorkspaceIndex | None:
        """Load and validate WorkspaceIndex from disk.

        Returns None if index does not exist.
        Raises IncompatibleIndexError if version mismatch occurs.
        Raises StorageError if JSON is corrupted.
        """
        index_file = cls.get_index_path(workspace_path)
        if not index_file.exists():
            return None

        data = JsonSerializer.read_json(index_file)

        # Version compatibility check
        schema_ver = str(data.get("index_version", "0.0"))
        if schema_ver not in ("1.0", "1.1", CURRENT_INDEX_SCHEMA_VERSION):
            raise IncompatibleIndexError(
                f"Incompatible index version '{schema_ver}' on disk. "
                f"Current software expects '{CURRENT_INDEX_SCHEMA_VERSION}'."
            )

        try:
            return WorkspaceIndex.from_dict(data)
        except Exception as err:
            raise StorageError(f"Failed to parse index record from disk: {err}")

    @classmethod
    def save_index(cls, workspace_path: str | Path, index: WorkspaceIndex) -> None:
        """Save WorkspaceIndex atomically to disk."""
        index_file = cls.get_index_path(workspace_path)
        JsonSerializer.atomic_write_json(index_file, index.to_dict())
