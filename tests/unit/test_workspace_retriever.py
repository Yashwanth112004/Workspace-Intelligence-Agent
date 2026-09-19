"""Unit tests for WorkspaceRetriever, IntentClassifier, and Context Budgeting."""

from pathlib import Path
from wia.core.index_model import WorkspaceIndex
from wia.core.metadata import FileRecord, IndexingStatus
from wia.core.retrieval import IntentClassifier, WorkspaceRetriever
from wia.knowledge.graph import WorkspaceGraph


def test_intent_classification():
    assert IntentClassifier.classify("Explain the project") == "GENERAL_PROJECT"
    assert IntentClassifier.classify("How is the architecture designed?") == "ARCHITECTURE"
    assert IntentClassifier.classify("How does application execution work?") == "FLOW"
    assert IntentClassifier.classify("What depends on Application?") == "DEPENDENCY"
    assert IntentClassifier.classify("What is the impact of changing database.py?") == "IMPACT"
    assert IntentClassifier.classify("Where are unit tests located?") == "TESTING"
    assert IntentClassifier.classify("How to configure environment variables?") == "CONFIGURATION"


def test_workspace_retriever_context_budgeting(tmp_path: Path):
    (tmp_path / "core.py").write_text(
        "class Application:\n    '''Main application orchestrator.'''\n    def run(self):\n        return True\n",
        encoding="utf-8",
    )

    index = WorkspaceIndex(
        workspace_path=str(tmp_path),
        files={
            "core.py": FileRecord(
                relative_path="core.py",
                file_size=100,
                modified_time=1.0,
                extension=".py",
                language="Python",
                file_type="Source Code",
                indexing_status=IndexingStatus.INDEXED,
                extra_metadata={
                    "symbols": [
                        {"name": "Application", "symbol_type": "class", "line_number": 1, "end_line_number": 4},
                        {"name": "run", "symbol_type": "method", "line_number": 3, "end_line_number": 4},
                    ]
                },
            )
        },
    )

    graph = WorkspaceGraph()
    graph.build_from_index(index)

    retriever = WorkspaceRetriever(index, graph=graph)
    result = retriever.retrieve("How does Application run?", max_files=5, token_budget=4000)

    assert result.intent == "FLOW"
    assert "core.py" in result.target_files
    assert len(result.evidence_items) > 0
    assert "Application" in result.assembled_context
    assert result.token_estimate > 0
