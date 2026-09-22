"""Unified Workspace Retrieval Layer and Evidence Model."""

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from wia.constants import DEFAULT_LLM_CONTEXT_TOKEN_BUDGET
from wia.core.architecture import ArchitectureAnalyzer
from wia.core.framework import FrameworkDetector
from wia.core.index_model import WorkspaceIndex
from wia.core.metadata import FileRecord, IndexingStatus
from wia.knowledge.graph import WorkspaceGraph


@dataclass
class EvidenceItem:
    """Grounding evidence item representing a verified workspace artifact."""

    file_path: str
    symbol_name: str | None = None
    line_range: tuple[int, int] | None = None
    relationship_type: str | None = None
    code_snippet: str | None = None
    relevance_score: float = 1.0
    description: str = ""

    def to_citation(self) -> str:
        """Format evidence into human-readable citation string."""
        if self.line_range and self.line_range[0] > 0:
            loc = f"{self.file_path}:{self.line_range[0]}-{self.line_range[1]}"
        else:
            loc = self.file_path

        if self.symbol_name:
            loc += f" (`{self.symbol_name}`)"
        if self.description:
            loc += f" — {self.description}"
        return loc


@dataclass
class RetrievalResult:
    """Structured context retrieval payload with evidence and budget management."""

    query: str
    intent: str
    target_files: list[str] = field(default_factory=list)
    evidence_items: list[EvidenceItem] = field(default_factory=list)
    assembled_context: str = ""
    token_estimate: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert retrieval result to dictionary."""
        return {
            "query": self.query,
            "intent": self.intent,
            "target_files": self.target_files,
            "evidence_items": [e.to_citation() for e in self.evidence_items],
            "token_estimate": self.token_estimate,
        }


class IntentClassifier:
    """Deterministic heuristic classifier for codebase intelligence queries."""

    INTENTS = {
        "GENERAL_PROJECT": [
            "explain the project", "overview", "what is this repo", "what does this project do",
            "summary of project", "codebase overview", "high level", "purpose of project",
        ],
        "ARCHITECTURE": [
            "architecture", "system design", "layers", "subsystem", "layout", "component map",
            "how is the code organized", "directory structure",
        ],
        "FLOW": [
            "execution flow", "data flow", "lifecycle", "how does execution work", "runtime flow",
            "request flow", "how does application execution work", "workflow",
        ],
        "DEPENDENCY": [
            "depends on", "dependencies", "what depends", "who calls", "importers", "used by",
            "dependency tree", "external libraries",
        ],
        "IMPACT": [
            "impact of changing", "what breaks", "blast radius", "downstream effects",
            "impact analysis", "risk of modifying",
        ],
        "TESTING": [
            "how is it tested", "unit test", "test coverage", "test suite", "testing structure",
            "where are tests",
        ],
        "CONFIGURATION": [
            "how to configure", "environment variables", "config settings", "pyproject", "setup",
            "configuration",
        ],
        "DEBUGGING": [
            "why did", "error handling", "exception", "bug", "traceback", "fix",
        ],
    }

    @classmethod
    def classify(cls, query: str) -> str:
        """Classify user query into canonical intent category."""
        q_lower = query.lower().strip()

        for intent, patterns in cls.INTENTS.items():
            if any(pat in q_lower for pat in patterns):
                return intent

        if any(w in q_lower for w in ("how to", "how do i", "how does")):
            return "FLOW"
        if any(w in q_lower for w in ("class ", "function ", "def ", "method ")):
            return "CODE_EXPLANATION"
        if any(ext in q_lower for ext in (".py", ".ts", ".js", ".ipynb", ".json", ".toml")):
            return "CODE_EXPLANATION"

        return "GENERAL_PROJECT"


class WorkspaceRetriever:
    """Multi-strategy context and evidence retriever with token budgeting."""

    def __init__(self, index: WorkspaceIndex, graph: WorkspaceGraph | None = None):
        self.index = index
        self.workspace_root = Path(index.workspace_path)
        if graph is None:
            self.graph = WorkspaceGraph()
            self.graph.build_from_index(index)
        else:
            self.graph = graph

    def retrieve(
        self,
        query: str,
        max_files: int = 15,
        token_budget: int = DEFAULT_LLM_CONTEXT_TOKEN_BUDGET,
    ) -> RetrievalResult:
        """Retrieve grounded workspace evidence and formatted context for a query."""
        intent = IntentClassifier.classify(query)
        evidence_items: list[EvidenceItem] = []
        target_files: set[str] = set()

        if intent in ("GENERAL_PROJECT", "ARCHITECTURE"):
            self._retrieve_project_level(evidence_items, target_files, max_files=max_files)
        elif intent in ("FLOW", "CODE_EXPLANATION", "DEPENDENCY", "IMPACT", "TESTING", "CONFIGURATION"):
            self._retrieve_targeted(query, intent, evidence_items, target_files, max_files=max_files)
        else:
            self._retrieve_targeted(query, intent, evidence_items, target_files, max_files=max_files)

        assembled_context = self._assemble_context(intent, query, evidence_items, token_budget=token_budget)
        token_est = len(assembled_context) // 4

        return RetrievalResult(
            query=query,
            intent=intent,
            target_files=sorted(list(target_files)),
            evidence_items=evidence_items,
            assembled_context=assembled_context,
            token_estimate=token_est,
        )

    def _retrieve_project_level(
        self,
        evidence_items: list[EvidenceItem],
        target_files: set[str],
        max_files: int = 15,
    ) -> None:
        """Retrieve foundational project-level architectural files, manifests, entrypoints, and tests."""
        # 1. Manifests & Configs
        for p, rec in self.index.files.items():
            if rec.file_type in ("Build", "CI/CD", "Configuration"):
                target_files.add(p)
                evidence_items.append(
                    EvidenceItem(
                        file_path=p,
                        description=f"{rec.file_type} manifest defining workspace metadata/build rules.",
                    )
                )

        # 2. Main Entry Points & Core Modules
        arch = ArchitectureAnalyzer.analyze_workspace(self.index)
        for ep in arch.entry_points[:6]:
            clean_ep = ep.strip("`").split(" -> ")[0].strip("`")
            for p in self.index.files:
                if clean_ep in p or Path(p).stem == clean_ep:
                    target_files.add(p)
                    evidence_items.append(
                        EvidenceItem(file_path=p, description=f"Entry point identified: {ep}")
                    )

        # 3. Core Source Files (by symbol density / connectivity)
        ranked_files = sorted(
            [
                (p, r)
                for p, r in self.index.files.items()
                if r.indexing_status == IndexingStatus.INDEXED and r.file_type in ("Source Code", "Notebook")
            ],
            key=lambda item: len(item[1].extra_metadata.get("symbols", [])),
            reverse=True,
        )

        for p, rec in ranked_files:
            if len(target_files) >= max_files:
                break
            if p not in target_files:
                target_files.add(p)
                syms = rec.extra_metadata.get("symbols", [])
                sym_names = ", ".join(s.get("name", "") for s in syms[:4] if s.get("name"))
                desc = f"Core module defining {len(syms)} symbols ({sym_names})" if sym_names else "Core module"
                evidence_items.append(EvidenceItem(file_path=p, description=desc))

    def _retrieve_targeted(
        self,
        query: str,
        intent: str,
        evidence_items: list[EvidenceItem],
        target_files: set[str],
        max_files: int = 15,
    ) -> None:
        """Retrieve specific files and symbols matching keywords and graph relationships."""
        keywords = [
            w.lower()
            for w in re.findall(r"[A-Za-z0-9_]{3,}", query)
            if w.lower() not in ("what", "how", "does", "the", "and", "for", "with", "from", "this", "explain")
        ]

        scored_files: dict[str, float] = {}

        for p, rec in self.index.files.items():
            if rec.indexing_status != IndexingStatus.INDEXED:
                continue
            score = 0.0
            p_lower = p.lower()

            for kw in keywords:
                if kw in p_lower:
                    score += 3.0
                if Path(p).stem.lower() == kw:
                    score += 5.0

            symbols = rec.extra_metadata.get("symbols", [])
            matched_syms: list[dict] = []
            for s in symbols:
                s_name = s.get("name", "").lower()
                for kw in keywords:
                    if kw == s_name:
                        score += 6.0
                        matched_syms.append(s)
                    elif kw in s_name:
                        score += 2.0
                        matched_syms.append(s)

            if intent == "TESTING" and (rec.file_type == "Test" or "test" in p_lower):
                score += 3.0

            if score > 0:
                scored_files[p] = score
                target_files.add(p)
                line_r = (matched_syms[0].get("line_number", 1), matched_syms[0].get("end_line_number", 1)) if matched_syms else None
                sym_n = matched_syms[0].get("name") if matched_syms else None
                evidence_items.append(
                    EvidenceItem(
                        file_path=p,
                        symbol_name=sym_n,
                        line_range=line_r,
                        relevance_score=score,
                        description=f"Matched keywords: {', '.join(keywords)}",
                    )
                )

        # Graph neighborhood expansion
        for p in list(scored_files.keys())[:5]:
            file_node_id = f"file:{p}"
            for edge in self.graph.get_outgoing_edges(file_node_id):
                if edge.target_id.startswith("file:") and len(target_files) < max_files:
                    tgt_p = edge.target_id.replace("file:", "")
                    if tgt_p not in target_files and tgt_p in self.index.files:
                        target_files.add(tgt_p)
                        evidence_items.append(
                            EvidenceItem(
                                file_path=tgt_p,
                                relationship_type=edge.relation_type,
                                description=f"{edge.relation_type} from `{p}`",
                            )
                        )

    def _assemble_context(
        self,
        intent: str,
        query: str,
        evidence_items: list[EvidenceItem],
        token_budget: int = DEFAULT_LLM_CONTEXT_TOKEN_BUDGET,
    ) -> str:
        """Construct concise markdown context with actual source snippets and strict token budgeting."""
        lines: list[str] = []
        lines.append(f"# Grounded Workspace Context: {Path(self.index.workspace_path).name}")
        lines.append(f"- **Query**: {query}")
        lines.append(f"- **Intent**: {intent}")
        lines.append(f"- **Total Indexed Files**: {len(self.index.get_indexed_files())}")
        lines.append("")

        # Frameworks & Tech Stack
        frameworks = FrameworkDetector.detect_frameworks(self.index.workspace_path)
        if frameworks:
            lines.append("## Detected Tech Stack & Frameworks")
            for fw in frameworks:
                lines.append(f"- **{fw.name}** ({fw.category}): evidenced by `{fw.evidence_source}`")
            lines.append("")

        # Relevant Evidence Items & Source Snippets
        lines.append("## Workspace Evidence & Code Snippets")
        char_budget = token_budget * 4
        current_chars = sum(len(l) for l in lines)

        for ev in evidence_items:
            if current_chars >= char_budget:
                lines.append("- *[Remaining context truncated to respect context budget]*")
                break

            file_abs = self.workspace_root / ev.file_path
            snippet = ""
            if file_abs.exists() and file_abs.is_file():
                try:
                    raw_text = file_abs.read_text(encoding="utf-8", errors="ignore")
                    file_lines = raw_text.splitlines()
                    if ev.line_range and ev.line_range[0] > 0:
                        start_l = max(1, ev.line_range[0])
                        end_l = min(len(file_lines), ev.line_range[1] or start_l + 30)
                        sub_lines = file_lines[start_l - 1 : end_l]
                        snippet = "\n".join(f"{start_l + i}: {l}" for i, l in enumerate(sub_lines[:40]))
                    else:
                        snippet = "\n".join(f"{i+1}: {l}" for i, l in enumerate(file_lines[:35]))
                except Exception:
                    snippet = ""

            ev_header = f"### File: `{ev.file_path}`"
            if ev.symbol_name:
                ev_header += f" (Symbol: `{ev.symbol_name}`)"
            if ev.description:
                ev_header += f" — {ev.description}"

            lines.append(ev_header)
            if snippet:
                lines.append("```")
                lines.append(snippet)
                lines.append("```")
            lines.append("")
            current_chars += len(ev_header) + len(snippet) + 10

        return "\n".join(lines)
