import os
import logging
from typing import List, Dict, Any
from app.models.workspace import FileNode, ASTSymbol, WorkspaceSummary, Repository
from app.core.llm import LLMClient

logger = logging.getLogger("wia.summarizer")

class HierarchicalSummarizerEngine:
    """Bottom-Up Hierarchical Summarizer generating structured summaries across 5 architectural levels."""

    @staticmethod
    def generate_all_summaries(repo: Repository, nodes: List[FileNode], symbols: List[ASTSymbol]) -> List[WorkspaceSummary]:
        summaries: List[WorkspaceSummary] = []

        symbols_by_file: Dict[str, List[ASTSymbol]] = {}
        for sym in symbols:
            symbols_by_file.setdefault(sym.file_path, []).append(sym)

        files = [n for n in nodes if not n.is_dir]
        dirs = [n for n in nodes if n.is_dir]
        dirs.sort(key=lambda d: d.depth, reverse=True) # Deepest folders first

        file_summary_map: Dict[str, str] = {}
        
        # Step 1 & 2: Functions & Files
        for f in files:
            f_symbols = symbols_by_file.get(f.relative_path, [])
            fn_symbols = [s for s in f_symbols if s.symbol_type == "function"]
            fn_summary_texts = []

            for fn in fn_symbols[:5]:
                fn_sum = f"Function {fn.name}({', '.join(fn.parameters)}): " + (fn.docstring or "Executes procedural and operational logic within file.")
                fn_summary_texts.append(fn_sum)
                summaries.append(WorkspaceSummary(
                    repo_id=repo.id,
                    level="function",
                    target_path=f"{f.relative_path}::{fn.name}",
                    name=fn.name,
                    summary_text=fn_sum,
                    key_components=fn.calls,
                    dependencies=fn.parameters
                ))

            file_prompt = f"""Summarize file '{f.relative_path}' ({f.language or 'Code'}, {f.loc_count} LOC).
Symbols: {[s.name for s in f_symbols]}
Function details: {'; '.join(fn_summary_texts[:3])}

Provide a concise 2-3 sentence overview of this module's primary responsibility, key exports, and dependencies."""
            
            file_sum_text = LLMClient.generate_completion(file_prompt, system_prompt="You are a senior software architect.")
            file_summary_map[f.relative_path] = file_sum_text

            summaries.append(WorkspaceSummary(
                repo_id=repo.id,
                level="file",
                target_path=f.relative_path,
                name=f.name,
                summary_text=file_sum_text,
                key_components=[s.name for s in f_symbols if s.symbol_type in ("function", "class")],
                dependencies=[s.name for s in f_symbols if s.symbol_type == "import"]
            ))

        # Fast lookup indices
        files_by_parent: Dict[str, List[FileNode]] = {}
        dirs_by_parent: Dict[str, List[FileNode]] = {}
        for f in files:
            files_by_parent.setdefault(f.parent_path or "", []).append(f)
        for d in dirs:
            dirs_by_parent.setdefault(d.parent_path or "", []).append(d)

        # Step 3 & 4: Folders (Child Folder -> Parent Folder)
        folder_summary_map: Dict[str, str] = {}
        for d in dirs:
            dir_path = d.relative_path
            child_files = files_by_parent.get(dir_path, [])
            child_file_sums = [f"{f.name}: {file_summary_map.get(f.relative_path, '')}" for f in child_files]

            sub_dirs = dirs_by_parent.get(dir_path, [])
            sub_dir_sums = [f"Folder '{sub.name}': {folder_summary_map.get(sub.relative_path, '')}" for sub in sub_dirs]

            combined_context = child_file_sums + sub_dir_sums
            if combined_context:
                folder_prompt = f"""Summarize directory '{dir_path}' based on its contents:
{chr(10).join(combined_context[:8])}

Provide a clear 2-3 sentence description of what subsystem or domain capability this directory provides."""

                level = "child_folder" if d.depth > 1 else "parent_folder"
                folder_sum_text = LLMClient.generate_completion(folder_prompt, system_prompt="You are a software architecture summarizer.")
                folder_summary_map[dir_path] = folder_sum_text

                summaries.append(WorkspaceSummary(
                    repo_id=repo.id,
                    level=level,
                    target_path=dir_path,
                    name=d.name,
                    summary_text=folder_sum_text,
                    key_components=[sub.name for sub in sub_dirs] + [f.name for f in child_files]
                ))

        # Step 5: Repository
        root_folders = [f"Folder '{d.name}': {folder_summary_map.get(d.relative_path, '')}" for d in dirs if d.depth == 1]
        top_files = [f"File '{f.name}': {file_summary_map.get(f.relative_path, '')}" for f in files if f.depth == 0]

        repo_prompt = f"""Generate a high-level architecture overview for repository '{repo.name}'.
Tech Stack: {repo.tech_stack}
Total Files: {repo.total_files}, Total LOC: {repo.total_loc}
Entry Points: {repo.entry_points}
Root Summaries:
{chr(10).join(root_folders + top_files)}

Provide an architectural overview:
1. Primary purpose of the workspace
2. Core modules & technology stack
3. Key components and data flow"""

        repo_sum_text = LLMClient.generate_completion(repo_prompt, system_prompt="You are a Lead AI Architect summarizing workspace repositories.")

        summaries.append(WorkspaceSummary(
            repo_id=repo.id,
            level="repository",
            target_path="",
            name=repo.name,
            summary_text=repo_sum_text,
            key_components=repo.entry_points,
            dependencies=repo.dependencies
        ))

        return summaries
