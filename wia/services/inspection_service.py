"""Inspection service for querying WIA index records."""

from pathlib import Path
from wia.core.validator import WorkspaceValidator
from wia.exceptions import IndexNotFoundError
from wia.services.base import BaseService, ServiceResult
from wia.storage.repository import IndexRepository


class InspectionService(BaseService):
    """Provides querying capabilities over stored WIA workspace indices."""

    @classmethod
    def list_files(
        cls, target_path: str | Path | None = None, language: str | None = None
    ) -> ServiceResult[dict]:
        """List active indexed files in workspace, optionally filtered by language."""
        path = Path(target_path).resolve() if target_path else Path.cwd().resolve()

        val_result = WorkspaceValidator.validate(path)
        if not val_result.is_valid:
            return ServiceResult.fail(
                val_result.error_message or f"Invalid workspace path: {path}"
            )

        if not IndexRepository.index_exists(path):
            return ServiceResult.fail(
                f"Workspace at '{path}' is not indexed. Run 'wia index' first.",
                error=IndexNotFoundError(f"Index not found: {path}"),
            )

        try:
            index = IndexRepository.load_index(path)
            if not index:
                return ServiceResult.fail(f"Workspace at '{path}' is not indexed.")

            if language:
                records = index.get_files_by_language(language)
            else:
                records = index.get_indexed_files()

            payload = {
                "workspace_path": str(path),
                "language_filter": language,
                "total_count": len(records),
                "files": [r.to_dict() for r in records],
            }

            return ServiceResult.ok(f"Retrieved {len(records)} file records", data=payload)

        except Exception as err:
            return ServiceResult.fail(
                f"Failed to query index files: {err}", error=err
            )

    @classmethod
    def get_info(cls, target_path: str | Path | None = None) -> ServiceResult[dict]:
        """Retrieve workspace summary information from persistent WIA index."""
        path = Path(target_path).resolve() if target_path else Path.cwd().resolve()

        val_result = WorkspaceValidator.validate(path)
        if not val_result.is_valid:
            return ServiceResult.fail(
                val_result.error_message or f"Invalid workspace path: {path}"
            )

        if not IndexRepository.index_exists(path):
            return ServiceResult.fail(
                f"Workspace at '{path}' is not indexed. Run 'wia index' first.",
                error=IndexNotFoundError(f"Index not found: {path}"),
            )

        try:
            index = IndexRepository.load_index(path)
            if not index:
                return ServiceResult.fail(f"Workspace at '{path}' is not indexed.")

            total_indexed = len(index.get_indexed_files())
            lang_breakdown = []

            if total_indexed > 0:
                for lang, count in sorted(
                    index.languages.items(), key=lambda x: x[1], reverse=True
                ):
                    pct = round((count / total_indexed) * 100, 1)
                    lang_breakdown.append({"language": lang, "count": count, "percentage": pct})

            payload = {
                "workspace_path": str(path),
                "wia_version": index.wia_version,
                "index_version": index.index_version,
                "indexed_at": index.indexed_at,
                "stats": index.stats,
                "languages": lang_breakdown,
                "frameworks": index.frameworks,
            }

            return ServiceResult.ok("Workspace info retrieved", data=payload)

        except Exception as err:
            return ServiceResult.fail(
                f"Failed to retrieve workspace info: {err}", error=err
            )
