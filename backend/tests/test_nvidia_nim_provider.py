import pytest
from unittest.mock import patch, MagicMock
from app.providers.nvidia_nim import NvidiaNIMProvider
from app.core.llm import LLMClient
from app.core.config import settings

def test_nvidia_nim_provider_availability():
    with patch.object(settings, "NVIDIA_NIM_API_KEY", "nvapi-test-key"):
        provider = NvidiaNIMProvider()
        assert provider.is_available() is True
        assert provider.api_key == "nvapi-test-key"

    with patch.object(settings, "NVIDIA_NIM_API_KEY", None), patch.object(settings, "NVIDIA_API_KEY", None):
        provider_none = NvidiaNIMProvider(api_key=None)
        assert provider_none.is_available() is False

def test_nvidia_nim_provider_generation_success():
    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "NVIDIA NIM response: Ingested authentication pipeline verified."
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        provider = NvidiaNIMProvider(
            api_key="nvapi-mock-token-123",
            base_url="https://integrate.api.nvidia.com/v1",
            model="meta/llama-3.1-70b-instruct"
        )
        res = provider.generate(prompt="Explain login flow", system_prompt="You are WIA.")
        assert "Ingested authentication pipeline verified" in res
        mock_client.chat.completions.create.assert_called_once()

def test_nvidia_nim_provider_unconfigured_error():
    provider = NvidiaNIMProvider(api_key="")
    with pytest.raises(RuntimeError) as exc_info:
        provider.generate(prompt="Explain flow")
    assert "NVIDIA NIM is not configured" in str(exc_info.value)

def test_llm_client_fallback_when_nim_unavailable():
    with patch.object(settings, "NVIDIA_NIM_API_KEY", None), patch.object(settings, "NVIDIA_API_KEY", None):
        res = LLMClient.generate_completion("Summarize file auth_service.py", allow_deterministic_fallback=True)
        assert isinstance(res, str)
        assert len(res) > 10
