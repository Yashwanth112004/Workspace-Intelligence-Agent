"""Unit tests for BatchPlanner."""

from pathlib import Path
from wia.core.batch_planner import BatchPlanner, BatchConfig


def test_batch_planner():
    files = [Path(f"file_{i}.py") for i in range(105)]
    batches = BatchPlanner.create_batches(files, batch_size=50)

    assert len(batches) == 3
    assert len(batches[0]) == 50
    assert len(batches[1]) == 50
    assert len(batches[2]) == 5
