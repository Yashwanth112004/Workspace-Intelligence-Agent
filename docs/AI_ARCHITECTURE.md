# 🤖 WIA AI Architecture & NVIDIA NOOA Agent

WIA's reasoning layer is designed around the **NVIDIA NOOA (NeMo Orchestrated Object Agent)** architecture, providing tool-augmented code understanding rather than monolithic vector search.

---

## 🛠️ Specialized AI Agent Capabilities

| Feature | Query Examples | Agent Tool / Action |
|---|---|---|
| **Architecture Explanation** | "Explain this system architecture", "How does backend talk to database?" | Synthesizes Level 5 & 4 summaries + knowledge graph subsystem edges |
| **Code Flow Tracing** | "Trace what happens when login is called", "Show execution flow" | `trace_flow()` traversing call graph BFS from root entry |
| **Dependency Impact** | "What breaks if I change AuthService?", "Who calls this function?" | `analyze_impact()` traversing 1st and 2nd degree incoming graph edges |
| **Developer Onboarding** | "Explain this repo to a new developer", "How do I get started?" | Generates structured guide with tech stack, entry points, and subsystems |
| **Repository Health Audit** | "Run code health audit", "Show complexity hotspots" | Analyzes LOC, functions, class ratios, and sensitive file coverage |
