# 🏗️ Workspace Intelligence Agent (WIA) - System Architecture

Workspace Intelligence Agent (WIA) is an AI-powered code intelligence platform designed for deep codebase ingestion, multi-language AST code parsing, bottom-up hierarchical workspace summarization, and interactive context-aware code Q&A.

WIA is delivered as a **High-Performance Python Core Engine & CLI Tool (`wia`)** and a **Native VS Code Extension**.

---

## 📐 High-Level Architecture

```
[ GitHub Repository URL / Local Directory ]
                   │
                   ▼
  ┌────────────────────────────────────────────────────────┐
  │ 1. Repository Ingestion & Secret Safety                │
  │    • Scans folders / clones Git repos                  │
  │    • Filters noise, SHA256 file hashing                │
  │    • Sensitive file detection & secret redaction       │
  └────────────────────────┬───────────────────────────────┘
                           │
                           ▼
  ┌────────────────────────────────────────────────────────┐
  │ 2. Extensible Multi-Language Parser Plugins            │
  │    • Python AST (classes, methods, docstrings, calls)  │
  │    • TypeScript / JavaScript (imports, classes, fns)   │
  │    • Go, Rust, Java, C/C++, C# structural extractors   │
  │    • API endpoint & unit test discovery                │
  └────────────────────────┬───────────────────────────────┘
                           │
                           ▼
  ┌────────────────────────────────────────────────────────┐
  │ 3. Workspace Knowledge Model & Code Knowledge Graph    │
  │    • Entities: Repository, Subsystem, File, Symbol...  │
  │    • Explicit Edges: CONTAINS, DEFINES, IMPORTS, CALLS │
  │    • Provenance (DETERMINISTIC_FACT vs LLM_SUMMARY)    │
  └────────────────────────┬───────────────────────────────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
  ┌──────────────────┐ ┌───────────────┐ ┌───────────────────┐
  │ 4A. Hierarchical │ │ 4B. Semantic  │ │ 4C. Portable OKF  │
  │     Summaries    │ │     Vector &  │ │     Knowledge     │
  │     (5 Levels)   │ │     BM25 RAG  │ │     Export        │
  └─────────┬────────┘ └───────┬───────┘ └─────────┬─────────┘
            │                  │                   │
            └──────────────────┼───────────────────┘
                               │
                               ▼
  ┌────────────────────────────────────────────────────────┐
  │ 5. Hybrid Retrieval Engine & Query Planner             │
  │    • Symbol lookup + BM25 + Vector + Graph Traversal   │
  │    • Intent classification (Architecture, Flow, Impact)│
  │    • Structured Context Builder with Line Citations    │
  └────────────────────────┬───────────────────────────────┘
                           │
                           ▼
  ┌────────────────────────────────────────────────────────┐
  │ 6. NVIDIA NOOA WIA Code Understanding Agent            │
  │    • Tool-augmented reasoning over Knowledge Graph     │
  │    • Flow tracing, impact analysis, health audits      │
  │    • Model-agnostic LLM client (Gemini/OpenAI/Claude)  │
  └────────────────────────┬───────────────────────────────┘
                           │
            ┌──────────────┴──────────────┐
            ▼                             ▼
 [ WIA Command-Line Interface (CLI) ] [ Native VS Code Extension ]
```
