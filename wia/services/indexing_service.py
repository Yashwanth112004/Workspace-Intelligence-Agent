import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from wia.analyzers.code.ast_parser import ASTParser
from wia.analyzers.dependency.conflict_detector import ConflictDetector
from wia.analyzers.dependency.manifest_parser import ManifestParser
from wia.analyzers.git.git_analyzer import GitAnalyzer
from wia.analyzers.security.secret_scanner import SecretScanner
from wia.core.batch_planner import BatchPlanner
from wia.core.change_detector import ChangeDetector
from wia.core.config import WorkspaceConfig
from wia.core.discovery import DiscoveredFile, FileDiscovery
from wia.core.filter import FileFilter
from wia.core.framework import FrameworkDetector
from wia.core.gitignore import GitignoreProcessor
from wia.core.hashing import FileHasher
from wia.core.index_model import BatchRecord, WorkspaceIndex
from wia.core.language import LanguageDetector
from wia.core.metadata import FileRecord, IndexingStatus
from wia.core.validator import WorkspaceValidator
from wia.knowledge.graph import WorkspaceGraph
from wia.services.base import BaseService, ServiceResult
from wia.storage.repository import IndexRepository


def _process_file_worker(
    file: DiscoveredFile,
    file_filter: FileFilter,
    config: WorkspaceConfig,
    prev_rec: FileRecord | None,
    batch_id: str,
) -> tuple[FileRecord, bool, bool, bool, bool]:
    """Worker function to process an individual file in parallel.

    Returns: (file_record, is_indexed, is_ignored, is_skipped_unchanged, is_failed)
    """
    filter_res = file_filter.evaluate(file)

    if not filter_res.should_index:
        rec = FileRecord(
            relative_path=file.relative_path,
            file_size=file.file_size,
            modified_time=file.modified_time,
            extension=Path(file.relative_path).suffix,
            file_type=LanguageDetector.detect_file_type(file.relative_path),
            indexing_status=IndexingStatus.IGNORED,
            exclusion_reason=filter_res.reason,
            extra_metadata={"batch_id": batch_id},
        )
        return (rec, False, True, False, False)

    # Check if unchanged from previous record
    if (
        prev_rec
        and prev_rec.indexing_status == IndexingStatus.INDEXED
        and prev_rec.modified_time == file.modified_time
        and prev_rec.file_size == file.file_size
        and "symbols" in prev_rec.extra_metadata
    ):
        updated_meta = prev_rec.extra_metadata.copy()
        updated_meta["batch_id"] = batch_id
        rec = FileRecord(
            relative_path=file.relative_path,
            file_size=file.file_size,
            modified_time=file.modified_time,
            extension=Path(file.relative_path).suffix,
            content_hash=prev_rec.content_hash,
            language=prev_rec.language,
            file_type=prev_rec.file_type or LanguageDetector.detect_file_type(file.relative_path),
            frameworks=prev_rec.frameworks,
            indexing_status=IndexingStatus.INDEXED,
            extra_metadata=updated_meta,
        )
        return (rec, True, False, True, False)

    # Process file with failure isolation
    extra_meta: dict[str, Any] = {"batch_id": batch_id}
    is_failed = False
    try:
        content_hash = FileHasher.hash_file(file.absolute_path, algorithm=config.hash_algorithm)
    except Exception as err:
        content_hash = ""
        extra_meta["hash_error"] = str(err)
        is_failed = True

    try:
        symbols = ASTParser.parse_file(file.absolute_path)
        extra_meta["symbols"] = [s.to_dict() for s in symbols]
        extra_meta["imports"] = [s.name for s in symbols if s.symbol_type == "import"]
    except Exception as err:
        extra_meta["symbols"] = []
        extra_meta["imports"] = []
        extra_meta["parse_error"] = str(err)
        is_failed = True

    language = LanguageDetector.detect_language(file.absolute_path)
    file_type = LanguageDetector.detect_file_type(file.absolute_path)

    rec = FileRecord(
        relative_path=file.relative_path,
        file_size=file.file_size,
        modified_time=file.modified_time,
        extension=Path(file.relative_path).suffix,
        content_hash=content_hash,
        language=language,
        file_type=file_type,
        indexing_status=IndexingStatus.INDEXED,
        extra_metadata=extra_meta,
    )
    return (rec, True, False, False, is_failed)


