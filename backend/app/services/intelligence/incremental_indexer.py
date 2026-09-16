import os
import hashlib
from typing import Dict, List, Set, Tuple

class IncrementalIndexer:
    """Manages file hashes and identifies modified files for fast incremental indexing."""

    @staticmethod
    def compute_file_hash(file_path: str) -> str:
        """Computes SHA256 hash of a file's contents."""
        hasher = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return ""

    @staticmethod
    def detect_changes(repo_root: str, previous_hashes: Dict[str, str]) -> Tuple[List[str], List[str], List[str], Dict[str, str]]:
        """
        Compares current directory files against previous hashes.
        Returns (added_files, modified_files, deleted_files, current_hashes).
        """
        current_hashes: Dict[str, str] = {}
        added: List[str] = []
        modified: List[str] = []
        deleted: List[str] = []

        # Scan current files
        for root, dirs, files in os.walk(repo_root):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in {"node_modules", ".venv", "build", "dist"}]
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, repo_root).replace("\\", "/")
                file_hash = IncrementalIndexer.compute_file_hash(abs_path)
                current_hashes[rel_path] = file_hash

                if rel_path not in previous_hashes:
                    added.append(rel_path)
                elif previous_hashes[rel_path] != file_hash:
                    modified.append(rel_path)

        for old_path in previous_hashes:
            if old_path not in current_hashes:
                deleted.append(old_path)

        return added, modified, deleted, current_hashes
