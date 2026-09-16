import logging
from typing import List, Dict, Any, Tuple
from app.models.workspace import Repository, VectorChunk, WorkspaceSummary
from app.services.rag.vector_store import VectorSearchStore
from app.core.llm import LLMClient

logger = logging.getLogger("wia.agent")

class WIACodeUnderstandingAgent:
    """
    NVIDIA NOOA (NeMo Orchestrated Object Agent) - WIA Code Understanding Agent.
    Responsible for code explanation, component identification, dependency mapping,
    and natural language Q&A using RAG context.
    """

    def __init__(self, repo: Repository, chunks: List[VectorChunk], summaries: List[WorkspaceSummary]):
        self.repo = repo
        self.chunks = chunks
        self.summaries = summaries

    def answer_question(self, user_query: str) -> Dict[str, Any]:
        """Processes user natural language query and returns response with context citations."""
        logger.info(f"WIA Agent processing query for repo '{self.repo.name}': {user_query}")

        # 1. Semantic Context Retrieval via RAG
        top_matches = VectorSearchStore.search(self.chunks, user_query, top_k=6)
        
        context_snippets = []
        citations = []
        
        for chunk, score in top_matches:
            snippet_str = f"--- Context Source ({chunk.file_path}) [Relevance: {score:.2f}] ---\n{chunk.content}\n"
            context_snippets.append(snippet_str)
            citations.append({
                "file_path": chunk.file_path,
                "chunk_type": chunk.chunk_type,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "score": round(score, 3)
            })

        # 2. Extract repository overview summary
        repo_summary_str = ""
        for s in self.summaries:
            if s.level == "repository":
                repo_summary_str = s.summary_text
                break

        # 3. Construct NOOA Agent System & Prompt Context
        system_prompt = """You are the WIA Code Understanding Agent, an AI software architect built on NVIDIA NOOA framework guidelines.
Your role is to explain code, summarize components, identify entry points, analyze dependencies, and answer technical questions about the workspace.
Always base your response on the provided repository context and citations. Include file names and structural relationships in your answer."""

        user_prompt = f"""[REPOSITORY METADATA]
Repository Name: {self.repo.name}
Tech Stack: {self.repo.tech_stack}
Total Files: {self.repo.total_files} | Total LOC: {self.repo.total_loc}
Entry Points: {self.repo.entry_points}
Dependencies: {self.repo.dependencies}

[HIGH-LEVEL REPOSITORY SUMMARY]
{repo_summary_str or 'Repository analysis ingested.'}

[RETRIEVED CODE & WORKSPACE CONTEXT]
{chr(10).join(context_snippets) if context_snippets else 'No specific code chunks retrieved.'}

[USER QUESTION]
{user_query}

Provide a clear, detailed, and structured technical response answering the user's question based on the repository context above."""

        # 4. Generate response via LLM Client
        response_text = LLMClient.generate_completion(user_prompt, system_prompt=system_prompt)

        return {
            "query": user_query,
            "response": response_text,
            "citations": citations,
            "repo_id": self.repo.id,
            "repo_name": self.repo.name
        }
