"""Unit tests for WorkspaceSearchEngine."""

from wia.core.index_model import WorkspaceIndex
from wia.core.metadata import FileRecord, IndexingStatus
from wia.core.search_engine import WorkspaceSearchEngine, SearchResult


def test_search_result_to_dict():
    res = SearchResult(
        file_path="wia/cli/app.py",
        language="Python",
        score=10.0,
        matched_symbols=["main (function)"],
        match_type="file_path",
    )
    data = res.to_dict()
    assert data["file_path"] == "wia/cli/app.py"
    assert data["score"] == 10.0


def test_search_file_path_and_symbol():
    index = WorkspaceIndex(
        workspace_path="/app",
        files={
            "wia/cli/app.py": FileRecord(
                relative_path="wia/cli/app.py",
                file_size=100,
                modified_time=1.0,
                extension=".py",
                language="Python",
                indexing_status=IndexingStatus.INDEXED,
                extra_metadata={
                    "symbols": [
                        {"name": "main", "symbol_type": "function"},
                        {"name": "AppConfig", "symbol_type": "class"},
                    ]
                },
            ),
            "wia/utils/logger.py": FileRecord(
                relative_path="wia/utils/logger.py",
                file_size=100,
                modified_time=1.0,
                extension=".py",
                language="Python",
                indexing_status=IndexingStatus.INDEXED,
                extra_metadata={"symbols": [{"name": "setup_logger", "symbol_type": "function"}]},
            ),
        },
    )

    # Search by symbol name
    results = WorkspaceSearchEngine.search(index, query="AppConfig")
    assert len(results) == 1
    assert results[0].file_path == "wia/cli/app.py"

    # Search by path
    results_path = WorkspaceSearchEngine.search(index, query="logger")
    assert len(results_path) == 1
    assert results_path[0].file_path == "wia/utils/logger.py"
