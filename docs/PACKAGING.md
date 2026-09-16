# 📦 WIA Python Packaging Guide

This guide documents the packaging architecture and PyPI distribution for **Workspace Intelligence Agent (WIA)**.

---

## 1. 🏷️ Distribution & Entry Points

- **PyPI Distribution Name**: `wia-agent`
- **CLI Executable Command**: `wia`
- **Package Root**: `app` / `wia`

```bash
# Standard user installation
pip install wia-agent

# Verify CLI
wia --help
```

---

## 2. 🏗️ Build Configuration (`pyproject.toml`)

WIA uses modern PEP 517 / PEP 621 packaging with `setuptools`:

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "wia-agent"
version = "0.3.0"
description = "Workspace Intelligence Agent (WIA) — Graph-grounded workspace intelligence platform for code understanding, AST parsing, flow tracing, and RAG Q&A"
readme = "README.md"
requires-python = ">=3.10"

[project.scripts]
wia = "app.cli:cli_entry"
```

---

## 3. 🛡️ Packaging Security & Exclusion Rules

The package manifest strictly excludes non-runtime files:
- `.env` and `.env.*` credentials
- Local databases (`*.db`, `*.sqlite3`)
- `data/repos/` local clone caches
- `node_modules/` and frontend build artifacts
- `tests/` and test caches (`.pytest_cache`)

---

## 4. 🚀 Local Build & Verification

```bash
# Clean previous builds
python -m build

# Install in isolated environment
pip install dist/wia_agent-0.3.0-py3-none-any.whl

# Test CLI
wia --help
wia scan /path/to/repo
wia architecture repo_name
wia symbols repo_name
```
