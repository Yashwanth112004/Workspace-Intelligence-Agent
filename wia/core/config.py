"""Workspace configuration model and loader."""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from wia.constants import (
    WIA_DIR_NAME,
    WIA_CONFIG_FILE,
    CURRENT_CONFIG_SCHEMA_VERSION,
    DEFAULT_MAX_FILE_SIZE_BYTES,
    DEFAULT_HASH_ALGORITHM,
)
from wia.exceptions import StorageError


@dataclass
class WorkspaceConfig:
    """Workspace configuration model for WIA metadata settings."""

    version: str = CURRENT_CONFIG_SCHEMA_VERSION
    workspace_path: str = ""
    max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES
    hash_algorithm: str = DEFAULT_HASH_ALGORITHM
    exclude_patterns: list[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        """Serialize configuration to a primitive dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "WorkspaceConfig":
        """Construct WorkspaceConfig from a primitive dictionary."""
        return cls(
            version=data.get("version", CURRENT_CONFIG_SCHEMA_VERSION),
            workspace_path=data.get("workspace_path", ""),
            max_file_size_bytes=data.get(
                "max_file_size_bytes", DEFAULT_MAX_FILE_SIZE_BYTES
            ),
            hash_algorithm=data.get("hash_algorithm", DEFAULT_HASH_ALGORITHM),
            exclude_patterns=data.get("exclude_patterns", []),
            created_at=data.get(
                "created_at", datetime.now(timezone.utc).isoformat()
            ),
        )

    @classmethod
    def load_from_workspace(cls, workspace_path: str | Path) -> "WorkspaceConfig":
        """Load configuration from .wia/config.json in workspace."""
        path = Path(workspace_path).resolve()
        config_file = path / WIA_DIR_NAME / WIA_CONFIG_FILE

        if not config_file.exists():
            # Return default config bound to workspace path
            return cls(workspace_path=str(path))

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as err:
            raise StorageError(f"Failed to load configuration file '{config_file}': {err}")

    def save_to_workspace(self, workspace_path: str | Path) -> None:
        """Save configuration to .wia/config.json in workspace."""
        path = Path(workspace_path).resolve()
        wia_dir = path / WIA_DIR_NAME
        wia_dir.mkdir(parents=True, exist_ok=True)
        config_file = wia_dir / WIA_CONFIG_FILE

        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2)
        except Exception as err:
            raise StorageError(f"Failed to write configuration file '{config_file}': {err}")
