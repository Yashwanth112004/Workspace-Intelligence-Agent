import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
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
from wia.core.index_model import WorkspaceIndex, BatchRecord
from wia.core.language import LanguageDetector
from wia.core.metadata import FileRecord, IndexingStatus
from wia.core.validator import WorkspaceValidator
from wia.services.base import BaseService, ServiceResult
from wia.services.explanation_service import ExplanationService
from wia.storage.repository import IndexRepository


def _process_single_file(
    file: DiscoveredFile,
    file_filter: FileFilter,
    previous_records: dict[str, FileRecord],
    hash_algorithm: str,
    batch_id: str,
) -> tuple[str, FileRecord, bool]:
    """Process a single candidate file: filter, hash, parse AST, and detect language."""
    filter_res = file_filter.evaluate(file)
    if not filter_res.should_index:
        rec = FileRecord(
            relative_path=file.relative_path,
            file_size=file.file_size,
            modified_time=file.modified_time,
            extension=Path(file.relative_path).suffix,
            indexing_status=IndexingStatus.IGNORED,
            exclusion_reason=filter_res.reason,
            extra_metadata={"batch_id": batch_id},
        )
        return file.relative_path, rec, False

    prev_rec = previous_records.get(file.relative_path) if previous_records else None
    extra_meta = prev_rec.extra_metadata.copy() if prev_rec else {}
    extra_meta["batch_id"] = batch_id

    if (
        prev_rec
        and prev_rec.indexing_status == IndexingStatus.INDEXED
        and prev_rec.modified_time == file.modified_time
        and prev_rec.file_size == file.file_size
        and "symbols" in prev_rec.extra_metadata
    ):
        content_hash = prev_rec.content_hash
    else:
        content_hash = FileHasher.hash_file(
            file.absolute_path, algorithm=hash_algorithm
        )
        symbols = ASTParser.parse_file(file.absolute_path)
        extra_meta["symbols"] = [s.to_dict() for s in symbols]
        extra_meta["imports"] = [
            s.name for s in symbols if s.symbol_type == "import"
        ]

    language = LanguageDetector.detect_language(file.absolute_path)

    rec = FileRecord(
        relative_path=file.relative_path,
        file_size=file.file_size,
        modified_time=file.modified_time,
        extension=Path(file.relative_path).suffix,
        content_hash=content_hash,
        language=language,
        indexing_status=IndexingStatus.INDEXED,
        extra_metadata=extra_meta,
    )
    return file.relative_path, rec, True


