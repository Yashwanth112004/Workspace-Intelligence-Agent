# WIA — Workspace Intelligence Agent

> **AI-powered Workspace Intelligence and Codebase Reasoning Engine.**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![PyPI Distribution](https://img.shields.io/badge/pypi-wia--agent-green.svg)](https://pypi.org/project/wia-agent/)
[![CLI Tool](https://img.shields.io/badge/cli-WIA-green.svg)](https://github.com/Yashwanth112004/Workspace-Intelligence-Agent)
[![Test Suite](https://img.shields.io/badge/tests-174%20passed-success.svg)](https://github.com/Yashwanth112004/Workspace-Intelligence-Agent/tree/main/tests)

WIA (Workspace Intelligence Agent) is a **CLI-first codebase reasoning engine and workspace intelligence platform**. It parses source structures, analyzes abstract syntax trees (AST), constructs rich entity relationship graphs, processes Jupyter notebooks, and grounds AI reasoning in verified codebase evidence.

```text
Repository
    ↓
Files & Notebooks
    ↓
Source Structure & AST
    ↓
Symbols & Base Classes
    ↓
Dependencies & Call Graphs
    ↓
Architecture & Boundaries
    ↓
WorkspaceRetriever & Context Budgeting
    ↓
AI Reasoning Engine (NVIDIA NIM / Provider Abstraction)
    ↓
Evidence-Grounded Answer with Line Citations
```

---

## ⚡ Core Principles & Capabilities

1. **Evidence-Grounded Reasoning (Zero-Hallucination Principle)**:
   Every explanation and reasoning response is derived strictly from verified workspace source files, AST symbols, imports, call graphs, tests, and configurations. Missing evidence is explicitly stated rather than replaced with generic template statements.
2. **Provider-Independent AI Architecture**:
   Modular AI provider abstraction (`AIProvider`) supporting NVIDIA NIM (`NvidiaNimProvider`), OpenAI (`OpenAIProvider`), and deterministic offline local reasoning (`LocalReasoningProvider`).
3. **Strict Credential Security**:
   The PyPI package contains **no bundled credentials**. Users supply their own API keys via environment variables (e.g. `NVIDIA_API_KEY`) or `wia config`. Secrets are 100% masked in logs and CLI outputs.
4. **Jupyter Notebook Understanding (`.ipynb`)**:
   Full cell-level parsing (markdown sections, code cells, imports, functions/classes, execution flow, output summaries) rather than classifying notebooks as "Unknown".
5. **Parallel & Incremental Indexing Engine**:
   High-speed multi-worker indexing (`ThreadPoolExecutor`) with SHA-256 hash delta matching, failure isolation on malformed files, and measurable performance duration metrics.
6. **Multi-Tier Impact Analysis**:
   Inspects direct dependents, indirect (transitive) dependents, symbol callers, importers, affected tests, affected examples/notebooks, and dependency paths.
7. **Granular File & Tech Stack Classification**:
   14 functional file categories (Source Code, Notebook, Test, CI/CD, Build, Dependency Lock, Documentation, Configuration, Data, Asset, Script, Binary, Generated, Unsupported).

---

## 💻 Installation & Quickstart

### 1. Installation

Install **`wia-agent`** from PyPI:

```bash
pip install wia-agent
```

Verify the installation:

```bash
wia --version
wia doctor
```

### 2. Configure AI Provider (Optional)

Deterministic features (`index`, `summary`, `search`, `explain`, `impact`) run completely offline without an API key. To enable LLM reasoning for `wia ask`:

```bash
# Option A: Set via Environment Variable
export NVIDIA_API_KEY="nvapi-..."

# Option B: Set via WIA Configuration CLI
wia config --set-key "nvapi-..."
wia config --set-provider nvidia
wia config --set-model meta/llama-3.1-70b-instruct
```

View active configuration:

```bash
wia config --show
```

---

## 🛠️ CLI Command Reference

### 1. `wia index` — Parallel & Incremental Workspace Indexing

Crawls the workspace, respects `.gitignore`, detects languages & file types, computes SHA-256 hashes, parses AST symbols, builds the `WorkspaceGraph`, and scans for security leaks.

```bash
# Standard indexing
wia index

# Index with 8 parallel worker threads
wia index --workers 8

# Force complete re-indexing
wia index --force-reindex
```

### 2. `wia summary` — Structured Repository Intelligence

Generates a comprehensive summary separating factual statistics from architectural intelligence.

```bash
wia summary
```

* **Repository Facts**: Discovered vs indexed files, languages breakdown, file types (Source, Notebooks, Tests, CI/CD, Manifests), total classes and functions.
* **Repository Intelligence**: Project purpose, categorized technology stack, entry points, and subsystem architecture.

### 3. `wia search` — Relevance-Aware Workspace Search

Queries file paths, exact symbols, functions, classes, and docstrings, providing exact line numbers and relevance explanations.

```bash
wia search Application
wia search "state persistence"
wia search --type class --language Python
```

### 4. `wia explain` — Code & Notebook Explanation

Produces 13-section technical breakdowns for source files, Jupyter notebooks, or individual symbols.

```bash
# Explain a source file
wia explain wia/core/retrieval.py

# Explain a Jupyter notebook
wia explain notebooks/analysis.ipynb

# Explain a specific function or class
wia explain WorkspaceRetriever
```

### 5. `wia impact` — Multi-Tier Refactoring Impact Analysis

Analyzes blast radius, direct callers, indirect transitive dependents, affected unit tests, and affected example workflows.

```bash
wia impact wia/core/index_model.py
wia impact WorkspaceIndex
```

### 6. `wia ask` — Evidence-Grounded AI Reasoning

Asks natural-language questions about codebase architecture, execution flow, component relationships, or debugging.

```bash
wia ask "Explain the project"
wia ask "How does application execution work?"
wia ask "What depends on WorkspaceRetriever?"
wia ask "Where are unit tests located and how is indexing tested?"
```

---

## 🏗️ Architecture

```text
               WIA CLI (Click)
                      │
           Intent Classification & Routing
                      │
       ┌──────────────┴──────────────┐
       │                             │
Deterministic Engine           Reasoning Engine
       │                             │
 ┌─────┴──────────────┐       ┌──────┴──────────────┐
 │ IndexingService    │       │ WorkspaceRetriever  │
 │ ASTParser          │       │ Context Budgeting   │
 │ NotebookParser     │       │ Evidence Assembly   │
 │ WorkspaceGraph     │       │ AIProvider Layer    │
 │ ImpactAnalyzer     │       │  ├─ NvidiaNim       │
 │ SearchEngine       │       │  ├─ OpenAI          │
 └────────────────────┘       │  └─ LocalReasoning  │
                              └─────────────────────┘
```

---

## 🔒 Security & Privacy

* **Zero Hardcoded Secrets**: No credentials or private tokens are packaged or committed.
* **100% Secret Masking**: Any API keys in environment or configuration files are masked (`nvapi-...***`).
* **Offline Determinism**: Indexing, searching, impact analysis, and graph building run 100% locally on your machine.

---

## 🧪 Testing

Run the full automated test suite (174+ unit, integration, and CLI tests):

```bash
python -m pytest -v
```

---

## 📄 License

Apache License 2.0. Distributed as `wia-agent` on PyPI.
