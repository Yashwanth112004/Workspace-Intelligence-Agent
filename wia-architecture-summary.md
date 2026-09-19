# Workspace Architecture & Intelligence Context: Workspace-Intelligence-Agent
- **Query Intent**: `GENERAL`
- **Indexed Path**: `C:\Users\pulig\OneDrive\Desktop\WIA\Workspace-Intelligence-Agent`
- **Indexed At**: `2026-09-19T03:49:50.619388+00:00`
- **WIA Version**: `0.1.1`

## Languages & Frameworks
- **Detected Frameworks**: Docker, FastAPI, pytest
- **Languages**: Unknown (19 files), YAML (5 files), Git Ignore (4 files), Markdown (27 files), Python (239 files), TOML (2 files), SQL (4 files), HTML (2 files), JSON (11 files), JavaScript (112 files), JavaScript React (30 files), CSS (2 files), Docker (2 files), TypeScript (6 files)

## Workspace File & Symbol Overview
### `.env.example` (Unknown)
  - **Declared Symbols**: None extracted

### `.github/workflows/ci.yml` (YAML)
  - **Declared Symbols**: None extracted

### `.github/workflows/release.yml` (YAML)
  - **Declared Symbols**: None extracted

### `.gitignore` (Git Ignore)
  - **Declared Symbols**: None extracted

### `.python-version` (Unknown)
  - **Declared Symbols**: None extracted

### `Dockerfile.backend` (Unknown)
  - **Declared Symbols**: None extracted

### `MANIFEST.in` (Unknown)
  - **Declared Symbols**: None extracted

### `README.md` (Markdown)
  - **Declared Symbols**: None extracted

### `backend/app/__init__.py` (Python)
  - **Declared Symbols**: None extracted

### `backend/app/agent/__init__.py` (Python)
  - **Declared Symbols**: `app.agent.nooa_agent.WIACodeUnderstandingAgent` (import)

### `backend/app/agent/nooa_agent.py` (Python)
  - **Declared Symbols**: `logging` (import), `typing.List` (import), `typing.Dict` (import), `typing.Any` (import), `typing.Tuple` (import), `typing.Optional` (import), `app.models.workspace.Repository` (import), `app.models.workspace.VectorChunk` (import), `app.models.workspace.WorkspaceSummary` (import), `app.models.workspace.ASTSymbol` (import)

### `backend/app/api/__init__.py` (Python)
  - **Declared Symbols**: `app.api.router.router` (import)

### `backend/app/api/router.py` (Python)
  - **Declared Symbols**: `fastapi.APIRouter` (import), `fastapi.HTTPException` (import), `fastapi.BackgroundTasks` (import), `fastapi.Depends` (import), `fastapi.Query` (import), `fastapi.Response` (import), `pydantic.BaseModel` (import), `pydantic.Field` (import), `typing.Optional` (import), `typing.List` (import)

### `backend/app/cli.py` (Python)
  - **Declared Symbols**: `os` (import), `sys` (import), `time` (import), `argparse` (import), `logging` (import), `typing.Optional` (import), `typing.List` (import), `typing.Dict` (import), `sqlmodel.Session` (import), `sqlmodel.select` (import)

### `backend/app/core/__init__.py` (Python)
  - **Declared Symbols**: None extracted

### `backend/app/core/config.py` (Python)
  - **Declared Symbols**: `os` (import), `typing.Optional` (import), `pydantic.ConfigDict` (import), `pydantic_settings.BaseSettings` (import), `Settings` (class)

### `backend/app/core/database.py` (Python)
  - **Declared Symbols**: `os` (import), `logging` (import), `sqlmodel.SQLModel` (import), `sqlmodel.create_engine` (import), `sqlmodel.Session` (import), `app.core.config.settings` (import), `get_engine` (function), `init_db` (function), `app.models.workspace` (import), `app.models.knowledge` (import)

### `backend/app/core/llm.py` (Python)
  - **Declared Symbols**: `os` (import), `logging` (import), `typing.Optional` (import), `typing.Dict` (import), `typing.Any` (import), `app.core.config.settings` (import), `app.providers.base.LLMProvider` (import), `app.providers.nvidia_nim.NvidiaNIMProvider` (import), `get_llm_provider` (function), `LLMClient` (class)

### `backend/app/main.py` (Python)
  - **Declared Symbols**: `fastapi.FastAPI` (import), `fastapi.middleware.cors.CORSMiddleware` (import), `contextlib.asynccontextmanager` (import), `logging` (import), `app.core.config.settings` (import), `app.core.database.init_db` (import), `app.api.router.router` (import), `lifespan` (function), `root` (function), `health` (function)

### `backend/app/models/__init__.py` (Python)
  - **Declared Symbols**: `app.models.workspace.Repository` (import), `app.models.workspace.FileNode` (import), `app.models.workspace.ASTSymbol` (import), `app.models.workspace.WorkspaceSummary` (import), `app.models.workspace.VectorChunk` (import)

