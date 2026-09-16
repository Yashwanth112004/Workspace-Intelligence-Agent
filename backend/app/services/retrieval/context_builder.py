from typing import Dict, Any, List
from app.models.workspace import Repository

class ContextBuilder:
    """Assembles structured, deduplicated context for the AI reasoning agent."""

    @staticmethod
    def build_structured_context(
        repo: Repository,
        retrieval_result: Dict[str, Any],
        max_tokens_approx: int = 4000
    ) -> str:
        sections = []

        # 1. Repository Overview
        sections.append(f"=== [REPOSITORY METADATA] ===")
        sections.append(f"Name: {repo.name} | Total Files: {repo.total_files} | Total LOC: {repo.total_loc}")
        sections.append(f"Tech Stack: {dict(repo.tech_stack or {})}")
        sections.append(f"Entry Points: {repo.entry_points or []}")
        sections.append(f"Dependencies: {len(repo.dependencies or [])} manifests\n")

        # 2. Graph & Relationship Evidence
        if retrieval_result.get("graph_evidence"):
            sections.append(f"=== [KNOWLEDGE GRAPH RELATIONSHIPS] ===")
            for g in retrieval_result["graph_evidence"]:
                sections.append(f"• {g}")
            sections.append("")

        # 3. Matching Symbols
        if retrieval_result.get("symbols"):
            sections.append(f"=== [AUTHORITATIVE AST SYMBOLS] ===")
            for s in retrieval_result["symbols"][:6]:
                sections.append(f"• {s['type'].upper()} `{s['name']}` ({s['file_path']}:{s['line']}) - Sig: {s['signature'] or 'N/A'}")
            sections.append("")

        # 4. Hierarchical Summaries
        if retrieval_result.get("summaries"):
            sections.append(f"=== [HIERARCHICAL ARCHITECTURAL SUMMARIES] ===")
            for sm in retrieval_result["summaries"]:
                sections.append(f"[{sm['level'].upper()}] {sm['name']} ({sm['target']}): {sm['text']}")
            sections.append("")

        # 5. Retrieved Code Chunks
        if retrieval_result.get("chunks"):
            sections.append(f"=== [SOURCE CODE CONTEXT] ===")
            for c in retrieval_result["chunks"][:6]:
                sections.append(f"--- File: {c['file_path']} (Lines {c['start_line']}-{c['end_line']}) ---")
                sections.append(c['content'])
                sections.append("")

        return "\n".join(sections)
