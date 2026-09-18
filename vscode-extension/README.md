# 🧠 Workspace Intelligence Agent (WIA) — VS Code Extension

**WIA for Visual Studio Code** is an AI-powered code intelligence companion providing in-editor symbol impact CodeLens, visual subsystem architecture maps, AST symbol exploration, and grounded AI reasoning over your repository.

---

## ⚡ Key Highlights & Capabilities

- **🔍 In-Editor Symbol Impact & Flow CodeLens**:
  - Automatically identifies classes, functions, and methods across Python, TypeScript, JavaScript, Go, and Rust.
  - Displays inline clickable CodeLens actions:
    - `⚡ WIA Impact (<symbol>)`: Inspects direct callers, importing modules, and refactoring risk rating (`LOW`, `MEDIUM`, `HIGH`).
    - `🔍 Trace Flow`: Traces execution call chains starting from that function.
- **🏛️ Architecture & Subsystems Visualizer**:
  - Dedicated interactive Webview panel rendering subsystem boundaries, circular import cycle warnings (detected via DFS cycle analysis), and high fan-in/fan-out metrics.
- **💥 Refactoring Change Impact Inspector**:
  - Deep-dive panel displaying risk classification badges, caller lists, and downstream affected files with click-to-open editor links.
- **🧠 Interactive AI Assistant Chat**:
  - Natural-language codebase Q&A powered by the WIA NOOA agent with quick-prompt chips (*Architecture*, *Onboarding Guide*, *Health Audit*, *Impact Risks*), markdown code rendering, and clickable source citations.
- **🌲 Activity Bar Explorer Views**:
  - `🏛️ Architecture & Subsystems`
  - `🔍 AST Symbol Explorer`
  - `📦 Dependencies & Imports`
- **🚀 Daemon Lifecycle Management**:
  - Integrated status bar indicator (`$(zap) WIA: Online` / `$(warning) WIA: Offline`).
  - One-click daemon startup command: `WIA: Start Local Intelligence Daemon`.

---

## 🛠️ Usage & Commands

| Command | Title | Action |
|---|---|---|
| `wia.scanWorkspace` | **WIA: Scan & Ingest Workspace** | Ingests and indexes the current workspace in background |
| `wia.openChat` | **WIA: Open AI Chat Assistant** | Opens the interactive WIA AI Assistant panel |
| `wia.showArchitecturePanel` | **WIA: Open Visual Architecture Map** | Visualizes subsystems, circular cycles, and tech stack |
| `wia.showImpactPanel` | **WIA: Open Change Impact Inspector** | Inspects refactoring blast radius and caller ripples |
| `wia.traceFlow` | **WIA: Trace Code Execution Flow** | Interactive call chain trace from an entry point |
| `wia.startDaemon` | **WIA: Start Local Intelligence Daemon** | Launches `run_dev.py` in an integrated terminal |
| `wia.exportOkf` | **WIA: Export Open Knowledge Format** | Exports `.wia/knowledge/` OKF artifacts |
| `wia.refreshViews` | **WIA: Refresh Knowledge Views** | Refreshes all tree views and CodeLens caches |

---

## ⚙️ Configuration

- `wia.apiBaseUrl`: Base URL of the local WIA Engine Daemon API (default: `http://127.0.0.1:8000`).
- `wia.enableCodeLens`: Enable/disable in-editor WIA CodeLens showing symbol impact and caller counts (default: `true`).

---

## 📝 License

Distributed under the MIT License. See `LICENSE` for details.
