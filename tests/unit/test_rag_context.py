"""Unit tests for RAGContextGenerator."""

from pathlib import Path
from wia.core.index_model import WorkspaceIndex
from wia.core.metadata import FileRecord, IndexingStatus
from wia.core.rag_context import RAGContextGenerator


def test_rag_context_generator(tmp_path: Path):
    index = WorkspaceIndex(
        workspace_path=str(tmp_path),
        files={
            "app.py": FileRecord(
                relative_path="app.py",
                file_size=100,
                modified_time=1.0,
                extension=".py",
                language="Python",
                indexing_status=IndexingStatus.INDEXED,
                extra_metadata={"symbols": [{"name": "run_server", "symbol_type": "function"}]},
            )
        },
        languages={"Python": 1},
        frameworks=["Flask"],
    )

    summary_md = RAGContextGenerator.generate_rag_context(index)
    assert "# Workspace Architecture & Intelligence Context" in summary_md
    assert "Flask" in summary_md
    assert "`app.py` (Python)" in summary_md
    assert "`run_server` (function)" in summary_md
