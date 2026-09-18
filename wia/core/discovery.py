"""Deterministic recursive file discovery engine for WIA workspaces."""

import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

GENERATED_REPORT_FILENAMES = {"wia-report.html", "report_data.json"}


@dataclass
class DiscoveredFile:
    """Represents a discovered candidate file in the workspace."""

    relative_path: str
    absolute_path: Path
    is_symlink: bool
    file_size: int
    modified_time: float


class FileDiscovery:
    """Recursively discovers files within a repository workspace."""

    @staticmethod
    def discover_files(
        root_path: str | Path, follow_symlinks: bool = False
    ) -> list[DiscoveredFile]:
        """Recursively traverse workspace and return sorted list of candidate files.

        Relative paths are normalized using POSIX slashes ('/') for cross-platform stability.
        Symbolic links are handled safely to prevent infinite recursion loops.
        """
        root = Path(root_path).resolve()
        discovered: list[DiscoveredFile] = []

        if not root.exists() or not root.is_dir():
            return discovered

        visited_dirs: set[Path] = set()
        visited_dirs.add(root.resolve())

        for current_root, dirs, files in os.walk(root, followlinks=follow_symlinks):
            current_path = Path(current_root)

            # Prevent symlink infinite recursion loops if followlinks is enabled
            if follow_symlinks:
                resolved_current = current_path.resolve()
                if resolved_current in visited_dirs and resolved_current != root.resolve():
                    dirs.clear()
                    continue
                visited_dirs.add(resolved_current)

            # Prune internal metadata, cache, and build directories from traversal
            pruned_dirs = {
                ".git", ".wia", "__pycache__", ".pytest_cache", ".mypy_cache",
                ".tox", "venv", ".venv", "env", ".env", "node_modules", "vendor",
                "dist", "build", "target", "out", "bin", "obj",
            }
            dirs[:] = [
                d for d in dirs
                if d.lower() not in pruned_dirs
                and not d.lower().endswith(".egg-info")
                and not d.lower().endswith(".dist-info")
            ]

            # Process files in current directory
            for filename in files:
                fname_lower = filename.lower()
                if fname_lower in GENERATED_REPORT_FILENAMES:
                    continue
                if fname_lower in ("pkg-info", ".ds_store", "thumbs.db", "desktop.ini"):
                    continue
                if fname_lower.endswith((".pyc", ".pyo", ".egg-info", ".dist-info")):
                    continue

                abs_path = current_path / filename
                is_symlink = abs_path.is_symlink()

                try:
                    rel_path = abs_path.relative_to(root)
                    posix_rel_path = PurePosixPath(rel_path).as_posix()

                    stat = abs_path.lstat() if is_symlink else abs_path.stat()
                    file_size = stat.st_size
                    mtime = stat.st_mtime

                    discovered.append(
                        DiscoveredFile(
                            relative_path=posix_rel_path,
                            absolute_path=abs_path,
                            is_symlink=is_symlink,
                            file_size=file_size,
                            modified_time=mtime,
                        )
                    )
                except (PermissionError, OSError):
                    # Skip unreadable or broken files during discovery
                    continue

        # Return deterministically sorted list by relative path
        return sorted(discovered, key=lambda f: f.relative_path)
