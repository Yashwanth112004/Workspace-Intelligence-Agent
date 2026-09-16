# 🧠 Workspace Intelligence Agent (WIA)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![VS Code Extension](https://img.shields.io/badge/VS_Code_Extension-Ready-007ACC.svg)](https://code.visualstudio.com/)
[![Tests](https://img.shields.io/badge/Tests-pytest-brightgreen.svg)](https://pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Workspace Intelligence Agent (WIA)** is an AI-powered code intelligence platform designed for deep codebase ingestion, multi-language AST code parsing, bottom-up hierarchical workspace summarization, code knowledge graph building, execution flow tracing, change impact analysis, and interactive context-aware code Q&A with exact source citations.

WIA is delivered as a **High-Performance Python Core Engine & CLI Tool (`wia`)** and a **Native VS Code Extension**.

---

## 📑 Table of Contents

- [🏗 System Architecture & Pipeline](#-system-architecture--pipeline)
- [⚡ Technology Stack](#-technology-stack)
- [📁 Repository Directory Structure](#-repository-directory-structure)
- [💻 Comprehensive CLI Guide](#-comprehensive-cli-guide)
- [🧩 Native VS Code Extension](#-native-vs-code-extension)
- [🚀 Setup & Execution Guide](#-setup--execution-guide)
- [📡 Core REST API Reference](#-core-rest-api-reference)
- [📊 5-Level Hierarchical Summarization Engine](#-5-level-hierarchical-summarization-engine)
- [🤖 NVIDIA NOOA Agent & Hybrid Retrieval](#-nvidia-nooa-agent--hybrid-retrieval)
- [📦 Open Knowledge Format (OKF) Export](#-open-knowledge-format-okf-export)
- [⚙️ Configuration & Environment Variables](#️-configuration--environment-variables)
- [🧪 Running Automated Tests](#-running-automated-tests)
- [📚 Documentation Index](#-documentation-index)

---

## 🏗 System Architecture & Pipeline

```
GitHub Repository URL or Local Directory
                  │
                  ▼
   1. Repository Ingestion & Secret Safety
   ├─ Scans local folder or clones GitHub repository
   ├─ Ignores noise (.git, node_modules, .venv, binaries)
   ├─ Computes SHA256 file hashes for incremental indexing
   └─ Redacts credentials, tokens, and private keys
                  │
                  ▼
   2. Extensible Multi-Language Parser Plugins
   ├─ Python AST (classes, async functions, docstrings, calls)
   ├─ TypeScript / JavaScript (classes, interfaces, arrow fns)
   ├─ Go, Rust, Java, C/C++, C# structural extractors
   └─ API endpoint & unit test discovery
                  │
                  ▼
   3. Workspace Knowledge Model & Code Knowledge Graph
   ├─ Entities: Repository, Subsystem, File, Symbol, Function, Class
   ├─ Edges: CONTAINS, DEFINES, IMPORTS, CALLS, INHERITS, REFERENCES
   └─ Strict Provenance (DETERMINISTIC_FACT vs LLM_SUMMARY)
                  │
                  ▼
   4. Hybrid Retrieval Engine & Query Planner
   ├─ Symbol Lookup + Lexical BM25 + Semantic Vector + Graph Traversal
   ├─ Intent Planner: Architecture, Flow, Impact, Onboarding, Health
   └─ Structured Context Builder with Line-Number Citations
                  │
                  ▼
   5. NVIDIA NOOA WIA Code Understanding Agent
   ├─ Architecture explanation & component synthesis
   ├─ Execution call flow tracing (`trace_flow`)
   ├─ Dependency ripple impact analysis (`analyze_impact`)
   └─ Developer onboarding walkthroughs & health audits
                  │
                  ▼
      ┌───────────┴───────────┐
      ▼                       ▼
 [ WIA CLI Tool ]   [ Native VS Code Extension ]
```

---

## ⚡ Technology Stack

| Layer | Technologies |
|---|---|
| **Core Engine** | Python 3.10+, FastAPI, SQLModel / SQLAlchemy, Pydantic v2, Uvicorn |
| **CLI Tool** | Python `argparse`, `sys.stdout` UTF-8 console output handler |
| **VS Code Extension** | TypeScript, VS Code Extensibility API, TreeView Providers, Webview API |
| **Agent Framework** | NVIDIA NOOA (NeMo Orchestrated Object Agent Architecture) |
| **Code Intelligence** | Extensible Plugin System: Python `ast`, TS/JS, Go, Rust, C-family plugins |
| **Knowledge Graph** | Relational & In-Memory Graph with BFS call tracing & impact analysis |
| **Hybrid Retrieval** | SentenceTransformers (`all-MiniLM-L6-v2`) + BM25 Lexical + Graph Walks |
| **AI Providers** | Model-Agnostic (Google Gemini, OpenAI, Anthropic Claude, NVIDIA Nemotron) |
| **Persistence** | PostgreSQL support with automatic SQLite (`wia.db`) fallback |
| **Testing** | `pytest` test suite with 100% pass rate |

---

## 📁 Repository Directory Structure

```
Workspace-Intelligence-Agent/
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   └── nooa_agent.py          # NVIDIA NOOA Agent with flow tracing & impact analysis
│   │   ├── api/
│   │   │   └── router.py              # FastAPI REST endpoints (/ingest, /architecture, /impact, etc.)
│   │   ├── core/
│   │   │   ├── config.py              # Pydantic v2 settings & environment variables
│   │   │   ├── database.py            # PostgreSQL engine with SQLite fallback
│   │   │   └── llm.py                 # Model-agnostic LLM Client
│   │   ├── models/
│   │   │   ├── workspace.py           # SQLModel schemas (Repository, FileNode, ASTSymbol, etc.)
│   │   │   └── knowledge.py           # Knowledge Entity, Relationship & Provenance schemas
│   │   ├── services/
│   │   │   ├── ingestion/
│   │   │   │   └── crawler.py         # Git cloning, scanning, tech stack detection
│   │   │   ├── parser/
│   │   │   │   ├── base.py            # BaseLanguageParser plugin interface
│   │   │   │   ├── plugins/           # Python, TS/JS, Go, Rust, C-family plugins
│   │   │   │   └── ast_parser.py      # Plugin registry & AST router
│   │   │   ├── graph/
│   │   │   │   └── code_graph.py      # CodeKnowledgeGraph (callers, callees, impact, flow)
│   │   │   ├── intelligence/
│   │   │   │   ├── endpoint_detector.py # Route & API discovery
│   │   │   │   ├── test_detector.py     # Test case discovery
│   │   │   │   ├── secret_safety.py     # Secret & credential redaction
│   │   │   │   └── incremental_indexer.py # SHA256 file hashing
│   │   │   ├── summarizer/
│   │   │   │   └── hierarchical.py    # Bottom-up 5-level hierarchical summarization engine
│   │   │   ├── export/
│   │   │   │   └── okf_exporter.py    # Open Knowledge Format (.wia/knowledge/) generator
│   │   │   ├── retrieval/
│   │   │   │   ├── hybrid_retriever.py  # Symbol + BM25 + Vector + Graph retriever
│   │   │   │   ├── query_planner.py     # Query intent planner
│   │   │   │   └── context_builder.py   # Structured context assembler
│   │   │   └── pipeline.py            # Background ingestion pipeline manager
│   │   ├── cli.py                     # Comprehensive WIA CLI implementation
│   │   └── main.py                    # FastAPI application entry point
│   └── tests/                         # Full automated pytest test suite
├── vscode-extension/                  # Native VS Code Extension
│   ├── src/
│   │   ├── providers/                 # Architecture, Symbols & Dependencies TreeViews
│   │   ├── panels/WiaChatPanel.ts     # Interactive AI Webview with jump-to-line citations
│   │   ├── apiClient.ts               # Local daemon HTTP client
│   │   └── extension.ts               # Main VS Code extension activation
│   ├── package.json
│   └── tsconfig.json
├── docs/                              # In-depth architectural documentation
├── docker-compose.yml
├── Dockerfile.backend
├── main.py                            # CLI entry point (`python main.py`)
├── run_dev.py                         # Daemon runner for VS Code & API
├── pyproject.toml                     # Project metadata & pytest configuration
└── README.md
```

---

## 💻 Comprehensive CLI Guide

WIA includes a command-line interface accessible via `python main.py` or `wia`.

```bash
# View all available CLI commands
python main.py --help
```

### CLI Commands Reference

| Command | Usage | Description |
|---|---|---|
| **`scan`** | `wia scan <path_or_url>` | Ingest and analyze a codebase |
| **`query`** | `wia query <repo> "<question>"` | Ask AI technical questions with exact line citations |
| **`architecture`** | `wia architecture <repo>` | View architecture overview and knowledge graph |
| **`flow`** | `wia flow <repo> --entry <symbol>` | Trace execution call flow starting from an entry point |
| **`impact`** | `wia impact <repo> --symbol <name>` | Analyze ripple change impact for a symbol or file |
| **`health`** | `wia health <repo>` | Run repository health and complexity audit |
| **`onboard`** | `wia onboard <repo>` | Generate developer onboarding walkthrough |
| **`symbols`** | `wia symbols <repo> [--search <term>]` | Search and list AST symbols across the codebase |
| **`dependencies`**| `wia dependencies <repo>` | Inspect import linkages and package dependencies |
| **`parse`** | `wia parse <file_path>` | Parse AST symbols from a source file |
| **`summarize`** | `wia summarize <repo>` | Show 5-level hierarchical summaries |
| **`list`** | `wia list` | List all ingested repositories |
| **`export`** | `wia export <repo> --format okf [-o dir]` | Export Open Knowledge Format (`.wia/knowledge/`) |
| **`delete`** | `wia delete <repo>` | Delete an ingested repository |
| **`serve`** | `wia serve [--port 8000]` | Start the local WIA backend server daemon |
| **`test`** | `wia test` | Run automated test suite |

---

## 🧩 Native VS Code Extension

The **WIA VS Code Extension** integrates graph-grounded code intelligence directly into your editor:

1. **🏛️ Architecture TreeView**: Explore subsystems, modules, and entry points.
2. **🔍 AST Symbol Explorer**: Browse functions, classes, interfaces, and methods.
3. **📦 Dependencies & Imports**: View package manifests and cross-file import statements.
4. **🧠 Interactive AI Chat**: Ask codebase questions and receive answers with **clickable source citations** that jump directly to the exact file line in VS Code.
5. **⚡ Editor Context Menu Actions**:
   - `WIA: Explain Code Architecture`
   - `WIA: Trace Code Execution Flow`
   - `WIA: Analyze Change Impact`
   - `WIA: Export Open Knowledge Format (.wia/knowledge/)`

---

## 🚀 Setup & Execution Guide

### Prerequisites
- **Python**: `3.10+`
- **Node.js**: `v18+` and `npm` (for VS Code extension)
- **Git**

### Installation

```bash
# 1. Install Backend dependencies
pip install -r backend/requirements.txt

# 2. Start the WIA Engine Daemon (for CLI and VS Code extension)
python run_dev.py
```

### Running the VS Code Extension
```bash
cd vscode-extension
npm install
npm run compile
# Press F5 in VS Code to launch the Extension Development Host!
```

---

## 📡 Core REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/ingest` | Ingest repository (GitHub URL or local path) |
| `GET` | `/api/v1/repos` | List all ingested repositories |
| `GET` | `/api/v1/repos/{repo_id}/status` | Get analysis progress status and metadata |
| `GET` | `/api/v1/repos/{repo_id}/tree` | Get repository file and folder hierarchy |
| `GET` | `/api/v1/repos/{repo_id}/file` | Get file content, AST symbols, and file summary |
| `GET` | `/api/v1/repos/{repo_id}/summary` | Get 5-level hierarchical workspace summaries |
| `POST` | `/api/v1/repos/{repo_id}/query` | Ask questions to WIA Agent + Hybrid RAG |
| `GET` | `/api/v1/repos/{repo_id}/architecture` | Get code knowledge graph & subsystem architecture |
| `GET` | `/api/v1/repos/{repo_id}/flow?entry={symbol}` | Trace code execution call flow |
| `GET` | `/api/v1/repos/{repo_id}/impact?target={symbol}`| Calculate change impact & affected callers/files |
| `GET` | `/api/v1/repos/{repo_id}/onboard` | Generate developer onboarding walkthrough |
| `GET` | `/api/v1/repos/{repo_id}/health` | Run codebase health & complexity audit |
| `GET` | `/api/v1/repos/{repo_id}/symbols/search` | Search symbols across codebase by name |
| `GET` | `/api/v1/repos/{repo_id}/metrics` | Get code metrics, LOC distribution, file stats |
| `GET` | `/api/v1/repos/{repo_id}/dependencies/graph` | Get import graph and external dependencies |
| `GET` | `/api/v1/repos/{repo_id}/export?format={okf\|json}` | Export architecture report or Open Knowledge Format |
| `DELETE` | `/api/v1/repos/{repo_id}` | Delete repository and all indexed artifacts |

---

## 📊 5-Level Hierarchical Summarization Engine

WIA prevents context window overflow by summarizing codebases bottom-up:

1. **Level 1 (Function / Method)**: Summarizes individual functions from docstrings, signatures, and internal function calls.
2. **Level 2 (File / Module)**: Aggregates function summaries and structural exports into a concise module description.
3. **Level 3 (Child Folder)**: Synthesizes file summaries within leaf directories into component summaries.
4. **Level 4 (Parent Folder)**: Aggregates child folder summaries up the tree into subsystem summaries.
5. **Level 5 (Repository Architecture)**: Merges subsystem summaries, entry points, and tech stack into an end-to-end architecture overview.

---

## 🤖 NVIDIA NOOA Agent & Hybrid Retrieval

Built according to NVIDIA NOOA (NeMo Orchestrated Object Agent) design principles:
- **Hybrid Retrieval**: Combines symbol matching, lexical BM25, semantic vector embeddings, graph walks, and hierarchical summaries.
- **Intent Query Planner**: Automatically recognizes architecture questions, flow tracing, impact analysis, or onboarding.
- **Precise Provenance Citations**: Every answer includes clickable file paths, chunk types, and exact line number ranges.

---

## 📦 Open Knowledge Format (OKF) Export

Generate a portable, Git-friendly documentation structure inside `.wia/knowledge/`:
```bash
python main.py export "My Project" --format okf --output ./
```

---

## ⚙️ Configuration & Environment Variables

Create a `.env` file in the project root:

```env
# AI / LLM Provider Keys (Optional - Local heuristic fallback activates if omitted)
GEMINI_API_KEY=your-gemini-key
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
NVIDIA_API_KEY=your-nvidia-key

# Provider Selection: auto, gemini, openai, anthropic, nvidia, heuristic
DEFAULT_LLM_PROVIDER=auto

# Database (Optional - Defaults to SQLite wia.db)
DATABASE_URL=postgresql://postgres:postgrespassword@localhost:5432/wia_db
```

---

## 🧪 Running Automated Tests

```bash
# Run pytest test suite
pytest

# Or via WIA CLI
python main.py test
```

---

## 📚 Documentation Index

- [System Architecture](docs/ARCHITECTURE.md)
- [Workspace Knowledge Model](docs/KNOWLEDGE_MODEL.md)
- [Hybrid Retrieval Engine](docs/RETRIEVAL.md)
- [Provenance & Trustworthiness](docs/PROVENANCE.md)
- [AI Architecture & Agent](docs/AI_ARCHITECTURE.md)
- [VS Code Extension Guide](docs/VSCODE_EXTENSION.md)
- [Open Knowledge Format Export](docs/OKF_EXPORT.md)
- [REST API Specification](docs/API.md)
- [CLI User Manual](docs/CLI.md)
- [Hierarchical Summarization Guide](docs/HIERARCHICAL_SUMMARIZATION.md)

---

## 📄 License

This project is licensed under the MIT License.
