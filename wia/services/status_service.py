"""Status service for checking workspace index state and pending changes."""

from pathlib import Path
from wia.constants import WIA_DIR_NAME
from wia.core.change_detector import ChangeDetector
from wia.core.config import WorkspaceConfig
from wia.core.discovery import FileDiscovery
from wia.core.filter import FileFilter
from wia.core.gitignore import GitignoreProcessor
from wia.core.hashing import FileHasher
from wia.core.metadata import FileRecord, IndexingStatus, WorkspaceStatusState
from wia.core.validator import WorkspaceValidator
from wia.services.base import BaseService, ServiceResult
from wia.storage.repository import IndexRepository


class StatusService(BaseService):
    """Calculates workspace indexing status and pending changes without mutating index."""

    @classmethod
    def get_status(cls, target_path: str | Path | None = None) -> ServiceResult[dict]:
        """Compute workspace status and pending file changes without modifying index state."""
        path = Path(target_path).resolve() if target_path else Path.cwd().resolve()

        val_result = WorkspaceValidator.validate(path)
        if not val_result.is_valid:
            return ServiceResult.fail(
                val_result.error_message or f"Invalid workspace path: {path}"
            )

        wia_dir = path / WIA_DIR_NAME
        if not wia_dir.exists():
            return ServiceResult.ok(
                "Workspace not initialized",
                data={
                    "status_code": WorkspaceStatusState.NOT_INITIALIZED,
                    "status_label": "Not Initialized",
                    "is_initialized": False,
                    "is_indexed": False,
                    "workspace_path": str(path),
                },
            )

        try:
            previous_index = IndexRepository.load_index(path)
            if not previous_index or not previous_index.get_indexed_files():
                return ServiceResult.ok(
                    "Workspace initialized but not indexed",
                    data={
                        "status_code": WorkspaceStatusState.NO_INDEX,
                        "status_label": "Initialized — Not Indexed",
                        "is_initialized": True,
                        "is_indexed": False,
                        "workspace_path": str(path),
                    },
                )

            config = WorkspaceConfig.load_from_workspace(path)
            discovered = FileDiscovery.discover_files(path)
            gi_processor = GitignoreProcessor(path)
            file_filter = FileFilter(config, gitignore_processor=gi_processor)

            current_records: dict[str, FileRecord] = {}

            for file in discovered:
                filter_res = file_filter.evaluate(file)
                if not filter_res.should_index:
                    continue

                prev_rec = previous_index.files.get(file.relative_path)
                if (
                    prev_rec
                    and prev_rec.indexing_status == IndexingStatus.INDEXED
                    and prev_rec.modified_time == file.modified_time
                    and prev_rec.file_size == file.file_size
                ):
                    content_hash = prev_rec.content_hash
                else:
                    content_hash = FileHasher.hash_file(
                        file.absolute_path, algorithm=config.hash_algorithm
                    )

                current_records[file.relative_path] = FileRecord(
                    relative_path=file.relative_path,
                    file_size=file.file_size,
                    modified_time=file.modified_time,
                    extension=Path(file.relative_path).suffix,
                    content_hash=content_hash,
                    indexing_status=IndexingStatus.INDEXED,
                )

            # Filter previous records to indexed files for change diffing
            prev_indexed = {
                k: v
                for k, v in previous_index.files.items()
                if v.indexing_status == IndexingStatus.INDEXED
            }

            change_summary = ChangeDetector.detect_changes(
                previous_records=prev_indexed, current_records=current_records
            )

            has_changes = (
                change_summary.counts["added"] > 0
                or change_summary.counts["modified"] > 0
                or change_summary.counts["deleted"] > 0
            )

            status_code = (
                WorkspaceStatusState.CHANGES_DETECTED
                if has_changes
                else WorkspaceStatusState.UP_TO_DATE
            )
            status_label = "Changes Detected" if has_changes else "Up to Date"

            payload = {
                "status_code": status_code,
                "status_label": status_label,
                "is_initialized": True,
                "is_indexed": True,
                "has_changes": has_changes,
                "workspace_path": str(path),
                "index_version": previous_index.index_version,
                "wia_version": previous_index.wia_version,
                "indexed_at": previous_index.indexed_at,
                "indexed_files_count": len(previous_index.get_indexed_files()),
                "changes": change_summary.counts,
            }

            return ServiceResult.ok("Workspace status retrieved", data=payload)

        except Exception as err:
            return ServiceResult.fail(
                f"Failed to inspect workspace status: {err}", error=err
            )
