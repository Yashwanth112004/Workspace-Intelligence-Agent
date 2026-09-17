"""LLM reasoning service connecting retrieval context to providers."""

from wia.core.index_model import WorkspaceIndex
from wia.core.rag_context import RAGContextGenerator
from wia.llm.base import LLMProvider, MockLLMProvider


class LLMService:
    """Orchestrates RAG context assembly and LLM provider queries."""

    def __init__(self, provider: LLMProvider | None = None):
        self.provider = provider or MockLLMProvider()

    def ask_question(self, question: str, index: WorkspaceIndex) -> str:
        """Answer a question about the workspace using grounded context."""
        context = RAGContextGenerator.generate_rag_context(index, prompt=question, max_files=20)
        return self.provider.generate_response(question, context)

    def explain_target(self, target_path_or_symbol: str, index: WorkspaceIndex) -> str:
        """Explain a specific file or symbol using ExplanationService grounding."""
        from wia.services.explanation_service import ExplanationService
        return ExplanationService.explain_target(target_path_or_symbol, index)
