# WIA — Workspace Intelligence Agent

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Package](https://img.shields.io/badge/PyPI-wia--agent-orange.svg)](https://pypi.org/project/wia-agent/)
[![VS Code Extension](https://img.shields.io/badge/VS%20Code-v0.1.6-007ACC.svg?logo=visualstudiocode)](https://marketplace.visualstudio.com/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-77%20Extension%20%2F%20185%20Core%20Passed-brightgreen.svg)](#-testing--verification)
[![Version](https://img.shields.io/badge/Version-v0.1.6-blue.svg)](pyproject.toml)

**Workspace Intelligence Agent (WIA)** is a high-performance, graph-grounded workspace intelligence platform, non-autoregressive decision router, and codebase reasoning engine for modern developers and IDEs.

WIA combines deterministic Abstract Syntax Tree (AST) parsing, directional entity-relationship graphs, multi-language code comprehension, and the **Laya JEV (Jaccard-Edit-Vector) Decision Engine** to ground developer queries in verified codebase evidence with zero hallucinations.

```text
                                Repository & Workspace
                                           ↓
                     Source Files, Manifests & Jupyter Notebooks
                                           ↓
                          Multi-Language AST & Token Extractors
                                           ↓
                     Inverted Search Index & Knowledge Graph (O(1))
                                           ↓
                 Architectural Subsystems & Refactoring Impact Analysis
                                           ↓
                            Laya Decision Engine (JEV Routing)
                                ┌──────────┴──────────┐
                                │                     │
                        [WIA Core Command]     [AI Fallback Layer]
                                │                     │
                       Deterministic CLI      Context Retrieval (7,500 Tokens)
                                │                     │
                                │              LLM Provider (OpenRouter / NVIDIA /
                                │                            OpenAI / Anthropic / Gemini)
                                └──────────┬──────────┘
                                           ↓
                      Evidence-Grounded, Citation-Backed UI & IDE Output
```

---

## ⚡ Core Capabilities & Highlights

1. **Non-Autoregressive Laya Decision Engine (JEV Routing)**:
   Routes natural-language developer intent to canonical deterministic WIA tools in sub-millisecond time using a multi-factor **Jaccard-Edit-Vector (JEV)** similarity metric with typo tolerance and vocabulary containment.
2. **Evidence-Grounded AI Reasoning (Zero Hallucination)**:
   Every explanation, refactoring suggestion, and architecture breakdown is strictly anchored to real source files, AST symbols, imports, dependency manifests, and line-level citations.
3. **Multi-Language AST & Notebook Parsing**:
   Deep AST symbol extraction for Python, TypeScript, JavaScript, Go, Rust, Java, C#, and C++, including cell-level hierarchy for Jupyter Notebooks (`.ipynb`).
4. **$O(1)$ Directional Knowledge Graph & Search**:
   Maintains high-speed directed dependency edges (`IMPORTS`, `DEFINES`, `CALLS`, `INHERITS`, `TESTS`) with sub-millisecond inverted index lookups.
5. **In-Editor VS Code & Antigravity IDE Extension**:
   Provides in-editor symbol impact CodeLens, interactive sidebar chat with full CSP compliance, dynamic architecture visualizer, and live environment diagnostics.
6. **Multi-Tier Refactoring Impact & Blast Radius**:
   Calculates direct callers, transitive dependents, affected unit tests, and change risk classifications (`LOW`, `MEDIUM`, `HIGH`) before refactoring.
7. **Automated Environment Diagnostics & Repair**:
   `wia doctor` and `wia deps` identify missing packages, version conflicts, and PATH issues, with one-click terminal resolution.
8. **Dual-Mode Offline & Cloud Operation**:
   All indexing, search, architecture, and impact tools execute **100% offline**. Cloud AI reasoning seamlessly integrates with OpenRouter, NVIDIA NIM, OpenAI, Anthropic Claude, and Google Gemini via secure SecretStorage.

---

## 🚀 Installation & Setup

### Option 1: Python Package (CLI & Core)

```bash
# Install WIA distribution from PyPI
pip install wia-agent

# Verify installation & system health
wia --version
wia doctor

# Or execute via python module directly
python -m wia --version
```

### Option 2: Local Development Setup

```bash
# 1. Clone the repository
git clone https://github.com/Yashwanth112004/Workspace-Intelligence-Agent.git
cd Workspace-Intelligence-Agent

# 2. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install in editable mode with development dependencies
pip install -e ".[dev]"

# 4. Run core test suite
pytest
```

### Option 3: VS Code & Antigravity Extension Installation

```bash
# Navigate to the extension directory
cd vscode-extension

# Install dependencies and compile
npm install
npm run compile

# Run full extension test suites (77/77 tests)
npm test

# Package into .vsix extension bundle
npm run package

# Install VSIX into VS Code / Antigravity IDE
code --install-extension wia-agent-0.1.6.vsix
```

---

## ⚙️ AI Provider Configuration

Deterministic commands run 100% offline without API keys. To enable AI reasoning for natural-language queries:

### Supported AI Providers
- **OpenRouter** (`anthropic/claude-3.5-sonnet`, `meta-llama/llama-3.3-70b-instruct`, etc.)
- **NVIDIA NIM** (`meta/llama-3.1-70b-instruct`, `mistralai/mixtral-8x22b-instruct`)
- **OpenAI** (`gpt-4o`, `gpt-4o-mini`, `o1-preview`)
- **Anthropic** (`claude-3-5-sonnet-20241022`, `claude-3-haiku-20240307`)
- **Google Gemini** (`gemini-1.5-flash`, `gemini-1.5-pro`)
- **Local Offline Engine** (No API key required)

### CLI Configuration
```bash
# Option A: Environment Variables (or .env file)
export OPENROUTER_API_KEY="sk-or-v1-..."
# or
export NVIDIA_API_KEY="nvapi-..."
export OPENAI_API_KEY="sk-..."

# Option B: WIA Configuration Manager
wia config --set-provider openrouter
wia config --set-model anthropic/claude-3.5-sonnet
wia config --set-key "sk-or-v1-..."

# View active configuration
wia config --show
```

---

## 🛠️ Complete CLI Command Reference

| Command | Syntax | Description | Example |
|---|---|---|---|
| **`init`** | `wia init [<path>]` | Initialize `.wia/` workspace configuration and index storage | `wia init ./` |
| **`index`** | `wia index [--workers N] [-f]` | High-speed parallel incremental indexing & AST extraction | `wia index --workers 8 -f` |
| **`status`** | `wia status` | Inspect index state, timestamps, and detected file changes | `wia status` |
| **`summary`** | `wia summary` | Generate comprehensive repository overview & tech stack | `wia summary` |
| **`search`** | `wia search "<term>" [--type <kind>]` | $O(1)$ inverted index search across symbols, files, docstrings | `wia search "WorkspaceIndex"` |
| **`explain`** | `wia explain <target>` | Evidence-grounded 13-section technical breakdown of a component | `wia explain wia/core/impact.py` |
| **`impact`** | `wia impact <symbol>` | Multi-tier refactoring blast radius and caller ripples | `wia impact WorkspaceGraph` |
| **`architecture`** | `wia architecture` | Subsystem boundaries, fan-in/fan-out, and import cycles | `wia architecture` |
| **`flow`** | `wia flow <entry_symbol>` | Forward call graph tracing and execution hierarchy | `wia flow main` |
| **`diff`** | `wia diff` | Git status diffing and affected symbol ripple analysis | `wia diff` |
| **`deps`** | `wia analyze deps` | Package manifest audit, missing imports, and version conflicts | `wia analyze deps` |
| **`git`** | `wia analyze git` | Git commit churn, hotspot files, and author contribution maps | `wia analyze git` |
| **`security`** | `wia analyze security` | High-throughput secret, token, and vulnerability scanner | `wia analyze security` |
| **`doctor`** | `wia doctor` | Diagnostic audit of Python environment, SQLite, and PATH | `wia doctor` |
| **`report`** | `wia report [--output <path>]` | Generate interactive standalone HTML intelligence report | `wia report --output wia-report.html` |
| **`export`** | `wia export [--format okf\|json]` | Export Open Knowledge Format artifacts into `.wia/knowledge/` | `wia export --format okf` |
| **`ask`** | `wia ask "<query>" [--offline]` | Evidence-grounded natural language Q&A with citations | `wia ask "How does Laya routing work?"` |
| **`config`** | `wia config [--show] [--set-provider <p>]` | Manage active AI providers, models, and credentials | `wia config --show` |
| **`serve`** | `wia serve [--port 8000]` | Start local FastAPI daemon for IDE extensions | `wia serve --port 8000` |
| **`version`** | `wia version` | Print version information and build metadata | `wia version` |

---

## 🧩 IDE & Extension Integration

The WIA VS Code & Antigravity IDE Extension (`wia-agent`) provides seamless workspace intelligence directly inside your editor:

- **🤖 WIA Interactive Agent & Sidebar Chat (`wia-agent-view`)**:
  Conversational interface with Laya non-autoregressive routing, quick-action chips, and instant execution of WIA commands.
- **🔍 In-Editor Symbol Impact CodeLens**:
  Clickable CodeLens inline above classes and functions:
  - `⚡ WIA Impact (<symbol>)`: Instant blast radius and risk rating.
  - `🔍 Trace Flow`: Interactive execution call graph.
- **🏛️ Visual Architecture & Subsystem Visualizer (`wia.architecture`)**:
  Interactive Webview mapping components, circular dependency cycles (DFS detection), and entry points.
- **⚡ Refactoring Change Impact Inspector (`wia.impact`)**:
  Deep-dive panel displaying risk level badges, callers list, and affected files.
- **🌲 Activity Bar Explorer Views**:
  - `🏛️ Architecture & Subsystems`
  - `🔍 AST Symbol Explorer`
  - `📦 Dependencies & Imports`
- **🔒 VS Code SecretStorage Integration**:
  API keys are encrypted in OS-level credential vaults without plaintext `.env` leakage.

---

## 🧠 Laya Decision Engine (JEV Routing)

WIA integrates the **Laya Non-Autoregressive Decision Engine** to classify user natural language requests with sub-millisecond latency:

$$\text{JEV Score} = 0.35 \cdot \text{SoftJaccard} + 0.35 \cdot \text{NormalizedEditSim} + 0.30 \cdot \text{VectorScore}$$

- **Soft Jaccard with Containment**: Evaluates word overlap and token containment.
- **Normalized Levenshtein Edit Similarity**: Handles typos and morphological variations (e.g. `archtecture map` $\to$ `architecture`).
- **Domain Keyword Vector Overlap**: Rewards technical keywords and intent matching.
- **AI Fallback Layer**: Conceptual, design, or open-ended questions seamlessly transition to the grounded AI reasoning layer.

---

## 📁 Repository Structure

```text
Workspace-Intelligence-Agent/
├── wia/                               # Core Python WIA Package
│   ├── analyzers/
│   │   ├── code/                      # AST parsers & Jupyter notebook parsers
│   │   ├── dependency/                # Single-pass manifest & conflict detector
│   │   ├── git/                       # Git churn & hotspot analyzer
│   │   └── security/                  # High-throughput secret & token scanner
│   ├── cli/
│   │   ├── app.py                     # Lazy CLI dispatcher
│   │   ├── formatting.py              # Terminal ANSI & table formatter
│   │   └── commands/                  # Individual CLI subcommands
│   ├── core/
│   │   ├── architecture.py            # Subsystem boundaries & DFS cycle detector
│   │   ├── discovery.py               # Fast path traversal & file discovery
│   │   ├── impact.py                  # Multi-tier blast radius & ripple evaluator
│   │   ├── index_model.py             # WorkspaceIndex schema & data structures
│   │   ├── inverted_index.py          # O(1) inverted token & symbol search index
│   │   └── retrieval.py               # 7,500-token evidence-grounded retriever
│   ├── knowledge/
│   │   ├── graph.py                   # Directional WorkspaceGraph (O(1) edge map)
│   │   ├── embeddings.py              # SentenceTransformers vector embeddings
│   │   └── vector_store.py            # Vector similarity search index
│   ├── llm/
│   │   ├── base.py                    # Provider abstractions (OpenRouter, NVIDIA, OpenAI, Anthropic, Gemini, Local)
│   │   ├── reasoning.py               # Grounded ReasoningEngine
│   │   └── relevance.py               # Grounding relevance grader
│   ├── services/                      # IndexingService, ExplanationService, StatusService
│   └── storage/                       # SQLiteStore with WAL mode & atomic batching
├── vscode-extension/                  # VS Code & Antigravity IDE Extension
│   ├── src/
│   │   ├── auth/                      # SecretStorage & multi-provider credentials
│   │   ├── decision/                  # LayaDecisionEngine & JEVRouter
│   │   ├── executor/                  # WiaExecutor CLI & terminal bridge
│   │   ├── llm/                       # WiaLLMClient multi-provider client
│   │   ├── panels/                    # Architecture, Impact, and Chat webviews
│   │   ├── providers/                 # AgentViewProvider, TreeViews, CodeLens
│   │   ├── registry/                  # Canonical WIA 30-command registry
│   │   └── test/                      # 77 automated extension unit tests
│   ├── package.json                   # Extension manifest & command registry
│   └── wia-agent-0.1.6.vsix           # Packaged extension distribution
├── tests/                             # Python Core Test Suites (185 tests)
│   ├── unit/                          # Unit tests for analyzers, core, and graph
│   ├── integration/                   # Pipeline and end-to-end tests
│   └── cli/                           # CLI command tests
├── pyproject.toml                     # PEP 517/621 build configuration
└── README.md                          # Project Documentation
```

---

## 🧪 Testing & Verification

WIA is backed by comprehensive automated test suites covering both the Python engine and the VS Code extension:

```bash
# 1. Run Core Python Engine Test Suite (185 tests)
pytest -v

# 2. Run VS Code Extension Test Suite (77 tests)
cd vscode-extension
npm test

# 3. Compile and Validate Extension Bundle
npm run compile
npm run package
```

---

## 🔒 Security & Privacy Guarantees

- **Zero Bundled Credentials**: No API keys or tokens are stored in repository code or distribution packages.
- **Automatic Secret Masking**: All API keys and sensitive tokens in configuration outputs and logs are masked.
- **Local-First Architecture**: Source code, AST models, and knowledge graphs remain entirely on your local machine.
- **Strict Content Security Policy (CSP)**: Extension webviews run under sandboxed CSP policies ensuring secure execution.

---

## 📄 License

Distributed under the **Apache License 2.0**. See [`LICENSE`](LICENSE) for details.
