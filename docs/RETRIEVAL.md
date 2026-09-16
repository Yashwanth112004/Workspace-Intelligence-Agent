# 🔍 WIA Hybrid Retrieval Engine

WIA replaces naive vector-only RAG with a multi-strategy **Hybrid Retrieval Engine** combining 5 specialized retrieval pathways.

---

## ⚡ Multi-Strategy Retrieval Pipeline

```
                              User Question
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    Query Planner     │
                         └──────────┬───────────┘
                                    │
    ┌───────────────┬───────────────┼───────────────┬───────────────┐
    ▼               ▼               ▼               ▼               ▼
1. Symbol       2. Lexical      3. Semantic     4. Graph        5. Summary
   Lookup          BM25            Vector          Traversal       Retrieval
(Exact Match)   (Keyword Boost) (Dense Embed)   (Callers/Deps)  (5 Hierarchy)
    │               │               │               │               │
    └───────────────┴───────────────┼───────────────┴───────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Context Builder    │
                         │(Deduplication & Budget│
                         └──────────┬───────────┘
                                    │
                                    ▼
                         Structured LLM Context
```

---

## 🎯 Retrieval Strategies

1. **Symbol Retrieval**: Exact and substring lookup against indexed AST symbols (functions, classes, interfaces).
2. **Lexical Retrieval**: BM25 term-frequency match for identifiers, imports, and exact code signatures.
3. **Semantic Vector Retrieval**: Cosine similarity using `all-MiniLM-L6-v2` embeddings over 40-line code chunks and summaries.
4. **Graph Traversal Retrieval**: Extracts callers, callees, and file import chains from the Code Knowledge Graph.
5. **Hierarchical Summary Retrieval**: Injects architectural subsystem summaries matching question scope.
