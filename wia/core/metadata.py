"""File record metadata representation."""

from dataclasses import dataclass, field, asdict
from typing import Any
from pathlib import Path


class IndexingStatus:
    """Status classifications for file records in the workspace index."""

    INDEXED = "INDEXED"
    IGNORED = "IGNORED"


class WorkspaceStatusState:
    """Status classifications for workspace indexing state."""

    NOT_INITIALIZED = "NOT_INITIALIZED"
    NO_INDEX = "NO_INDEX"
    UP_TO_DATE = "UP_TO_DATE"
    CHANGES_DETECTED = "CHANGES_DETECTED"


@dataclass
class FileRecord:
    """Persistent metadata record for an individual workspace file.

    Designed to be extensible across WIA Phase 1-7 transitions.
    """

    relative_path: str
    file_size: int
    modified_time: float
    extension: str
    content_hash: str = ""
    language: str = "Unknown"
    file_type: str = "Source Code"
    frameworks: list[str] = field(default_factory=list)
    indexing_status: str = IndexingStatus.INDEXED
    exclusion_reason: str | None = None
    extra_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize file record to dictionary for JSON persistence."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FileRecord":
        """Construct FileRecord from deserialized JSON dictionary."""
        return cls(
            relative_path=data["relative_path"],
            file_size=data["file_size"],
            modified_time=data["modified_time"],
            extension=data.get("extension", Path(data["relative_path"]).suffix),
            content_hash=data.get("content_hash", ""),
            language=data.get("language", "Unknown"),
            file_type=data.get("file_type", "Source Code"),
            frameworks=data.get("frameworks", []),
            indexing_status=data.get("indexing_status", IndexingStatus.INDEXED),
            exclusion_reason=data.get("exclusion_reason", None),
            extra_metadata=data.get("extra_metadata", {}),
        )
