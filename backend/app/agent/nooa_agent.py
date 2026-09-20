import logging
from typing import List, Dict, Any, Tuple, Optional
from app.models.workspace import Repository, VectorChunk, WorkspaceSummary, ASTSymbol
from app.models.knowledge import KnowledgeEntity, KnowledgeRelationship
from app.services.graph.code_graph import CodeKnowledgeGraph
from app.services.retrieval.hybrid_retriever import HybridRetriever
from app.services.retrieval.query_planner import QueryPlanner
from app.services.retrieval.context_builder import ContextBuilder
from app.core.llm import LLMClient
from app.services.intelligence.secret_safety import SecretSafetyService

logger = logging.getLogger("wia.agent")

class WIACodeUnderstandingAgent:
    """
    NVIDIA NOOA (NeMo Orchestrated Object Agent) - WIA Code Understanding Agent.
    Augmented with Knowledge Graph, Hybrid Retrieval, Code Flow Tracing,
    Impact Analysis, Onboarding Guides, and Repository Health Auditing.
    """

    def __init__(
        self,
        repo: Repository,
        chunks: List[VectorChunk],
        summaries: List[WorkspaceSummary],
        symbols: Optional[List[ASTSymbol]] = None,
        graph: Optional[CodeKnowledgeGraph] = None
    ):
        self.repo = repo
        self.chunks = chunks
        self.summaries = summaries
        self.symbols = symbols or []
        self.graph = graph

    def answer_question(self, user_query: str) -> Dict[str, Any]:
        """Processes user query with Query Planning, Hybrid Retrieval, and Context Building."""
        logger.info(f"WIA Agent answering query for '{self.repo.name}': {user_query}")

        # 1. Plan query intent
        plan = QueryPlanner.plan_query(user_query)
        intent = plan.get("intent", "GENERAL_QA")

        # 2. Route specialized tools if query matches direct intent
        if intent == "CODE_FLOW":
            # Extract potential symbol from query
            words = user_query.replace("?", "").replace("'", "").replace('"', "").split()
            target_sym = next((w for w in words if len(w) > 3 and not w.lower() in {"trace", "flow", "execution", "what", "happens", "when", "call"}), "")
            if target_sym:
                flow_data = self.trace_flow(target_sym)
                if flow_data.get("flow"):
                    return flow_data

        if intent == "DEPENDENCY_IMPACT":
            words = user_query.replace("?", "").replace("'", "").replace('"', "").split()
            target_sym = next((w for w in words if len(w) > 3 and not w.lower() in {"impact", "affect", "modify", "change", "what", "happens", "if"}), "")
            if target_sym:
                impact_data = self.analyze_impact(target_sym)
                if impact_data.get("impact"):
                    return impact_data

        if intent == "ONBOARDING":
            return self.onboarding_guide()

        if intent == "HEALTH_AUDIT":
            return self.audit_health()

        # 3. Hybrid Retrieval
        retrieval = HybridRetriever.retrieve(
            query=user_query,
            chunks=self.chunks,
            summaries=self.summaries,
            symbols=self.symbols,
            graph=self.graph,
            top_k=6
        )

        # 4. Context Building
        has_evidence = bool(retrieval.get("chunks") or retrieval.get("symbols") or retrieval.get("summaries"))
        context_str = ContextBuilder.build_structured_context(self.repo, retrieval)
        sanitized_context = SecretSafetyService.sanitize_content(context_str)

        system_prompt = """You are the WIA Code Understanding Agent, a Lead AI Software Architect.
Your role is to explain code architecture, component relationships, trace data flow, and answer technical questions.
Always ground your answers in the provided authoritative source facts, knowledge graph relations, and code chunks.
Always reference specific file paths, symbols, and line numbers.
If the requested feature, component, or question cannot be answered from the provided context, state clearly that no evidence was found in the codebase rather than inventing details."""

        user_prompt = f"""[STRUCTURED CODEBASE CONTEXT]
{sanitized_context}

[USER QUESTION]
{user_query}

Provide a structured, authoritative technical response grounded strictly in the codebase context above."""

        if LLMClient.is_nim_available():
            response_text = LLMClient.generate_completion(user_prompt, system_prompt=system_prompt)
        elif not has_evidence or (not retrieval.get("chunks") and not retrieval.get("symbols")):
            response_text = f"No relevant implementation, symbol, or evidence for '{user_query}' was found in the indexed workspace knowledge base for '{self.repo.name}'."
        else:
            # Deterministic synthesis from retrieved evidence
            chunks_summary = "\n".join([
                f"- `{c['file_path'] if isinstance(c, dict) else c.file_path}` (lines {c.get('start_line', 1) if isinstance(c, dict) else getattr(c, 'start_line', 1)}-{c.get('end_line', 1) if isinstance(c, dict) else getattr(c, 'end_line', 1)}): {(c.get('content', '') if isinstance(c, dict) else getattr(c, 'content', ''))[:180]}..."
                for c in retrieval.get("chunks", [])[:3]
            ])
            response_text = f"### Grounded Codebase Evidence for `{self.repo.name}`\n\nBased on indexed AST symbols and source chunks:\n\n{chunks_summary}\n\n*Note: Configure `NVIDIA_NIM_API_KEY` to enable advanced multi-step LLM reasoning.*"

        return {
            "query": user_query,
            "intent": intent,
            "response": response_text,
            "citations": retrieval.get("citations", []),
            "repo_id": self.repo.id,
            "repo_name": self.repo.name
        }


    def trace_flow(self, entry_symbol: str) -> Dict[str, Any]:
        """Traces execution call flow starting from an entry point."""
        if not self.graph:
            return {"flow": [], "message": "Knowledge graph not available."}

        flow = self.graph.trace_flow(entry_symbol)
        citations = [
            {"file_path": step["file"], "start_line": step["line"], "end_line": step["line"], "chunk_type": "function", "score": 1.0}
            for step in flow if step.get("file")
        ]

        summary_lines = [f"Step {s['step']}: `{s['symbol']}` ({s['file']}:{s['line']}) - {s['reason']}" for s in flow]
        response_text = f"### Execution Flow Trace for `{entry_symbol}`\n\n" + "\n".join(summary_lines)

        return {
            "query": f"Trace flow for {entry_symbol}",
            "intent": "CODE_FLOW",
            "flow": flow,
            "response": response_text,
            "citations": citations,
            "repo_id": self.repo.id,
            "repo_name": self.repo.name
        }

    def analyze_impact(self, symbol_or_file: str) -> Dict[str, Any]:
        """Calculates dependency ripple impact for a symbol or file."""
        if not self.graph:
            return {"impact": {}, "message": "Knowledge graph not available."}

        impact = self.graph.analyze_impact(symbol_or_file)
        citations = [
            {"file_path": f, "start_line": 1, "end_line": 1, "chunk_type": "file", "score": 0.9}
            for f in impact.get("affected_files", [])
        ]

        response_text = f"""### Change Impact Analysis for `{symbol_or_file}`

- **Direct Dependents**: {impact['direct_impact_count']} entities
- **Indirect Dependents**: {impact['indirect_impact_count']} entities
- **Total Affected Files**: {impact['affected_files_count']} files

#### Affected Callers & Dependents:
{chr(10).join([f'- `{dep}`' for dep in impact['direct_dependents'][:10]]) or '- None directly impacted'}

#### Affected Files:
{chr(10).join([f'- `{fl}`' for fl in impact['affected_files'][:10]]) or '- None'}
"""
        return {
            "query": f"Analyze impact of {symbol_or_file}",
            "intent": "DEPENDENCY_IMPACT",
            "impact": impact,
            "response": response_text,
            "citations": citations,
            "repo_id": self.repo.id,
            "repo_name": self.repo.name
        }

    def onboarding_guide(self) -> Dict[str, Any]:
        """Generates a developer onboarding walkthrough for the codebase."""
        repo_sum = next((s.summary_text for s in self.summaries if s.level == "repository"), "Architecture summary available.")
        folder_sums = [s for s in self.summaries if s.level in ("parent_folder", "child_folder")]

        response_text = f"""# 🚀 Developer Onboarding Guide for `{self.repo.name}`

## 1. System Overview
{repo_sum}

## 2. Technology Stack & Size
- **Total Files**: {self.repo.total_files} | **Total LOC**: {self.repo.total_loc}
- **Languages**: {', '.join([f'{k} ({v} LOC)' for k, v in (self.repo.tech_stack or {}).items()])}

## 3. Key Entry Points
{chr(10).join([f'- `{ep}`' for ep in (self.repo.entry_points or ['None detected'])])}

## 4. Subsystem Layout
{chr(10).join([f'- **`{f.target_path}`**: {f.summary_text}' for f in folder_sums[:6]])}

## 5. Getting Started Tips
- Review the configuration files: {', '.join([f'`{c}`' for c in (self.repo.config_files or [])])}
- Trace main entry points before modifying subsystem logic.
"""
        return {
            "query": "Explain codebase to a new developer",
            "intent": "ONBOARDING",
            "response": response_text,
            "citations": [{"file_path": ep, "start_line": 1, "end_line": 1, "chunk_type": "file", "score": 1.0} for ep in (self.repo.entry_points or [])],
            "repo_id": self.repo.id,
            "repo_name": self.repo.name
        }

    def audit_health(self) -> Dict[str, Any]:
        """Performs repository health, complexity, and structural audit."""
        functions = [s for s in self.symbols if s.symbol_type == "function"]
        classes = [s for s in self.symbols if s.symbol_type == "class"]

        response_text = f"""# 🏥 Repository Health & Complexity Audit for `{self.repo.name}`

## Metrics Summary
- **Total Code Files**: {self.repo.total_files}
- **Total Lines of Code**: {self.repo.total_loc}
- **Functions Defined**: {len(functions)}
- **Classes Defined**: {len(classes)}

## Health Indicators
- **Dependency Structure**: {len(self.repo.dependencies or [])} dependency manifests
- **Entry Points Configured**: {'Yes (' + str(len(self.repo.entry_points or [])) + ')' if self.repo.entry_points else 'No clear entry point detected'}
- **Secret Safety**: Sensitive file protection & secret pattern redaction active.
"""
        return {
            "query": "Repository health audit",
            "intent": "HEALTH_AUDIT",
            "response": response_text,
            "citations": [],
            "repo_id": self.repo.id,
            "repo_name": self.repo.name
        }
