import os
import logging
from typing import List, Dict, Any, Optional
from app.models.workspace import Repository, FileNode, ASTSymbol, WorkspaceSummary
from app.services.graph.code_graph import CodeKnowledgeGraph

logger = logging.getLogger("wia.export.okf")

class OKFExporter:
    """
    Exports codebase intelligence in Open Knowledge Format (OKF).
    Writes a human-readable, Git-friendly `.wia/knowledge/` documentation tree.
    """

    @staticmethod
    def export_repository_knowledge(
        repo: Repository,
        files: List[FileNode],
        symbols: List[ASTSymbol],
        summaries: List[WorkspaceSummary],
        graph: Optional[CodeKnowledgeGraph] = None,
        output_dir: str = ""
    ) -> Dict[str, Any]:
        """Exports OKF knowledge package and returns manifest metadata."""
        out = output_dir or os.path.join(repo.source_path or ".", ".wia", "knowledge")
        knowledge_dir = OKFExporter.export_okf_tree(
            repo=repo,
            nodes=files,
            symbols=symbols,
            summaries=summaries,
            output_dir=os.path.dirname(os.path.dirname(out)) if out.endswith(".wia/knowledge") or out.endswith(".wia\\knowledge") else out
        )
        return {
            "schema_version": "okf/v1.0",
            "repo_id": repo.id,
            "repo_name": repo.name,
            "knowledge_dir": knowledge_dir,
            "entities_count": len(files) + len(symbols),
            "relations_count": len(symbols) * 2
        }

    @staticmethod
    def export_okf_tree(
        repo: Repository,
        nodes: List[FileNode],
        symbols: List[ASTSymbol],
        summaries: List[WorkspaceSummary],
        output_dir: str
    ) -> str:
        """Generates the `.wia/knowledge/` directory tree."""
        knowledge_dir = os.path.join(output_dir, ".wia", "knowledge")
        os.makedirs(knowledge_dir, exist_ok=True)
        os.makedirs(os.path.join(knowledge_dir, "subsystems"), exist_ok=True)
        os.makedirs(os.path.join(knowledge_dir, "modules"), exist_ok=True)
        os.makedirs(os.path.join(knowledge_dir, "symbols"), exist_ok=True)

        repo_sum = next((s.summary_text for s in summaries if s.level == "repository"), "Architecture summary pending.")
        folder_sums = [s for s in summaries if s.level in ("parent_folder", "child_folder")]
        file_sums = [s for s in summaries if s.level == "file"]

        # 1. index.md
        index_content = f"""---
title: {repo.name} - Codebase Knowledge Index
format: okf/v1
generated_at: {repo.created_at}
total_files: {repo.total_files}
total_loc: {repo.total_loc}
---

# 📚 {repo.name} Knowledge Base

Welcome to the automated Open Knowledge Format documentation for **{repo.name}**.

## 📑 Contents
- [Repository Overview](repository.md)
- [Architecture & Subsystems](architecture.md)
- [Subsystem Breakdowns](subsystems/)
- [Module Guides](modules/)
- [Symbol Index](symbols/)

---

## ⚡ Tech Stack & Metrics
{chr(10).join([f"- **{k}**: {v} Lines of Code" for k, v in (repo.tech_stack or {}).items()])}

- **Entry Points**: {', '.join(repo.entry_points or ['None detected'])}
- **Dependencies**: {len(repo.dependencies or [])} manifests identified
"""
        with open(os.path.join(knowledge_dir, "index.md"), "w", encoding="utf-8") as f:
            f.write(index_content)

        # 2. repository.md
        repo_content = f"""---
title: {repo.name} Repository Overview
source_type: {repo.source_type}
source_path: {repo.source_path}
---

# Repository Overview: {repo.name}

## Executive Summary
{repo_sum}

## Project Entry Points
{chr(10).join([f"- `{ep}`" for ep in (repo.entry_points or [])])}

## Configuration Files
{chr(10).join([f"- `{cf}`" for cf in (repo.config_files or [])])}
"""
        with open(os.path.join(knowledge_dir, "repository.md"), "w", encoding="utf-8") as f:
            f.write(repo_content)

        # 3. architecture.md
        arch_content = f"""---
title: {repo.name} Subsystem Architecture
---

# 🏛️ Architecture & Subsystems Breakdown

{repo_sum}

## Key Subsystems
{chr(10).join([f"### 📁 `{f.target_path}` ({f.name})\n{f.summary_text}\n" for f in folder_sums])}
"""
        with open(os.path.join(knowledge_dir, "architecture.md"), "w", encoding="utf-8") as f:
            f.write(arch_content)

        # 4. modules/ directory files
        for fl in file_sums[:30]:
            safe_name = fl.target_path.replace("/", "_").replace("\\", "_") + ".md"
            mod_symbols = [s for s in symbols if s.file_path == fl.target_path]
            mod_content = f"""---
file: {fl.target_path}
language: {next((n.language for n in nodes if n.relative_path == fl.target_path), 'Code')}
symbols_count: {len(mod_symbols)}
---

# Module: `{fl.target_path}`

## Responsibility
{fl.summary_text}

## Defined Symbols
{chr(10).join([f"- **`{s.name}`** ({s.symbol_type}, Lines {s.start_line}-{s.end_line}): `{s.signature or s.name}`" for s in mod_symbols])}
"""
            with open(os.path.join(knowledge_dir, "modules", safe_name), "w", encoding="utf-8") as f:
                f.write(mod_content)

        logger.info(f"OKF knowledge export generated at: {knowledge_dir}")
        return knowledge_dir
