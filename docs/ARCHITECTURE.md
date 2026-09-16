# 🏗️ Workspace Intelligence Agent (WIA) - System Architecture

Workspace Intelligence Agent (WIA) is an AI-powered multi-agent platform designed for deep codebase ingestion, AST code understanding, bottom-up hierarchical workspace summarization, and context-aware code Q&A.

---

## 📐 High-Level Architecture

```
[ GitHub Repository URL / Local Directory ]
                   │
                   ▼
  ┌────────────────────────────────────────────────────────┐
  │ 1. Repository Ingestion & Crawler Engine               │
  │    • Clones git repos / scans directory recursively    │
  │    • Excludes .git, node_modules, .venv, binaries      │
  │    • Detects languages, LOC, dependencies, configs     │
  └────────────────────────┬───────────────────────────────┘
                           │
                           ▼
  ┌────────────────────────────────────────────────────────┐
  │ 2. Multi-Language AST & Structural Parser              │
  │    • Python AST (classes, methods, docstrings, calls)  │
  │    • TypeScript / JavaScript (imports, classes, fns)   │
  │    • Go, Rust, Java, C/C++, C# structural extractors   │
  └────────────────────────┬───────────────────────────────┘
                           │
                           ▼
  ┌────────────────────────────────────────────────────────┐
  │ 3. Bottom-Up Hierarchical Summarizer (5 Levels)        │
  │    • Level 1: Function / Method Summaries              │
  │    • Level 2: File / Module Summaries                  │
  │    • Level 3: Child Folder Summaries                   │
  │    • Level 4: Parent Folder Summaries                  │
  │    • Level 5: Repository Architecture Overview         │
  └────────────────────────┬───────────────────────────────┘
                           │
                           ▼
  ┌────────────────────────────────────────────────────────┐
  │ 4. RAG Vector Embedding & Retrieval Engine             │
  │    • SentenceTransformers (`all-MiniLM-L6-v2`) / TF-IDF│
  │    • Dense Cosine Similarity + BM25 Term Boost         │
  │    • Indexes Code Chunks, Symbols & Summaries          │
  └────────────────────────┬───────────────────────────────┘
                           │
                           ▼
  ┌────────────────────────────────────────────────────────┐
  │ 5. NVIDIA NOOA WIA Code Understanding Agent            │
  │    • Multi-turn technical context assembly             │
  │    • Exact file path & line number citations           │
  │    • Model-agnostic LLM client (Gemini/OpenAI/Claude)  │
  └────────────────────────┬───────────────────────────────┘
                           │
            ┌──────────────┴──────────────┐
            ▼                             ▼
   [ FastAPI REST API ]          [ WIA Command-Line CLI ]
            │
            ▼
 [ React + TypeScript Dashboard ]
```

---

## 🧩 Core Components

### 1. Ingestion Engine (`backend/app/services/ingestion/crawler.py`)
- Traverses codebases while pruning standard noise directories (`.git`, `node_modules`, `build`, `.venv`, cache).
- Classifies files by language extension and computes exact Lines of Code (LOC) and byte sizes.
- Extracts package dependency manifests (`package.json`, `requirements.txt`, `pyproject.toml`, `Cargo.toml`, `go.mod`).
- Detects configuration files and system entry points (`main.py`, `App.tsx`, `index.ts`, `server.js`).

### 2. AST Parser Engine (`backend/app/services/parser/ast_parser.py`)
- **Python**: Uses native `ast` library to extract class definitions, inheritance hierarchies, synchronous & asynchronous functions, docstrings, arguments, decorators, imports with aliases, and function call graphs.
- **JavaScript & TypeScript**: Extracts classes, constructors, methods, arrow functions, exported components, imports, and require statements.
- **Go**: Identifies package declarations, structs, interfaces, method receivers `func (r *Receiver) Method()`, and standalone functions.
- **Rust**: Extracts `struct`, `enum`, `trait`, and `pub fn` declarations.
- **C/C++/Java/C#**: Extracts classes, interfaces, method signatures, access modifiers, and header includes.

### 3. Hierarchical Summarization (`backend/app/services/summarizer/hierarchical.py`)
- Employs a deterministic **bottom-up DAG traversal**:
  1. **Functions**: Generates functional purpose summaries from signatures, parameters, docstrings, and call chains.
  2. **Files**: Synthesizes function summaries and structural exports into 2-3 sentence module overviews.
  3. **Child Folders**: Aggregates summaries of files within deepest directories.
  4. **Parent Folders**: Aggregates child folder summaries up the directory tree.
  5. **Repository**: Synthesizes top-level folder summaries, tech stack metrics, entry points, and dependencies into an overall architecture summary.

### 4. RAG Vector Search Store (`backend/app/services/rag/vector_store.py`)
- Chunks source code at 40-line overlapping intervals, AST symbols, and hierarchical summaries.
- Computes dense vector embeddings using `all-MiniLM-L6-v2` with deterministic TF-IDF hashing fallback when offline.
- Performs cosine similarity matching with lexical term-frequency boosting for exact symbol matching.

### 5. NVIDIA NOOA Agent (`backend/app/agent/nooa_agent.py`)
- Formulates structured context using repository metadata, high-level architecture overview, and retrieved code chunks.
- Returns comprehensive technical explanations accompanied by precise citation objects containing `file_path`, `start_line`, `end_line`, and `score`.

---

## 🗄️ Database Schema

Implemented via `SQLModel` with SQLite / PostgreSQL support:
- `Repository`: Top-level metadata, status, LOC, tech stack, entry points, dependencies.
- `FileNode`: Hierarchical tree representation of files and directories with depth, parent relations, and LOC.
- `ASTSymbol`: Extracted functions, classes, imports, signatures, parameters, calls, and line ranges.
- `WorkspaceSummary`: 5-level summaries (`repository`, `parent_folder`, `child_folder`, `file`, `function`).
- `VectorChunk`: Embeddable text chunks with vector representations for RAG search.
