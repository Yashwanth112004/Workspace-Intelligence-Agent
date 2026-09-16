# 📡 WIA Core REST API Reference

Base URL: `http://localhost:8000/api/v1`

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
| `POST` | `/api/v1/repos/{repo_id}/query` | Ask natural-language questions to WIA Agent + RAG |
| `GET` | `/api/v1/repos/{repo_id}/symbols/search` | Search symbols across codebase by name |
| `GET` | `/api/v1/repos/{repo_id}/metrics` | Get code metrics, LOC distribution, file stats |
| `GET` | `/api/v1/repos/{repo_id}/dependencies/graph` | Get import graph and external dependencies |
| `GET` | `/api/v1/repos/{repo_id}/export` | Export architecture report as Markdown or JSON |
| `DELETE` | `/api/v1/repos/{repo_id}` | Delete repository and all indexed artifacts |

---

## Detailed Endpoint Specifications

### 1. Ingest Repository
- **`POST /api/v1/ingest`**
- **Request Body:**
```json
{
  "source_path": "https://github.com/fastapi/fastapi",
  "name": "FastAPI Repo"
}
```
- **Response (200 OK):**
```json
{
  "repo_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "name": "FastAPI Repo",
  "status": "pending",
  "message": "Repository ingestion started in background."
}
```

---

### 2. Check Status
- **`GET /api/v1/repos/{repo_id}/status`**
- **Response (200 OK):**
```json
{
  "repo_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "name": "FastAPI Repo",
  "source_type": "github",
  "source_path": "https://github.com/fastapi/fastapi",
  "status": "completed",
  "progress_pct": 100,
  "status_message": "Workspace Intelligence Analysis Complete!",
  "total_files": 45,
  "total_loc": 3200,
  "tech_stack": { "Python": 3200 },
  "dependencies": ["pydantic", "starlette"],
  "entry_points": ["main.py"],
  "config_files": ["pyproject.toml"]
}
```

---

### 3. Ask Questions (NOOA Agent + RAG)
- **`POST /api/v1/repos/{repo_id}/query`**
- **Request Body:**
```json
{
  "query": "How is authentication handled in this repository?"
}
```
- **Response (200 OK):**
```json
{
  "query": "How is authentication handled in this repository?",
  "response": "Authentication is implemented using OAuth2 password flow in auth.py...",
  "citations": [
    {
      "file_path": "app/core/auth.py",
      "chunk_type": "code",
      "start_line": 24,
      "end_line": 64,
      "score": 0.884
    }
  ],
  "repo_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "repo_name": "FastAPI Repo"
}
```

---

### 4. Search Symbols
- **`GET /api/v1/repos/{repo_id}/symbols/search?q=login&symbol_type=function`**
- **Response (200 OK):**
```json
{
  "repo_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "query": "login",
  "total_matches": 1,
  "symbols": [
    {
      "id": "sym-123",
      "file_path": "app/api/auth.py",
      "symbol_type": "function",
      "name": "login_access_token",
      "signature": "async def login_access_token(form_data: OAuth2PasswordRequestForm)",
      "start_line": 32,
      "end_line": 48
    }
  ]
}
```

---

### 5. Code Metrics
- **`GET /api/v1/repos/{repo_id}/metrics`**
- **Response (200 OK):**
```json
{
  "repo_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "name": "FastAPI Repo",
  "total_files": 45,
  "total_directories": 8,
  "total_loc": 3200,
  "total_bytes": 128400,
  "tech_stack": { "Python": 3200 },
  "symbol_counts": {
    "functions": 62,
    "classes": 14,
    "imports": 85,
    "total_symbols": 161
  }
}
```

---

### 6. Export Architecture Report
- **`GET /api/v1/repos/{repo_id}/export?format=markdown`**
- Returns a structured Markdown document summarizing the workspace architecture, module breakdown, entry points, and key symbols.
