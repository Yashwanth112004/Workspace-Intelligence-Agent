"""RAG Context and Architecture Summary Generator for LLM context injection and workspace summaries."""

from pathlib import Path
from wia.core.architecture import ArchitectureAnalyzer
from wia.core.framework import FrameworkDetector
from wia.core.index_model import WorkspaceIndex
from wia.core.metadata import IndexingStatus


class RAGContextGenerator:
    """Generates structured Markdown summaries separating repository facts from repository intelligence."""

    @classmethod
    def classify_intent(cls, prompt: str) -> str:
        """Classify user reasoning prompt into canonical intent."""
        from wia.core.retrieval import IntentClassifier
        return IntentClassifier.classify(prompt)

    @classmethod
    def generate_rag_context(
        cls, index: WorkspaceIndex, prompt: str = "", max_files: int = 50
    ) -> str:
        """Format WorkspaceIndex into structured Markdown separating Repository Facts from Repository Intelligence."""
        ws_name = Path(index.workspace_path).name
        intent = cls.classify_intent(prompt) if prompt else "GENERAL"

        indexed_files = [f for f in index.files.values() if f.indexing_status == IndexingStatus.INDEXED]
        ignored_files = [f for f in index.files.values() if f.indexing_status == IndexingStatus.IGNORED]

        # File type distribution
        file_types: dict[str, int] = {}
        total_classes = 0
        total_functions = 0
        test_files: list[str] = []
        config_files: list[str] = []

        for rec in indexed_files:
            ft = rec.file_type or "Source Code"
            file_types[ft] = file_types.get(ft, 0) + 1

            syms = rec.extra_metadata.get("symbols", [])
            for s in syms:
                st = s.get("symbol_type")
                if st == "class":
                    total_classes += 1
                elif st in ("function", "method"):
                    total_functions += 1

            if ft == "Test" or "test" in rec.relative_path.lower():
                test_files.append(rec.relative_path)
            if ft in ("Configuration", "Build", "CI/CD"):
                config_files.append(rec.relative_path)

        arch = ArchitectureAnalyzer.analyze_workspace(index)
        framework_evidence = FrameworkDetector.detect_frameworks(index.workspace_path)

        lines: list[str] = []
        lines.append(f"# Workspace Intelligence Summary: {ws_name}")
        lines.append(f"- **Workspace Path**: `{index.workspace_path}`")
        lines.append(f"- **WIA Version**: `{index.wia_version}`")
        lines.append(f"- **Query Intent**: `{intent}`")
        lines.append("")

        # 1. REPOSITORY FACTS
        lines.append("## 1. Repository Facts")
        lines.append(f"- **Total Discovered Files**: {len(index.files)}")
        lines.append(f"- **Indexed Active Files**: {len(indexed_files)}")
        lines.append(f"- **Excluded / Ignored Files**: {len(ignored_files)}")
        lines.append(f"- **Total Declared Classes**: {total_classes}")
        lines.append(f"- **Total Declared Functions / Methods**: {total_functions}")
        lines.append("")

        lines.append("### Languages")
        if index.languages:
            for lang, count in sorted(index.languages.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"- **{lang}**: {count} file(s)")
        else:
            lines.append("- None detected")
        lines.append("")

        lines.append("### File Classification Breakdown")
        for ft, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- **{ft}**: {count} file(s)")
        lines.append("")

        lines.append("### Testing & Configuration")
        lines.append(f"- **Identified Test Files**: {len(test_files)}")
        if test_files:
            sample_tests = ", ".join(f"`{t}`" for t in test_files[:5])
            lines.append(f"  - Examples: {sample_tests}")
        lines.append(f"- **Configuration & Manifests**: {len(config_files)}")
        if config_files:
            sample_configs = ", ".join(f"`{c}`" for c in config_files[:6])
            lines.append(f"  - Files: {sample_configs}")
        lines.append("")

        # 2. REPOSITORY INTELLIGENCE
        lines.append("## 2. Repository Intelligence")
        lines.append(f"- **Project Purpose**: {arch.summary}")
        lines.append("")

        lines.append("### Technology Stack")
        if framework_evidence:
            for fw in framework_evidence:
                lines.append(f"- **{fw.name}** ({fw.category}): evidenced in `{fw.evidence_source}`")
        elif index.frameworks:
            for fw_name in index.frameworks:
                lines.append(f"- **{fw_name}**: configured in workspace")
        else:
            lines.append("- Standard multi-module codebase")
        lines.append("")

        lines.append("### Entry Points & Execution Roots")
        if arch.entry_points:
            for ep in arch.entry_points[:6]:
                lines.append(f"- {ep}")
        else:
            lines.append("- Core library / module layout")
        lines.append("")

        lines.append("### Architecture & Subsystems")
        active_components = [c for c in arch.components if c.file_count > 0]
        if active_components:
            for c in active_components:
                desc = getattr(c, "description", None) or getattr(c, "responsibility", "") or getattr(c, "role", "")
                lines.append(f"- **{c.name}** ({c.file_count} files): {desc}")
        else:
            lines.append("- Unified codebase structure")
        lines.append("")

        # 3. EVIDENCE & FILE OVERVIEW
        lines.append("## 3. Key Workspace Modules & Symbols")
        for rec in indexed_files[:max_files]:
            symbols = rec.extra_metadata.get("symbols", [])
            sym_count = len(symbols)
            if sym_count > 0:
                top_syms = ", ".join(f"`{s.get('name')}`" for s in symbols[:6] if s.get("name"))
                lines.append(f"- `{rec.relative_path}` ({rec.language}, {rec.file_type}): defines {sym_count} symbols ({top_syms})")
            else:
                lines.append(f"- `{rec.relative_path}` ({rec.language}, {rec.file_type})")
        lines.append("")

        lines.append("## Evidence")
        lines.append("- Grounded in AST symbol parsing, FrameworkDetector, and active WorkspaceIndex records.")

        return "\n".join(lines)
