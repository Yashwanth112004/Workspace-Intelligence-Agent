import logging
from typing import List, Dict, Any, Tuple, Optional
from app.models.workspace import VectorChunk, WorkspaceSummary, ASTSymbol, FileNode
from app.services.rag.vector_store import VectorSearchStore
from app.services.graph.code_graph import CodeKnowledgeGraph

logger = logging.getLogger("wia.retrieval.hybrid")

class HybridRetriever:
    """
    Unified Hybrid Retrieval Engine combining:
    1. Symbol Lookup (Exact/Fuzzy)
    2. Lexical & Exact Token Match
    3. Semantic Vector Search
    4. Graph Traversal (Callers/Callees/Dependencies)
    5. Hierarchical Summary Retrieval
    """

    @staticmethod
    def retrieve(
        query: str,
        chunks: List[VectorChunk],
        summaries: List[WorkspaceSummary],
        symbols: List[ASTSymbol],
        graph: Optional[CodeKnowledgeGraph] = None,
        top_k: int = 8
    ) -> Dict[str, Any]:
        retrieved_chunks = []
        retrieved_symbols = []
        retrieved_summaries = []
        graph_evidence = []
        citations = []

        q_terms = set(query.lower().split())

        # 1. Symbol Retrieval
        matched_symbols = []
        for s in symbols:
            if s.name.lower() in q_terms or any(t in s.name.lower() for t in q_terms if len(t) > 3):
                matched_symbols.append(s)
                retrieved_symbols.append({
                    "name": s.name,
                    "type": s.symbol_type,
                    "file_path": s.file_path,
                    "line": s.start_line,
                    "signature": s.signature,
                    "docstring": s.docstring
                })

        # 2. Graph Traversal Retrieval
        if graph and matched_symbols:
            for s in matched_symbols[:3]:
                callers = graph.find_callers(s.name)
                callees = graph.find_callees(s.name)
                if callers:
                    graph_evidence.append(f"Callers of `{s.name}`: {', '.join([c[0].name for c in callers[:4]])}")
                if callees:
                    graph_evidence.append(f"`{s.name}` calls: {', '.join([c[0].name for c in callees[:4]])}")

        # 3. Hierarchical Summary Retrieval
        for sm in summaries:
            if sm.level == "repository":
                retrieved_summaries.append({
                    "level": sm.level,
                    "target": sm.target_path or "root",
                    "name": sm.name,
                    "text": sm.summary_text
                })
                continue
            sm_terms = set(sm.summary_text.lower().split()) | set(sm.name.lower().split())
            if len(q_terms & sm_terms) >= 2:
                retrieved_summaries.append({
                    "level": sm.level,
                    "target": sm.target_path or "root",
                    "name": sm.name,
                    "text": sm.summary_text
                })

        # 4. Semantic & Lexical Vector Retrieval
        vector_matches = VectorSearchStore.search(chunks, query, top_k=top_k)
        for chunk, score in vector_matches:
            retrieved_chunks.append({
                "content": chunk.content,
                "file_path": chunk.file_path,
                "chunk_type": chunk.chunk_type,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "score": round(score, 3)
            })
            citations.append({
                "file_path": chunk.file_path,
                "chunk_type": chunk.chunk_type,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "score": round(score, 3),
                "evidence_type": "semantic_and_lexical"
            })

        return {
            "query": query,
            "chunks": retrieved_chunks,
            "symbols": retrieved_symbols,
            "summaries": retrieved_summaries[:4],
            "graph_evidence": graph_evidence,
            "citations": citations
        }
