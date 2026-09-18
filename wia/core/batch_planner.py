"""Batch planner for chunking and parallelizing file processing workloads."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class BatchConfig:
    """Configuration options for workload batching."""

    batch_size: int = 50
    max_workers: int = 4


from datetime import datetime, timezone
from wia.core.index_model import BatchRecord


class BatchPlanner:
    """Partitions file lists into balanced processing batches."""

    @classmethod
    def create_batches(cls, files: list[Path], batch_size: int = 50) -> list[list[Path]]:
        """Partition list of file paths into chunks of specified batch size."""
        if batch_size <= 0:
            batch_size = 50
        return [files[i : i + batch_size] for i in range(0, len(files), batch_size)]

    @classmethod
    def plan_batch_records(
        cls, file_batches: list[list[Path]], start_batch_num: int = 1
    ) -> list[BatchRecord]:
        """Generate initialized BatchRecord objects for partitioned file batches."""
        records: list[BatchRecord] = []
        now_str = datetime.now(timezone.utc).isoformat()
        for idx, b_files in enumerate(file_batches, start=start_batch_num):
            rel_paths = [str(f) for f in b_files]
            records.append(
                BatchRecord(
                    batch_id=f"Batch {idx}",
                    status="PENDING",
                    file_paths=rel_paths,
                    discovered_count=len(b_files),
                    indexed_count=0,
                    ignored_count=0,
                    duration_seconds=0.0,
                    started_at=now_str,
                )
            )
        return records
