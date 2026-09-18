"""Incremental change detection engine."""

from dataclasses import dataclass, field
from wia.core.metadata import FileRecord


class FileChangeType:
    """Classifications for file state changes."""

    ADDED = "ADDED"
    MODIFIED = "MODIFIED"
    DELETED = "DELETED"
    UNCHANGED = "UNCHANGED"


@dataclass
class ChangeSummary:
    """Encapsulates change classification lists and summary counts."""

    added: list[FileRecord] = field(default_factory=list)
    modified: list[FileRecord] = field(default_factory=list)
    deleted: list[FileRecord] = field(default_factory=list)
    unchanged: list[FileRecord] = field(default_factory=list)

    @property
    def counts(self) -> dict[str, int]:
        """Return dict of change category counts."""
        return {
            "added": len(self.added),
            "modified": len(self.modified),
            "deleted": len(self.deleted),
            "unchanged": len(self.unchanged),
        }

    @property
    def total_current_files(self) -> int:
        """Total current files (added + modified + unchanged)."""
        return len(self.added) + len(self.modified) + len(self.unchanged)


class ChangeDetector:
    """Diffs current workspace state against previous WIA index state in O(N + M) time."""

    @staticmethod
    def detect_changes(
        previous_records: dict[str, FileRecord],
        current_records: dict[str, FileRecord],
    ) -> ChangeSummary:
        """Diff previous file records against current file records."""
        summary = ChangeSummary()

        prev_paths = set(previous_records.keys())
        curr_paths = set(current_records.keys())

        # 1. ADDED files (present in current, absent from previous)
        for path in sorted(curr_paths - prev_paths):
            summary.added.append(current_records[path])

        # 2. DELETED files (present in previous, absent from current)
        for path in sorted(prev_paths - curr_paths):
            summary.deleted.append(previous_records[path])

        # 3. MODIFIED vs UNCHANGED files (present in both)
        for path in sorted(curr_paths & prev_paths):
            prev_rec = previous_records[path]
            curr_rec = current_records[path]

            if curr_rec.content_hash != prev_rec.content_hash:
                summary.modified.append(curr_rec)
            else:
                summary.unchanged.append(curr_rec)

        return summary