### `backend/app/models/knowledge.py` (Python)
  - **Declared Symbols**: `typing.Optional` (import), `typing.List` (import), `typing.Dict` (import), `typing.Any` (import), `sqlmodel.SQLModel` (import), `sqlmodel.Field` (import), `sqlmodel.JSON` (import), `sqlmodel.Column` (import), `datetime.datetime` (import), `enum.Enum` (import)

### `backend/app/models/workspace.py` (Python)
  - **Declared Symbols**: `typing.Optional` (import), `typing.List` (import), `typing.Dict` (import), `typing.Any` (import), `sqlmodel.SQLModel` (import), `sqlmodel.Field` (import), `sqlmodel.JSON` (import), `sqlmodel.Column` (import), `datetime.datetime` (import), `uuid` (import)

### `backend/app/providers/__init__.py` (Python)
  - **Declared Symbols**: `app.providers.base.LLMProvider` (import), `app.providers.nvidia_nim.NvidiaNIMProvider` (import)

### `backend/app/providers/base.py` (Python)
  - **Declared Symbols**: `abc.ABC` (import), `abc.abstractmethod` (import), `typing.Optional` (import), `typing.Dict` (import), `typing.Any` (import), `LLMProvider` (class), `generate` (method), `is_available` (method)

### `backend/app/providers/nvidia_nim.py` (Python)
  - **Declared Symbols**: `os` (import), `logging` (import), `typing.Optional` (import), `typing.Dict` (import), `typing.Any` (import), `app.providers.base.LLMProvider` (import), `app.core.config.settings` (import), `NvidiaNIMProvider` (class), `__init__` (method), `is_available` (method)

### `backend/app/services/export/okf_exporter.py` (Python)
  - **Declared Symbols**: `os` (import), `logging` (import), `typing.List` (import), `typing.Dict` (import), `typing.Any` (import), `typing.Optional` (import), `app.models.workspace.Repository` (import), `app.models.workspace.FileNode` (import), `app.models.workspace.ASTSymbol` (import), `app.models.workspace.WorkspaceSummary` (import)

### `backend/app/services/graph/code_graph.py` (Python)
  - **Declared Symbols**: `logging` (import), `typing.List` (import), `typing.Dict` (import), `typing.Any` (import), `typing.Optional` (import), `typing.Set` (import), `typing.Tuple` (import), `collections.defaultdict` (import), `collections.deque` (import), `sqlmodel.Session` (import)

### `backend/app/services/ingestion/__init__.py` (Python)
  - **Declared Symbols**: `app.services.ingestion.crawler.RepositoryCrawler` (import)

### `backend/app/services/ingestion/crawler.py` (Python)
  - **Declared Symbols**: `os` (import), `shutil` (import), `logging` (import), `git` (import), `typing.Dict` (import), `typing.List` (import), `typing.Tuple` (import), `typing.Any` (import), `app.models.workspace.FileNode` (import), `RepositoryCrawler` (class)

### `backend/app/services/intelligence/endpoint_detector.py` (Python)
  - **Declared Symbols**: `re` (import), `typing.List` (import), `typing.Dict` (import), `typing.Any` (import), `EndpointDetector` (class), `detect_endpoints` (method), `TestDetector` (class), `is_test_file` (method), `extract_test_cases` (method)

### `backend/app/services/intelligence/git_intel.py` (Python)
  - **Declared Symbols**: `os` (import), `logging` (import), `typing.Dict` (import), `typing.List` (import), `typing.Any` (import), `typing.Optional` (import), `app.services.parser.ast_parser.ASTParserEngine` (import), `GitIntelligence` (class), `get_git_diff_status` (method), `git` (import)

### `backend/app/services/intelligence/incremental_indexer.py` (Python)
  - **Declared Symbols**: `os` (import), `hashlib` (import), `typing.Dict` (import), `typing.List` (import), `typing.Set` (import), `typing.Tuple` (import), `IncrementalIndexer` (class), `compute_file_hash` (method), `detect_changes` (method)

### `backend/app/services/intelligence/secret_safety.py` (Python)
  - **Declared Symbols**: `re` (import), `logging` (import), `typing.List` (import), `typing.Tuple` (import), `SecretSafetyService` (class), `is_sensitive_file` (method), `sanitize_content` (method)

### `backend/app/services/parser/__init__.py` (Python)
  - **Declared Symbols**: `app.services.parser.ast_parser.ASTParserEngine` (import)

### `backend/app/services/parser/ast_parser.py` (Python)
  - **Declared Symbols**: `logging` (import), `typing.List` (import), `typing.Dict` (import), `typing.Optional` (import), `app.models.workspace.ASTSymbol` (import), `app.services.parser.base.BaseLanguageParser` (import), `app.services.parser.plugins.ALL_PARSER_PLUGINS` (import), `ASTParserEngine` (class), `_initialize_registry` (method), `parse_file` (method)

