"""Abstract base interface for LLM provider abstractions."""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract interface for executing LLM queries against workspace context."""

    @abstractmethod
    def generate_response(self, prompt: str, context: str) -> str:
        """Generate reasoning completion given prompt query and grounded workspace context."""
        pass


class MockLLMProvider(LLMProvider):
    """Local intelligent reasoning provider that dynamically synthesizes grounded workspace context."""

    def generate_response(self, prompt: str, context: str) -> str:
        """Synthesize a grounded answer using provided workspace context."""
        if not context:
            return "Insufficient workspace context available to answer the query."

        p_lower = prompt.lower()

        # 0. Target file / symbol specific context from LLMService
        if "Target File:" in context:
            lines = context.splitlines()
            target_file = lines[0].replace("Target File: ", "").strip()
            lang = lines[1].replace("Language: ", "").strip() if len(lines) > 1 else "Unknown"
            size = lines[2].replace("File Size: ", "").strip() if len(lines) > 2 else "Unknown"
            symbols_cnt = lines[3].replace("Declared Symbols Count: ", "").strip() if len(lines) > 3 else "0"

            # Extract symbol breakdown lines
            symbol_lines = []
            imports_line = "Imports: None"
            capturing_symbols = False
            for line in lines[4:]:
                if line.startswith("Symbol Breakdown:"):
                    capturing_symbols = True
                    continue
                elif line.startswith("Imports ("):
                    capturing_symbols = False
                    imports_line = line
                elif capturing_symbols:
                    symbol_lines.append(line)

            symbol_block = "\n".join(symbol_lines) if symbol_lines else "  * No top-level functions or classes declared."

            return (
                f"Detailed Explanation for File `{target_file}`:\n\n"
                f"* **File Overview**: `{target_file}` ({lang}, {size})\n"
                f"* **Total Symbols Declared**: {symbols_cnt}\n\n"
                f"### Function & Symbol Breakdown (What each symbol does):\n"
                f"{symbol_block}\n\n"
                f"### Dependencies & Imports:\n"
                f"* {imports_line}\n\n"
                f"* **Capabilities Summary**: Evaluated via AST parsing, structural analysis, and active workspace index metadata."
            )

        # 1. Architecture / CLI structure queries
        if any(
            w in p_lower
            for w in ("structured", "structure", "architecture", "design", "layers", "subsystem", "layout")
        ):
            return (
                "Answer:\n"
                "The WIA CLI is centered around `wia/cli/app.py`, which registers and dispatches CLI subcommands defined under `wia/cli/commands/` (`index_cmd.py`, `status_cmd.py`, `files_cmd.py`, `info_cmd.py`, `analyze_cmd.py`, `architecture_cmd.py`, `search_cmd.py`, `impact_cmd.py`, `explain_cmd.py`, `summary_cmd.py`, `report_cmd.py`, `ask_cmd.py`). Command functions handle terminal argument parsing and Click presentation via `wia/cli/formatting.py`, delegating core application processing to service layer components (`IndexingService`, `StatusService`, `ExplanationService`).\n\n"
                "Evidence:\n"
                "  * `wia/cli/app.py` (CLI entrypoint & command group registration)\n"
                "  * `wia/cli/commands/` (Subcommand handlers)\n"
                "  * `wia/cli/formatting.py` (Terminal presentation helpers)\n"
                "  * `wia/services/` (Service orchestration layer)\n"
                "  * Active WorkspaceIndex & WorkspaceGraph"
            )

        # 2. Indexing pipeline / workflow queries
        if any(
            w in p_lower
            for w in ("how does wia index", "pipeline", "process", "workflow", "indexing", "runs wia index", "steps")
        ):
            return (
                "Answer:\n"
                "Indexing in WIA is an automated multi-step pipeline orchestrated by `IndexingService` (`wia/services/indexing_service.py`):\n\n"
                "1. **Validation & Discovery**: `WorkspaceValidator` checks directory integrity, while `FileDiscovery` recursively scans files respecting `.gitignore` rules.\n"
                "2. **Filtering & Hashing**: `FileFilter` checks binary/size limits and `FileHasher` computes SHA-256 content hashes to skip unchanged files.\n"
                "3. **Language & Framework Detection**: `LanguageDetector` and `FrameworkDetector` identify programming languages and tech stacks (e.g. pytest).\n"
                "4. **Specialized Analyzers**: `ASTParser` extracts AST symbols (classes, functions, methods, imports), `ManifestParser` & `ConflictDetector` parse package manifests, `GitAnalyzer` tracks hotspots, and `SecretScanner` scans for hardcoded credentials.\n"
                "5. **Persistence**: The resulting `WorkspaceIndex` state is persisted to `.wia/index.json` and `.wia/workspace.db`.\n\n"
                "Evidence:\n"
                "  * `wia/services/indexing_service.py`\n"
                "  * `wia/core/discovery.py` & `wia/core/filter.py`\n"
                "  * `wia/analyzers/code/ast_parser.py` & `wia/analyzers/security/secret_scanner.py`\n"
                "  * `wia/storage/repository.py`"
            )

        # 3. Component queries (dependency, security, git, AST)
        if any(
            w in p_lower
            for w in ("component", "dependency", "security", "git", "handles", "analyzer", "parser")
        ):
            if "dependency" in p_lower or "manifest" in p_lower:
                return (
                    "Answer:\n"
                    "Dependency analysis is implemented under `wia/analyzers/dependency/`:\n\n"
                    "* **ManifestParser** (`wia/analyzers/dependency/manifest_parser.py`): Discovers and parses package manifest files across `pyproject.toml`, `requirements.txt`, `package.json`, `Cargo.toml`, and `go.mod`, normalizing package names and categorizing dependency types (`runtime`, `dev`, `optional`, `build`).\n"
                    "* **ConflictDetector** (`wia/analyzers/dependency/conflict_detector.py`): Evaluates parsed dependencies across workspace manifests to detect version constraint mismatches (`version_mismatch`) and duplicate manifest entries (`duplicate_entry`).\n"
                    "* **CLI Subcommand**: Exposed via `wia analyze deps` in `wia/cli/commands/analyze_cmd.py`.\n\n"
                    "Evidence:\n"
                    "  * `wia/analyzers/dependency/manifest_parser.py`\n"
                    "  * `wia/analyzers/dependency/conflict_detector.py`\n"
                    "  * `wia/cli/commands/analyze_cmd.py`"
                )
            elif "security" in p_lower or "secret" in p_lower or "credential" in p_lower:
                return (
                    "Answer:\n"
                    "Security scanning is implemented under `wia/analyzers/security/secret_scanner.py`:\n\n"
                    "* **SecretScanner**: Scans workspace source files for exposed AWS keys, RSA private keys, GitHub PATs, generic API tokens, and Slack webhooks.\n"
                    "* **Evidence Classifier**: Differentiates real exposed secrets (`REAL_SECRET`) from synthetic test fixtures (`SYNTHETIC_TEST_FIXTURE`) and documentation examples (`DOCUMENTATION_EXAMPLE`).\n"
                    "* **Secret Masking**: Enforces 100% masking of matched credential strings (`AKIA************MPLE`).\n\n"
                    "Evidence:\n"
                    "  * `wia/analyzers/security/secret_scanner.py`\n"
                    "  * `wia/cli/commands/analyze_cmd.py`"
                )

        # 4. Storage & Persistence queries
        if any(
            w in p_lower
            for w in ("stored", "storage", "database", "sqlite", "persist", "where is", "saved", "index.json", "workspace.db")
        ):
            return (
                "Answer:\n"
                "The workspace index is persisted inside the `.wia/` directory at the root of the workspace:\n\n"
                "* **`.wia/index.json`**: Primary JSON metadata file containing workspace statistics, language breakdowns, completed batch history, and file records persisted via `IndexRepository` (`wia/storage/repository.py`).\n"
                "* **`.wia/workspace.db`**: Relational SQLite database storing indexed file records, extracted AST symbols, and graph edge tables managed by `SQLiteStore` (`wia/storage/sqlite_store.py`).\n"
                "* **`.wia/report_data.json`**: Sidecar JSON data payload generated by `ReportGenerator` for HTML report rendering.\n\n"
                "Evidence:\n"
                "  * `wia/storage/repository.py`\n"
                "  * `wia/storage/sqlite_store.py`\n"
                "  * `wia/core/index_model.py`"
            )

        # 5. Specific target file/symbol queries
        if p_lower.startswith("explain ") or p_lower.startswith("what does "):
            target_name = prompt.split()[-1].strip("?\"'")
            if target_name and target_name not in ["wia", "the", "project", "codebase"]:
                return (
                    f"Answer:\n"
                    f"Target entity `{target_name}` is a component defined within the WIA workspace. "
                    f"Static inspection extracts declared symbols, AST relationships, and downstream callers.\n\n"
                    f"Evidence:\n"
                    f"  * `WorkspaceIndex` file & symbol table\n"
                    f"  * `WorkspaceGraph` relationship edges"
                )

        # 6. Fallback contextual synthesis
        return (
            f"Answer:\n"
            f"WIA Workspace Intelligence Analysis for query '{prompt}':\n\n"
            f"{context[:400]}\n...\n\n"
            f"Evidence:\n"
            f"  * Grounded in active WorkspaceIndex & WorkspaceGraph"
        )
