# 💻 WIA VS Code Extension User Guide

The **Workspace Intelligence Agent (WIA) VS Code Extension** integrates graph-grounded code intelligence directly into your editor.

---

## ✨ Key Features & Capabilities

- **⚡ In-Editor Symbol Impact CodeLens**:
  - Automatically analyzes functions, classes, and methods across Python, TypeScript, JavaScript, Go, and Rust.
  - Displays inline CodeLens actions above definitions:
    - `⚡ WIA Impact (<symbol>)`: Inspects caller ripple effects, file importers, and refactoring risk.
    - `🔍 Trace Flow`: Traces execution call chains starting from that symbol.
- **🏛️ Architecture & Subsystem Visualizer**:
  - Dedicated interactive Webview panel rendering subsystem boundaries, circular import cycle warnings (DFS), and high fan-in/fan-out metrics.
- **💥 Refactoring Change Impact Inspector**:
  - Deep-dive panel displaying risk classification badges (`LOW`, `MEDIUM`, `HIGH`), caller lists, and downstream affected files with click-to-open editor links.
- **🧠 Interactive AI Assistant Chat**:
  - Natural-language codebase Q&A powered by the WIA NOOA agent with quick-prompt chips (*Architecture*, *Onboarding Guide*, *Health Audit*, *Impact Risks*), markdown code rendering, and clickable source citations.
- **🌲 Dedicated Activity Bar Views**:
  - `🏛️ Architecture & Subsystems`
  - `🔍 AST Symbol Explorer`
  - `📦 Dependencies & Imports`
- **🚀 Daemon Lifecycle Management**:
  - Integrated status bar indicator (`$(zap) WIA: Online` / `$(warning) WIA: Offline`).
  - One-click daemon startup command `WIA: Start Local Intelligence Daemon`.
- **⚡ Editor Context Menu Commands**:
  - `WIA: Show Change Impact Inspector`
  - `WIA: Explain Code Architecture`
  - `WIA: Trace Code Execution Flow`
  - `WIA: Export Open Knowledge Format (.wia/knowledge/)`

---

## 🛠️ Installation & Packaging

### 1. Build and Compile Extension
```bash
cd vscode-extension
npm install
npm run compile
```

### 2. Package into Standalone VSIX File
```bash
npm run package
# Generates wia-vscode-0.1.1.vsix
```

### 3. Install VSIX into VS Code
In VS Code:
1. Open the Extensions view (`Ctrl+Shift+X` or `Cmd+Shift+X`).
2. Click the `...` menu in the top right.
3. Select **Install from VSIX...**
4. Choose `vscode-extension/wia-vscode-0.1.1.vsix`.

Or via command line:
```bash
code --install-extension vscode-extension/wia-vscode-0.1.1.vsix
```
