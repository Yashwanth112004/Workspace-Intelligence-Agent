"""Unit tests for AIProvider abstraction and reasoning engine."""

from pathlib import Path
from wia.core.index_model import WorkspaceIndex
from wia.core.metadata import FileRecord, IndexingStatus
from wia.llm.base import LocalReasoningProvider, MockLLMProvider, NvidiaNimProvider
from wia.llm.service import LLMService


def test_local_reasoning_provider():
    provider = LocalReasoningProvider()
    res = provider.generate("How is the WIA CLI structured?", "### File: `wia/cli/app.py`\n```\nimport click\n```")
    assert "wia/cli/app.py" in res
    assert "Evidence" in res


def test_nvidia_nim_provider_availability():
    provider = NvidiaNimProvider(api_key="")
    assert not provider.is_available()
    res = provider.generate("Explain project", "Context")
    assert "not configured" in res or "NVIDIA_API_KEY" in res


def test_llm_service_ask_intent_queries(tmp_path: Path):
    index = WorkspaceIndex(
        workspace_path=str(tmp_path),
        files={
            "wia/cli/app.py": FileRecord("wia/cli/app.py", 100, 1.0, ".py", language="Python", indexing_status=IndexingStatus.INDEXED),
            "wia/services/indexing_service.py": FileRecord("wia/services/indexing_service.py", 200, 1.0, ".py", language="Python", indexing_status=IndexingStatus.INDEXED),
        }
    )
    service = LLMService()

    # 1. Architecture intent query
    ans_arch = service.ask_question("How is the WIA CLI structured?", index)
    assert "wia/cli/app.py" in ans_arch or "Evidence" in ans_arch

    # 2. Workflow intent query
    ans_idx = service.ask_question("How does WIA index a repository?", index)
    assert "indexing_service.py" in ans_idx or "wia/cli/app.py" in ans_idx or "Evidence" in ans_idx

    # 3. Target file explanation
    explanation = service.explain_target("wia/cli/app.py", index)
    assert "WIA Code Explanation" in explanation
    assert "1. WHAT THIS CODE IS" in explanation

