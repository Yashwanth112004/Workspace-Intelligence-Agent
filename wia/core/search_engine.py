"""Workspace Search Engine for querying indexed symbols, files, and relationships."""

from dataclasses import asdict, dataclass
from wia.core.index_model import WorkspaceIndex
from wia.core.metadata import IndexingStatus


@dataclass
class SearchResult:
    """Represents a workspace search result item."""

    file_path: str
    language: str
    score: float
    matched_symbols: list[str]
    match_type: str  # "file_path", "symbol", "language"

    def to_dict(self) -> dict:
        """Convert search result to serializable dictionary."""
        return asdict(self)


class WorkspaceSearchEngine:
    """Queries workspace index for symbols, file paths, and language definitions."""

    @classmethod
    def search(
        cls,
        index: WorkspaceIndex,
        query: str,
        language_filter: str | None = None,
        symbol_type_filter: str | None = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        """Search workspace index for query matching symbols or file paths."""
        query_norm = query.strip().lower()
        if not query_norm and not language_filter and not symbol_type_filter:
            return []

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

            # 1. Match against file path
            rel_path_lower = rel_path.lower()
            if query_norm and query_norm in rel_path_lower:
                if rel_path_lower.endswith(query_norm) or Path_name_match(rel_path_lower, query_norm):
                    score += 10.0
                else:
                    score += 5.0
                match_type = "file_path"

            # 2. Match against AST symbols in extra_metadata
            symbols_list = rec.extra_metadata.get("symbols", [])
            for sym in symbols_list:
                sym_name = sym.get("name", "")
                sym_type = sym.get("symbol_type", "")

                if symbol_type_filter and sym_type.lower() != symbol_type_filter.strip().lower():
                    continue

                if query_norm and query_norm in sym_name.lower():
                    score += 7.5 if sym_name.lower() == query_norm else 3.5
                    matched_symbols.append(f"{sym_name} ({sym_type})")
                    if not match_type:
                        match_type = "symbol"

            if score > 0 or (language_filter and not query_norm):
                if not match_type:
                    match_type = "language"
                    score = 1.0

                results.append(
                    SearchResult(
                        file_path=rel_path,
                        language=rec.language,
                        score=round(score, 2),
                        matched_symbols=matched_symbols,
                        match_type=match_type,
                    )
                )

        # Sort by relevance score descending
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]


def Path_name_match(path_str: str, query: str) -> bool:
    """Helper to check if query matches file basename."""
    parts = path_str.replace("\\", "/").split("/")
    return query in parts[-1] if parts else False
