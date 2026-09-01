# WIA — Workspace Intelligence Agent

> **AI-powered workspace intelligence engine for analyzing, understanding, reporting on, and reasoning over software codebases.**

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![CLI Tool](https://img.shields.io/badge/cli-WIA-green.svg)](file:///c:/Users/pulig/OneDrive/Desktop/git_wia/Workspace-Intelligence-Agent)
[![Test Suite](https://img.shields.io/badge/tests-154%20passed-success.svg)](file:///c:/Users/pulig/OneDrive/Desktop/git_wia/Workspace-Intelligence-Agent/tests)

WIA (Workspace Intelligence Agent) is a **CLI-first repository intelligence platform** designed to analyze software repositories, build a structured **Workspace Knowledge Model**, detect change impacts, evaluate architectural boundaries, track dependencies, scan for security leaks, and provide grounded AI reasoning.

Unlike simple chatbot assistants that read raw text snippets, WIA parses abstract syntax trees (AST), constructs directed entity relationship graphs (`IMPORTS`, `DEFINES`, `CALLS`, `DEPENDS_ON`), tracks incremental file hashing, and synthesizes developer explanations grounded in empirical workspace evidence.

---

## ⚡ Key Highlights & Core Capabilities

* 🔍 **Multi-Stage Indexing Pipeline**: Crawls workspace, respects `.gitignore`, computes SHA-256 content hashes, detects programming languages & tech stacks, and runs specialized analyzers.
* 🌳 **Tree-sitter AST & Symbol Parser**: Extracts classes, functions, methods, parameters, docstrings, parent classes, and import statements across multi-language codebases.
* 🕸️ **Workspace Knowledge Graph**: Maps directional dependency edges (`IMPORTS`, `DEFINES`, `CALLS`, `DEPENDS_ON`) between files and symbols in a persistent SQLite relational store.
* 📦 **Dependency Manifest & Conflict Detection**: Parses package manifests (`pyproject.toml`, `requirements.txt`, `package.json`, `Cargo.toml`, `go.mod`), normalizes package names, categorizes dependency types (`runtime`, `dev`, `optional`, `build`), and flags version mismatches.
* 🔒 **Security Secret Scanner with 100% Masking**: Identifies exposed credentials (AWS keys, RSA private keys, GitHub PATs, API tokens, Slack webhooks), classifies test fixtures vs real secrets, and enforces 100% secret masking (`AKIA************MPLE`).
* 📊 **Architecture Boundary & Cycle Intelligence**: Maps 9 system component boundaries, detects circular import dependencies via DFS traversal, computes high fan-in/fan-out metrics, and identifies main entrypoints.
* 💥 **Symbol Refactoring Impact Analysis**: Evaluates symbol callers and file importers, resolves same-name symbols, differentiates direct callers from file importers, and assigns risk classifications (`LOW`, `MEDIUM`, `HIGH`).
* 🧠 **Intent-Grounded AI Reasoning Agent**: Answers developer queries (`wia ask`) using lightweight query intent classification (`ARCHITECTURE`, `WORKFLOW`, `COMPONENT`, `STORAGE`, `FILE_SYMBOL`, `GENERAL`) and custom RAG context retrieval.
* 📖 **Developer-Level Code Explanation**: Explains target files and symbols (`wia explain`), detailing purpose, architectural role, symbols breakdown, used-by dependents, and likely modification consequences.
* 📊 **Persistent HTML Narrative Dashboard**: Generates self-contained, batch-accumulating HTML reports (`wia-report.html`) with executive narrative summaries, component architecture cards, and file intelligence tables.

---

## 💻 Quickstart & Installation

### 1. Installation

Clone or navigate to the repository directory (where `pyproject.toml` is located) and install WIA in editable mode:

```bash
pip install -e .
```

Verify installation:

```bash
wia --version
wia doctor
```

---

## 🛠️ Complete CLI Command Reference Manual

### 1. `wia init` — Initialize Workspace

Initializes the `.wia/` metadata directory and creates `config.json` inside the specified target directory.

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

Executes file discovery, `.gitignore` filtering, SHA-256 change detection, language & framework detection, Tree-sitter AST parsing, dependency manifest analysis, Git hotspot tracking, secret scanning, graph building, and SQLite database persistence.

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

**Example Output**:
```text
=== WIA Workspace Status ===
Workspace: Workspace-Intelligence-Agent
Status: Up to Date
Last Indexed: 2026-09-01T13:00:16.340439+00:00
Indexed Files: 137

Changes Since Last Index:
  Added: 0
  Modified: 0
  Deleted: 0
  Unchanged: 137
```

---

### 4. `wia files` — List Indexed Workspace Files

Lists all files currently indexed in the workspace with metadata.

```bash
wia files [PATH] [--language LANG]
```

* **Flags**:
  * `--language`, `-l`: Filter listed files by language (e.g. `Python`, `Markdown`, `TOML`).

**Example**:
```bash
wia files --language Python
```

---

### 5. `wia info` — Workspace Overview & Statistics

Displays file counts, language distribution percentages, detected frameworks, and index metadata.

```bash
wia info [PATH]
```

**Example Output**:
```text
=== WIA Workspace Information ===
  Workspace: Workspace-Intelligence-Agent
  WIA Version: 0.1.0
  Index Schema Version: 1.0

  File Statistics:
    Discovered Files: 137
    Indexed Files: 137
    Ignored Files: 0

  Language Distribution:
    Python: 134 files (97.8%)
    Git Ignore: 1 files (0.7%)
    Markdown: 1 files (0.7%)
    TOML: 1 files (0.7%)

  Frameworks & Development Tools:
    - pytest
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

* **`analyze deps`**: Parses `pyproject.toml`, `requirements.txt`, `package.json`, `Cargo.toml`, `go.mod`, categorizing runtime vs dev dependencies and detecting version conflicts.
* **`analyze git`**: Identifies high-churn risk files based on Git commit frequency and author activity.
* **`analyze security`**: Scans workspace source files for AWS keys, RSA private keys, PATs, and API tokens with 100% secret masking (`AKIA************MPLE`) and test fixture classification.

**Example**:
```bash
wia analyze security
```

---

### 7. `wia architecture` — System Subsystem & Component Boundary Map

Analyzes the workspace to produce a factually grounded architectural explanation, mapping subsystem boundaries, entrypoints, circular import cycles (DFS), high fan-in/fan-out metrics, and directory hierarchy.

```bash
wia architecture [--workspace PATH]
```

**Example Output**:
```text
=== Architecture Intelligence for 'Workspace-Intelligence-Agent' ===

Subsystem Boundaries (9 mapped):
  * CLI Presentation & Commands (14 files)
  * Service & Workflow Orchestration (6 files)
  * Code, Git & Security Analyzers (8 files)
  * Knowledge Graph & Relationship Engine (4 files)
  * Storage & Persistence Layer (4 files)
  * Core Domain Models & Utilities (18 files)
  * LLM Reasoning & RAG Layer (3 files)
  * Report Generators & Utilities (2 files)
  * Test Suite & Integration Verification (78 files)

High Fan-In Components (Top Consumed Modules):
  * wia/core/index_model.py (Fan-In: 23)
  * wia/cli/formatting.py (Fan-In: 16)
  * wia/core/metadata.py (Fan-In: 15)

High Fan-Out Components (Top Dependent Modules):
  * wia/services/indexing_service.py (Fan-Out: 21)
  * wia/cli/app.py (Fan-Out: 18)

Circular Import Dependency Cycles:
  * No circular import cycles detected (0 cycles found).
```

---

### 8. `wia impact` — Refactoring Impact Analysis

Evaluates downstream callers and file importers for a given target symbol or file, assigning an evidence-backed change risk classification (`LOW`, `MEDIUM`, `HIGH`).

```bash
wia impact <symbol_or_file> [--workspace PATH]
```

**Example**:
```bash
wia impact format_bytes
```

**Example Output**:
```text
=== Impact Analysis for 'format_bytes' ===
  Target Entity: format_bytes
  Defined In: wia/cli/formatting.py
  Target Type: symbol (function)
  Risk Classification: MEDIUM
  Explanation: Modifying 'format_bytes' (defined in 'wia/cli/formatting.py') affects terminal presentation across 16 consuming CLI module(s). Evaluated risk level: MEDIUM.

=== Direct Symbol Callers ===
  * tests/cli/test_formatting.py (CALLS format_bytes)
  * wia/cli/commands/files_cmd.py (CALLS format_bytes)

=== File-Level Dependents (16 modules import defining file) ===
  * tests/cli/test_formatting.py
  * wia/cli/app.py
  * wia/cli/commands/analyze_cmd.py
  ... and 13 additional consuming modules.
```

---

### 9. `wia explain` — Developer-Level Code & Symbol Explanation

Generates a complete technical explanation answering: *"What is this code, what does it do, why does it exist, how does it work, how does it fit into the project, what depends on it, and what should a developer know before modifying it?"*

```bash
wia explain <file_or_symbol> [--workspace PATH]
```

**Example**:
```bash
wia explain wia/services/indexing_service.py
```

---

### 10. `wia ask` — Grounded AI Reasoning Agent

Answers natural language developer questions grounded in indexed workspace evidence using query intent classification (`ARCHITECTURE`, `WORKFLOW`, `COMPONENT`, `STORAGE`, `FILE_SYMBOL`, `GENERAL`).

```bash
wia ask "<question>" [--workspace PATH]
```

**Supported Question Types**:
* `"How is the WIA CLI structured?"` (Architecture intent)
* `"How does WIA index a repository?"` (Workflow intent)
* `"Which component handles dependency analysis?"` (Component intent)
* `"Where is the workspace index stored?"` (Storage intent)

**Example Output**:
```text
=== WIA Workspace Reasoning for 'Workspace-Intelligence-Agent' ===

Question: How is the WIA CLI structured?

Answer:
The WIA CLI is centered around `wia/cli/app.py`, which registers and dispatches CLI subcommands defined under `wia/cli/commands/` (`index_cmd.py`, `status_cmd.py`, `files_cmd.py`, `info_cmd.py`, `analyze_cmd.py`, `architecture_cmd.py`, `search_cmd.py`, `impact_cmd.py`, `explain_cmd.py`, `summary_cmd.py`, `report_cmd.py`, `ask_cmd.py`). Command functions handle terminal argument parsing and Click presentation via `wia/cli/formatting.py`, delegating core application processing to service layer components (`IndexingService`, `StatusService`, `ExplanationService`).

Evidence:
  * `wia/cli/app.py` (CLI entrypoint & command group registration)
  * `wia/cli/commands/` (Subcommand handlers)
  * `wia/cli/formatting.py` (Terminal presentation helpers)
  * `wia/services/` (Service orchestration layer)
  * Active WorkspaceIndex & WorkspaceGraph
```

---

### 11. `wia report` — Generate HTML Intelligence Dashboard

Compiles all workspace intelligence into a self-contained, batch-accumulating HTML report (`wia-report.html`).

```bash
wia report [--workspace PATH] [--output FILE]
```

* **Behavior**: Produces `wia-report.html` and `.wia/report_data.json`. Excludes itself from subsequent indexing to prevent modification feedback loops.

---

### 12. `wia search` — Query Workspace Symbols & Files

Executes relevance-scored search across declared AST symbols, function definitions, classes, and file paths.

```bash
wia search <query> [--workspace PATH] [--language LANG] [--type TYPE] [--limit N]
```

**Example**:
```bash
wia search "format_bytes" --type function
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

**Current Test Status**: `154 passed in 2.51s`.

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
- FileDiscovery                - ASTParser (Tree-sitter)       - WorkspaceIndex
- FileFilter & Gitignore       - ManifestParser (pyproject)    - WorkspaceGraph
- FileHasher (SHA-256)         - SecretScanner (Masking)       - SQLiteStore
- LanguageDetector             - GitAnalyzer                   - VectorStore
```

---

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.
