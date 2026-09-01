"""Workspace Index schema data model."""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any
import wia
from wia.constants import CURRENT_INDEX_SCHEMA_VERSION
from wia.core.metadata import FileRecord, IndexingStatus


@dataclass
class BatchRecord:
    """Persistent execution record for a workspace processing batch."""

    batch_id: str
    status: str = "COMPLETED"  # COMPLETED, RUNNING, PENDING, FAILED
    file_paths: list[str] = field(default_factory=list)
    discovered_count: int = 0
    indexed_count: int = 0
    ignored_count: int = 0
    duration_seconds: float = 0.0
    started_at: str = ""
    completed_at: str | None = None
    error_message: str | None = None
    failure_stage: str | None = None
    narrative_summary: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize batch record to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BatchRecord":
        """Construct BatchRecord from deserialized dictionary."""
        return cls(
            batch_id=data.get("batch_id", ""),
            status=data.get("status", "COMPLETED"),
            file_paths=data.get("file_paths", []),
            discovered_count=data.get("discovered_count", 0),
            indexed_count=data.get("indexed_count", 0),
            ignored_count=data.get("ignored_count", 0),
            duration_seconds=data.get("duration_seconds", 0.0),
            started_at=data.get("started_at", ""),
            completed_at=data.get("completed_at"),
            error_message=data.get("error_message"),
            failure_stage=data.get("failure_stage"),
            narrative_summary=data.get("narrative_summary"),
        )


@dataclass
class WorkspaceIndex:
    """Versioned schema model for persistent WIA workspace index state."""

    index_version: str = CURRENT_INDEX_SCHEMA_VERSION
    wia_version: str = field(default_factory=lambda: wia.__version__)
    workspace_path: str = ""
    indexed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    files: dict[str, FileRecord] = field(default_factory=dict)
    languages: dict[str, int] = field(default_factory=dict)
    frameworks: list[str] = field(default_factory=list)
    batches: list[BatchRecord] = field(default_factory=list)
    stats: dict[str, Any] = field(
        default_factory=lambda: {
            "total_discovered": 0,
            "total_indexed": 0,
            "total_ignored": 0,
            "indexing_duration_seconds": 0.0,
        }
    )

    def get_indexed_files(self) -> list[FileRecord]:
        """Return list of active indexed file records."""
        return [
            f for f in self.files.values() if f.indexing_status == IndexingStatus.INDEXED
        ]

    def get_files_by_language(self, language: str) -> list[FileRecord]:
        """Return indexed files matching target language (case-insensitive)."""
        target = language.lower()
        return [
            f
            for f in self.get_indexed_files()
            if f.language.lower() == target
        ]

    def to_dict(self) -> dict[str, Any]:
        """Serialize WorkspaceIndex to dictionary for JSON persistence."""
        return {
            "index_version": self.index_version,
            "wia_version": self.wia_version,
            "workspace_path": self.workspace_path,
            "indexed_at": self.indexed_at,
            "files": {path: rec.to_dict() for path, rec in self.files.items()},
            "languages": self.languages,
            "frameworks": self.frameworks,
            "batches": [b.to_dict() for b in self.batches],
            "stats": self.stats,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkspaceIndex":
        """Construct WorkspaceIndex from deserialized JSON dictionary."""
        files_data = data.get("files", {})
        file_records = {
            path: FileRecord.from_dict(rec_dict)
            for path, rec_dict in files_data.items()
        }
        batches_data = data.get("batches", [])
        batch_records = [BatchRecord.from_dict(b) for b in batches_data]

        return cls(
            index_version=data.get("index_version", CURRENT_INDEX_SCHEMA_VERSION),
            wia_version=data.get("wia_version", wia.__version__),
            workspace_path=data.get("workspace_path", ""),
            indexed_at=data.get("indexed_at", datetime.now(timezone.utc).isoformat()),
            files=file_records,
            languages=data.get("languages", {}),
            frameworks=data.get("frameworks", []),
            batches=batch_records,
            stats=data.get("stats", {}),
        )
