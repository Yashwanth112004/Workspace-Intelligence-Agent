# 📦 Open Knowledge Format (OKF) Export

WIA supports exporting codebase intelligence in **Open Knowledge Format (OKF)**, producing a portable, human-readable, Git-friendly documentation structure inside `.wia/knowledge/`.

---

## 📁 `.wia/knowledge/` Structure

```
.wia/
└── knowledge/
    ├── index.md           # Master documentation index with tech stack & stats
    ├── repository.md      # Executive summary, entry points, config files
    ├── architecture.md    # Subsystems breakdown and high-level architecture
    ├── subsystems/        # Deep-dive guides for every major subsystem
    ├── modules/           # Markdown per-module guides with defined symbols
    └── symbols/           # Exported symbol index with signatures
```

---

## 🚀 Generating OKF Exports

### Via CLI
```bash
wia export "My Repo" --format okf --output ./
```

### Via VS Code Extension
Run the command: `WIA: Export Open Knowledge Format (.wia/knowledge/)`
