# WIA — Workspace Intelligence Agent

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Package](https://img.shields.io/badge/PyPI-wia--agent-orange.svg)](https://pypi.org/project/wia-agent/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-185%20Passed-brightgreen.svg)](#-testing)
[![Version](https://img.shields.io/badge/Version-v0.1.5-blue.svg)](pyproject.toml)

**Workspace Intelligence Agent (WIA)** is a high-performance, graph-grounded workspace intelligence platform and codebase reasoning engine. It builds a deep, structured understanding of software repositories by parsing Abstract Syntax Trees (AST), building entity relationship graphs, processing Jupyter notebooks, and grounding AI reasoning in verified codebase evidence.

```text
Repository
    ↓
Files & Jupyter Notebooks
    ↓
Source AST & Structural Tokens
    ↓
Inverted Search Index & Symbol Graph
    ↓
Architectural Subsystem & Boundary Discovery
    ↓
WorkspaceRetriever & Dynamic Context Budgeting (7,500 Tokens)
    ↓
AI Reasoning Engine (NVIDIA NIM / OpenAI / Claude / Local)
    ↓
Grounded, Citation-Backed Structured Response
```

---

## ⚡ Key Highlights & Core Capabilities

1. **Evidence-Grounded AI Reasoning (Zero-Hallucination)**:
   Every answer is derived strictly from verified workspace source files, AST symbols, imports, call graphs, tests, and configuration manifests.
2. **High-Performance Inverted Search Index ($O(1)$ Symbol Lookup)**:
   Sub-millisecond token and symbol resolution across codebases with thousands of files and tens of thousands of symbols.
3. **Massive 7,500-Token LLM Context Budget**:
   Expanded retrieval budget with adaptive context reduction and retry for remote models with tight TPM/RPM quotas.
4. **Response Relevance Grader & Structured Formatting**:
   Validates responses for query relevance (0–100%), verified grounding citations, and consistent section breakdowns.
5. **Multi-Language AST & Structural Parser**:
   Deep parsing for Python (`ast`), plus multi-language regex fallback for TypeScript/JavaScript, Go, Rust, Java, C#, and C++.
6. **Jupyter Notebook (`.ipynb`) Understanding**:
   Full cell-level parsing (markdown hierarchy, code AST symbols, execution flow, output summaries) rather than opaque classification.
7. **High-Speed Relational Persistence**:
   SQLite persistence layer using atomic `executemany` batch operations and relational indices for instant queries.
8. **$O(1)$ Workspace Knowledge Graph**:
   Maintains directional dependency edges (`IMPORTS`, `DEFINES`, `CALLS`, `INHERITS`, `TESTS`) with $O(1)$ edge management.
9. **Multi-Tier Blast Radius & Impact Analysis**:
   Inspects direct callers, transitive dependents, affected unit tests, and dependent workflows before refactoring.
10. **Zero-Credential PyPI Package**:
    100% credential-safe. API keys are masked in logs and outputs. Deterministic commands run 100% offline without API keys.

---

## 🚀 Installation & Quickstart

### PyPI Installation
```bash
# Install WIA distribution from PyPI
pip install wia-agent

# Verify CLI installation
wia --version
wia doctor

# Or execute directly via Python module
python -m wia --version
```

### Local Development Setup
```bash
# 1. Clone repository
git clone https://github.com/Yashwanth112004/Workspace-Intelligence-Agent.git
cd Workspace-Intelligence-Agent

# 2. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install in editable mode with development dependencies
pip install -e ".[dev]"

# 4. Run automated test suite
pytest
```

---

## ⚙️ AI Provider Configuration

Deterministic commands (`wia index`, `wia status`, `wia summary`, `wia search`, `wia explain`, `wia impact`, `wia architecture`, `wia flow`, `wia diff`) run completely offline.

To enable AI reasoning for `wia ask`:

```bash
# Option A: Set via Environment Variable
export NVIDIA_API_KEY="nvapi-..."
# or for OpenAI: export OPENAI_API_KEY="sk-..."

# Option B: Set via WIA Configuration CLI
wia config --set-key "nvapi-..."
wia config --set-provider nvidia
wia config --set-model meta/llama-3.1-70b-instruct

# View active configuration
wia config --show
```

---

## 🛠️ Complete CLI Command Reference

| Command | Syntax | Description | Example |
|---|---|---|---|
| **`init`** | `wia init [<path>]` | Initialize `.wia/` workspace configuration and directory structure | `wia init ./` |
| **`index`** | `wia index [--workers N] [--force-reindex]` | Parallel incremental workspace indexing and graph construction | `wia index --workers 8` |
| **`status`** | `wia status` | Sub-millisecond incremental change detector and index status | `wia status` |
| **`summary`** | `wia summary` | Executive repository intelligence, language distribution, and tech stack | `wia summary` |
| **`search`** | `wia search "<term>" [--type <kind>]` | High-speed inverted index search for symbols, files, and docstrings | `wia search "SQLiteStore"` |
| **`explain`** | `wia explain <file_or_symbol>` | Comprehensive 13-section breakdown of source files, notebooks, or symbols | `wia explain wia/core/retrieval.py` |
| **`impact`** | `wia impact <file_or_symbol>` | Multi-tier refactoring impact analysis and blast radius | `wia impact WorkspaceIndex` |
| **`architecture`**| `wia architecture` | Subsystem boundaries, fan-in/fan-out, entry points, and dependency cycles | `wia architecture` |
| **`flow`** | `wia flow <entry_symbol>` | Forward call graph and execution tracing from entry symbol | `wia flow main` |
| **`diff`** | `wia diff` | Git status diffing and affected symbol analysis | `wia diff` |
| **`ask`** | `wia ask "<question>" [--offline]` | Evidence-grounded natural language codebase Q&A with line citations | `wia ask "Explain indexing flow"` |
| **`config`** | `wia config [--set-key <key>] [--set-provider <p>]` | Manage LLM providers, models, and API keys | `wia config --show` |
| **`auth`** | `wia auth --provider <p> --key <key>` | Authenticate and securely store AI provider credentials | `wia auth --provider openai --key sk-...` |
| **`doctor`** | `wia doctor` | Diagnostic health check for Python environment, SQLite, and index | `wia doctor` |
| **`report`** | `wia report [--output <path>]` | Generate interactive HTML repository intelligence report | `wia report --output report.html` |
| **`export`** | `wia export [--format okf\|markdown\|json]` | Export Open Knowledge Format documentation into `.wia/knowledge/` | `wia export --format okf` |
| **`serve`** | `wia serve [--port 8000]` | Start local FastAPI daemon for VS Code extension and external integrations | `wia serve --port 8000` |
| **`version`** | `wia version` | Print version information and build metadata | `wia version` |

---

## 🏗️ Architectural Flow & Subsystem Breakdown

```text
               WIA CLI Dispatcher (`wia/cli`)
                             │
                  Intent Classification & Routing
                             │
        ┌────────────────────┴────────────────────┐
        │                                         │
Deterministic Engine                      Reasoning Engine (`wia/llm`)
        │                                         │
 ┌──────┴──────────────────────────┐       ┌──────┴──────────────────────────┐
 │ IndexingService & DiscoveryPool │       │ WorkspaceRetriever              │
 │ InvertedSearchIndex (O(1))      │       │ Dynamic Context (7,500 Tokens)  │
 │ ASTParser & NotebookParser      │       │ ResponseRelevanceGrader         │
 │ SQLiteStore (executemany)       │       │ AIProvider Layer                │
 │ WorkspaceGraph (O(1) Edges)     │       │  ├─ NvidiaNimProvider           │
 │ ManifestParser (Single Walk)    │       │  ├─ OpenAIProvider              │
 │ SecretScanner & GitAnalyzer     │       │  └─ LocalReasoningProvider      │
 └─────────────────────────────────┘       └─────────────────────────────────┘
```

---

## 📁 Repository Structure

```text
Workspace-Intelligence-Agent/
├── wia/
│   ├── analyzers/
│   │   ├── code/                  # AST parser & Jupyter notebook parser
│   │   ├── dependency/            # Single-pass manifest parser & conflict detector
│   │   ├── git/                   # Git commit churn and hotspot analyzer
│   │   └── security/              # High-throughput secret & credential scanner
│   ├── cli/
│   │   ├── app.py                 # Lazy CLI dispatcher
│   │   ├── formatting.py          # Terminal styling & table formatting
│   │   └── commands/              # Individual subcommand implementations
│   ├── core/
│   │   ├── architecture.py        # Subsystem boundaries & cycle detector
│   │   ├── discovery.py           # Fast path slicing & directory traversal
│   │   ├── gitignore.py           # Memoized gitignore pattern matching
│   │   ├── index_model.py         # WorkspaceIndex & batch data structures
│   │   ├── inverted_index.py      # O(1) inverted search index
│   │   ├── retrieval.py           # Evidence-grounded WorkspaceRetriever
│   │   └── search_engine.py       # Relevance-scored search engine
│   ├── knowledge/
│   │   ├── graph.py               # Directional WorkspaceGraph with O(1) edge map
│   │   ├── embeddings.py          # Local SentenceTransformers embeddings
│   │   └── vector_store.py        # In-memory vector index
│   ├── llm/
│   │   ├── base.py                # AIProvider abstractions (NVIDIA, OpenAI, Local)
│   │   ├── reasoning.py           # ReasoningEngine & prompt synthesis
│   │   └── relevance.py           # Grounding & ResponseRelevanceGrader
│   ├── services/                  # IndexingService, ExplanationService, StatusService
│   ├── storage/                   # Relational SQLiteStore & serializers
│   └── utils/                     # HTML report generator & structured logging
├── tests/
│   ├── unit/                      # 60+ modular unit test suites
│   ├── integration/               # End-to-end indexing and pipeline tests
│   └── cli/                       # CLI subcommand execution tests
├── pyproject.toml                 # PEP 517/621 build definition
└── README.md                      # Comprehensive documentation
```

---

## 🔒 Security & Privacy Guarantees

* **Zero Hardcoded Credentials**: The distribution package contains no bundled credentials or private API tokens.
* **100% Secret Masking**: Keys in configuration files and console logs are automatically masked (`nvapi-...***`).
* **Offline Determinism**: Indexing, searching, impact analysis, AST parsing, and graph construction run 100% locally on your machine without external network requests.

---

## 🧪 Testing

Run the full automated test suite (185 unit, integration, and CLI tests):

```bash
# Run pytest test suite
pytest -v

# Run with test coverage report
pytest --cov=wia
```

---

## 📄 License

Distributed under the **Apache License 2.0**. See `LICENSE` for details.
