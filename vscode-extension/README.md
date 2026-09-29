# 🧠 Workspace Intelligence Agent (WIA) — VS Code & Antigravity IDE Extension

[![VS Code Extension](https://img.shields.io/badge/VS%20Code-v0.1.1-007ACC.svg?logo=visualstudiocode)](https://marketplace.visualstudio.com/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](../LICENSE)
[![Tests](https://img.shields.io/badge/Tests-82%20Passed-brightgreen.svg)](#-automated-testing)

**WIA for Visual Studio Code & Antigravity IDE** is an AI-powered code intelligence companion providing in-editor symbol impact CodeLens, interactive sidebar agent chat, live subsystem architecture visualizers, and grounded AI reasoning over your entire repository.

---

## ⚡ Core Features & Views

### 1. 🤖 Interactive Sidebar Agent & Chat (`wia-agent-view`)
- **Laya JEV (Jaccard-Edit-Vector) Router**: Instantly classifies natural-language queries into canonical WIA commands or routes conceptual questions to grounded AI reasoning.
- **Pure Natural-Language Interface**: Type natural questions without requiring slash-command syntax.
- **Quick-Action Chips**: One-click shortcuts for *Architecture*, *Dependencies*, *Doctor Diagnostics*, and *Status*.
- **Interactive Markdown & Cards**: Rich rendering for impact analysis, caller lists, code blocks, and direct file jump links.
- **Content Security Policy (CSP)**: Fully compliant and sandboxed for fast, reliable interaction.

### 2. 🔍 In-Editor Symbol Impact & Flow CodeLens
- Automatically analyzes classes, functions, and methods across **Python, TypeScript, JavaScript, Go, Rust, Java, C#, C++**.
- Inline clickable CodeLens indicators:
  - `⚡ WIA Impact (<symbol>)`: Calculates direct callers, importing modules, and refactoring risk classification (`LOW`, `MEDIUM`, `HIGH`).
  - `🔍 Trace Flow`: Traces execution call chains starting from that function.

### 3. 🏛️ Architecture & Subsystems Visualizer (`wia.architecture`)
- Interactive visual panel displaying:
  - Component boundaries and roles.
  - Circular dependency cycles detected via DFS cycle analysis.
  - Fan-in and fan-out metrics with click-to-open file navigation.

### 4. 💥 Refactoring Change Impact Inspector (`wia.impact`)
- Deep-dive panel evaluating downstream ripple effects before refactoring:
  - Risk classification badges (`HIGH`, `MEDIUM`, `LOW`).
  - Direct callers and dependent modules.
  - Affected test suites and execution paths.

### 5. 🌲 Activity Bar Tree Views
- **🏛️ Architecture & Subsystems**: Hierarchical component tree.
- **🔍 AST Symbol Explorer**: Indexed classes, functions, and global symbols.
- **📦 Dependencies & Imports**: Manifest dependencies, missing packages, and conflict indicators.

### 6. 🔒 Multi-Provider AI Credentials via SecretStorage
- Store API keys securely in OS-level credential vaults (VS Code SecretStorage).
- Seamlessly switch between **OpenRouter, NVIDIA NIM, OpenAI, Anthropic Claude, Google Gemini**, and **Local Offline Mode**.

---

## 🛠️ Complete Registered Commands

| Command Identifier | Title | Description |
|---|---|---|
| `wia.openAgent` | **WIA: Open WIA Agent & Chat** | Opens and focuses the sidebar interactive agent |
| `wia.openChat` | **WIA: Open AI Chat Assistant** | Alias to open WIA Agent & Chat |
| `wia.scanWorkspace` | **WIA: Scan & Ingest Workspace** | Ingests and indexes the active workspace |
| `wia.architecture` | **WIA: Open Visual Architecture Map** | Displays subsystem boundaries and cycle analysis |
| `wia.showArchitecturePanel` | **WIA: Open Architecture Visualizer** | Opens visual architecture Webview panel |
| `wia.explainArchitecture` | **WIA: Explain Architecture** | Generates architectural component breakdown |
| `wia.impact` | **WIA: Open Change Impact Inspector** | Inspects symbol refactoring blast radius |
| `wia.showImpactPanel` | **WIA: Open Change Impact Panel** | Opens the change impact Webview panel |
| `wia.analyzeImpactForSymbol` | **WIA: Analyze Impact for Symbol** | CodeLens handler to evaluate symbol risk |
| `wia.flow` | **WIA: Trace Code Execution Flow** | Traces call hierarchy from an entry point |
| `wia.traceFlowForSymbol` | **WIA: Trace Call Flow for Symbol** | CodeLens handler to trace symbol call chains |
| `wia.deps` | **WIA: Analyze Dependencies & Conflicts** | Audits manifests for missing packages and conflicts |
| `wia.fixEnvironment` | **WIA: Fix Environment & Install Dependencies** | Executes automatic package installation |
| `wia.status` | **WIA: Workspace Index Status** | Shows indexing status and timestamp |
| `wia.doctor` | **WIA: Run Environment Diagnostics** | Runs system diagnostics on Python, SQLite, PATH |
| `wia.summary` | **WIA: Generate Codebase Summary** | Generates comprehensive repository overview |
| `wia.files` | **WIA: List Indexed Files** | QuickPick search across all indexed files |
| `wia.info` | **WIA: Show Tech Stack Info** | Displays detected frameworks and languages |
| `wia.search` | **WIA: Search Symbols & Files** | Inverted index search for functions and classes |
| `wia.explainSymbol` | **WIA: Explain Symbol or File** | Generates detailed 13-section technical explanation |
| `wia.diff` | **WIA: Audit Git Diff Impact** | Analyzes uncommitted git changes and ripple effects |
| `wia.gitHotspots` | **WIA: Analyze Git Churn & Hotspots** | Identifies frequently modified hotspot files |
| `wia.securityScan` | **WIA: Scan for Secrets & Vulnerabilities** | Scans workspace for leaked tokens and secrets |
| `wia.generateReport` | **WIA: Generate HTML Intelligence Report** | Creates standalone interactive HTML report |
| `wia.runProject` | **WIA: Run Project** | Executes detected project run command in terminal |
| `wia.runTests` | **WIA: Run Tests** | Executes detected automated test suite |
| `wia.buildProject` | **WIA: Build Project** | Executes detected build/compile command |
| `wia.config` | **WIA: Configure AI Provider & Models** | Interactive modal for LLM provider and API key setup |
| `wia.refreshViews` | **WIA: Refresh Knowledge Views** | Refreshes tree views, CodeLens, and index caches |
| `wia.startDaemon` | **WIA: Start Local Engine Daemon** | Starts the local WIA backend daemon on port 8000 |

---

## ⚙️ Configuration Settings

Configure extension settings via `settings.json` or the VS Code Settings UI:

| Setting | Type | Default | Description |
|---|---|---|---|
| `wia.provider` | `string` | `"openrouter"` | Active AI reasoning provider (`openrouter`, `nvidia`, `openai`, `anthropic`, `gemini`, `local`) |
| `wia.model` | `string` | `"anthropic/claude-3.5-sonnet"` | Model identifier for AI reasoning |
| `wia.apiBaseUrl` | `string` | `"http://127.0.0.1:8000"` | Base URL of the local WIA Engine Daemon API |
| `wia.enableCodeLens` | `boolean` | `true` | Enable/disable in-editor CodeLens for symbol impact and flow tracing |

---

## 🧪 Automated Testing

The extension includes 82 automated unit tests covering JEV routing, health models, and execution pipelines:

```bash
# Compile TypeScript
npm run compile

# Run all 82 automated extension tests
npm test

# Package VSIX distribution
npx @vscode/vsce package
```

---

## 📄 License

Distributed under the **Apache License 2.0**. See [`LICENSE`](../LICENSE) for details.
