"""Unit tests for AIProvider abstraction, NvidiaNimProvider, and LocalReasoningProvider."""

import os
from unittest.mock import MagicMock, patch
from wia.llm.base import (
    AIProvider,
    AIProviderFactory,
    LocalReasoningProvider,
    NvidiaNimProvider,
    OpenAIProvider,
)


def test_ai_provider_base_interface():
    class CustomProvider(AIProvider):
        def generate(self, prompt: str, context: str, options=None) -> str:
            return f"Answer for: {prompt}"

    provider = CustomProvider()
    assert provider.is_available()
    assert provider.generate("hello", "context") == "Answer for: {prompt}".format(prompt="hello")
    # Test backward compatibility alias
    assert provider.generate_response("test", "ctx") == "Answer for: test"


def test_nvidia_nim_provider_unconfigured():
    provider = NvidiaNimProvider(api_key="")
    assert not provider.is_available()
    res = provider.generate("test prompt", "context")
    assert "not configured" in res
    assert "NVIDIA_API_KEY" in res


def test_nvidia_nim_provider_successful_mock():
    provider = NvidiaNimProvider(api_key="nvapi-mock-key-12345", model="meta/llama-3.1-70b-instruct")
    assert provider.is_available()

    mock_resp_data = b'{"choices": [{"message": {"content": "Grounded answer from NVIDIA NIM"}}]}'
    mock_resp = MagicMock()
    mock_resp.read.return_value = mock_resp_data
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        ans = provider.generate("How does indexing work?", "Context about indexing")
        assert ans == "Grounded answer from NVIDIA NIM"


def test_local_reasoning_provider():
    provider = LocalReasoningProvider()
    res = provider.generate(
        "Explain the project",
        "### File: `wia/core/retrieval.py`\n```\nclass WorkspaceRetriever:\n    pass\n```\n- **FastAPI** (Frameworks): in `pyproject.toml`",
    )
    assert "Project Overview" in res
    assert "Technology Stack" in res
    assert "Evidence" in res


def test_ai_provider_factory():
    # 1. Local fallback
    with patch.dict(os.environ, {}, clear=True):
        p = AIProviderFactory.get_provider()
        assert isinstance(p, LocalReasoningProvider)

    # 2. Nvidia via explicit name
    p_nvidia = AIProviderFactory.get_provider("nvidia")
    assert isinstance(p_nvidia, NvidiaNimProvider)

    # 3. Nvidia via env var
    with patch.dict(os.environ, {"NVIDIA_API_KEY": "nvapi-test"}):
        p_env = AIProviderFactory.get_provider()
        assert isinstance(p_env, NvidiaNimProvider)
