# 📡 WIA Core Engine API Reference

Base URL: `http://127.0.0.1:8000/api/v1`

---

## Endpoints Overview

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/ingest` | Ingest repository (GitHub URL or local path) |
| `GET` | `/api/v1/repos` | List all ingested repositories |
| `GET` | `/api/v1/repos/{repo_id}/status` | Get analysis progress status and metadata |
| `GET` | `/api/v1/repos/{repo_id}/tree` | Get repository file and folder hierarchy |
| `GET` | `/api/v1/repos/{repo_id}/file` | Get file content, AST symbols, and file summary |
| `GET` | `/api/v1/repos/{repo_id}/function/{func_id}` | Get AST symbol details |
| `GET` | `/api/v1/repos/{repo_id}/summary` | Get 5-level hierarchical workspace summaries |
| `POST` | `/api/v1/repos/{repo_id}/query` | Ask natural-language questions to WIA Agent + Hybrid RAG |
| `GET` | `/api/v1/repos/{repo_id}/architecture` | Get code knowledge graph & subsystem architecture |
| `GET` | `/api/v1/repos/{repo_id}/flow?entry={symbol}` | Trace code execution call flow |
| `GET` | `/api/v1/repos/{repo_id}/impact?target={symbol}`| Calculate change impact & affected callers/files |
| `GET` | `/api/v1/repos/{repo_id}/onboard` | Generate developer onboarding walkthrough |
| `GET` | `/api/v1/repos/{repo_id}/health` | Run codebase health & complexity audit |
| `GET` | `/api/v1/repos/{repo_id}/symbols/search` | Search symbols across codebase by name |
| `GET` | `/api/v1/repos/{repo_id}/metrics` | Get code metrics, LOC distribution, file stats |
| `GET` | `/api/v1/repos/{repo_id}/dependencies/graph` | Get import graph and external dependencies |
| `GET` | `/api/v1/repos/{repo_id}/export?format={okf\|json}` | Export architecture report or Open Knowledge Format |
| `DELETE` | `/api/v1/repos/{repo_id}` | Delete repository and all indexed artifacts |
