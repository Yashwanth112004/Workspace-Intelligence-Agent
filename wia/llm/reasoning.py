"""Grounded Codebase Reasoning Engine combining retrieval, evidence, and AI providers."""

from pathlib import Path
from typing import Any

from wia.core.index_model import WorkspaceIndex
from wia.core.retrieval import RetrievalResult, WorkspaceRetriever
from wia.knowledge.graph import WorkspaceGraph
from wia.llm.base import AIProvider, AIProviderFactory


class ReasoningEngine:
    """Orchestrates workspace context retrieval, intent routing, and evidence-grounded AI reasoning."""

    def __init__(
        self,
        index: WorkspaceIndex,
        provider: AIProvider | None = None,
        graph: WorkspaceGraph | None = None,
    ):
        self.index = index
        self.retriever = WorkspaceRetriever(index, graph=graph)
        self.provider = provider or AIProviderFactory.get_provider()

    def ask(self, query: str, max_files: int = 15, token_budget: int = 6000) -> str:
        """Execute full reasoning pipeline: intent -> retrieval -> evidence assembly -> AI reasoning."""
        # 1. Retrieve grounded context and citations
        retrieval: RetrievalResult = self.retriever.retrieve(
            query=query, max_files=max_files, token_budget=token_budget
        )

        # 2. Invoke AI Provider
        raw_response = self.provider.generate(
            prompt=query,
            context=retrieval.assembled_context,
            options={"intent": retrieval.intent, "target_files": retrieval.target_files},
        )

        # 3. If the provider returned a response with evidence, return directly; else append citations
        if "Evidence" not in raw_response and retrieval.evidence_items:
            citations = "\n".join(f"- {e.to_citation()}" for e in retrieval.evidence_items[:8])
            raw_response += f"\n\nEvidence:\n{citations}"

        return raw_response
