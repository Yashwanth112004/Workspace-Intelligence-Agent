# 🧠 Workspace Intelligence Agent (WIA)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178c6.svg)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38bdf8.svg)](https://tailwindcss.com/)
[![Tests](https://img.shields.io/badge/Tests-pytest-brightgreen.svg)](https://pytest.org/)

**Workspace Intelligence Agent (WIA)** is an AI-powered multi-agent platform designed for deep codebase ingestion, multi-language AST code parsing, bottom-up hierarchical workspace summarization, and interactive context-aware code Q&A with precise source citations.

Whether pointing to a local directory or cloning a public GitHub repository, WIA extracts symbols, generates 5 levels of architectural summaries, indexes code vectors, and provides both a **FastAPI REST API**, a **Dark-Mode React + Vite Dashboard**, and a **Rich Command-Line Interface (CLI)**.

---

## 📑 Table of Contents

- [🏗 System Architecture & Pipeline](#-system-architecture--pipeline)
- [⚡ Technology Stack](#-technology-stack)
- [📁 Repository Directory Structure](#-repository-directory-structure)
- [💻 Comprehensive CLI Guide](#-comprehensive-cli-guide)
- [🚀 Setup & Execution Guide](#-setup--execution-guide)
  - [Option 1: Quick Dev Launcher](#option-1-quick-dev-launcher-recommended)
  - [Option 2: Manual Terminal Execution](#option-2-manual-terminal-execution)
  - [Option 3: Docker Compose](#option-3-docker-compose)
- [📡 Core REST API Reference](#-core-rest-api-reference)
- [📊 5-Level Hierarchical Summarization Engine](#-5-level-hierarchical-summarization-engine)
- [🤖 NVIDIA NOOA Agent & RAG Architecture](#-nvidia-nooa-agent--rag-architecture)
- [⚙️ Configuration & Environment Variables](#️-configuration--environment-variables)
- [🧪 Running Automated Tests](#-running-automated-tests)
- [📋 Features Matrix & Roadmap](#-features-matrix--roadmap)
- [📚 Further Documentation](#-further-documentation)

---

## 🏗 System Architecture & Pipeline

```
GitHub Repository URL or Local Directory
                  │
                  ▼
   1. Repository Ingestion & Scanning
   ├─ Clones GitHub repo / scans local folder
   ├─ Ignores .git, node_modules, .venv, build, binary files
   └─ Detects languages, LOC, dependencies, configs, entry points
                  │
                  ▼
   2. Multi-Language AST Code Parser
   ├─ Python AST standard library parser (classes, methods, docstrings, calls)
   ├─ TypeScript / JavaScript structural parser (imports, classes, arrow fns)
   └─ Go, Rust, Java, C/C++, C# structural & signature extractors
                  │
                  ▼
   3. Hierarchical Workspace Summarization Engine
   ├─ Level 1: Function / Method Summaries
   ├─ Level 2: File / Module Summaries
   ├─ Level 3: Child Folder Summaries
   ├─ Level 4: Parent Folder Subsystem Summaries
   └─ Level 5: Repository Architecture Overview
                  │
                  ▼
   4. RAG & Vector Semantic Store
   ├─ SentenceTransformers (`all-MiniLM-L6-v2`) / Cosine similarity indexer
   ├─ Hybrid BM25 lexical term boost for symbol matching
   └─ Chunks code snippets, AST symbols, and hierarchical summaries
                  │
                  ▼
   5. NVIDIA NOOA WIA Code Understanding Agent
   ├─ Contextual retrieval & technical synthesis
   ├─ Model-agnostic LLM (Gemini, OpenAI, Claude, Nemotron, Heuristic fallback)
   └─ Precise citations with file paths and line number ranges
                  │
                  ▼
   User Question → Relevant Context + Citations → Answer Response
```

---

## ⚡ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, Axios |
| **Backend** | Python 3.10+, FastAPI, SQLModel / SQLAlchemy, Uvicorn, Pydantic v2 |
| **CLI** | Python `argparse`, `sys.stdout` UTF-8 console handler |
| **Agent Framework** | NVIDIA NOOA (NeMo Orchestrated Object Agent Architecture) |
| **Code Parsing** | Python `ast` Standard Library + Multi-Language Regex/Structural Extractors |
| **AI & LLM** | Model-Agnostic (Google Gemini, OpenAI, Anthropic Claude, NVIDIA Nemotron) + Heuristic Fallback |
| **RAG / Vector Store** | SentenceTransformers (`all-MiniLM-L6-v2`) + Cosine Similarity Indexer |
| **Database** | PostgreSQL support with automatic SQLite (`wia.db`) fallback |
| **Containerization** | Docker, Docker Compose |
| **Testing** | `pytest` test suite (18 unit & integration tests) |

---

## 📁 Repository Directory Structure

```
Workspace-Intelligence-Agent/
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   └── nooa_agent.py        # NVIDIA NOOA Code Understanding Agent
│   │   ├── api/
│   │   │   └── router.py            # FastAPI REST endpoints (/ingest, /status, /tree, /export, etc.)
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic v2 settings & environment variables
│   │   │   ├── database.py          # PostgreSQL engine with SQLite fallback
│   │   │   └── llm.py               # Model-agnostic LLM Client (Gemini, OpenAI, Claude, Nemotron)
│   │   ├── models/
│   │   │   └── workspace.py         # SQLModel schemas (Repository, FileNode, ASTSymbol, etc.)
│   │   ├── services/
│   │   │   ├── ingestion/
│   │   │   │   └── crawler.py       # Git cloning, file scanning, filtering, tech stack detection
│   │   │   ├── parser/
│   │   │   │   └── ast_parser.py    # Multi-language AST parsing & symbol extraction
│   │   │   ├── summarizer/
│   │   │   │   └── hierarchical.py  # Bottom-up 5-level hierarchical summarization engine
│   │   │   ├── rag/
│   │   │   │   └── vector_store.py  # Semantic vector embedding and retrieval
│   │   │   └── pipeline.py          # Background ingestion pipeline manager
│   │   ├── cli.py                   # Comprehensive WIA Command-Line Interface
│   │   └── main.py                  # FastAPI application entry point with lifespan handler
│   ├── tests/
│   │   ├── test_wia_pipeline.py     # End-to-end pipeline tests
│   │   ├── test_ast_multilang.py    # Multi-language AST parser tests (TS, Go, Rust, C++)
│   │   └── test_api_endpoints.py    # FastAPI endpoint integration tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── RepoIngestion.tsx    # GitHub/Local repo ingestion card
│   │   │   ├── AnalysisStatus.tsx   # Live step-by-step progress tracker
│   │   │   ├── RepoOverview.tsx     # Tech stack, LOC, entry points & architecture summary
│   │   │   ├── FileExplorer.tsx     # Directory tree explorer with search filter
│   │   │   ├── CodeViewer.tsx       # Code viewer with line numbers & AST symbol inspector
│   │   │   └── AIChat.tsx           # WIA Agent chat interface with RAG citations
│   │   ├── App.tsx                  # Main dashboard container
│   │   ├── main.tsx
│   │   └── index.css                # Tailwind CSS styling
│   ├── package.json
│   ├── vite.config.ts               # Vite dev proxy configuration
│   └── tailwind.config.js
├── docs/
│   ├── ARCHITECTURE.md              # In-depth architectural breakdown
│   ├── API.md                       # Complete REST API documentation
│   ├── CLI.md                       # Complete CLI manual
│   └── HIERARCHICAL_SUMMARIZATION.md # 5-level DAG summarization details
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── main.py                          # CLI entry point (`python main.py`)
├── run_dev.py                       # All-in-one development launcher
├── pyproject.toml                   # Project metadata and pytest configuration
└── README.md
```

---

## 💻 Comprehensive CLI Guide

WIA includes a command-line interface accessible via `python main.py` or `wia` (when installed).

```bash
# View all available CLI commands
python main.py --help
```

### Command Reference

| Command | Usage | Description |
|---|---|---|
| **`scan`** | `python main.py scan <path_or_url> [--name <name>]` | Scan and ingest a local folder or GitHub URL |
| **`query`** | `python main.py query <repo_id_or_name> "<question>"` | Ask AI technical questions about a codebase |
| **`parse`** | `python main.py parse <file_path>` | Parse AST symbols (functions, classes, imports) from a file |
| **`summarize`** | `python main.py summarize <repo_id_or_name>` | Print 5-level hierarchical summaries |
| **`list`** | `python main.py list` | List all ingested repositories |
| **`metrics`** | `python main.py metrics <repo_id_or_name>` | Display LOC, language distribution, and symbol metrics |
| **`export`** | `python main.py export <repo_id_or_name> [--format markdown\|json] [-o out.md]` | Export architecture report |
| **`delete`** | `python main.py delete <repo_id_or_name>` | Delete an ingested repository |
| **`serve`** | `python main.py serve [--port 8000] [--reload]` | Start FastAPI backend server |
| **`dev`** | `python main.py dev` | Launch FastAPI backend + React Vite dashboard |
| **`test`** | `python main.py test` | Run automated test suite |

#### Examples:
```bash
# 1. Ingest current directory
python main.py scan ./ --name "WIA Project"

# 2. Parse symbols from a file
python main.py parse backend/app/services/parser/ast_parser.py

# 3. Query codebase from terminal
python main.py query "WIA Project" "How does the hierarchical summarizer work?"

# 4. Export architecture document
python main.py export "WIA Project" --format markdown --output docs/ARCHITECTURE_REPORT.md
```

---

## 🚀 Setup & Execution Guide

### Prerequisites
- **Python**: `3.10+`
- **Node.js**: `v18+` and `npm`
- **Git**

---

### Option 1: Quick Dev Launcher (Recommended)

Start both the backend and frontend with a single command:

```bash
# 1. Install dependencies
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..

# 2. Run both FastAPI backend and React frontend
python run_dev.py
```

Optional flags for `run_dev.py`:
- `python run_dev.py --backend-only` : Start only FastAPI backend
- `python run_dev.py --frontend-only` : Start only React Vite frontend
- `python run_dev.py --streamlit` : Start Streamlit client
- `python run_dev.py --port 8080` : Specify custom backend port

Access the services:
- **React Dashboard**: [http://localhost:5173](http://localhost:5173)
- **FastAPI Backend**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Option 2: Manual Terminal Execution

- **Terminal 1 (Backend FastAPI)**:
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

- **Terminal 2 (Frontend React Vite)**:
```bash
cd frontend
npm run dev
```

---

### Option 3: Docker Compose

Build and launch the full stack (PostgreSQL + FastAPI Backend + React Nginx Frontend):
```bash
docker-compose up --build
```
Access dashboard at [http://localhost:5173](http://localhost:5173).

---

## 📡 Core REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/ingest` | Ingest a GitHub repository URL or local directory path |
| `GET` | `/api/v1/repos` | List all ingested repositories |
| `GET` | `/api/v1/repos/{repo_id}/status` | Check live ingestion & analysis progress status |
| `GET` | `/api/v1/repos/{repo_id}/tree` | Get complete file and directory tree structure |
| `GET` | `/api/v1/repos/{repo_id}/file?path={rel_path}` | Get code content, AST symbols, and file summary |
| `GET` | `/api/v1/repos/{repo_id}/function/{func_id}` | Get specific function AST details & calls |
| `GET` | `/api/v1/repos/{repo_id}/summary` | Get 5-level hierarchical workspace summaries |
| `POST` | `/api/v1/repos/{repo_id}/query` | Natural language Q&A via NOOA Agent + RAG |
| `GET` | `/api/v1/repos/{repo_id}/symbols/search?q={term}` | Search symbols across codebase |
| `GET` | `/api/v1/repos/{repo_id}/metrics` | Get code metrics, LOC distribution, symbol counts |
| `GET` | `/api/v1/repos/{repo_id}/dependencies/graph` | Extract import graph and dependencies |
| `GET` | `/api/v1/repos/{repo_id}/export?format={md\|json}` | Export architecture report |
| `DELETE` | `/api/v1/repos/{repo_id}` | Delete repository and all analysis data |

*Detailed request/response schemas are available in [docs/API.md](docs/API.md) or `/docs` (Swagger UI).*

---

## 📊 5-Level Hierarchical Summarization Engine

WIA prevents context window overflow by summarizing codebases bottom-up:

1. **Level 1 (Function / Method)**: Summarizes individual functions from docstrings, signatures, and internal function calls.
2. **Level 2 (File / Module)**: Aggregates function summaries and structural exports into a concise module description.
3. **Level 3 (Child Folder)**: Synthesizes file summaries within leaf directories into component summaries.
4. **Level 4 (Parent Folder)**: Aggregates child folder summaries up the tree into subsystem summaries.
5. **Level 5 (Repository Architecture)**: Merges subsystem summaries, entry points, and tech stack into an end-to-end architecture overview.

*Detailed documentation: [docs/HIERARCHICAL_SUMMARIZATION.md](docs/HIERARCHICAL_SUMMARIZATION.md).*

---

## 🤖 NVIDIA NOOA Agent & RAG Architecture

Built according to NVIDIA NOOA (NeMo Orchestrated Object Agent) design principles:
- **Semantic Retrieval**: Uses SentenceTransformers vector embeddings with lexical TF-IDF boost to retrieve exact code chunks, functions, and summaries.
- **Context Construction**: Assembles repository metadata, high-level overview, and retrieved code chunks.
- **Precise Citations**: Every answer includes clickable file paths, chunk types, and exact line number ranges (`Lines X-Y`).
- **Model Agnostic**: Seamlessly switches between Gemini, OpenAI GPT-4o, Anthropic Claude 3.5 Sonnet, NVIDIA Nemotron, and local heuristic fallback.

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
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/wia_db
```

---

## 🧪 Running Automated Tests

Run the complete test suite (18 unit & integration tests covering the ingestion crawler, multi-language AST parser, hierarchical summarizer, RAG vector store, NOOA agent, and FastAPI endpoints):

```bash
# Using pytest directly
pytest

# Or via the WIA CLI
python main.py test
```

---

## 📋 Features Matrix & Roadmap

### ✅ Implemented Core Features:
- [x] **Repository Ingestion & Scanning**: Clones GitHub repos & scans local folders, ignoring noise. Detects tech stack, LOC, configs, and entry points.
- [x] **Multi-Language AST Parsing**: Python `ast`, JavaScript/TypeScript, Go, Rust, and C-like language symbol extractors.
- [x] **5-Level Hierarchical Workspace Summarizer**: Bottom-up aggregation (`Function` → `File` → `Child Folder` → `Parent Folder` → `Repository`).
- [x] **NVIDIA NOOA Code Understanding Agent**: Context-aware technical Q&A with file and line citations.
- [x] **Semantic RAG Vector Store**: Chunks code, symbols, and summaries with dense embeddings and lexical scoring.
- [x] **FastAPI REST API**: 13 endpoints covering ingestion, tree, code viewer, symbols search, metrics, dependency graph, and export.
- [x] **WIA Command-Line Interface (CLI)**: 11 CLI subcommands for direct terminal execution.
- [x] **React + TypeScript + Vite + Tailwind CSS Dashboard**: Dark-mode interface with live status tracker, tree explorer, code viewer, and AI chat.
- [x] **Persistence & Resilience**: PostgreSQL support with automatic SQLite fallback, and local heuristic fallback when API keys are absent.
- [x] **Automated Test Suite**: 18 unit & integration tests with 100% pass rate.

### ⏳ Future Roadmap (Remaining 70% Scope):
- [ ] Specialized Domain Agents (Security Compliance Agent, Code Refactoring Agent, Test Generator).
- [ ] Autonomous Code Modifications & Pull Request Generation.
- [ ] Multi-Agent Inter-Agent Bus & Orchestration.
- [ ] Distributed Queue with Celery / Redis for large-scale enterprise indexing.
- [ ] GitHub App Webhook Integration for continuous CI/CD codebase indexing.

---

## 📚 Further Documentation

- [System Architecture Details](docs/ARCHITECTURE.md)
- [REST API Specification](docs/API.md)
- [CLI User Manual](docs/CLI.md)
- [Hierarchical Summarization Engine Guide](docs/HIERARCHICAL_SUMMARIZATION.md)

---

## 📄 License

This project is licensed under the MIT License.
