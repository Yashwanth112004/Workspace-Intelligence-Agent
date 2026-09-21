"""LLM reasoning service connecting retrieval context to providers."""

import os
from pathlib import Path
from typing import Optional
from wia.core.index_model import WorkspaceIndex
from wia.llm.base import (
    AIProvider,
    AIProviderFactory,
    LLMProvider,
    LocalReasoningProvider,
    MockLLMProvider,
    NvidiaNimProvider,
    OpenAIProvider,
    GeminiProvider,
    AnthropicProvider,
    _get_stored_user_config,
)
from wia.llm.reasoning import ReasoningEngine


def _load_env_file():
    """Lightweight loader for .env file in workspace root."""
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass


class LLMService:
    """Orchestrates workspace context retrieval and AI provider queries."""

    def __init__(
        self,
        provider: AIProvider | None = None,
        api_key: Optional[str] = None,
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
        offline: bool = False,
    ):
        if provider:
            self.provider = provider
        elif offline:
            self.provider = LocalReasoningProvider()
        else:
            self.provider = self.create_provider(
                api_key=api_key,
                provider_name=provider_name,
                model=model,
            )

    @classmethod
    def create_provider(
        cls,
        api_key: Optional[str] = None,
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> AIProvider:
        """Construct best available AI provider based on keys and configuration."""
        _load_env_file()
        cfg = _get_stored_user_config()

        p_name = (
            provider_name
            or cfg.get("ai_provider")
            or os.getenv("WIA_AI_PROVIDER")
            or os.getenv("WIA_LLM_PROVIDER")
            or ""
        ).lower().strip()

        # 1. NVIDIA NIM (Default primary)
        nim_key = (
            api_key
            if (p_name in ("nvidia", "nim") and api_key)
            else (api_key or cfg.get("ai_api_key") or os.getenv("NVIDIA_NIM_API_KEY") or os.getenv("NVIDIA_API_KEY"))
        )
        if (p_name in ("nvidia", "nim") or not p_name) and nim_key:
            return NvidiaNimProvider(
                api_key=nim_key,
                endpoint=base_url or cfg.get("ai_endpoint") or os.getenv("NVIDIA_NIM_ENDPOINT") or os.getenv("NVIDIA_ENDPOINT"),
                model=model or cfg.get("ai_model") or os.getenv("NVIDIA_NIM_MODEL") or os.getenv("NVIDIA_MODEL") or "meta/llama-3.3-70b-instruct",
            )

        # 2. OpenAI / Groq / OpenRouter / Ollama / Custom
        openai_key = (
            api_key
            if (p_name in ("openai", "groq", "openrouter", "ollama", "custom") and api_key)
            else (api_key or cfg.get("ai_api_key") or os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY") or os.getenv("OPENROUTER_API_KEY"))
        )
        if (p_name in ("openai", "groq", "openrouter", "ollama", "custom") or (not p_name and openai_key)):
            return OpenAIProvider(
                api_key=openai_key,
                base_url=base_url or cfg.get("ai_endpoint") or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
                model=model or cfg.get("ai_model") or os.getenv("OPENAI_MODEL") or "gpt-4o",
            )

        # 3. Google Gemini
        gemini_key = (
            api_key
            if (p_name == "gemini" and api_key)
            else (api_key or cfg.get("ai_api_key") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
        )
        if (p_name == "gemini" or not p_name) and gemini_key:
            return GeminiProvider(
                api_key=gemini_key,
                model=model or cfg.get("ai_model") or os.getenv("GEMINI_MODEL") or "gemini-1.5-flash",
            )

        # 4. Anthropic
        anthropic_key = (
            api_key
            if (p_name == "anthropic" and api_key)
            else (api_key or cfg.get("ai_api_key") or os.getenv("ANTHROPIC_API_KEY"))
        )
        if (p_name == "anthropic" or not p_name) and anthropic_key:
            return AnthropicProvider(
                api_key=anthropic_key,
                model=model or cfg.get("ai_model") or os.getenv("ANTHROPIC_MODEL") or "claude-3-5-sonnet-20241022",
            )

        # Fallback via Factory / Local Reasoning
        return AIProviderFactory.get_provider(provider_name=p_name or provider_name)

    def ask_question(self, question: str, index: WorkspaceIndex) -> str:
        """Answer a question about the workspace using grounded context and reasoning."""
        engine = ReasoningEngine(index, provider=self.provider)
        return engine.ask(question)

    def explain_target(self, target_path_or_symbol: str, index: WorkspaceIndex) -> str:
        """Explain a specific file or symbol using ExplanationService grounding."""
        from wia.services.explanation_service import ExplanationService
        return ExplanationService.explain_target(target_path_or_symbol, index)
