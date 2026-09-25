"""Relevance evaluation, hallucination validation, and structured output formatting for LLM reasoning."""

import re
from dataclasses import dataclass, field
from typing import Any

from wia.core.index_model import WorkspaceIndex


@dataclass
class RelevanceAssessment:
    """Structured assessment of LLM response relevance, grounding, and formatting quality."""

    relevance_score: float  # 0.0 to 1.0 (0% - 100%)
    is_relevant: bool
    grounding_score: float  # 0.0 to 1.0
    structure_score: float  # 0.0 to 1.0
    verified_citations: list[str] = field(default_factory=list)
    unverified_citations: list[str] = field(default_factory=list)
    missing_sections: list[str] = field(default_factory=list)
    hallucination_warnings: list[str] = field(default_factory=list)
    formatted_response: str = ""

    def summary_badge(self) -> str:
        """Generate human-readable relevance and grounding badge."""
        pct = int(self.relevance_score * 100)
        ground_pct = int(self.grounding_score * 100)
        status = "Verified Grounded" if self.is_relevant and ground_pct >= 70 else "Partially Grounded"
        return f"**Relevance & Grounding**: {pct}% ({status} | Citations: {len(self.verified_citations)} verified)"


class ResponseRelevanceGrader:
    """Evaluates and enforces query relevance, structural integrity, and verified evidence grounding."""

    STANDARD_SECTIONS = [
        ("Executive Summary / Direct Answer", ["executive summary", "overview", "summary", "direct answer", "purpose"]),
        ("Architecture & System Context", ["architecture", "subsystem", "component", "design", "structure", "layout"]),
        ("Key Symbols & Implementation", ["symbols", "classes", "functions", "modules", "methods", "key components"]),
        ("Evidence & Citations", ["evidence", "citations", "references", "grounded evidence"]),
    ]

    @classmethod
    def evaluate(
        cls,
        prompt: str,
        response_text: str,
        index: WorkspaceIndex | None = None,
        retrieved_files: list[str] | None = None,
    ) -> RelevanceAssessment:
        """Evaluate response relevance, verify citations against index, and check structural sections."""
        if not response_text or not response_text.strip():
            return RelevanceAssessment(
                relevance_score=0.0,
                is_relevant=False,
                grounding_score=0.0,
                structure_score=0.0,
                missing_sections=[s[0] for s in cls.STANDARD_SECTIONS],
                formatted_response="No response generated.",
            )

        resp_lower = response_text.lower()
        prompt_lower = prompt.lower()

        # 1. Query Term Relevance
        query_terms = [
            t for t in re.findall(r"[a-zA-Z0-9_]{3,}", prompt_lower)
            if t not in ("what", "how", "does", "the", "and", "for", "with", "from", "this", "explain", "where", "show")
        ]
        if query_terms:
            matched_terms = [t for t in query_terms if t in resp_lower]
            term_relevance = len(matched_terms) / len(query_terms)
        else:
            term_relevance = 1.0

        # 2. Structural Section Verification
        missing_secs: list[str] = []
        found_sec_count = 0
        for sec_name, keywords in cls.STANDARD_SECTIONS:
            if any(kw in resp_lower for kw in keywords):
                found_sec_count += 1
            else:
                missing_secs.append(sec_name)
        structure_score = round(found_sec_count / len(cls.STANDARD_SECTIONS), 2)

        # 3. Evidence & Citation Verification against WorkspaceIndex
        verified_cits: list[str] = []
        unverified_cits: list[str] = []
        warnings: list[str] = []

        # Extract file citations like `path/to/file.py` or `file.py:10-20`
        cited_paths = set(re.findall(r"`([a-zA-Z0-9_\-/\\]+\.[a-zA-Z0-9]+(?::\d+(?:-\d+)?)?)`", response_text))

        if index:
            indexed_rel_paths = set(index.files.keys())
            for cit in cited_paths:
                clean_p = cit.split(":")[0].replace("\\", "/")
                if clean_p in indexed_rel_paths or any(clean_p in ip for ip in indexed_rel_paths):
                    verified_cits.append(cit)
                else:
                    unverified_cits.append(cit)
                    warnings.append(f"Cited path `{clean_p}` not found in active workspace index.")
            
            if cited_paths:
                grounding_score = round(len(verified_cits) / len(cited_paths), 2)
            else:
                # If no direct citations in text but retrieved files exist
                grounding_score = 0.8 if retrieved_files else 0.5
        else:
            verified_cits = list(cited_paths)
            grounding_score = 0.9 if verified_cits else 0.6

        # Composite Relevance Score
        composite_score = round(
            (term_relevance * 0.40) + (grounding_score * 0.35) + (structure_score * 0.25), 2
        )
        is_relevant = composite_score >= 0.55

        # Format and polish response if missing essential structure
        formatted = cls.format_and_structure(
            response_text=response_text,
            prompt=prompt,
            verified_citations=verified_cits,
            retrieved_files=retrieved_files,
            composite_score=composite_score,
        )

        return RelevanceAssessment(
            relevance_score=composite_score,
            is_relevant=is_relevant,
            grounding_score=grounding_score,
            structure_score=structure_score,
            verified_citations=verified_cits,
            unverified_citations=unverified_cits,
            missing_sections=missing_secs,
            hallucination_warnings=warnings,
            formatted_response=formatted,
        )

    @classmethod
    def format_and_structure(
        cls,
        response_text: str,
        prompt: str,
        verified_citations: list[str] | None = None,
        retrieved_files: list[str] | None = None,
        composite_score: float = 1.0,
    ) -> str:
        """Ensure the response adheres to standard high-clarity Markdown structure."""
        text = response_text.strip()

        # If already formatted with Evidence section, verify clean presentation
        has_evidence = "Evidence" in text or "### Evidence" in text or "## Evidence" in text
        if not has_evidence and (verified_citations or retrieved_files):
            citations_to_show = verified_citations or [f"`{f}`" for f in (retrieved_files or [])[:8]]
            if citations_to_show:
                evidence_block = "\n\n### Evidence & Grounded Citations\n" + "\n".join(
                    f"- {c}" if not c.startswith("-") else c for c in citations_to_show[:8]
                )
                text += evidence_block

        return text
