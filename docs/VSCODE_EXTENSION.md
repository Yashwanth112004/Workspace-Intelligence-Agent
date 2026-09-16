# 💻 WIA VS Code Extension User Guide

The **Workspace Intelligence Agent (WIA) VS Code Extension** integrates graph-grounded code intelligence directly into your editor.

---

## ✨ Features

- **🏛️ Architecture Map**: Explore subsystems, modules, and entry points in a dedicated Tree View.
- **🔍 AST Symbol Explorer**: Navigate functions, classes, interfaces, and methods.
- **📦 Dependencies & Imports**: Inspect package manifests and cross-file import statements.
- **🧠 Interactive AI Chat**: Natural-language codebase Q&A with clickable source citations that jump directly to exact file line ranges in the editor.
- **⚡ Editor Context Menu Commands**:
  - `WIA: Explain Code Architecture`
  - `WIA: Trace Code Execution Flow`
  - `WIA: Analyze Change Impact`
  - `WIA: Export Open Knowledge Format (.wia/knowledge/)`

---

## 🛠️ Installation & Development

```bash
# 1. Navigate to extension directory
cd vscode-extension

# 2. Install dependencies & compile TypeScript
npm install
npm run compile

# 3. Press F5 in VS Code to launch the Extension Development Host!
```
