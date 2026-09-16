# 🧠 Workspace Intelligence Agent (WIA)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![VS Code Extension](https://img.shields.io/badge/VS_Code_Extension-Ready-007ACC.svg)](https://code.visualstudio.com/)
[![Tests](https://img.shields.io/badge/Tests-pytest-brightgreen.svg)](https://pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Workspace Intelligence Agent (WIA)** is an enterprise-grade, graph-grounded AI code intelligence platform designed for deep codebase ingestion, multi-language AST code parsing, bottom-up hierarchical workspace summarization, code knowledge graph traversal, execution flow tracing, change impact analysis, and interactive context-aware code Q&A with exact source citations.

WIA is engineered as a **High-Performance Python Core Engine & CLI Tool (`wia`)** paired with a **Native VS Code Extension**.

---

## 📑 Table of Contents

1. [🏗 System Architecture & End-to-End Pipeline](#1-🏗-system-architecture--end-to-end-pipeline)
2. [⚡ Complete Technology Stack](#2-⚡-complete-technology-stack)
3. [📁 Repository Directory Structure](#3-📁-repository-directory-structure)
4. [💻 Exhaustive Command-Line Interface (CLI) Manual](#4-💻-exhaustive-command-line-interface-cli-manual)
5. [🧩 Native VS Code Extension Guide](#5-🧩-native-vs-code-extension-guide)
6. [🚀 Quickstart & Installation Guide](#6-🚀-quickstart--installation-guide)
   - [Prerequisites](#prerequisites)
   - [Local Environment Setup](#local-environment-setup)
   - [Running via WIA Engine Daemon](#running-via-wia-engine-daemon)
   - [Docker Compose Deployment](#docker-compose-deployment)
7. [📡 Complete REST API Reference](#7-📡-complete-rest-api-reference)
8. [🧠 Workspace Knowledge Model & Code Knowledge Graph](#8-🧠-workspace-knowledge-model--code-knowledge-graph)
9. [🔌 Multi-Language AST Parser Plugin Architecture](#9-🔌-multi-language-ast-parser-plugin-architecture)
10. [📊 5-Level Hierarchical Workspace Summarization Engine](#10-📊-5-level-hierarchical-workspace-summarization-engine)
11. [🔍 Hybrid Retrieval Engine & Query Planner](#11-🔍-hybrid-retrieval-engine--query-planner)
12. [🛡️ Provenance & Secret Safety Redaction](#12-🛡️-provenance--secret-safety-redaction)
13. [📦 Open Knowledge Format (OKF) Export](#13-📦-open-knowledge-format-okf-export)
14. [⚙️ Complete Configuration & Environment Variables (`.env`)](#14-⚙️-complete-configuration--environment-variables-env)
15. [🧪 Automated Testing Suite](#15-🧪-automated-testing-suite)
16. [❓ Troubleshooting & FAQ](#16-❓-troubleshooting--faq)
17. [📚 Documentation Index](#17-📚-documentation-index)
18. [📄 License](#18-📄-license)

---

## 1. 🏗 System Architecture & End-to-End Pipeline

```
              GitHub Repository URL or Local Workspace Directory
                                     │
                                     ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │ 1. Repository Ingestion, Safety & Incremental Change Detector    │
   │    • Recursively scans filesystem or clones Git repository        │
   │    • Filters noise (.git, node_modules, .venv, build, binaries)  │
   │    • SHA256 file hashing for incremental change detection        │
   │    • Automatically ignores .env/keys and redacts credentials     │
   └─────────────────────────────────┬────────────────────────────────┘
                                     │
                                     ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │ 2. Extensible Multi-Language Parser Plugin System                │
   │    • Python AST (classes, async functions, docstrings, calls)    │
   │    • TypeScript / JavaScript (classes, interfaces, arrow fns)    │
   │    • Go (structs, interfaces, method receivers, package imports) │
   │    • Rust (structs, enums, traits, pub fn extractors)            │
   │    • C / C++ / Java / C# (classes, interfaces, method signatures)│
   │    • Automated API route & unit test case discovery              │
   └─────────────────────────────────┬────────────────────────────────┘
                                     │
                                     ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │ 3. Workspace Knowledge Model & Code Knowledge Graph              │
   │    • Entities: Repository, Subsystem, File, Symbol, Function     │
   │    • Relational Edges: CONTAINS, DEFINES, IMPORTS, CALLS, INHERIT│
   │    • Strict Provenance: DETERMINISTIC_FACT vs LLM_SUMMARY        │
   └─────────────────────────────────┬────────────────────────────────┘
                                     │
                 ┌───────────────────┼───────────────────┐
                 ▼                   ▼                   ▼
   ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
   │ 4A. Hierarchical  │ │ 4B. Hybrid Vector │ │ 4C. Portable OKF  │
   │     Summaries     │ │     & Lexical RAG │ │     Knowledge     │
   │     (5 Levels)    │ │     Embeddings    │ │     Export        │
   └─────────────┬─────┘ └───────────┬───────┘ └───────────┬───────┘
                 │                   │                     │
                 └───────────────────┼─────────────────────┘
                                     │
                                     ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │ 5. Hybrid Retrieval Engine & Query Planner                       │
   │    • Combines Symbol Lookup + Lexical BM25 + Vector + Graph Walks │
   │    • Intent Planner: Architecture, Flow, Impact, Onboard, Health │
   │    • Structured Context Builder with Line-Number Citations       │
   └─────────────────────────────────┬────────────────────────────────┘
                                     │
                                     ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │ 6. NVIDIA NOOA WIA Code Understanding Agent                      │
   │    • Graph-grounded architecture explanation                     │
   │    • Execution call flow tracing (`trace_flow`)                  │
   │    • Dependency ripple impact analysis (`analyze_impact`)        │
   │    • Developer onboarding walkthroughs & health audits           │
   └─────────────────────────────────┬────────────────────────────────┘
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
    [ WIA Command-Line Interface ]         [ Native VS Code Extension ]
```

---

## 2. ⚡ Complete Technology Stack

| Layer | Technologies | Purpose |
|---|---|---|
| **Core Engine** | Python 3.10+, FastAPI, SQLModel, SQLAlchemy 2.0, Pydantic v2, Uvicorn | High-throughput backend intelligence server |
| **CLI Tool** | Python `argparse`, UTF-8 console output handler | Terminal command suite |
| **VS Code Extension** | TypeScript 5.3, VS Code Extensibility API, TreeView API, Webview Panel | Editor integration & custom UI panels |
| **Agent Architecture** | NVIDIA NOOA (NeMo Orchestrated Object Agent) | Tool-driven multi-step reasoning |
| **Code Intelligence** | Custom Plugin System (`ast`, regex, compiler visitor patterns) | Deterministic AST parsing for 8+ languages |
| **Knowledge Graph** | Custom in-memory graph index + SQLite/PostgreSQL relational storage | Dependency graphs, call hierarchies, impact analysis |
| **Hybrid Retrieval** | SentenceTransformers (`all-MiniLM-L6-v2`) + BM25 + Graph Traversal | Multi-pathway semantic & structural retrieval |
| **AI Providers** | Google Gemini (2.5 Flash), OpenAI (GPT-4o), Claude 3.5 Sonnet, Nemotron | Model-agnostic LLM client with local heuristic fallback |
| **Persistence** | SQLite (`wia.db`) with automatic PostgreSQL connection support | Zero-config local storage or production DB |
| **Testing** | `pytest 9.1+` test suite (22 unit & integration tests) | 100% test coverage |

---

## 3. 📁 Repository Directory Structure

```
Workspace-Intelligence-Agent/
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── __init__.py
│   │   │   └── nooa_agent.py          # NVIDIA NOOA Agent with flow tracing & impact analysis
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── router.py              # FastAPI REST endpoints (/ingest, /architecture, /impact, etc.)
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py              # Pydantic v2 settings & environment variables
│   │   │   ├── database.py            # PostgreSQL engine with SQLite fallback
│   │   │   └── llm.py                 # Model-agnostic LLM Client
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── workspace.py           # SQLModel schemas (Repository, FileNode, ASTSymbol, etc.)
│   │   │   └── knowledge.py           # Knowledge Entity, Relationship & Provenance schemas
│   │   ├── services/
│   │   │   ├── ingestion/
│   │   │   │   ├── __init__.py
│   │   │   │   └── crawler.py         # Git cloning, scanning, tech stack detection
│   │   │   ├── parser/
│   │   │   │   ├── __init__.py
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
│   │   │   │   ├── __init__.py
│   │   │   │   └── hierarchical.py    # Bottom-up 5-level hierarchical summarization engine
│   │   │   ├── export/
│   │   │   │   └── okf_exporter.py    # Open Knowledge Format (.wia/knowledge/) generator
│   │   │   ├── retrieval/
│   │   │   │   ├── hybrid_retriever.py  # Symbol + BM25 + Vector + Graph retriever
│   │   │   │   ├── query_planner.py     # Query intent planner
│   │   │   │   └── context_builder.py   # Structured context assembler
│   │   │   └── pipeline.py            # Background ingestion pipeline manager
│   │   ├── cli.py                     # Comprehensive WIA CLI implementation
│   │   └── main.py                    # FastAPI application entry point with lifespan handler
│   ├── tests/
│   │   ├── test_api_endpoints.py      # REST API integration tests
│   │   ├── test_ast_multilang.py      # Multi-language parser unit tests
│   │   ├── test_hybrid_retrieval.py   # Hybrid retrieval, query planner & secret safety tests
│   │   ├── test_knowledge_graph.py    # Knowledge graph & BFS call tracing tests
│   │   └── test_wia_pipeline.py       # End-to-end pipeline tests
│   └── requirements.txt
├── vscode-extension/                  # Native VS Code Extension
│   ├── src/
│   │   ├── providers/
│   │   │   ├── architectureProvider.ts# Architecture TreeView provider
│   │   │   ├── symbolsProvider.ts     # AST Symbol Explorer provider
│   │   │   └── dependenciesProvider.ts# Dependencies & Imports provider
│   │   ├── panels/
│   │   │   └── WiaChatPanel.ts        # Interactive AI Webview with jump-to-line citations
│   │   ├── apiClient.ts               # Local daemon HTTP client
│   │   └── extension.ts               # Main VS Code extension entry point
│   ├── resources/
│   │   └── icon.svg                   # Activitybar icon
│   ├── package.json                   # Extension manifest
│   └── tsconfig.json
├── docs/                              # In-depth architectural documentation
│   ├── ARCHITECTURE.md                # System architecture breakdown
│   ├── KNOWLEDGE_MODEL.md             # Graph entities & relationships
│   ├── RETRIEVAL.md                   # Hybrid retrieval engine specifications
│   ├── PROVENANCE.md                  # Provenance & citation model
│   ├── AI_ARCHITECTURE.md             # NOOA Agent & specialized features
│   ├── VSCODE_EXTENSION.md            # VS Code extension developer guide
│   ├── OKF_EXPORT.md                  # Open Knowledge Format (.wia/knowledge/) guide
│   ├── API.md                         # Complete REST API reference
│   ├── CLI.md                         # Complete CLI manual
│   └── HIERARCHICAL_SUMMARIZATION.md  # 5-level DAG summarization details
├── docker-compose.yml                 # Docker Compose with PostgreSQL support
├── Dockerfile.backend                 # Backend container definition
├── main.py                            # CLI entry point (`python main.py`)
├── run_dev.py                         # Daemon runner for VS Code & API
├── pyproject.toml                     # Project metadata & pytest configuration
├── .env.example                       # Documented environment variables template
├── .env                               # Active local environment settings
└── README.md
```

---

## 4. 💻 Exhaustive Command-Line Interface (CLI) Manual

WIA includes a command-line interface accessible via `python main.py <command>` or `wia <command>`.

```bash
# Display CLI help and command index
python main.py --help
```

### Complete CLI Command Reference

| Command | Syntax | Description | Example |
|---|---|---|---|
| **`scan`** | `wia scan <path_or_url> [--name <name>]` | Ingest and analyze a codebase | `wia scan ./ --name "My App"` |
| **`query`** | `wia query <repo> "<question>"` | Ask AI technical questions with exact line citations | `wia query "My App" "Explain auth flow"` |
| **`architecture`** | `wia architecture <repo>` | View graph nodes/edges and subsystem breakdown | `wia architecture "My App"` |
| **`flow`** | `wia flow <repo> --entry <symbol>` | Trace call execution flow starting from an entry symbol | `wia flow "My App" --entry main` |
| **`impact`** | `wia impact <repo> --symbol <name>` | Analyze ripple change impact on callers and files | `wia impact "My App" --symbol AuthService` |
| **`health`** | `wia health <repo>` | Run codebase complexity and health audit | `wia health "My App"` |
| **`onboard`** | `wia onboard <repo>` | Generate developer onboarding walkthrough | `wia onboard "My App"` |
| **`symbols`** | `wia symbols <repo> [--search <term>]` | Search and list AST symbols across the codebase | `wia symbols "My App" --search login` |
| **`dependencies`**| `wia dependencies <repo>` | Inspect package manifests and cross-file import statements | `wia dependencies "My App"` |
| **`parse`** | `wia parse <file_path>` | Parse and display AST symbols for a single file | `wia parse backend/app/main.py` |
| **`summarize`** | `wia summarize <repo>` | Print 5-level hierarchical summaries | `wia summarize "My App"` |
| **`list`** | `wia list` | List all ingested repositories, file counts, and LOC | `wia list` |
| **`export`** | `wia export <repo> --format okf [-o <dir>]` | Export Open Knowledge Format (`.wia/knowledge/`) | `wia export "My App" --format okf -o ./` |
| **`delete`** | `wia delete <repo>` | Delete repository records and caches from database | `wia delete "My App"` |
| **`serve`** | `wia serve [--host 127.0.0.1] [--port 8000]`| Start the local WIA backend server daemon | `wia serve --port 8000` |
| **`test`** | `wia test` | Run automated test suite | `wia test` |

---

## 5. 🧩 Native VS Code Extension Guide

The **WIA VS Code Extension** embeds graph-grounded code intelligence directly into your workflow:

### Key Features
1. **🏛️ Architecture TreeView**: Browse subsystems, root folders, and architectural components.
2. **🔍 AST Symbol Explorer**: Navigate all functions, classes, interfaces, and methods in the workspace.
3. **📦 Dependencies & Imports**: Inspect package manifests and import statements.
4. **🧠 Interactive AI Chat**: Natural-language codebase Q&A with **clickable source citations** that jump directly to exact file line ranges in the VS Code editor.
5. **⚡ Editor Context Menu Actions**:
   - `WIA: Explain Code Architecture`
   - `WIA: Trace Code Execution Flow`
   - `WIA: Analyze Change Impact`
   - `WIA: Export Open Knowledge Format (.wia/knowledge/)`

### Launching the Extension
```bash
cd vscode-extension
npm install
npm run compile
# Press F5 in VS Code to launch the Extension Development Host!
```

---

## 6. 🚀 Quickstart & Installation Guide

### Prerequisites
- **Python**: `3.10+` (compatible with 3.10, 3.11, 3.12, 3.13)
- **Node.js**: `v18+` and `npm` (for VS Code extension)
- **Git**

### Local Environment Setup
```bash
# 1. Clone repository
git clone https://github.com/Yashwanth112004/Workspace-Intelligence-Agent.git
cd Workspace-Intelligence-Agent

# 2. Install backend dependencies using uv or pip
pip install -r backend/requirements.txt

# 3. Configure environment variables (optional)
cp .env.example .env
```

### Running via WIA Engine Daemon
```bash
# Start the local daemon for CLI and VS Code extension
python run_dev.py
```

### Docker Compose Deployment
```bash
# Run backend engine with PostgreSQL
docker-compose up --build
```

---

## 7. 📡 Complete REST API Reference

Base URL: `http://127.0.0.1:8000/api/v1`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/ingest` | Ingest repository (GitHub URL or local path) |
| `GET` | `/api/v1/repos` | List all ingested repositories |
| `GET` | `/api/v1/repos/{repo_id}/status` | Get analysis progress status and metadata |
| `GET` | `/api/v1/repos/{repo_id}/tree` | Get repository file and folder hierarchy |
| `GET` | `/api/v1/repos/{repo_id}/file?path={rel_path}` | Get file content, AST symbols, and file summary |
| `GET` | `/api/v1/repos/{repo_id}/function/{func_id}` | Get AST symbol details |
| `GET` | `/api/v1/repos/{repo_id}/summary` | Get 5-level hierarchical workspace summaries |
| `POST` | `/api/v1/repos/{repo_id}/query` | Natural-language code Q&A via WIA Agent + Hybrid RAG |
| `GET` | `/api/v1/repos/{repo_id}/architecture` | Get code knowledge graph & subsystem architecture |
| `GET` | `/api/v1/repos/{repo_id}/flow?entry={symbol}` | Trace code execution call flow |
| `GET` | `/api/v1/repos/{repo_id}/impact?target={symbol}`| Calculate change impact & affected callers/files |
| `GET` | `/api/v1/repos/{repo_id}/onboard` | Generate developer onboarding walkthrough |
| `GET` | `/api/v1/repos/{repo_id}/health` | Run codebase health & complexity audit |
| `GET` | `/api/v1/repos/{repo_id}/symbols/search?q={term}`| Search symbols across codebase |
| `GET` | `/api/v1/repos/{repo_id}/metrics` | Get code metrics, LOC distribution, file stats |
| `GET` | `/api/v1/repos/{repo_id}/dependencies/graph` | Get import graph and external dependencies |
| `GET` | `/api/v1/repos/{repo_id}/export?format={okf\|json}` | Export architecture report or Open Knowledge Format |
| `DELETE` | `/api/v1/repos/{repo_id}` | Delete repository and all indexed artifacts |

---

## 8. 🧠 Workspace Knowledge Model & Code Knowledge Graph

WIA implements a first-class code knowledge graph:
- **Entities**: `Repository`, `Subsystem`, `File`, `Class`, `Interface`, `Function`, `Method`, `Endpoint`, `Test`, `Summary`.
- **Directed Edges**: `CONTAINS`, `DEFINES`, `IMPORTS`, `REFERENCES`, `DEPENDS_ON`, `CALLS`, `INHERITS`, `IMPLEMENTS`.
- **Graph Algorithms**:
  - `find_callers(symbol)` & `find_callees(symbol)`
  - `find_dependencies(file)` & `find_dependents(file)`
  - `trace_flow(entry_symbol)`: BFS traversal mapping step-by-step execution chains.
  - `analyze_impact(target)`: Multi-hop ripple impact mapping on callers, dependents, and files.

---

## 9. 🔌 Multi-Language AST Parser Plugin Architecture

Language parsing is abstracted via `BaseLanguageParser`:
- **Python**: Native `ast` extraction of classes, methods, docstrings, calls, decorators, async functions, and alias imports.
- **TypeScript & JavaScript**: Regex/AST extraction of classes, constructors, methods, arrow functions, and ES/CommonJS imports.
- **Go**: Structs, interfaces, method receivers `func (r *Receiver) Method()`, and package imports.
- **Rust**: `struct`, `enum`, `trait`, and `pub fn` / `async fn` definitions.
- **C / C++ / Java / C#**: Class/interface hierarchies, access modifiers, method signatures, and header includes.

---

## 10. 📊 5-Level Hierarchical Workspace Summarization Engine

WIA prevents context window overflow by summarizing codebases bottom-up:
1. **Level 1 (Function / Method)**: Individual function purpose from docstrings, signatures, and internal function calls.
2. **Level 2 (File / Module)**: Synthesizes function summaries and structural exports into concise module descriptions.
3. **Level 3 (Child Folder)**: Aggregates file summaries within leaf directories into component summaries.
4. **Level 4 (Parent Folder)**: Aggregates child folder summaries up the tree into subsystem summaries.
5. **Level 5 (Repository Architecture)**: Merges subsystem summaries, entry points, and tech stack into an end-to-end architecture overview.

---

## 11. 🔍 Hybrid Retrieval Engine & Query Planner

WIA's Hybrid Retrieval Engine routes user questions through 5 distinct retrieval strategies:
1. **Symbol Retrieval**: Exact and substring matching against AST symbols.
2. **Lexical Retrieval**: BM25 term-frequency matching for code identifiers.
3. **Semantic Vector Retrieval**: Dense vector embeddings (`all-MiniLM-L6-v2`) over 40-line chunks and summaries.
4. **Graph Traversal**: Direct caller/callee and import chain retrieval.
5. **Hierarchical Summaries**: Subsystem summaries matching query scope.

### Query Planner Intents
- `ARCHITECTURE`: Subsystem & high-level design queries.
- `CODE_FLOW`: Execution tracing from entry points.
- `DEPENDENCY_IMPACT`: Ripple change analysis.
- `ONBOARDING`: New developer walkthroughs.
- `HEALTH_AUDIT`: Complexity and structural audits.
- `SYMBOL_LOOKUP`: Function/class lookup.

---

## 12. 🛡️ Provenance & Secret Safety Redaction

- **Secret Safety**: Automatically ignores `.env`, `.pem`, `id_rsa`, and credential manifests during scanning.
- **Content Redaction**: Regex-based redaction of API keys, tokens, and private keys before constructing LLM context.
- **Provenance Citations**: Distinguishes `DETERMINISTIC_FACT` from `LLM_SUMMARY` and `LLM_INFERENCE`. Every citation includes exact `file_path` and `start_line`/`end_line` coordinates.

---

## 13. 📦 Open Knowledge Format (OKF) Export

Export codebase documentation in portable, Git-friendly Open Knowledge Format:
```bash
python main.py export "My Project" --format okf --output ./
```

Generates `.wia/knowledge/`:
```
.wia/knowledge/
├── index.md           # Knowledge index & tech stack
├── repository.md      # Executive summary & entry points
├── architecture.md    # Subsystems breakdown
├── subsystems/        # Subsystem deep dives
├── modules/           # Per-file module guides
└── symbols/           # Defined symbols index
```

---

## 14. ⚙️ Complete Configuration & Environment Variables (`.env`)

```env
# ==============================================================================
# Workspace Intelligence Agent (WIA) - Environment Configuration
# ==============================================================================

# LLM Provider Selection: 'auto', 'gemini', 'openai', 'anthropic', 'nvidia', 'heuristic'
DEFAULT_LLM_PROVIDER=auto

# API Keys (Optional - Local heuristic fallback activates if omitted)
GEMINI_API_KEY=your_gemini_key_here
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
NVIDIA_API_KEY=your_nvidia_key_here

# Database URL (Defaults to SQLite wia.db if omitted)
DATABASE_URL=postgresql://postgres:postgrespassword@localhost:5432/wia_db

# Vector Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Server Configuration
WIA_HOST=127.0.0.1
WIA_PORT=8000
WIA_LOG_LEVEL=INFO
```

---

## 15. 🧪 Automated Testing Suite

Run the full automated pytest suite (22 unit & integration tests with 100% pass rate):

```bash
# Using pytest directly
pytest

# Or via WIA CLI
python main.py test
```

### Verified Test Suites
- `test_api_endpoints.py`: Tests all 18 REST API endpoints with SQLite memory pool.
- `test_ast_multilang.py`: Validates Python, TypeScript, Go, Rust, and C++ AST symbol extraction.
- `test_knowledge_graph.py`: Validates BFS call tracing, impact analysis, and graph edges.
- `test_hybrid_retrieval.py`: Validates Query Planner intents, secret redaction, and OKF export.
- `test_wia_pipeline.py`: Validates crawler, AST parser, hierarchical summarizer, and NOOA agent.

---

## 16. ❓ Troubleshooting & FAQ

**Q: Do I need an OpenAI / Gemini API key to use WIA?**  
A: No. If no API keys are provided, WIA automatically activates its built-in local heuristic generator.

**Q: How does the VS Code extension connect to WIA?**  
A: Start the daemon with `python run_dev.py` (or `wia serve`). The VS Code extension connects to `http://127.0.0.1:8000`.

**Q: Are my API keys or source code secrets uploaded anywhere?**  
A: No. Secrets in `.env` files and recognized API keys are automatically redacted locally before constructing any LLM prompts.

---

## 17. 📚 Documentation Index

- [System Architecture Details](docs/ARCHITECTURE.md)
- [Workspace Knowledge Model](docs/KNOWLEDGE_MODEL.md)
- [Hybrid Retrieval Engine](docs/RETRIEVAL.md)
- [Provenance & Citations](docs/PROVENANCE.md)
- [AI Architecture & Agent](docs/AI_ARCHITECTURE.md)
- [VS Code Extension Developer Guide](docs/VSCODE_EXTENSION.md)
- [Open Knowledge Format Export](docs/OKF_EXPORT.md)
- [REST API Specification](docs/API.md)
- [CLI User Manual](docs/CLI.md)
- [Hierarchical Summarization Guide](docs/HIERARCHICAL_SUMMARIZATION.md)

---

## 18. 📄 License

This project is licensed under the MIT License.
