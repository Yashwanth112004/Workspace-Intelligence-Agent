"""Grounded Codebase Reasoning Engine combining retrieval, evidence, AI providers, and relevance evaluation."""

from pathlib import Path
from typing import Any

from wia.constants import DEFAULT_LLM_CONTEXT_TOKEN_BUDGET
from wia.core.index_model import WorkspaceIndex
from wia.core.retrieval import RetrievalResult, WorkspaceRetriever
from wia.knowledge.graph import WorkspaceGraph
from wia.llm.base import AIProvider, AIProviderFactory
from wia.llm.relevance import RelevanceAssessment, ResponseRelevanceGrader


class ReasoningEngine:
    """Orchestrates workspace context retrieval, intent routing, evidence grounding, and relevance validation."""

    def __init__(
        self,
        index: WorkspaceIndex,
        provider: AIProvider | None = None,
        graph: WorkspaceGraph | None = None,
    ):
        self.index = index
        self.retriever = WorkspaceRetriever(index, graph=graph)
        self.provider = provider or AIProviderFactory.get_provider()

    def ask(
        self,
        query: str,
        max_files: int = 15,
        token_budget: int = DEFAULT_LLM_CONTEXT_TOKEN_BUDGET,
    ) -> str:
        """Execute full reasoning pipeline: intent -> retrieval -> evidence assembly -> AI reasoning -> relevance grading."""
        assessment = self.ask_with_assessment(
            query=query, max_files=max_files, token_budget=token_budget
        )
        return assessment.formatted_response

    def ask_with_assessment(
        self,
        query: str,
        max_files: int = 15,
        token_budget: int = DEFAULT_LLM_CONTEXT_TOKEN_BUDGET,
    ) -> RelevanceAssessment:
        """Execute full reasoning pipeline and return comprehensive RelevanceAssessment."""
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

        # 3. Evaluate response relevance and structure
        assessment = ResponseRelevanceGrader.evaluate(
            prompt=query,
            response_text=raw_response,
            index=self.index,
            retrieved_files=retrieval.target_files,
        )

        # 4. If evidence was not in the raw response, append citation items
        if "Evidence" not in assessment.formatted_response and retrieval.evidence_items:
            citations = "\n".join(f"- {e.to_citation()}" for e in retrieval.evidence_items[:8])
            assessment.formatted_response += f"\n\nEvidence:\n{citations}"

        return assessment
