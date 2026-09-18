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


class LanguageDetector:
    """Multi-evidence programming language detection engine."""

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