class IndexingService(BaseService):
    """Orchestrates the WIA repository indexing pipeline with high-throughput parallel processing."""

    @classmethod
    def index_workspace(
        cls,
        target_path: str | Path | None = None,
        force_reindex: bool = False,
        batch_size: int = 50,
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
            previous_index = (
                None if force_reindex else IndexRepository.load_index(path)
            )
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
            ignored_count = 0
            max_workers = min(32, (os.cpu_count() or 4) * 4)

            # Process file chunks in batches with multi-threading
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
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        futures = [
                            executor.submit(
                                _process_single_file,
                                file,
                                file_filter,
                                previous_records,
                                config.hash_algorithm,
                                batch_id,
                            )
                            for file in chunk
                        ]
                        for fut in futures:
                            rel_p, rec, is_indexed = fut.result()
                            current_records[rel_p] = rec
                            if is_indexed:
                                b_indexed_cnt += 1
                            else:
                                b_ignored_cnt += 1
                                ignored_count += 1

                    # Synthesize batch narrative explanation
                    b_roles: set[str] = set()
                    b_sym_cnt = 0
                    for fp in b_file_paths:
                        rec = current_records.get(fp)
                        if rec and rec.indexing_status == IndexingStatus.INDEXED:
                            role_str = ExplanationService.infer_architectural_role(
                                fp, rec.extra_metadata.get("symbols", []), rec.extra_metadata.get("imports", [])
                            )
                            b_roles.add(role_str.split(" — ")[0])
                            b_sym_cnt += len(rec.extra_metadata.get("symbols", []))

                    roles_label = ", ".join(sorted(b_roles)) if b_roles else "Core Components"
                    sample_files = ", ".join([f"`{Path(p).name}`" for p in b_file_paths[:4]]) + (f" and {len(b_file_paths)-4} other files" if len(b_file_paths) > 4 else "")
                    b_narrative = (
                        f"**{batch_id}** evaluated {len(b_file_paths)} repository components including {sample_files}. "
                        f"This batch analyzed architectural roles spanning {roles_label}, discovering {b_sym_cnt} AST symbols and mapping component interactions."
                    )

                    # Mark batch completed
                    b_duration = round(time.perf_counter() - batch_start_t, 3)
                    b_record.status = "COMPLETED"
                    b_record.indexed_count = b_indexed_cnt
                    b_record.ignored_count = b_ignored_cnt
                    b_record.duration_seconds = b_duration
                    b_record.completed_at = datetime.now(timezone.utc).isoformat()
                    b_record.narrative_summary = b_narrative

                except Exception as err:
                    b_duration = round(time.perf_counter() - batch_start_t, 3)
                    b_record.status = "FAILED"
                    b_record.error_message = str(err)
                    b_record.failure_stage = "File Processing"
                    b_record.duration_seconds = b_duration
                    b_record.completed_at = datetime.now(timezone.utc).isoformat()

            # 7. Run workspace-wide analyzers ONCE concurrently
            lang_counts: dict[str, int] = {}
            for rec in current_records.values():
                if rec.indexing_status == IndexingStatus.INDEXED:
                    lang_counts[rec.language] = lang_counts.get(rec.language, 0) + 1

            indexed_file_paths = [
                path / fp for fp, r in current_records.items() if r.indexing_status == IndexingStatus.INDEXED
            ]

            with ThreadPoolExecutor(max_workers=4) as analyzer_pool:
                fut_frameworks = analyzer_pool.submit(FrameworkDetector.detect_frameworks, path)
                fut_deps = analyzer_pool.submit(ManifestParser.parse_workspace_manifests, path)
                fut_git = analyzer_pool.submit(GitAnalyzer.get_file_hotspots, path, 10)
                fut_sec = analyzer_pool.submit(SecretScanner.scan_workspace, path, 2 * 1024 * 1024, indexed_file_paths)

                detected_frameworks = fut_frameworks.result()
                deps = fut_deps.result()
                git_hotspots = fut_git.result()
                security_findings = fut_sec.result()

            framework_names = [f.name for f in detected_frameworks]
            dep_conflicts = ConflictDetector.detect_conflicts(deps)

            total_duration = round(time.perf_counter() - start_time, 3)
            tot_ignored = sum(1 for r in current_records.values() if r.indexing_status == IndexingStatus.IGNORED)

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

            # Calculate change summary
            change_summary = ChangeDetector.detect_changes(
                previous_records=previous_records, current_records=current_records
            )

            duration = round(time.perf_counter() - start_time, 3)

            payload = {
                "workspace_path": str(path),
                "total_discovered": total_discovered,
                "total_indexed": len(current_records) - tot_ignored,
                "total_ignored": tot_ignored,
                "changes": change_summary.counts,
                "languages": lang_counts,
                "frameworks": framework_names,
                "dependencies_count": len(deps),
                "dependency_conflicts_count": len(dep_conflicts),
                "git_hotspots_count": len(git_hotspots),
                "security_findings_count": len(security_findings),
                "duration_seconds": duration,
                "completed_batches": len([b for b in accumulated_batches if b.status == "COMPLETED"]),
                "total_batches": len(accumulated_batches),
            }

            return ServiceResult.ok(
                f"Indexed workspace '{path}' in {duration}s across {len(accumulated_batches)} batches", data=payload
            )

        except Exception as err:
            return ServiceResult.fail(
                f"Indexing pipeline failed: {err}", error=err
            )
