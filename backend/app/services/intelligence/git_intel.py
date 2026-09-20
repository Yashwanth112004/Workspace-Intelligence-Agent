import os
import logging
from typing import Dict, List, Any, Optional
from app.services.parser.ast_parser import ASTParserEngine

logger = logging.getLogger("wia.intelligence.git")

class GitIntelligence:
    """Provides Git-aware diff analysis, changed symbol discovery, and blast radius estimation."""

    @staticmethod
    def get_git_diff_status(repo_root: str) -> Dict[str, Any]:
        """Inspects git status for modified, added, and deleted files in the repository."""
        changed_files: List[str] = []
        added_files: List[str] = []
        deleted_files: List[str] = []
        is_git_repo = False

        git_dir = os.path.join(repo_root, ".git")
        if os.path.exists(git_dir):
            is_git_repo = True
            try:
                import git
                repo = git.Repo(repo_root)
                # Unstaged / modified files
                try:
                    for item in repo.index.diff(None):
                        if item.change_type == 'M':
                            changed_files.append(item.a_path.replace("\\", "/"))
                        elif item.change_type == 'D':
                            deleted_files.append(item.a_path.replace("\\", "/"))
                except Exception as diff_err:
                    logger.debug(f"Unstaged diff: {diff_err}")

                # Staged files
                try:
                    for item in repo.index.diff("HEAD"):
                        if item.change_type == 'M' and item.a_path not in changed_files:
                            changed_files.append(item.a_path.replace("\\", "/"))
                        elif item.change_type == 'A' and item.a_path not in added_files:
                            added_files.append(item.a_path.replace("\\", "/"))
                        elif item.change_type == 'D' and item.a_path not in deleted_files:
                            deleted_files.append(item.a_path.replace("\\", "/"))
                except Exception as head_err:
                    logger.debug(f"Staged diff: {head_err}")

                # Untracked files
                try:
                    for untracked in repo.untracked_files:
                        added_files.append(untracked.replace("\\", "/"))
                except Exception as untracked_err:
                    logger.debug(f"Untracked files: {untracked_err}")
            except Exception as e:
                logger.warning(f"Git diff inspection fallback: {e}")

        return {
            "is_git_repo": is_git_repo,
            "modified_files": sorted(list(set(changed_files))),
            "added_files": sorted(list(set(added_files))),
            "deleted_files": sorted(list(set(deleted_files))),
            "total_changes": len(set(changed_files + added_files + deleted_files))
        }

    @staticmethod
    def analyze_diff_symbols(repo_root: str, changed_files: List[str]) -> List[Dict[str, Any]]:
        """Parses changed files to identify affected symbol definitions and imports."""
        symbols_found: List[Dict[str, Any]] = []
        for rel_path in changed_files:
            abs_path = os.path.join(repo_root, rel_path)
            if not os.path.exists(abs_path):
                continue
            ext = os.path.splitext(rel_path)[1].lower()
            try:
                with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                file_symbols = ASTParserEngine.parse_file_symbols(content, ext, rel_path)
                for sym in file_symbols:
                    symbols_found.append({
                        "name": sym.name,
                        "type": sym.symbol_type,
                        "file": rel_path,
                        "line": sym.start_line
                    })
            except Exception as e:
                logger.warning(f"Failed to parse symbols in changed file {rel_path}: {e}")

        return symbols_found
