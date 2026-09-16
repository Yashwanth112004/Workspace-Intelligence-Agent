# 📊 Bottom-Up Hierarchical Workspace Summarization Engine

The Hierarchical Summarizer generates deep, multi-tiered contextual summaries of a codebase using a 5-level bottom-up Directed Acyclic Graph (DAG) aggregation approach.

---

## 🎯 The 5 Summarization Levels

```
                     ┌────────────────────────────────┐
                     │   Level 5: Repository Overview │
                     └────────────────┬───────────────┘
                                      ▲
                     ┌────────────────┴───────────────┐
                     │  Level 4: Parent Folder Sums   │
                     └────────────────┬───────────────┘
                                      ▲
                     ┌────────────────┴───────────────┐
                     │   Level 3: Child Folder Sums   │
                     └────────────────┬───────────────┘
                                      ▲
                     ┌────────────────┴───────────────┐
                     │     Level 2: File Summaries    │
                     └────────────────┬───────────────┘
                                      ▲
                     ┌────────────────┴───────────────┐
                     │   Level 1: Function Summaries  │
                     └────────────────────────────────┘
```

---

## 🔄 Bottom-Up Execution Process

### 1. Level 1: Function & Method Summaries
- **Input**: Extracted AST symbols (function name, arguments, docstring, internal function calls).
- **Process**: Formulates concise operational descriptions for each individual function/method.
- **Output**: Granular summaries stored with symbol line numbers.

### 2. Level 2: File & Module Summaries
- **Input**: File language, LOC count, extracted imports, class definitions, and Level 1 function summaries.
- **Process**: LLM synthesizes module-level responsibility, public exports, and dependencies.
- **Output**: 2-3 sentence overview for each source code file.

### 3. Level 3: Child Folder Summaries
- **Input**: Level 2 file summaries of all files residing directly in leaf/deepest directories (e.g. `backend/app/services/parser/`).
- **Process**: Synthesizes the collective functional purpose of the leaf directory.
- **Output**: Child directory component summary.

### 4. Level 4: Parent Folder Summaries
- **Input**: Level 3 child directory summaries and top-level folder files.
- **Process**: Merges subsystem summaries into a coherent domain description (e.g. `backend/app/services/`).
- **Output**: Parent subsystem architecture summary.

### 5. Level 5: Repository Architecture Overview
- **Input**: Tech stack breakdown, total LOC, entry points (`main.py`, `App.tsx`), dependency manifests, and Level 4 root folder summaries.
- **Process**: Generates the complete high-level workspace architectural overview:
  1. Primary mission & purpose of the repository.
  2. Core technology stack and architectural layers.
  3. End-to-end data flow and component interactions.

---

## 💡 Key Benefits
- **Zero Token Loss**: Summaries roll up hierarchically, allowing million-line codebases to be compressed into high-density architectural summaries without blowing LLM context windows.
- **Bi-Directional Retrieval**: RAG queries can zoom into fine-grained function citations or zoom out to high-level architecture overviews.
