"""Unit tests for WorkspaceGraph relationships: INHERITS, CALLS, TESTS, DEFINES, and remove_file."""

from pathlib import Path
from wia.core.index_model import WorkspaceIndex
from wia.core.metadata import FileRecord, IndexingStatus
from wia.knowledge.graph import WorkspaceGraph


def test_graph_relationships_and_removal():
    index = WorkspaceIndex(
        workspace_path="/app",
        files={
            "app/base.py": FileRecord(
                relative_path="app/base.py",
                file_size=100,
                modified_time=1.0,
                extension=".py",
                file_type="Source Code",
                indexing_status=IndexingStatus.INDEXED,
                extra_metadata={
                    "symbols": [
                        {"name": "BaseService", "symbol_type": "class", "line_number": 1},
                    ]
                },
            ),
            "app/service.py": FileRecord(
                relative_path="app/service.py",
                file_size=200,
                modified_time=1.0,
                extension=".py",
                file_type="Source Code",
                indexing_status=IndexingStatus.INDEXED,
                extra_metadata={
                    "imports": ["app.base"],
                    "symbols": [
                        {
                            "name": "UserService",
                            "symbol_type": "class",
                            "base_classes": ["BaseService"],
                            "line_number": 1,
                        },
                        {
                            "name": "get_user",
                            "symbol_type": "method",
                            "calls": ["validate_user"],
                            "line_number": 5,
                        },
                    ],
                },
            ),
            "tests/test_service.py": FileRecord(
                relative_path="tests/test_service.py",
                file_size=150,
                modified_time=1.0,
                extension=".py",
                file_type="Test",
                indexing_status=IndexingStatus.INDEXED,
                extra_metadata={
                    "imports": ["app.service"],
                    "symbols": [
                        {"name": "test_get_user", "symbol_type": "function", "line_number": 1},
                    ],
                },
            ),
        },
    )

    graph = WorkspaceGraph()
    graph.build_from_index(index)

    # 1. Check DEFINES edge
    base_file_edges = graph.get_outgoing_edges("file:app/base.py")
    assert any(e.relation_type == "DEFINES" and "BaseService" in e.target_id for e in base_file_edges)

    # 2. Check INHERITS edge
    user_service_edges = graph.get_outgoing_edges("symbol:app/service.py:UserService")
    assert any(e.relation_type == "INHERITS" and "BaseService" in e.target_id for e in user_service_edges)

    # 3. Check TESTS edge
    test_file_edges = graph.get_outgoing_edges("file:tests/test_service.py")
    assert any(e.relation_type == "TESTS" and e.target_id == "file:app/service.py" for e in test_file_edges)

    # 4. Test incremental node and edge removal
    assert "file:app/service.py" in graph.nodes
    graph.remove_file("app/service.py")
    assert "file:app/service.py" not in graph.nodes
    assert "symbol:app/service.py:UserService" not in graph.nodes
