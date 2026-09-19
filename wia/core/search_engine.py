"""Workspace Search Engine querying indexed symbols, files, relationships, and semantic relevance."""

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from wia.core.index_model import WorkspaceIndex
from wia.core.metadata import IndexingStatus


@dataclass
class SearchResult:
    """Represents an evidence-grounded workspace search result item."""

    file_path: str
    language: str
    score: float
    matched_symbols: list[str] = field(default_factory=list)
    match_type: str = "file_path"  # "exact_symbol", "symbol", "file_path", "semantic_keyword", "language"
    relevance_explanation: str = ""
    line_number: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert search result to serializable dictionary."""
        return asdict(self)


class WorkspaceSearchEngine:
    """Multi-evidence search engine across filenames, symbols, docstrings, and relationships."""

    @classmethod
    def search(
        cls,
        index: WorkspaceIndex,
        query: str,
        language_filter: str | None = None,
        symbol_type_filter: str | None = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        """Search workspace index for query matching symbols, file paths, and semantic relevance."""
        query_norm = query.strip().lower()
        if not query_norm and not language_filter and not symbol_type_filter:
            return []

        tokens = [t for t in re.findall(r"[a-zA-Z0-9_]+", query_norm) if len(t) >= 2]
        results: list[SearchResult] = []

        for rel_path, rec in index.files.items():
            if rec.indexing_status != IndexingStatus.INDEXED:
                continue

            # Apply language filter if specified
            if language_filter and rec.language.lower() != language_filter.strip().lower():
                continue

            score = 0.0
            match_type = ""
            matched_symbols: list[str] = []
            explanations: list[str] = []
            best_line: int | None = None

            rel_path_lower = rel_path.lower()
            file_stem_lower = Path(rel_path).stem.lower()

            # 1. Exact or partial file path match
            if query_norm and query_norm in rel_path_lower:
                if file_stem_lower == query_norm:
                    score += 15.0
                    match_type = "file_path"
                    explanations.append(f"Filename stem matches '{query}' exactly")
                else:
                    score += 8.0
                    match_type = "file_path"
                    explanations.append(f"File path matches '{query}'")

            # 2. Token matches against file path
            for t in tokens:
                if t in rel_path_lower and t != query_norm:
                    score += 3.0

            # 3. Match against AST symbols in extra_metadata
            symbols_list = rec.extra_metadata.get("symbols", [])
            for sym in symbols_list:
                sym_name = sym.get("name", "")
                sym_type = sym.get("symbol_type", "")
                sym_doc = sym.get("docstring", "") or ""
                sym_name_lower = sym_name.lower()

                if symbol_type_filter and sym_type.lower() != symbol_type_filter.strip().lower():
                    continue

                if query_norm:
                    if sym_name_lower == query_norm:
                        score += 20.0
                        matched_symbols.append(f"{sym_name} ({sym_type})")
                        match_type = "exact_symbol"
                        explanations.append(f"Defines {sym_type} `{sym_name}` exactly")
                        if best_line is None:
                            best_line = sym.get("line_number")
                    elif query_norm in sym_name_lower:
                        score += 10.0
                        matched_symbols.append(f"{sym_name} ({sym_type})")
                        if not match_type:
                            match_type = "symbol"
                        explanations.append(f"Defines {sym_type} `{sym_name}`")
                        if best_line is None:
                            best_line = sym.get("line_number")
                    elif any(t in sym_name_lower for t in tokens):
                        score += 4.0
                        matched_symbols.append(f"{sym_name} ({sym_type})")
                        if not match_type:
                            match_type = "symbol"

                    # Check docstring keywords
                    if sym_doc and any(t in sym_doc.lower() for t in tokens):
                        score += 3.5
                        if not match_type:
                            match_type = "semantic_keyword"
                        explanations.append(f"Docstring mentions query concepts in `{sym_name}`")

            if score > 0 or (language_filter and not query_norm):
                if not match_type:
                    match_type = "language"
                    score = 1.0

                # Assemble comprehensive relevance summary
                sym_count = len(symbols_list)
                if not explanations:
                    if sym_count > 0:
                        top_syms = ", ".join(s.get("name", "") for s in symbols_list[:3] if s.get("name"))
                        relevance_text = f"Defines {sym_count} symbols ({top_syms})"
                    else:
                        relevance_text = f"{rec.file_type} module in {rec.language}"
                else:
                    relevance_text = "; ".join(explanations[:2])
                    if sym_count > 0 and len(matched_symbols) < sym_count:
                        relevance_text += f" (defines {sym_count} total symbols)"

                results.append(
                    SearchResult(
                        file_path=rel_path,
                        language=rec.language,
                        score=round(score, 2),
                        matched_symbols=matched_symbols[:8],
                        match_type=match_type,
                        relevance_explanation=relevance_text,
                        line_number=best_line,
                    )
                )

        # Sort by relevance score descending
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]
