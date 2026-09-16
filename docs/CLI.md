# 💻 WIA Command-Line Interface (CLI) User Guide

The WIA CLI provides direct terminal access to repository scanning, AST code parsing, hierarchical summarization, RAG queries, metric extraction, and developer environments.

---

## 🛠️ Installation & Execution

Run via `python main.py` or `uv run python main.py` from the project root:

```bash
# Display CLI help
python main.py --help
```

---

## 📋 Available CLI Commands

### 1. `scan` - Ingest and Analyze a Codebase
Ingest a local repository directory or clone a public GitHub repository and run the full intelligence pipeline.
```bash
# Ingest current local directory
python main.py scan ./

# Ingest a specific folder with custom name
python main.py scan /path/to/project --name "My Backend"

# Ingest a GitHub repository
python main.py scan https://github.com/fastapi/fastapi
```

---

### 2. `query` - Ask AI Technical Questions with RAG
Ask technical questions about any ingested repository directly from your terminal. Includes source file citations and line numbers.
```bash
# Query by repository name
python main.py query "My Backend" "What database models are defined?"

# Query by repository ID
python main.py query 9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d "Explain the authentication flow"
```

---

### 3. `parse` - Inspect AST Symbols in a Source File
Parse and inspect functions, methods, classes, signatures, and imports in any supported file.
```bash
python main.py parse backend/app/services/parser/ast_parser.py
```

---

### 4. `summarize` - View 5-Level Hierarchical Summaries
Print the bottom-up hierarchical summaries (Repository → Parent Folders → Child Folders → Files → Functions).
```bash
python main.py summarize "My Backend"
```

---

### 5. `list` - List All Ingested Repositories
Display a table of all analyzed repositories, their IDs, status, file counts, and LOC.
```bash
python main.py list
```

---

### 6. `metrics` - Codebase Complexity & Statistics
Display lines of code, language breakdown, total directories, and symbol counts.
```bash
python main.py metrics "My Backend"
```

---

### 7. `export` - Generate Architecture Documentation
Export the complete architectural overview and module summaries into Markdown or JSON.
```bash
# Output to terminal
python main.py export "My Backend" --format markdown

# Save directly to a file
python main.py export "My Backend" --format markdown --output architecture_report.md
```

---

### 8. `delete` - Remove an Ingested Repository
Delete repository records, symbols, summaries, and disk caches.
```bash
python main.py delete 9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d
```

---

### 9. `serve` - Run the FastAPI Server
```bash
python main.py serve --port 8000 --reload
```

---

### 10. `dev` - Launch Full Development Environment
Starts both FastAPI backend and React Vite dashboard concurrently.
```bash
python main.py dev
```

---

### 11. `test` - Run Automated Tests
```bash
python main.py test
```
