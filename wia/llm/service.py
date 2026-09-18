"""LLM reasoning service connecting retrieval context to providers."""

from wia.core.index_model import WorkspaceIndex
from wia.llm.base import AIProvider, AIProviderFactory
from wia.llm.reasoning import ReasoningEngine


class LLMService:
    """Orchestrates workspace context retrieval and AI provider queries."""

    def __init__(self, provider: AIProvider | None = None):
        self.provider = provider or AIProviderFactory.get_provider()

    def ask_question(self, question: str, index: WorkspaceIndex) -> str:
        """Answer a question about the workspace using grounded context and reasoning."""
        engine = ReasoningEngine(index, provider=self.provider)
        return engine.ask(question)

    def explain_target(self, target_path_or_symbol: str, index: WorkspaceIndex) -> str:
        """Explain a specific file or symbol using ExplanationService grounding."""
        from wia.services.explanation_service import ExplanationService
        return ExplanationService.explain_target(target_path_or_symbol, index)

