"""RAG Context and Architecture Summary Generator for LLM context injection."""

from pathlib import Path
from wia.core.architecture import ArchitectureAnalyzer
from wia.core.index_model import WorkspaceIndex


class RAGContextGenerator:
    """Generates structured Markdown summaries for LLM prompt context injection."""

    @classmethod
    def classify_intent(cls, prompt: str) -> str:
        """Classify user reasoning prompt into architectural, pipeline, component, storage, or symbol intent."""
        p_lower = prompt.lower()

        if any(
            w in p_lower
            for w in (
                "structured",
                "structure",
                "architecture",
                "design",
                "layers",
                "subsystem",
                "layout",
                "component map",
            )
        ):
            return "ARCHITECTURE"
        elif any(
            w in p_lower
            for w in (
                "how does wia index",
                "pipeline",
                "process",
                "workflow",
                "indexing",
                "steps",
                "runs wia index",
            )
        ):
            return "WORKFLOW"
        elif any(
            w in p_lower
            for w in (
                "component",
                "analyzer",
                "scanner",
                "handles",
                "dependency",
                "security",
                "git",
                "parser",
            )
        ):
            return "COMPONENT"
        elif any(
            w in p_lower
            for w in (
                "stored",
                "storage",
                "database",
                "sqlite",
                "persist",
                "where is",
                "saved",
                "index.json",
                "workspace.db",
            )
        ):
            return "STORAGE"
        elif any(w in p_lower for w in (".py", "function", "class")) and not any(
            w in p_lower for w in ("cli", "project", "repo", "wia")
        ):
            return "FILE_SYMBOL"
        else:
            return "GENERAL"

    @classmethod
    def generate_rag_context(
        cls, index: WorkspaceIndex, prompt: str = "", max_files: int = 50
    ) -> str:
        """Format WorkspaceIndex into structured Markdown suitable for RAG context windows."""
        ws_name = Path(index.workspace_path).name
        intent = cls.classify_intent(prompt) if prompt else "GENERAL"

        lines: list[str] = []
        lines.append(f"# Workspace Architecture & Intelligence Context: {ws_name}")
        lines.append(f"- **Query Intent**: `{intent}`")
        lines.append(f"- **Indexed Path**: `{index.workspace_path}`")
        lines.append(f"- **Indexed At**: `{index.indexed_at}`")
        lines.append(f"- **WIA Version**: `{index.wia_version}`")
        lines.append("")

        # 1. Intent-Driven Context Header
        if intent == "ARCHITECTURE":
            arch = ArchitectureAnalyzer.analyze_workspace(index)
            lines.append("## Architecture Overview")
            lines.append(f"- **Summary**: {arch.summary}")
            lines.append(
                f"- **Subsystems ({len(arch.components)})**: {', '.join(c.name for c in arch.components if c.file_count > 0)}"
            )
            lines.append(f"- **Entry Points**: {', '.join(arch.entry_points)}")
            lines.append("")
        elif intent == "WORKFLOW":
            lines.append("## Indexing Pipeline Stages")
            lines.append("1. Validation & Discovery (`WorkspaceValidator`, `FileDiscovery`)")
            lines.append("2. Filtering & Hashing (`FileFilter`, `FileHasher`)")
            lines.append("3. Language & Tech Stack Detection (`LanguageDetector`, `FrameworkDetector`)")
            lines.append(
                "4. AST & Analyzer Intelligence (`ASTParser`, `ManifestParser`, `GitAnalyzer`, `SecretScanner`)"
            )
            lines.append("5. Persistence (`IndexRepository`, `SQLiteStore`)")
            lines.append("")
        elif intent == "STORAGE":
            lines.append("## Persistence Storage Specification")
            lines.append(
                f"- **JSON Index**: `.wia/index.json` (Managed by `IndexRepository` in `wia/storage/repository.py`)"
            )
            lines.append(
                f"- **SQLite DB**: `.wia/workspace.db` (Managed by `SQLiteStore` in `wia/storage/sqlite_store.py`)"
            )
            lines.append(
                f"- **HTML Sidecar**: `.wia/report_data.json` (Managed by `ReportGenerator` in `wia/utils/report_generator.py`)"
            )
            lines.append("")
        elif intent == "COMPONENT":
            lines.append("## Analyzer & Subsystem Components")
            lines.append(
                "- **Dependency Analyzer**: `ManifestParser` (`manifest_parser.py`), `ConflictDetector` (`conflict_detector.py`)"
            )
            lines.append("- **Security Analyzer**: `SecretScanner` (`secret_scanner.py`)")
            lines.append("- **Git Analyzer**: `GitAnalyzer` (`git_analyzer.py`)")
            lines.append("- **AST Parser**: `ASTParser` (`ast_parser.py`)")
            lines.append("- **Relationship Graph**: `WorkspaceGraph` (`graph.py`)")
            lines.append("")

        # 2. Languages & Frameworks
        lines.append("## Languages & Frameworks")
        if index.frameworks:
            lines.append(f"- **Detected Frameworks**: {', '.join(index.frameworks)}")
        else:
            lines.append("- **Detected Frameworks**: None")

        if index.languages:
            langs_str = ", ".join(
                f"{lang} ({cnt} files)" for lang, cnt in index.languages.items()
            )
            lines.append(f"- **Languages**: {langs_str}")
        lines.append("")

        # 3. Key Symbols & File Map
        lines.append("## Workspace File & Symbol Overview")
        indexed_files = index.get_indexed_files()[:max_files]

        if not indexed_files:
            lines.append("*No indexed files available.*")
        else:
            for rec in indexed_files:
                lines.append(f"### `{rec.relative_path}` ({rec.language})")
                symbols = rec.extra_metadata.get("symbols", [])
                if symbols:
                    sym_list = [f"`{s['name']}` ({s['symbol_type']})" for s in symbols[:10]]
                    lines.append(f"  - **Declared Symbols**: {', '.join(sym_list)}")
                else:
                    lines.append("  - **Declared Symbols**: None extracted")
                lines.append("")

        return "\n".join(lines)
