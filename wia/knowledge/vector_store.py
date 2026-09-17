"""Persistent local vector store for semantic code chunk retrieval."""

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from wia.core.chunker import SemanticChunk
from wia.knowledge.embeddings import EmbeddingService


@dataclass
class VectorRecord:
    """Record entry storing semantic chunk metadata and embedding vector."""

    chunk_id: str
    file_path: str
    content: str
    chunk_type: str
    symbol_name: str
    line_start: int
    line_end: int
    content_hash: str
    vector: list[float]

    def to_dict(self) -> dict:
        """Convert vector record to serializable dictionary."""
        return asdict(self)


class VectorStore:
    """Persistent vector store supporting cosine similarity search and incremental updates."""

    def __init__(self, storage_path: str | Path | None = None, embedding_service: EmbeddingService | None = None):
        self.storage_path = Path(storage_path) if storage_path else None
        self.embedding_service = embedding_service or EmbeddingService()
        self.records: dict[str, VectorRecord] = {}
        if self.storage_path and self.storage_path.exists():
            self.load()

    @staticmethod
    def cosine_similarity(v1: list[float], v2: list[float]) -> float:
        """Compute cosine similarity between two float vectors."""
        if len(v1) != len(v2) or not v1:
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        n1 = math.sqrt(sum(a * a for a in v1))
        n2 = math.sqrt(sum(b * b for b in v2))
        if n1 == 0 or n2 == 0:
            return 0.0
        return dot / (n1 * n2)

    def add_chunk(self, chunk: SemanticChunk) -> VectorRecord:
        """Add or update a semantic chunk with generated vector embedding."""
        vec = self.embedding_service.generate_embedding(chunk.content)
        rec = VectorRecord(
            chunk_id=chunk.chunk_id,
            file_path=chunk.file_path,
            content=chunk.content,
            chunk_type=chunk.chunk_type,
            symbol_name=chunk.symbol_name,
            line_start=chunk.line_start,
            line_end=chunk.line_end,
            content_hash=chunk.content_hash,
            vector=vec,
        )
        self.records[chunk.chunk_id] = rec
        return rec

    def search_similarity(
        self, query: str, top_k: int = 5, file_filter: str | None = None
    ) -> list[tuple[VectorRecord, float]]:
        """Search vector store by semantic cosine similarity against query embedding."""
        query_vec = self.embedding_service.generate_embedding(query)
        scored: list[tuple[VectorRecord, float]] = []

        for rec in self.records.values():
            if file_filter and file_filter.lower() not in rec.file_path.lower():
                continue
            sim = self.cosine_similarity(query_vec, rec.vector)
            scored.append((rec, round(sim, 4)))

        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_k]

    def remove_file_chunks(self, file_path: str) -> None:
        """Remove all indexed vector chunks belonging to target file path."""
        target_p = str(file_path).replace("\\", "/")
        keys_to_remove = [k for k, r in self.records.items() if r.file_path == target_p]
        for k in keys_to_remove:
            del self.records[k]

    def save(self) -> None:
        """Persist vector records to JSON storage file."""
        if not self.storage_path:
            return
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {k: r.to_dict() for k, r in self.records.items()}
        self.storage_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self) -> None:
        """Load vector records from JSON storage file."""
        if not self.storage_path or not self.storage_path.exists():
            return
        try:
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))
            self.records = {k: VectorRecord(**v) for k, v in data.items()}
        except Exception:
            self.records = {}