class IndexingService(BaseService):
    """Orchestrates the WIA repository indexing pipeline with parallel and incremental processing."""

    @classmethod
    def index_workspace(
        cls,
        target_path: str | Path | None = None,
        force_reindex: bool = False,
        batch_size: int = 50,
        max_workers: int | None = None,
    ) -> ServiceResult[dict]:
        """Execute complete or incremental workspace indexing operation in persistent batches."""
        start_time = time.perf_counter()
        path = Path(target_path).resolve() if target_path else Path.cwd().resolve()

        # 1. Validate workspace
        val_result = WorkspaceValidator.validate(path)
        if not val_result.is_valid:
            return ServiceResult.fail(
                val_result.error_message or f"Invalid workspace path: {path}"
            )

        try:
            # 2. Load configuration
            config = WorkspaceConfig.load_from_workspace(path)

            # 3. Load previous index (unless force_reindex is specified)
            previous_index = None if force_reindex else IndexRepository.load_index(path)
            previous_records = previous_index.files if previous_index else {}

            # 4. Discover candidate files
            discovered = FileDiscovery.discover_files(path)

            # 5. Initialize Gitignore processor & File filter
            gi_processor = GitignoreProcessor(path)
            file_filter = FileFilter(config, gitignore_processor=gi_processor)

            # 6. Partition discovered files into processing batches
            file_chunks = BatchPlanner.create_batches(discovered, batch_size=batch_size)
            discovered_rel_paths = {f.relative_path for f in discovered}

            if previous_index and not force_reindex:
                current_records: dict[str, FileRecord] = {
                    k: v for k, v in previous_records.items() if k in discovered_rel_paths
                }
            else:
                current_records = {}

            accumulated_batches: list[BatchRecord] = []
            total_discovered = len(discovered)
            total_skipped_unchanged = 0
            total_failed = 0

            # Determine concurrency
            workers = max_workers or min(8, (os.cpu_count() or 4))

            # Process file chunks in batches
            for idx, chunk in enumerate(file_chunks, start=1):
                batch_id = f"Batch {idx}"
                batch_start_t = time.perf_counter()
                b_started_at = datetime.now(timezone.utc).isoformat()
                b_file_paths = [file.relative_path for file in chunk]

                b_record = BatchRecord(
                    batch_id=batch_id,
                    status="RUNNING",
                    file_paths=b_file_paths,
                    discovered_count=len(chunk),
                    started_at=b_started_at,
                )
                accumulated_batches.append(b_record)

                b_indexed_cnt = 0
                b_ignored_cnt = 0

                try:
                    # Parallel worker pool execution for file processing
                    with ThreadPoolExecutor(max_workers=workers) as executor:
                        future_to_file = {
                            executor.submit(
                                _process_file_worker,
                                file,
                                file_filter,
                                config,
                                previous_records.get(file.relative_path),
                                batch_id,
                            ): file
                            for file in chunk
                        }

                        for future in as_completed(future_to_file):
                            rec, is_idx, is_ign, is_skip, is_fail = future.result()
                            current_records[rec.relative_path] = rec
                            if is_idx:
                                b_indexed_cnt += 1
                            if is_ign:
                                b_ignored_cnt += 1
                            if is_skip:
                                total_skipped_unchanged += 1
                            if is_fail:
                                total_failed += 1

                    # Mark batch completed
                    b_duration = round(time.perf_counter() - batch_start_t, 3)
                    b_record.status = "COMPLETED"
                    b_record.indexed_count = b_indexed_cnt
                    b_record.ignored_count = b_ignored_cnt
                    b_record.duration_seconds = b_duration
                    b_record.completed_at = datetime.now(timezone.utc).isoformat()

                    sample_files = ", ".join([f"`{Path(p).name}`" for p in b_file_paths[:4]]) + (
                        f" and {len(b_file_paths)-4} other files" if len(b_file_paths) > 4 else ""
                    )
                    b_record.narrative_summary = (
                        f"**{batch_id}** processed {len(b_file_paths)} files ({sample_files}) in {b_duration}s."
                    )

                except Exception as err:
                    b_duration = round(time.perf_counter() - batch_start_t, 3)
                    b_record.status = "FAILED"
                    b_record.error_message = str(err)
                    b_record.failure_stage = "File Processing"
                    b_record.duration_seconds = b_duration
                    b_record.completed_at = datetime.now(timezone.utc).isoformat()

                # Persist state after batch completion
                lang_counts: dict[str, int] = {}
                for rec in current_records.values():
                    if rec.indexing_status == IndexingStatus.INDEXED:
                        lang_counts[rec.language] = lang_counts.get(rec.language, 0) + 1

                detected_frameworks = FrameworkDetector.detect_frameworks(path)
                framework_names = [f.name for f in detected_frameworks]

                deps = ManifestParser.parse_workspace_manifests(path)
                dep_conflicts = ConflictDetector.detect_conflicts(deps)
                git_hotspots = GitAnalyzer.get_file_hotspots(path, top_n=10)
                security_findings = SecretScanner.scan_workspace(path)

                total_duration = round(time.perf_counter() - start_time, 3)
                tot_ignored = sum(
                    1 for r in current_records.values() if r.indexing_status == IndexingStatus.IGNORED
                )

                new_index = WorkspaceIndex(
                    workspace_path=str(path),
                    files=current_records,
                    languages=lang_counts,
                    frameworks=framework_names,
                    batches=accumulated_batches,
                    stats={
                        "total_discovered": total_discovered,
                        "total_indexed": len(current_records) - tot_ignored,
                        "total_ignored": tot_ignored,
                        "total_skipped_unchanged": total_skipped_unchanged,
                        "total_failed": total_failed,
                        "workers_used": workers,
                        "indexing_duration_seconds": total_duration,
                        "dependencies_count": len(deps),
                        "dependency_conflicts_count": len(dep_conflicts),
                        "git_hotspots_count": len(git_hotspots),
                        "security_findings_count": len(security_findings),
                    },
                )
                IndexRepository.save_index(path, new_index)
                try:
                    from wia.utils.report_generator import ReportGenerator

                    ReportGenerator.export_report_json(new_index)
                    if (path / "wia-report.html").exists():
                        ReportGenerator.generate_html_report(new_index)
                except Exception:
                    pass

            # Construct / refresh WorkspaceGraph
            graph_t0 = time.perf_counter()
            ws_graph = WorkspaceGraph()
            ws_graph.build_from_index(new_index)
            graph_duration = round(time.perf_counter() - graph_t0, 3)

            # Calculate change summary
            change_summary = ChangeDetector.detect_changes(
                previous_records=previous_records, current_records=current_records
            )

            tot_ignored = sum(
                1 for r in current_records.values() if r.indexing_status == IndexingStatus.IGNORED
            )
            duration = round(time.perf_counter() - start_time, 3)

            payload = {
                "workspace_path": str(path),
                "total_discovered": total_discovered,
                "total_indexed": len(current_records) - tot_ignored,
                "total_ignored": tot_ignored,
                "total_skipped_unchanged": total_skipped_unchanged,
                "total_failed": total_failed,
                "workers_used": workers,
                "changes": change_summary.counts,
                "languages": lang_counts if "lang_counts" in locals() else {},
                "frameworks": framework_names if "framework_names" in locals() else [],
                "dependencies_count": len(deps) if "deps" in locals() else 0,
                "dependency_conflicts_count": len(dep_conflicts) if "dep_conflicts" in locals() else 0,
                "git_hotspots_count": len(git_hotspots) if "git_hotspots" in locals() else 0,
                "security_findings_count": len(security_findings) if "security_findings" in locals() else 0,
                "graph_nodes_count": len(ws_graph.nodes),
                "graph_edges_count": len(ws_graph.edges),
                "graph_construction_duration_seconds": graph_duration,
                "duration_seconds": duration,
                "completed_batches": len([b for b in accumulated_batches if b.status == "COMPLETED"]),
                "total_batches": len(accumulated_batches),
            }

            return ServiceResult.ok(
                f"Indexed workspace '{path}' in {duration}s using {workers} workers across {len(accumulated_batches)} batches",
                data=payload,
            )

        except Exception as err:
            return ServiceResult.fail(f"Indexing pipeline failed: {err}", error=err)
