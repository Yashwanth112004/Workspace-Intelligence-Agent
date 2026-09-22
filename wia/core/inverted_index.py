"""High-performance inverted index and token search structures for sub-millisecond workspace retrieval."""

import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from wia.core.index_model import WorkspaceIndex
from wia.core.metadata import IndexingStatus


def _extract_trigrams(text: str) -> set[str]:
    """Generate 3-character n-grams from normalized text."""
    clean = re.sub(r"[^a-zA-Z0-9_]", "", text.lower())
    if len(clean) < 3:
        return {clean} if clean else set()
    return {clean[i : i + 3] for i in range(len(clean) - 2)}


@dataclass
class WorkspaceInvertedIndex:
    """In-memory inverted index providing sub-millisecond symbol, token, and trigram candidate lookup."""

    # Exact lowercase symbol name -> list of (file_path, symbol_dict)
    exact_symbols: dict[str, list[tuple[str, dict[str, Any]]]] = field(
        default_factory=lambda: defaultdict(list)
    )
    # Lowercase filename stem -> set of relative file paths
    stem_to_files: dict[str, set[str]] = field(
        default_factory=lambda: defaultdict(set)
    )
    # Lowercase tokens -> set of relative file paths
    token_to_files: dict[str, set[str]] = field(
        default_factory=lambda: defaultdict(set)
    )
    # Language -> set of relative file paths
    language_to_files: dict[str, set[str]] = field(
        default_factory=lambda: defaultdict(set)
    )
    # Symbol type -> set of relative file paths
    symbol_type_to_files: dict[str, set[str]] = field(
        default_factory=lambda: defaultdict(set)
    )
    # Trigram -> set of relative file paths
    trigram_to_files: dict[str, set[str]] = field(
        default_factory=lambda: defaultdict(set)
    )
    # Cached count
    _indexed_count: int = 0

    @classmethod
    def build_from_index(cls, index: WorkspaceIndex) -> "WorkspaceInvertedIndex":
        """Construct inverted search index from WorkspaceIndex."""
        inv = cls()
        for rel_path, rec in index.files.items():
            if rec.indexing_status != IndexingStatus.INDEXED:
                continue

            inv._indexed_count += 1
            rel_path_lower = rel_path.lower()
            stem_lower = Path(rel_path).stem.lower()

            # 1. Stem and Language index
            inv.stem_to_files[stem_lower].add(rel_path)
            if rec.language:
                inv.language_to_files[rec.language.lower()].add(rel_path)

            # 2. Path tokens & trigrams
            path_tokens = set(re.findall(r"[a-zA-Z0-9_]{2,}", rel_path_lower))
            for tok in path_tokens:
                inv.token_to_files[tok].add(rel_path)

            for tri in _extract_trigrams(rel_path_lower):
                inv.trigram_to_files[tri].add(rel_path)

            # 3. Symbol indexing
            symbols = rec.extra_metadata.get("symbols", [])
            for sym in symbols:
                s_name = sym.get("name", "")
                s_type = sym.get("symbol_type", "")
                s_doc = sym.get("docstring", "") or ""

                if not s_name:
                    continue

                s_name_lower = s_name.lower()
                inv.exact_symbols[s_name_lower].append((rel_path, sym))

                if s_type:
                    inv.symbol_type_to_files[s_type.lower()].add(rel_path)

                # Symbol tokens & trigrams
                sym_tokens = set(re.findall(r"[a-zA-Z0-9_]{2,}", s_name_lower))
                for stok in sym_tokens:
                    inv.token_to_files[stok].add(rel_path)

                for tri in _extract_trigrams(s_name_lower):
                    inv.trigram_to_files[tri].add(rel_path)

                # Docstring tokens
                if s_doc:
                    doc_tokens = set(re.findall(r"[a-zA-Z0-9_]{3,}", s_doc.lower()))
                    for dtok in doc_tokens:
                        inv.token_to_files[dtok].add(rel_path)

        return inv

    def find_candidate_files(
        self,
        query: str,
        language_filter: str | None = None,
        symbol_type_filter: str | None = None,
    ) -> set[str]:
        """Rapidly retrieve matching candidate files in O(1) time."""
        query_norm = query.strip().lower()
        if not query_norm:
            if language_filter and symbol_type_filter:
                return (
                    self.language_to_files.get(language_filter.strip().lower(), set())
                    & self.symbol_type_to_files.get(symbol_type_filter.strip().lower(), set())
                )
            if language_filter:
                return set(self.language_to_files.get(language_filter.strip().lower(), set()))
            if symbol_type_filter:
                return set(self.symbol_type_to_files.get(symbol_type_filter.strip().lower(), set()))
            return set()

        candidates: set[str] = set()

        # 1. Exact stem matches
        if query_norm in self.stem_to_files:
            candidates.update(self.stem_to_files[query_norm])

        # 2. Exact symbol matches
        if query_norm in self.exact_symbols:
            for fpath, _ in self.exact_symbols[query_norm]:
                candidates.add(fpath)

        # 3. Token matches
        tokens = [t for t in re.findall(r"[a-zA-Z0-9_]+", query_norm) if len(t) >= 2]
        for t in tokens:
            if t in self.token_to_files:
                candidates.update(self.token_to_files[t])

        # 4. Trigram / Substring candidate matching
        q_trigrams = _extract_trigrams(query_norm)
        if q_trigrams:
            matching_by_tri = [
                self.trigram_to_files[tri] for tri in q_trigrams if tri in self.trigram_to_files
            ]
            if matching_by_tri:
                for tri_set in matching_by_tri:
                    candidates.update(tri_set)

        # Apply filters
        if language_filter:
            lang_files = self.language_to_files.get(language_filter.strip().lower(), set())
            candidates &= lang_files

        if symbol_type_filter:
            sym_files = self.symbol_type_to_files.get(symbol_type_filter.strip().lower(), set())
            candidates &= sym_files

        return candidates
