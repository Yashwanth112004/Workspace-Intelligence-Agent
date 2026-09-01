"""Unit tests for ExplanationService deep file and symbol explanations."""

from pathlib import Path
from wia.core.index_model import WorkspaceIndex
from wia.core.metadata import FileRecord, IndexingStatus
from wia.knowledge.graph import WorkspaceGraph
from wia.services.explanation_service import ExplanationService


def test_explanation_service_file_explanation():
    index = WorkspaceIndex(
        workspace_path="/app",
        files={
            "wia/constants.py": FileRecord(
                relative_path="wia/constants.py",
                file_size=412,
                modified_time=1.0,
                extension=".py",
                language="Python",
                indexing_status=IndexingStatus.INDEXED,
                extra_metadata={"symbols": [{"name": "pathlib.Path", "symbol_type": "import"}]},
            ),
            "wia/cli/app.py": FileRecord(
                relative_path="wia/cli/app.py",
                file_size=3000,
                modified_time=1.0,
                extension=".py",
                language="Python",
                indexing_status=IndexingStatus.INDEXED,
                extra_metadata={
                    "symbols": [
                        {"name": "wia.constants", "symbol_type": "import"},
                        {"name": "main", "symbol_type": "function", "parameters": ["ctx", "verbose"]},
                    ]
                },
            ),
        },
    )

    graph = WorkspaceGraph()
    graph.build_from_index(index)

    explanation = ExplanationService.explain_target("constants.py", index, graph)

    assert "WIA Code Explanation" in explanation
    assert "1. WHAT THIS CODE IS" in explanation
    assert "2. WHAT THIS CODE DOES" in explanation
    assert "3. HOW IT WORKS" in explanation
    assert "4. WHY IT EXISTS" in explanation
    assert "5. ROLE IN THE PROJECT" in explanation
    assert "6. HOW IT CONNECTS TO THE CODEBASE" in explanation
    assert "7. SYMBOL / FUNCTION EXPLANATIONS" in explanation
    assert "8. DEPENDENCIES" in explanation
    assert "9. USED BY" in explanation
    assert "10. RELATED TESTS" in explanation
    assert "11. CHANGE IMPACT" in explanation
    assert "12. DEVELOPER TAKEAWAY" in explanation
    assert "13. EVIDENCE" in explanation
    assert "wia/cli/app.py" in explanation


def test_explanation_service_symbol_explanation():
    index = WorkspaceIndex(
        workspace_path="/app",
        files={
            "wia/llm/service.py": FileRecord(
                relative_path="wia/llm/service.py",
                file_size=1500,
                modified_time=1.0,
                extension=".py",
                language="Python",
                indexing_status=IndexingStatus.INDEXED,
                extra_metadata={
                    "symbols": [
                        {"name": "LLMService", "symbol_type": "class", "line_number": 8, "docstring": "Orchestrates RAG context queries."}
                    ]
                },
            )
        },
    )

    graph = WorkspaceGraph()
    graph.build_from_index(index)

    explanation = ExplanationService.explain_target("LLMService", index, graph)

    assert "WIA Symbol Explanation" in explanation
    assert "1. WHAT THIS SYMBOL IS & TYPE" in explanation
    assert "2. WHAT IT DOES & HOW IT WORKS" in explanation
    assert "3. WHY IT EXISTS" in explanation
    assert "4. DEPENDENCIES & CALLS" in explanation
    assert "5. CALLED BY / USED BY" in explanation
    assert "6. RELATED TESTS" in explanation
    assert "7. POTENTIAL IMPACT" in explanation
    assert "8. DEVELOPER TAKEAWAY" in explanation
    assert "9. EVIDENCE" in explanation
    assert "Orchestrates RAG context queries" in explanation


def test_explanation_service_target_not_found():
    index = WorkspaceIndex(workspace_path="/app")
    explanation = ExplanationService.explain_target("NonExistentModule.py", index)
    assert "WIA could not determine target 'NonExistentModule.py' reliably from the indexed workspace" in explanation


def test_explanation_service_quality_and_facts():
    source_code = """
def format_bytes(num_bytes: int) -> str:
    if num_bytes < 0:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(num_bytes) < 1024.0:
            if unit == "B":
                return f"{int(num_bytes)} B"
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"
"""
    desc = ExplanationService._describe_symbol_implementation("format_bytes", "function", ["num_bytes"], "", "wia/cli/formatting.py", source_code)

    assert "Converts raw byte counts into human-readable size strings" in desc
    assert "1024.0" in desc
    assert "'0 B'" in desc
    assert "abs()" in desc
    assert "inspects AST nodes" not in desc
    assert "Evaluates core function logic" not in desc
