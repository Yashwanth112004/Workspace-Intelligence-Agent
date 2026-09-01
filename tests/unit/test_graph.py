"""Unit tests for WorkspaceGraph."""

from wia.core.index_model import WorkspaceIndex
from wia.core.metadata import FileRecord, IndexingStatus
from wia.knowledge.graph import WorkspaceGraph


def test_workspace_graph_build_and_query():
    index = WorkspaceIndex(
        workspace_path="/app",
        files={
            "service.py": FileRecord(
                relative_path="service.py",
                file_size=100,
                modified_time=1.0,
                extension=".py",
                language="Python",
                indexing_status=IndexingStatus.INDEXED,
                extra_metadata={
                    "symbols": [
                        {"name": "UserService", "symbol_type": "class"},
                        {"name": "os", "symbol_type": "import"},
                    ]
                },
            )
        },
    )

    graph = WorkspaceGraph()
    graph.build_from_index(index)

    assert "file:service.py" in graph.nodes
    assert "symbol:service.py:UserService" in graph.nodes
    assert "external:os" in graph.nodes

    outgoing = graph.get_outgoing_edges("file:service.py")
    assert len(outgoing) == 2
    rel_types = {e.relation_type for e in outgoing}
    assert "DEFINES" in rel_types
    assert "IMPORTS" in rel_types
