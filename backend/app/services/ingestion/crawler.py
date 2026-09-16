import os
import shutil
import logging
import git
from typing import Dict, List, Tuple, Any
from app.models.workspace import FileNode

logger = logging.getLogger("wia.ingestion")

IGNORED_DIRS = {
    ".git", "node_modules", ".venv", "venv", "env", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".next", "dist", "build", "target",
    "out", ".idea", ".vscode", ".claude", "coverage", ".gemini", "scratch",
    ".cache", "bin", "obj", ".turbo", ".vercel"
}

IGNORED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp", ".mp4",
    ".pdf", ".zip", ".tar", ".gz", ".7z", ".rar", ".exe", ".dll", ".so",
    ".dylib", ".pyc", ".pyo", ".pyd", ".db", ".sqlite", ".sqlite3",
    ".bin", ".wasm", ".lock", ".woff", ".woff2", ".ttf", ".eot", ".map",
    ".ds_store"
}

LANG_EXTENSIONS = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".c": "C",
    ".cpp": "C++",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".cs": "C#",
    ".php": "PHP",
    ".rb": "Ruby",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".md": "Markdown",
    ".sh": "Shell",
    ".sql": "SQL"
}

DEPENDENCY_FILES = {
    "package.json", "requirements.txt", "pyproject.toml", "setup.py",
    "Pipfile", "Cargo.toml", "go.mod", "pom.xml", "build.gradle",
    "Gemfile", "composer.json"
}

CONFIG_FILES = {
    "docker-compose.yml", "docker-compose.yaml", "dockerfile", "Dockerfile",
    ".env", ".env.example", "tsconfig.json", "vite.config.ts", "vite.config.js",
    "webpack.config.js", "tailwind.config.js", "tailwind.config.ts",
    "makefile", "Makefile", "README.md", "readme.md"
}


class RepositoryCrawler:
    """Clones or scans a repository and ingests file metadata."""

    @staticmethod
    def prepare_repository(source: str, target_dir: str) -> Tuple[str, str]:
        """
        Prepares local repository directory.
        If source is a GitHub URL, clone it into target_dir.
        If source is a local directory path, verify it exists.
        Returns (local_path, source_type).
        """
        source = source.strip()
        
        # GitHub URL check
        if source.startswith("http://") or source.startswith("https://") or source.endswith(".git"):
            logger.info(f"Cloning GitHub repository from {source} into {target_dir}")
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir, ignore_errors=True)
            os.makedirs(target_dir, exist_ok=True)
            git.Repo.clone_from(source, target_dir, depth=1)
            return target_dir, "github"
        
        # Local directory check
        if os.path.exists(source) and os.path.isdir(source):
            logger.info(f"Ingesting local directory: {source}")
            return source, "local"

        raise ValueError(f"Invalid repository source: '{source}'. Must be a valid local folder path or GitHub URL.")

    @staticmethod
    def scan_repository(repo_id: str, repo_root: str) -> Tuple[List[FileNode], Dict[str, Any]]:
        """
        Scans repository directory recursively while applying exclusion rules.
        Extracts files, folders, language distribution, LOC, dependencies, configs.
        """
        nodes: List[FileNode] = []
        tech_stack: Dict[str, int] = {}
        detected_dependencies: List[str] = []
        detected_configs: List[str] = []
        entry_points: List[str] = []
        total_files = 0
        total_loc = 0

        repo_root = os.path.abspath(repo_root)

        for root, dirs, files in os.walk(repo_root):
            # Prune ignored directories in-place
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]

            rel_root = os.path.relpath(root, repo_root)
            if rel_root == ".":
                rel_root = ""

            # Add directory node if not root
            if rel_root:
                depth = rel_root.count(os.sep) + 1
                parent = os.path.dirname(rel_root) if os.sep in rel_root else ""
                dir_node = FileNode(
                    repo_id=repo_id,
                    path=root,
                    relative_path=rel_root.replace("\\", "/"),
                    name=os.path.basename(root),
                    is_dir=True,
                    parent_path=parent.replace("\\", "/"),
                    depth=depth
                )
                nodes.append(dir_node)

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in IGNORED_EXTENSIONS or file.startswith("."):
                    continue

                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, repo_root).replace("\\", "/")
                depth = rel_path.count("/")
                parent = os.path.dirname(rel_path) if "/" in rel_path else ""

                # Detect config and dependency files
                file_lower = file.lower()
                if file_lower in DEPENDENCY_FILES or file in DEPENDENCY_FILES:
                    detected_dependencies.append(rel_path)
                if file_lower in CONFIG_FILES or file in CONFIG_FILES:
                    detected_configs.append(rel_path)
                if file_lower in {"main.py", "app.py", "index.js", "index.ts", "main.go", "main.rs", "server.js", "App.tsx", "main.tsx"}:
                    entry_points.append(rel_path)

                # Calculate lines of code & size
                loc = 0
                size_bytes = 0
                try:
                    size_bytes = os.path.getsize(abs_path)
                    with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                        loc = len(lines)
                except Exception as e:
                    logger.debug(f"Error reading {abs_path}: {e}")

                lang = LANG_EXTENSIONS.get(ext, "Other")
                if lang != "Other":
                    tech_stack[lang] = tech_stack.get(lang, 0) + loc

                file_node = FileNode(
                    repo_id=repo_id,
                    path=abs_path,
                    relative_path=rel_path,
                    name=file,
                    is_dir=False,
                    language=lang,
                    size_bytes=size_bytes,
                    loc_count=loc,
                    parent_path=parent,
                    depth=depth
                )
                nodes.append(file_node)
                total_files += 1
                total_loc += loc

        stats = {
            "total_files": total_files,
            "total_loc": total_loc,
            "tech_stack": tech_stack,
            "dependencies": detected_dependencies,
            "config_files": detected_configs,
            "entry_points": entry_points
        }

        return nodes, stats
