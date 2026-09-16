import logging
import math
import re
from typing import List, Dict, Any, Tuple
from app.models.workspace import VectorChunk, WorkspaceSummary, FileNode, ASTSymbol

logger = logging.getLogger("wia.rag")

# Try importing sentence_transformers, fallback gracefully to TF-IDF vectorizer if needed
HAS_ST = False
try:
    from sentence_transformers import SentenceTransformer
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    HAS_ST = True
    logger.info("SentenceTransformers initialized for vector embeddings.")
except Exception as e:
    logger.info(f"SentenceTransformers not loaded ({e}). Using TF-IDF fallback for embeddings.")

class VectorSearchStore:
    """RAG Vector Store for Code Chunks and Hierarchical Summaries."""

    @staticmethod
    def build_index(repo_id: str, nodes: List[FileNode], summaries: List[WorkspaceSummary], symbols: List[ASTSymbol]) -> List[VectorChunk]:
        chunks: List[VectorChunk] = []

        # 1. Index Hierarchical Summaries
        for s in summaries:
            content = f"[{s.level.upper()} SUMMARY] Path: {s.target_path or 'Repository Root'}\nName: {s.name}\nSummary: {s.summary_text}"
            emb = VectorSearchStore._compute_embedding(content)
            chunks.append(VectorChunk(
                repo_id=repo_id,
                file_path=s.target_path or "root",
                chunk_type="summary",
                content=content,
                embedding=emb
            ))

        # 2. Index AST Symbols / Functions
        for sym in symbols:
            if sym.symbol_type in ("function", "class"):
                content = f"[SYMBOL] File: {sym.file_path} | Type: {sym.symbol_type} | Name: {sym.name} | Signature: {sym.signature or sym.name}\nDocstring: {sym.docstring or 'N/A'}\nCalls: {', '.join(sym.calls)}"
                emb = VectorSearchStore._compute_embedding(content)
                chunks.append(VectorChunk(
                    repo_id=repo_id,
                    file_path=sym.file_path,
                    chunk_type="function",
                    content=content,
                    start_line=sym.start_line,
                    end_line=sym.end_line,
                    embedding=emb
                ))

        # 3. Index File Content Chunks
        for node in nodes:
            if not node.is_dir and node.loc_count > 0:
                try:
                    with open(node.path, "r", encoding="utf-8", errors="ignore") as f:
                        code = f.read()
                    lines = code.splitlines()
                    # Chunk every 40 lines
                    chunk_size = 40
                    for i in range(0, len(lines), chunk_size):
                        chunk_lines = lines[i:i+chunk_size]
                        chunk_text = "\n".join(chunk_lines)
                        content = f"[CODE CHUNK] File: {node.relative_path} (Lines {i+1}-{i+len(chunk_lines)})\n{chunk_text}"
                        emb = VectorSearchStore._compute_embedding(content)
                        chunks.append(VectorChunk(
                            repo_id=repo_id,
                            file_path=node.relative_path,
                            chunk_type="code",
                            content=content,
                            start_line=i+1,
                            end_line=i+len(chunk_lines),
                            embedding=emb
                        ))
                except Exception as e:
                    logger.debug(f"Failed to chunk code file {node.path}: {e}")

        return chunks

    @staticmethod
    def search(chunks: List[VectorChunk], query: str, top_k: int = 5) -> List[Tuple[VectorChunk, float]]:
        """Retrieves top_k relevant vector chunks for a natural language query."""
        if not chunks:
            return []

        query_emb = VectorSearchStore._compute_embedding(query)
        scored_chunks: List[Tuple[VectorChunk, float]] = []

        for chunk in chunks:
            sim = VectorSearchStore._cosine_similarity(query_emb, chunk.embedding)
            # Text term match boost
            terms = query.lower().split()
            content_lower = chunk.content.lower()
            term_matches = sum(1 for t in terms if len(t) > 2 and t in content_lower)
            boost = 0.1 * term_matches

            scored_chunks.append((chunk, sim + boost))

        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return scored_chunks[:top_k]

    @staticmethod
    def _compute_embedding(text: str) -> List[float]:
        if HAS_ST:
            try:
                emb = embedder.encode(text, convert_to_numpy=True).tolist()
                return emb
            except Exception:
                pass

        # TF-IDF / Term Frequency Hash Embedding Fallback
        words = re.findall(r"\w+", text.lower())
        vec = [0.0] * 64
        for w in words:
            idx = abs(hash(w)) % 64
            vec[idx] += 1.0
        norm = math.sqrt(sum(v*v for v in vec)) or 1.0
        return [v / norm for v in vec]

    @staticmethod
    def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        n1 = math.sqrt(sum(a * a for a in v1)) or 1.0
        n2 = math.sqrt(sum(b * b for b in v2)) or 1.0
        return dot / (n1 * n2)
