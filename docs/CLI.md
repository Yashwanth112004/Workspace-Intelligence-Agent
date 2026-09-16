# 💻 WIA Command-Line Interface (CLI) User Manual

The WIA CLI provides direct terminal access to repository scanning, AST code parsing, hierarchical summarization, code flow tracing, impact analysis, health audits, and OKF exports.

---

## 🛠️ Installation & Execution

```bash
# Display CLI help
python main.py --help
# Or when installed via pip:
wia --help
```

---

## 📋 Available CLI Commands

| Command | Usage | Description |
|---|---|---|
| **`scan`** | `wia scan <path_or_url> [--name <name>]` | Ingest and analyze a codebase |
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

## 💡 Practical Examples

```bash
# 1. Scan current repository
python main.py scan ./ --name "My Project"

# 2. Trace execution call flow
python main.py flow "My Project" --entry "main"

# 3. Analyze change impact
python main.py impact "My Project" --symbol "ASTParserEngine"

# 4. Generate Open Knowledge Format documentation
python main.py export "My Project" --format okf --output ./

# 5. Ask technical questions with hybrid retrieval
python main.py query "My Project" "How does secret safety redaction work?"
```
