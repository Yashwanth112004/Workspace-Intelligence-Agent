"""Unit tests for LLM abstraction and reasoning service."""

from pathlib import Path
from wia.core.index_model import WorkspaceIndex
from wia.core.metadata import FileRecord, IndexingStatus
from wia.llm.base import MockLLMProvider
from wia.llm.service import LLMService


def test_mock_llm_provider():
    provider = MockLLMProvider()
    res = provider.generate_response("How is the WIA CLI structured?", "Context")
    assert "wia/cli/app.py" in res
    assert "Explanation of target entity" not in res


def test_llm_service_ask_intent_queries(tmp_path: Path):
    index = WorkspaceIndex(
        workspace_path=str(tmp_path),
        files={
            "wia/cli/app.py": FileRecord("wia/cli/app.py", 100, 1.0, ".py", language="Python", indexing_status=IndexingStatus.INDEXED)
        }
    )
    service = LLMService()

    # 1. Architecture intent query
    ans_arch = service.ask_question("How is the WIA CLI structured?", index)
    assert "wia/cli/app.py" in ans_arch
    assert "Explanation of target entity" not in ans_arch

    # 2. Workflow intent query
    ans_idx = service.ask_question("How does WIA index a repository?", index)
    assert "IndexingService" in ans_idx or "indexing_service.py" in ans_idx

    # 3. Component intent query
    ans_dep = service.ask_question("Which component handles dependency analysis?", index)
    assert "ManifestParser" in ans_dep

    # 4. Storage intent query
    ans_store = service.ask_question("Where is the workspace index stored?", index)
    assert ".wia/index.json" in ans_store or ".wia/workspace.db" in ans_store

    # 5. Target file explanation
    explanation = service.explain_target("wia/cli/app.py", index)
    assert "WIA Code Explanation" in explanation
    assert "1. WHAT THIS CODE IS" in explanation
