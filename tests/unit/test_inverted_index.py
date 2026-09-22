"""Unit tests for WorkspaceInvertedIndex and accelerated search."""

from wia.core.index_model import WorkspaceIndex
from wia.core.inverted_index import WorkspaceInvertedIndex
from wia.core.metadata import FileRecord, IndexingStatus
from wia.core.search_engine import WorkspaceSearchEngine


def _create_sample_index() -> WorkspaceIndex:
    files = {
        "wia/core/retrieval.py": FileRecord(
            relative_path="wia/core/retrieval.py",
            file_size=1024,
            modified_time=1700000000.0,
            extension=".py",
            language="Python",
            file_type="Source Code",
            indexing_status=IndexingStatus.INDEXED,
            extra_metadata={
                "symbols": [
                    {"name": "WorkspaceRetriever", "symbol_type": "class", "line_number": 120, "docstring": "Multi-strategy context retriever."},
                    {"name": "IntentClassifier", "symbol_type": "class", "line_number": 63, "docstring": "Classify user query into canonical intent."},
                ]
            },
        ),
        "wia/core/search_engine.py": FileRecord(
            relative_path="wia/core/search_engine.py",
            file_size=2048,
            modified_time=1700000000.0,
            extension=".py",
            language="Python",
            file_type="Source Code",
            indexing_status=IndexingStatus.INDEXED,
            extra_metadata={
                "symbols": [
                    {"name": "WorkspaceSearchEngine", "symbol_type": "class", "line_number": 30, "docstring": "Multi-evidence search engine across filenames and symbols."},
                    {"name": "SearchResult", "symbol_type": "class", "line_number": 13, "docstring": "Represents an evidence-grounded search result."},
                ]
            },
        ),
        "frontend/src/App.tsx": FileRecord(
            relative_path="frontend/src/App.tsx",
            file_size=512,
            modified_time=1700000000.0,
            extension=".tsx",
            language="TypeScript",
            file_type="Source Code",
            indexing_status=IndexingStatus.INDEXED,
            extra_metadata={
                "symbols": [
                    {"name": "App", "symbol_type": "function", "line_number": 10, "docstring": "Main dashboard application UI component."},
                ]
            },
        ),
    }
    return WorkspaceIndex(workspace_path="/test", files=files)


def test_inverted_index_building():
    index = _create_sample_index()
    inv = WorkspaceInvertedIndex.build_from_index(index)

    assert "workspaceretriever" in inv.exact_symbols
    assert "app" in inv.exact_symbols
    assert "search_engine" in inv.stem_to_files
    assert "python" in inv.language_to_files
    assert "typescript" in inv.language_to_files
    assert len(inv.language_to_files["python"]) == 2


def test_inverted_index_candidate_search():
    index = _create_sample_index()
    inv = WorkspaceInvertedIndex.build_from_index(index)

    # 1. Exact symbol query
    cands = inv.find_candidate_files("WorkspaceRetriever")
    assert "wia/core/retrieval.py" in cands

    # 2. Stem match
    cands = inv.find_candidate_files("search_engine")
    assert "wia/core/search_engine.py" in cands

    # 3. Substring / Token match
    cands = inv.find_candidate_files("retriever")
    assert "wia/core/retrieval.py" in cands

    # 4. Language filter
    cands_ts = inv.find_candidate_files("", language_filter="TypeScript")
    assert "frontend/src/App.tsx" in cands_ts
    assert "wia/core/retrieval.py" not in cands_ts


def test_search_engine_with_inverted_index():
    index = _create_sample_index()
    results = WorkspaceSearchEngine.search(index, "WorkspaceRetriever")
    assert len(results) >= 1
    assert results[0].file_path == "wia/core/retrieval.py"
    assert results[0].match_type == "exact_symbol"
    assert results[0].score >= 20.0
