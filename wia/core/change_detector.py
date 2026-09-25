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
        """Diff previous file records against current file records with linear set operations."""
        summary = ChangeSummary()

        prev_paths = set(previous_records.keys())
        curr_paths = set(current_records.keys())

        # 1. ADDED files (present in current, absent from previous)
        added_paths = curr_paths - prev_paths
        summary.added = [current_records[p] for p in sorted(added_paths)]

        # 2. DELETED files (present in previous, absent from current)
        deleted_paths = prev_paths - curr_paths
        summary.deleted = [previous_records[p] for p in sorted(deleted_paths)]

        # 3. MODIFIED vs UNCHANGED files (present in both)
        common_paths = curr_paths & prev_paths
        for path in sorted(common_paths):
            prev_rec = previous_records[path]
            curr_rec = current_records[path]

            if curr_rec.content_hash != prev_rec.content_hash:
                summary.modified.append(curr_rec)
            else:
                summary.unchanged.append(curr_rec)

        return summary

    @staticmethod
    def has_changes(
        previous_records: dict[str, FileRecord],
        current_records: dict[str, FileRecord],
    ) -> bool:
        """Fast-path boolean check whether workspace has any added, deleted, or modified files."""
        if len(previous_records) != len(current_records):
            return True
        prev_keys = previous_records.keys()
        curr_keys = current_records.keys()
        if prev_keys != curr_keys:
            return True
        return any(
            current_records[k].content_hash != previous_records[k].content_hash
            for k in prev_keys
        )
