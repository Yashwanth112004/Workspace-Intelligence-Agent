# WIA — Workspace Intelligence Agent

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Package](https://img.shields.io/badge/PyPI-wia--agent-orange.svg)](https://pypi.org/project/wia-agent/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![VS Code Extension](https://img.shields.io/badge/VS_Code_Extension-Ready-007ACC.svg)](https://code.visualstudio.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Workspace Intelligence Agent (WIA)** is an enterprise-grade, graph-grounded workspace intelligence platform that builds a structured understanding of an entire software repository. It uses that knowledge to answer questions, explain architecture, trace execution flow, analyze dependency impact, onboard developers, and provide grounded AI reasoning with exact file and line citations.

WIA is distributed on PyPI as **`wia-agent`** providing the **`wia`** CLI tool, paired with a **Native VS Code Extension**.


---

## ⚡ Key Highlights & Core Capabilities

* 🔍 **Multi-Stage Indexing Pipeline**: Crawls workspace, respects `.gitignore`, computes SHA-256 content hashes, detects programming languages & tech stacks, and runs specialized analyzers.
* 🌳 **AST & Symbol Parser**: Extracts classes, functions, methods, parameters, docstrings, parent classes, and import statements across multi-language codebases.
* 🕸️ **Workspace Knowledge Graph**: Maps directional dependency edges (`IMPORTS`, `DEFINES`, `CALLS`, `DEPENDS_ON`) between files and symbols in a persistent SQLite relational store.
* 📦 **Dependency Manifest & Conflict Detection**: Parses package manifests (`pyproject.toml`, `requirements.txt`, `package.json`, `Cargo.toml`, `go.mod`), normalizes package names, categorizes dependency types (`runtime`, `dev`, `optional`, `build`), and flags version mismatches.
* 🔒 **Security Secret Scanner with 100% Masking**: Identifies exposed credentials (AWS keys, RSA private keys, GitHub PATs, API tokens, Slack webhooks), classifies test fixtures vs real secrets, and enforces 100% secret masking (`AKIA************MPLE`).
* 📊 **Architecture Boundary & Cycle Intelligence**: Maps system component boundaries, detects circular import dependencies via DFS traversal, computes high fan-in/fan-out metrics, and identifies main entrypoints.
* 💥 **Symbol Refactoring Impact Analysis**: Evaluates symbol callers and file importers, resolves same-name symbols, differentiates direct callers from file importers, and assigns risk classifications (`LOW`, `MEDIUM`, `HIGH`).
* 🧠 **Intent-Grounded AI Reasoning Agent**: Answers developer queries (`wia ask`) using lightweight query intent classification and custom RAG context retrieval with NVIDIA NIM, OpenAI, Gemini, Anthropic, or offline intelligence.
* 📖 **Developer-Level Code Explanation**: Explains target files and symbols (`wia explain`), detailing purpose, architectural role, symbols breakdown, used-by dependents, and likely modification consequences.
* 📊 **Persistent HTML Narrative Dashboard**: Generates self-contained, batch-accumulating HTML reports (`wia-report.html`) with executive narrative summaries, component architecture cards, and file intelligence tables.


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
   │ 6. NVIDIA NIM Reasoning Layer & Grounded Output                  │
   │    • Grounded generation powered by NVIDIA NIM                   │
   │    • Exact source file and line-number citations                 │
   │    • Deterministic offline mode when NIM is not configured       │
   └─────────────────────────────────┬────────────────────────────────┘
                                     │
                                     ▼
      ┌────────────────────────────────────────────────────────┐
      │  CLI (`wia`)   │   VS Code Extension   │   REST API    │
      └────────────────────────────────────────────────────────┘
```

---

## 2. ⚡ Complete Technology Stack

| Layer | Component | Implementation |
|---|---|---|
| **Language & Engine** | Python 3.10+ | FastAPI, Pydantic v2, SQLModel, Uvicorn |
| **CLI Framework** | Python CLI | `argparse` with UTF-8 console output |
| **Code Parsing** | Multi-Language Parser Plugins | `ast` (Python), Regex/Structural Extractors (TS/JS, Go, Rust, Java, C++, C#) |
| **Knowledge Graph** | NetworkX Graph Engine | Directed graph with SQLite / PostgreSQL persistence |
| **Hybrid Retrieval** | Hybrid Engine | Exact Symbol Index + BM25 Lexical + SentenceTransformers Vector + Graph BFS |
| **AI Reasoning** | NVIDIA NIM Provider | OpenAI-compatible NIM API (`meta/llama-3.1-70b-instruct`) |
| **IDE Extension** | VS Code Extension | TypeScript, VS Code Extension API, Webview Chat, TreeView Provider |
| **Knowledge Export** | Open Knowledge Format (OKF) | Deterministic `.wia/knowledge/` Markdown / YAML documentation |

---

## 3. 📁 Repository Directory Structure

```
Workspace-Intelligence-Agent/
├── backend/
│   ├── app/
│   │   ├── __init__.py                # Package version definition (v0.3.0)
│   │   ├── cli.py                     # WIA CLI command implementations
│   │   ├── main.py                    # FastAPI application & lifespan management
│   │   ├── agent/                     # WIA Code Understanding Agent
│   │   ├── api/                       # REST API routers & Pydantic models
│   │   ├── core/                      # Config, database engine, & LLM client
│   │   ├── models/                    # SQLModel workspace & knowledge entities
│   │   ├── providers/                 # NVIDIA NIM & base LLM providers
│   │   └── services/
│   │       ├── export/                # OKF exporter
│   │       ├── graph/                 # Code knowledge graph & graph traversal
│   │       ├── ingestion/             # Crawler & file discovery
│   │       ├── intelligence/          # Git diff, watcher, secret safety
│   │       ├── parser/                # Multi-language parser plugins
│   │       ├── rag/                   # VectorStore & embeddings
│   │       ├── retrieval/             # HybridRetriever, QueryPlanner, ContextBuilder
│   │       └── summarizer/            # 5-level hierarchical summarizer
│   └── tests/                         # Pytest automated test suite (26 tests)
├── docs/                              # Detailed design & user documentation
│   ├── AI_ARCHITECTURE.md             # NVIDIA NIM & Agent architecture
│   ├── API.md                         # Complete REST API reference
│   ├── ARCHITECTURE.md                # System design & component breakdown
│   ├── CLI.md                         # CLI reference manual
│   ├── HIERARCHICAL_SUMMARIZATION.md  # 5-level summarization engine
│   ├── KNOWLEDGE_MODEL.md             # Graph entities & relation schema
│   ├── OKF_EXPORT.md                  # Open Knowledge Format guide
│   ├── PACKAGING.md                   # PyPI packaging & distribution guide
│   ├── PROVENANCE.md                  # Deterministic fact vs summary model
│   ├── RETRIEVAL.md                   # Hybrid retrieval pipeline
│   └── VSCODE_EXTENSION.md            # VS Code extension architecture
├── vscode-extension/                  # Native VS Code Extension (TypeScript)
│   ├── package.json
│   ├── src/
│   │   ├── extension.ts               # Extension activation & commands
│   │   ├── api.ts                     # WIA Backend API client
│   │   ├── chatViewProvider.ts        # Interactive AI chat webview
│   │   └── treeViews.ts               # Architecture, Symbols, & Dependency trees
├── docker-compose.yml                 # Docker Compose with PostgreSQL support
├── Dockerfile.backend                 # Backend container definition
├── pyproject.toml                     # PEP 517/621 packaging metadata
├── .env.example                       # Documented environment variables template
└── README.md
```

---

## 4. 💻 Exhaustive Command-Line Interface (CLI) Manual

```bash
# Display CLI help and command index
wia --help
```

### Complete CLI Command Reference

| Command | Syntax | Description | Example |
|---|---|---|---|
| **`scan`** | `wia scan <path_or_url> [--name <name>]` | Ingest and analyze a codebase | `wia scan ./ --name "My App"` |
| **`query`** | `wia query <repo> "<question>"` | Ask AI technical questions with exact line citations | `wia query "My App" "Explain auth flow"` |
| **`architecture`** | `wia architecture <repo>` | View graph nodes/edges and subsystem breakdown | `wia architecture "My App"` |
| **`flow`** | `wia flow <repo> <symbol>` | Trace call execution flow starting from an entry symbol | `wia flow "My App" handle_login` |
| **`impact`** | `wia impact <repo> <symbol>` | Analyze ripple change impact on callers and files | `wia impact "My App" AuthService` |
| **`diff`** | `wia diff [<repo>]` | Analyze Git diff changes and affected symbols | `wia diff "My App"` |
| **`watch`** | `wia watch <path_or_repo> [--interval 3]` | Watch workspace and incrementally reindex on change | `wia watch ./` |
| **`health`** | `wia health <repo>` | Run codebase complexity and health audit | `wia health "My App"` |
| **`onboard`** | `wia onboard <repo>` | Generate developer onboarding walkthrough | `wia onboard "My App"` |
| **`symbols`** | `wia symbols <repo> [--search <term>]` | Search and list AST symbols across the codebase | `wia symbols "My App" --search login` |
| **`dependencies`**| `wia dependencies <repo>` | Inspect package manifests and cross-file import statements | `wia dependencies "My App"` |
| **`parse`** | `wia parse <file>` | Extract AST classes, functions, and imports from a single file | `wia parse backend/app/main.py` |
| **`summarize`** | `wia summarize <repo>` | View the 5-level hierarchical summaries | `wia summarize "My App"` |
| **`export`** | `wia export <repo> --format [markdown\|json\|okf]` | Export architecture report or Open Knowledge Format | `wia export "My App" --format okf` |
| **`list`** | `wia list` | List all ingested repositories | `wia list` |
| **`delete`** | `wia delete <repo>` | Delete repository and purge all cached knowledge | `wia delete "My App"` |
| **`serve`** | `wia serve [--port 8000]` | Start local FastAPI daemon server for VS Code | `wia serve --port 8000` |
| **`test`** | `wia test` | Run the automated test suite | `wia test` |

---

## 5. 🧩 Native VS Code Extension Guide

The **WIA VS Code Extension** embeds graph-grounded code intelligence directly into your editor:

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

---

## 6. 🚀 Quickstart & Installation Guide

### PyPI Installation
```bash
# Install WIA distribution from PyPI
pip install wia-agent

# Verify CLI installation
wia --help

# Alternatively, run directly via Python module (works without PATH configuration):
python -m wia --help
```

> [!TIP]
> **PATH Troubleshooting**: If `wia` is not recognized after installing with `pip install --user`, add Python's `Scripts` directory to your system `PATH`, or run `wia doctor` / `python -m wia doctor` for automatic diagnostic guidance.
> - **Windows (PowerShell)**: `[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$([System.IO.Path]::Combine($env:APPDATA, 'Python', 'Python312', 'Scripts'))", "User")`
> - **macOS / Linux**: `export PATH="$HOME/.local/bin:$PATH"`


### Local Development Setup
```bash
# 1. Clone repository
git clone https://github.com/Yashwanth112004/Workspace-Intelligence-Agent.git
cd Workspace-Intelligence-Agent

# 2. Install package in editable development mode with dev tools
pip install -e ".[dev]"

# 3. Configure environment variables
cp .env.example .env
```

### Running via WIA Engine Daemon
```bash
# Start the local daemon for CLI and VS Code extension
wia serve
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
| `GET` | `/api/v1/repos/{repo_id}/symbols` | Search and filter AST symbols |
| `GET` | `/api/v1/repos/{repo_id}/dependencies` | Get package manifests and module imports |
| `GET` | `/api/v1/repos/{repo_id}/graph` | Get interactive Code Knowledge Graph JSON |
| `GET` | `/api/v1/repos/{repo_id}/flow?entry={symbol}` | Trace execution call paths |
| `GET` | `/api/v1/repos/{repo_id}/impact?symbol={symbol}` | Compute dependency change blast radius |
| `GET` | `/api/v1/repos/{repo_id}/onboard` | Generate developer onboarding walkthrough |
| `GET` | `/api/v1/repos/{repo_id}/health` | Run codebase complexity and health audit |
| `GET` | `/api/v1/repos/{repo_id}/summaries` | Retrieve 5-level hierarchical summaries |
| `GET` | `/api/v1/repos/{repo_id}/export?format={okf\|markdown}` | Export knowledge or Open Knowledge Format |
| `POST` | `/api/v1/repos/{repo_id}/query` | Ask AI technical questions with exact source citations |
| `DELETE` | `/api/v1/repos/{repo_id}` | Purge repository from database and storage |

---

## 8. 🧠 Workspace Knowledge Model & Code Knowledge Graph

WIA structures repository understanding into first-class typed entities:
- **`Repository`**: Top-level workspace metadata, entry points, dependencies.
- **`FileNode`**: File/directory structure with language classification and SHA256 hashes.
- **`ASTSymbol`**: Extracted classes, functions, methods, variables, interfaces, and imports with line numbers.
- **`WorkspaceSummary`**: 5-level structured responsibilities with confidence scores.

The **Code Knowledge Graph** represents relationships:
- `CONTAINS` (Directory → File, File → Class)
- `DEFINES` (File → Function / Class)
- `IMPORTS` (File → Module)
- `CALLS` (Function → Function / Method)
- `INHERITS` (Class → Base Class)

---

## 9. 🔌 Multi-Language AST Parser Plugin Architecture

WIA features dedicated parser plugins:
- **Python**: Full `ast` parsing for classes, async functions, decorators, method binding, docstrings, and call invocations.
- **TypeScript & JavaScript**: Extracts exported interfaces, types, ES6 classes, arrow functions, and imported modules.
- **Go**: Extracts package declarations, structs, interfaces, and method receivers.
- **Rust**: Extracts structs, enums, traits, implementations, and `pub fn` functions.
- **C / C++ / Java / C#**: Extracts class definitions, interfaces, methods, and header includes.

---

## 10. 📊 5-Level Hierarchical Workspace Summarization Engine

1. **Level 1 (Function/Method)**: Deterministic purpose and signature.
2. **Level 2 (File/Module)**: Primary responsibility and defined symbols.
3. **Level 3 (Child Folder)**: Component domain grouping.
4. **Level 4 (Parent Folder / Subsystem)**: Subsystem boundaries and architectural responsibility.
5. **Level 5 (Repository Architecture)**: Executive repository purpose, tech stack, entry points.

---

## 11. 🔍 Hybrid Retrieval Engine & Query Planner

WIA combines multiple retrieval strategies:
- **Exact Symbol Lookup**: Instant index lookup for symbols matching query terms.
- **Lexical BM25 Search**: Matches identifiers, docstrings, and signatures.
- **Semantic Vector Search**: `SentenceTransformers` embeddings for conceptual queries.
- **Graph Traversal**: Inbound/outbound graph walks for callers, callees, and dependencies.

The **Query Planner** classifies query intent:
- `CODE_FLOW`: Traces call paths.
- `DEPENDENCY_IMPACT`: Calculates blast radius.
- `ONBOARDING`: Synthesizes walkthrough.
- `HEALTH_AUDIT`: Computes complexity metrics.
- `GENERAL_QA`: Synthesizes grounded answer.

---

## 12. 🤖 NVIDIA NIM AI Reasoning Provider

WIA uses **NVIDIA NIM (NeMo Inference Microservices)** as its primary LLM reasoning layer:

```env
DEFAULT_LLM_PROVIDER=nvidia
NVIDIA_NIM_API_KEY=nvapi-your-key-here
NVIDIA_NIM_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_NIM_MODEL=meta/llama-3.1-70b-instruct
```

- **Grounded Reasoning**: The LLM receives only retrieved repository facts, symbols, and graph context.
- **Offline Deterministic Fallback**: If NVIDIA NIM is not configured, deterministic analysis commands (`scan`, `architecture`, `symbols`, `flow`, `impact`, `export`) continue working seamlessly.

---

## 13. 🛡️ Provenance & Secret Safety Redaction

- **Strict Provenance**: WIA distinguishes `DETERMINISTIC_FACT` (parsed symbols, imports, lines) from `LLM_SUMMARY` (AI-generated text).
- **Secret Safety**: Sensitive files (`.env`, `.pem`, `.key`, `id_rsa`) and patterns (API keys, tokens) are redacted before constructing LLM context.

---

## 14. 📦 Open Knowledge Format (OKF) Export

Export codebase intelligence into portable Markdown:
```bash
wia export "My Project" --format okf --output ./
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

## 15. ⚙️ Complete Configuration & Environment Variables (`.env`)

```env
# ==============================================================================
# Workspace Intelligence Agent (WIA) - Environment Configuration
# ==============================================================================

DEFAULT_LLM_PROVIDER=nvidia
NVIDIA_NIM_API_KEY=your_nvidia_nim_api_key_here
NVIDIA_NIM_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_NIM_MODEL=meta/llama-3.1-70b-instruct

# Local Vector Embeddings (SentenceTransformers)
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Server Configuration
WIA_HOST=127.0.0.1
WIA_PORT=8000
WIA_LOG_LEVEL=INFO
```

---

## 16. 🧪 Automated Testing Suite

Run the full automated pytest suite (26 unit & integration tests, 55% measured test coverage):

```bash
# Run pytest with coverage
pytest --cov=app

# Or via WIA CLI
wia test
```

### Verified Test Suites
- `test_api_endpoints.py`: Tests all REST API endpoints with SQLite memory pool.
- `test_ast_multilang.py`: Validates Python, TypeScript, Go, Rust, and C++ AST symbol extraction.
- `test_knowledge_graph.py`: Validates BFS call tracing, impact analysis, and graph edges.
- `test_hybrid_retrieval.py`: Validates Query Planner intents, secret redaction, and OKF export.
- `test_nvidia_nim_provider.py`: Validates NVIDIA NIM provider request building, authentication, and fallback.
- `test_wia_pipeline.py`: Validates crawler, AST parser, hierarchical summarizer, and agent.

---

## 17. ❓ Troubleshooting & FAQ

**Q: Do I need an OpenAI / Gemini API key to use WIA?**  
A: No. WIA uses NVIDIA NIM as its primary AI provider. If no LLM keys are provided, deterministic commands (`scan`, `architecture`, `symbols`, `flow`, `impact`, `export`) continue working completely.

**Q: How does the VS Code extension connect to WIA?**  
A: Start the daemon with `wia serve` (or `python run_dev.py`). The VS Code extension connects to `http://127.0.0.1:8000`.
=======
### 1. Installation

Install **WIA** from PyPI:

```bash
pip install wia-agent
```

Or install locally for development:

```bash
pip install -e .
```

Verify installation:

```bash
wia --version
wia --help
wia doctor
```

---

## 🛠️ Complete CLI Command Reference Manual

### 1. `wia init` — Initialize Workspace

Initializes the `.wia/` metadata directory and creates `config.json` inside the specified target directory.
>>>>>>> 2ab78d98fcf322c67e73494bb177e2091fdefaf5

```bash
wia init [PATH]
```

* **Arguments**: `PATH` (Optional, defaults to current working directory).
* **Behavior**: Prepares the workspace for indexing and configures default file limit thresholds.

**Example**:
```bash
wia init .
```

---

### 2. `wia index` — Run Indexing & Multi-Analyzer Pipeline

Executes file discovery, `.gitignore` filtering, SHA-256 change detection, language & framework detection, AST parsing, dependency manifest analysis, Git hotspot tracking, secret scanning, graph building, and SQLite database persistence.

```bash
wia index [PATH] [--force-reindex]
```

* **Flags**:
  * `--force-reindex`, `-f`: Clears existing index state and forces a full re-indexing of all files.
* **Behavior**: Processes files in deterministic batches, skipping unchanged files via hash comparison. Automatically excludes generated artifacts (`wia-report.html`, `.wia/`, `__pycache__/`, `*.pyc`).

**Example**:
```bash
wia index --force-reindex
```

---

### 3. `wia status` — Check Workspace Synchronization Status

Compares the last completed index state against the current filesystem to detect added, modified, or deleted files without mutating index data.

```bash
wia status [PATH]
```

* **States**:
  * `NOT_INITIALIZED`: Workspace lacks `.wia/` directory.
  * `NO_INDEX`: Workspace initialized but not yet indexed.
  * `UP_TO_DATE`: Workspace is synchronized with the filesystem.
  * `CHANGES_DETECTED`: Files have been added, modified, or deleted since last index.

---

### 4. `wia files` — List Indexed Workspace Files

Lists all files currently indexed in the workspace with metadata.

```bash
wia files [PATH] [--language LANG]
```

* **Flags**:
  * `--language`, `-l`: Filter listed files by language (e.g. `Python`, `Markdown`, `TOML`).

---

### 5. `wia info` — Workspace Overview & Statistics

Displays file counts, language distribution percentages, detected frameworks, and index metadata.

```bash
wia info [PATH]
```

---

### 6. `wia analyze` — Run Specialized Workspace Analyzers

Executes targeted security, dependency, or Git repository analyzers.

```bash
# Package Manifest & Dependency Conflicts
wia analyze deps [--workspace PATH]

# Git Commit History & File Churn Hotspots
wia analyze git [--workspace PATH] [--max-commits 50] [--top-hotspots 10]

# Security Hardcoded Secret Scanner
wia analyze security [--workspace PATH]
```

---

### 7. `wia architecture` — System Subsystem & Component Boundary Map

Analyzes the workspace to produce a factually grounded architectural explanation, mapping subsystem boundaries, entrypoints, circular import cycles (DFS), high fan-in/fan-out metrics, and directory hierarchy.

```bash
wia architecture [--workspace PATH]
```

---

### 8. `wia impact` — Refactoring Impact Analysis

Evaluates downstream callers and file importers for a given target symbol or file, assigning an evidence-backed change risk classification (`LOW`, `MEDIUM`, `HIGH`).

```bash
wia impact <symbol_or_file> [--workspace PATH]
```

---

### 9. `wia explain` — Developer-Level Code & Symbol Explanation

Generates a complete technical explanation answering: *"What is this code, what does it do, why does it exist, how does it work, how does it fit into the project, what depends on it, and what should a developer know before modifying it?"*

```bash
wia explain <file_or_symbol> [--workspace PATH]
```

---

### 10. `wia ask` — Grounded AI Reasoning Agent

Answers natural language developer questions grounded in indexed workspace evidence using query intent classification (`ARCHITECTURE`, `WORKFLOW`, `COMPONENT`, `STORAGE`, `FILE_SYMBOL`, `GENERAL`).

```bash
wia ask "<question>" [--workspace PATH]
```

---

### 11. `wia report` — Generate HTML Intelligence Dashboard

Compiles all workspace intelligence into a self-contained, batch-accumulating HTML report (`wia-report.html`).

```bash
wia report [--workspace PATH] [--output FILE]
```

---

### 12. `wia search` — Query Workspace Symbols & Files

Executes relevance-scored search across declared AST symbols, function definitions, classes, and file paths.

```bash
wia search <query> [--workspace PATH] [--language LANG] [--type TYPE] [--limit N]
```

---

### 13. `wia summary` — Export LLM RAG Context Markdown

Exports a structured Markdown summary of the workspace suitable for prompt context injection into external LLMs.

```bash
wia summary [--workspace PATH] [--output summary.md]
```

---

### 14. `wia doctor` — Environment Health Diagnostic Check

Runs system diagnostics verifying Python version, installed package entrypoints, SQLite database connectivity, and Git CLI availability.

```bash
wia doctor
```

---

## 🧪 Testing & Quality Assurance

WIA includes a comprehensive automated suite of 154 unit, CLI, and integration tests using `pytest`.

To run the complete test suite:

```bash
python -m pytest
```

**Current Test Status**: `154 passed`.

---

## 🏗️ Architecture & Internal Subsystem Design

```text
                                WIA CLI (app.py)
                                       │
                                       ▼
                       Service Layer Orchestration
              (IndexingService, StatusService, ExplanationService)
                                       │
       ┌───────────────────────────────┼───────────────────────────────┐
       ▼                               ▼                               ▼
Core Inspection                Specialized Analyzers           Knowledge & Storage
- FileDiscovery                - ASTParser (Python AST)        - WorkspaceIndex
- FileFilter & Gitignore       - ManifestParser (pyproject)    - WorkspaceGraph
- FileHasher (SHA-256)         - SecretScanner (Masking)       - SQLiteStore
- LanguageDetector             - GitAnalyzer                   - VectorStore
```

---

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.