### `backend/app/services/parser/base.py` (Python)
  - **Declared Symbols**: `abc.ABC` (import), `abc.abstractmethod` (import), `typing.List` (import), `app.models.workspace.ASTSymbol` (import), `BaseLanguageParser` (class), `supported_languages` (method), `parse` (method)

### `backend/app/services/parser/plugins/__init__.py` (Python)
  - **Declared Symbols**: `app.services.parser.plugins.python_parser.PythonParserPlugin` (import), `app.services.parser.plugins.typescript_parser.TypeScriptParserPlugin` (import), `app.services.parser.plugins.go_parser.GoParserPlugin` (import), `app.services.parser.plugins.c_family_parser.RustParserPlugin` (import), `app.services.parser.plugins.c_family_parser.CFamilyParserPlugin` (import)

### `backend/app/services/parser/plugins/c_family_parser.py` (Python)
  - **Declared Symbols**: `re` (import), `typing.List` (import), `app.models.workspace.ASTSymbol` (import), `app.services.parser.base.BaseLanguageParser` (import), `RustParserPlugin` (class), `supported_languages` (method), `parse` (method), `CFamilyParserPlugin` (class), `supported_languages` (method), `parse` (method)

### `backend/app/services/parser/plugins/go_parser.py` (Python)
  - **Declared Symbols**: `re` (import), `typing.List` (import), `app.models.workspace.ASTSymbol` (import), `app.services.parser.base.BaseLanguageParser` (import), `GoParserPlugin` (class), `supported_languages` (method), `parse` (method)

### `backend/app/services/parser/plugins/python_parser.py` (Python)
  - **Declared Symbols**: `ast` (import), `logging` (import), `typing.List` (import), `app.models.workspace.ASTSymbol` (import), `app.services.parser.base.BaseLanguageParser` (import), `PythonParserPlugin` (class), `supported_languages` (method), `parse` (method), `FunctionCallVisitor` (class), `__init__` (method)

### `backend/app/services/parser/plugins/typescript_parser.py` (Python)
  - **Declared Symbols**: `re` (import), `typing.List` (import), `app.models.workspace.ASTSymbol` (import), `app.services.parser.base.BaseLanguageParser` (import), `TypeScriptParserPlugin` (class), `supported_languages` (method), `parse` (method)

### `backend/app/services/pipeline.py` (Python)
  - **Declared Symbols**: `os` (import), `logging` (import), `typing.Dict` (import), `typing.Any` (import), `typing.List` (import), `typing.Optional` (import), `sqlmodel.Session` (import), `sqlmodel.select` (import), `app.core.database.engine` (import), `app.core.config.settings` (import)

### `backend/app/services/rag/__init__.py` (Python)
  - **Declared Symbols**: `app.services.rag.vector_store.VectorSearchStore` (import)

### `backend/app/services/rag/vector_store.py` (Python)
  - **Declared Symbols**: `logging` (import), `math` (import), `re` (import), `typing.List` (import), `typing.Dict` (import), `typing.Any` (import), `typing.Tuple` (import), `app.models.workspace.VectorChunk` (import), `app.models.workspace.WorkspaceSummary` (import), `app.models.workspace.FileNode` (import)

### `backend/app/services/retrieval/context_builder.py` (Python)
  - **Declared Symbols**: `typing.Dict` (import), `typing.Any` (import), `typing.List` (import), `app.models.workspace.Repository` (import), `ContextBuilder` (class), `build_structured_context` (method)

### `backend/app/services/retrieval/hybrid_retriever.py` (Python)
  - **Declared Symbols**: `logging` (import), `typing.List` (import), `typing.Dict` (import), `typing.Any` (import), `typing.Tuple` (import), `typing.Optional` (import), `app.models.workspace.VectorChunk` (import), `app.models.workspace.WorkspaceSummary` (import), `app.models.workspace.ASTSymbol` (import), `app.models.workspace.FileNode` (import)

### `backend/app/services/retrieval/query_planner.py` (Python)
  - **Declared Symbols**: `enum.Enum` (import), `typing.Dict` (import), `typing.Any` (import), `typing.Optional` (import), `QueryIntent` (class), `QueryPlanner` (class), `plan_query` (method)

### `backend/app/services/summarizer/__init__.py` (Python)
  - **Declared Symbols**: `app.services.summarizer.hierarchical.HierarchicalSummarizerEngine` (import)

### `backend/app/services/summarizer/hierarchical.py` (Python)
  - **Declared Symbols**: `os` (import), `logging` (import), `typing.List` (import), `typing.Dict` (import), `typing.Any` (import), `app.models.workspace.FileNode` (import), `app.models.workspace.ASTSymbol` (import), `app.models.workspace.WorkspaceSummary` (import), `app.models.workspace.Repository` (import), `app.core.llm.LLMClient` (import)

### `backend/data/repos/454a8dd6-67e9-4116-a65b-81fc3c7010c4/.env.example` (Unknown)
  - **Declared Symbols**: None extracted
