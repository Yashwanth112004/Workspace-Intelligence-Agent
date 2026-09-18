"""Programming language detection engine."""

from pathlib import Path

# Extension to language map
EXTENSION_MAP: dict[str, str] = {
    ".py": "Python",
    ".pyw": "Python",
    ".js": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".jsx": "JavaScript React",
    ".ts": "TypeScript",
    ".mts": "TypeScript",
    ".cts": "TypeScript",
    ".tsx": "TypeScript React",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "Less",
    ".c": "C",
    ".h": "C/C++ Header",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".hpp": "C++ Header",
    ".cs": "C#",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".ps1": "PowerShell",
    ".sql": "SQL",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
    ".md": "Markdown",
    ".markdown": "Markdown",
    ".xml": "XML",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".r": "R",
    ".dart": "Dart",
    ".lua": "Lua",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".scala": "Scala",
    ".ipynb": "Jupyter Notebook",
}

# Filename to language map
FILENAME_MAP: dict[str, str] = {
    "dockerfile": "Docker",
    "containerfile": "Docker",
    "makefile": "Makefile",
    "cmakelists.txt": "CMake",
    "jenkinsfile": "Groovy",
    "procfile": "Procfile",
    ".gitignore": "Git Ignore",
    ".env": "Environment Config",
}


class FileType:
    """Standardized classification categories for workspace files."""

    SOURCE_CODE = "Source Code"
    NOTEBOOK = "Notebook"
    CONFIGURATION = "Configuration"
    DOCUMENTATION = "Documentation"
    TEST = "Test"
    BUILD = "Build"
    CI_CD = "CI/CD"
    DATA = "Data"
    GENERATED = "Generated"
    ASSET = "Asset"
    DEPENDENCY_LOCK = "Dependency Lock"
    SCRIPT = "Script"
    BINARY = "Binary"
    UNSUPPORTED = "Unsupported"


class LanguageDetector:
    """Multi-evidence programming language detection and file classification engine."""

    @classmethod
    def detect_language(cls, file_path: str | Path) -> str:
        """Detect programming language using filename, extension, and shebang analysis."""
        path = Path(file_path)
        filename_lower = path.name.lower()

        # 1. Exact filename evidence
        if filename_lower in FILENAME_MAP:
            return FILENAME_MAP[filename_lower]

        # 2. Extension evidence
        ext_lower = path.suffix.lower()
        if ext_lower in EXTENSION_MAP:
            return EXTENSION_MAP[ext_lower]

        # 3. Shebang evidence (if file is readable)
        if path.exists() and path.is_file():
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    first_line = f.readline().strip()
                    if first_line.startswith("#!"):
                        shebang_lang = cls._detect_shebang(first_line)
                        if shebang_lang:
                            return shebang_lang
            except Exception:
                pass

        return "Unknown"

    @classmethod
    def detect_file_type(cls, file_path: str | Path) -> str:
        """Classify file into functional categories (Source, Notebook, Test, CI/CD, Build, etc.)."""
        path = Path(file_path)
        rel_str = str(file_path).replace("\\", "/").lower()
        filename_lower = path.name.lower()
        ext_lower = path.suffix.lower()
        parts = [p.lower() for p in path.parts]

        # 1. Notebooks
        if ext_lower == ".ipynb":
            return FileType.NOTEBOOK

        # 2. CI / CD Workflows
        if ".github/workflows" in rel_str or ".gitlab-ci" in filename_lower or "jenkinsfile" in filename_lower or ".circleci" in rel_str:
            return FileType.CI_CD

        # 3. Dependency Locks
        if filename_lower in (
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
            "poetry.lock",
            "uv.lock",
            "cargo.lock",
            "gemfile.lock",
            "composer.lock",
            "pipfile.lock",
        ) or ext_lower == ".lock":
            return FileType.DEPENDENCY_LOCK

        # 4. Tests
        if (
            filename_lower.startswith("test_")
            or filename_lower.endswith("_test.py")
            or ".test." in filename_lower
            or ".spec." in filename_lower
            or any(part in ("tests", "test", "__tests__", "spec", "specs") for part in parts[:-1])
        ):
            return FileType.TEST

        # 5. Build & Packaging Manifests
        if filename_lower in (
            "pyproject.toml",
            "requirements.txt",
            "requirements-dev.txt",
            "setup.py",
            "setup.cfg",
            "package.json",
            "cargo.toml",
            "go.mod",
            "go.sum",
            "pom.xml",
            "build.gradle",
            "makefile",
            "cmakelists.txt",
            "gemfile",
        ) or filename_lower.startswith("dockerfile") or filename_lower.startswith("containerfile"):
            return FileType.BUILD

        # 6. Documentation
        if ext_lower in (".md", ".markdown", ".rst", ".adoc") or (
            ext_lower == ".txt" and any(k in filename_lower for k in ("readme", "license", "notice", "contributing", "changelog", "authors"))
        ) or any(part in ("docs", "doc", "documentation") for part in parts[:-1]):
            return FileType.DOCUMENTATION

        # 7. Configuration
        if filename_lower in (
            ".env",
            ".env.example",
            ".gitignore",
            ".dockerignore",
            ".editorconfig",
            ".eslintrc",
            ".prettierrc",
            "tsconfig.json",
            "vite.config.js",
            "vite.config.ts",
            "webpack.config.js",
            "docker-compose.yml",
            "docker-compose.yaml",
        ) or ext_lower in (".toml", ".ini", ".cfg", ".conf") or (
            ext_lower in (".yaml", ".yml", ".json") and not any(part in ("src", "lib", "app") for part in parts)
        ):
            return FileType.CONFIGURATION

        # 8. Scripts
        if ext_lower in (".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd") or any(
            part in ("scripts", "bin", "tools") for part in parts[:-1]
        ):
            return FileType.SCRIPT

        # 9. Data files
        if ext_lower in (".csv", ".tsv", ".parquet", ".jsonl", ".sqlite", ".sqlite3", ".db", ".sql"):
            return FileType.DATA

        # 10. Assets / Media
        if ext_lower in (
            ".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp", ".svg",
            ".woff", ".woff2", ".ttf", ".eot", ".mp3", ".mp4", ".wav",
        ):
            return FileType.ASSET

        # 11. Source Code for recognized programming languages
        lang = cls.detect_language(file_path)
        if lang != "Unknown":
            return FileType.SOURCE_CODE

        return FileType.UNSUPPORTED

    @staticmethod
    def _detect_shebang(first_line: str) -> str | None:
        """Parse shebang line for interpreter hints."""
        line_lower = first_line.lower()

        if "python" in line_lower:
            return "Python"
        if "node" in line_lower or "bun" in line_lower or "deno" in line_lower:
            return "JavaScript"
        if "bash" in line_lower or "sh" in line_lower or "zsh" in line_lower:
            return "Shell"
        if "ruby" in line_lower:
            return "Ruby"
        if "perl" in line_lower:
            return "Perl"
        if "php" in line_lower:
            return "PHP"

        return None

