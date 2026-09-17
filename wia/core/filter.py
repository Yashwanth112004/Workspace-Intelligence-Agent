"""WIA file exclusion and filter engine."""

from dataclasses import dataclass
from pathlib import Path
from wia.core.config import WorkspaceConfig
from wia.core.discovery import DiscoveredFile
from wia.core.gitignore import GitignoreProcessor


class FilterReason:
    """Exclusion reason classifications."""

    GIT_IGNORED = "GIT_IGNORED"
    EXCEEDS_MAX_SIZE = "EXCEEDS_MAX_SIZE"
    BINARY_FILE = "BINARY_FILE"
    VENDOR_DEPENDENCY = "VENDOR_DEPENDENCY"
    BUILD_ARTIFACT = "BUILD_ARTIFACT"
    SYSTEM_FILE = "SYSTEM_FILE"
    CUSTOM_PATTERN = "CUSTOM_PATTERN"


# Known sets for fast lookup
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp", ".svg",
    ".pdf", ".zip", ".tar", ".gz", ".7z", ".rar", ".bz2",
    ".exe", ".dll", ".so", ".dylib", ".bin",
    ".pyc", ".pyo", ".class", ".o", ".a", ".obj",
    ".db", ".sqlite", ".sqlite3",
    ".woff", ".woff2", ".ttf", ".eot",
    ".mp3", ".mp4", ".wav", ".avi", ".mov",
}

VENDOR_DIRECTORIES = {
    "node_modules", "venv", ".venv", "env", ".env", "vendor",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".tox",
    ".cargo", ".gradle", ".idea", ".vscode", ".wia",
}

BUILD_DIRECTORIES = {
    "dist", "build", "target", "out", "bin", "obj",
    ".next", ".nuxt",
}

SYSTEM_FILENAMES = {
    ".ds_store", "thumbs.db", "desktop.ini",
}

GENERATED_REPORT_FILENAMES = {
    "wia-report.html", "report_data.json",
}


@dataclass
class FilterResult:
    """Filter evaluation result for a candidate file."""

    should_index: bool
    reason: str | None = None


class FileFilter:
    """Evaluates candidate files against Gitignore, binary, size, and WIA exclusion rules."""

    def __init__(
        self,
        config: WorkspaceConfig,
        gitignore_processor: GitignoreProcessor | None = None,
    ):
        self.config = config
        self.gitignore_processor = gitignore_processor

    def evaluate(self, file: DiscoveredFile) -> FilterResult:
        """Evaluate if a discovered file should be indexed."""
        rel_path = file.relative_path.lower()
        parts = [p.lower() for p in Path(rel_path).parts]
        filename = Path(rel_path).name.lower()

        # 0. WIA generated report artifacts check
        if filename in GENERATED_REPORT_FILENAMES or rel_path == "wia-report.html":
            return FilterResult(should_index=False, reason=FilterReason.BUILD_ARTIFACT)

        # 1. System metadata & build artifact filenames (DS_Store, Thumbs.db, PKG-INFO, egg-info)
        if (
            filename in SYSTEM_FILENAMES
            or filename == "pkg-info"
            or filename.endswith(".egg-info")
            or filename.endswith(".dist-info")
            or filename.endswith(".pyc")
        ):
            return FilterResult(should_index=False, reason=FilterReason.BUILD_ARTIFACT)

        # 2. Git ignore check
        if self.gitignore_processor and self.gitignore_processor.is_ignored(file.relative_path):
            return FilterResult(should_index=False, reason=FilterReason.GIT_IGNORED)

        # 3. Vendor dependency directory check
        for part in parts[:-1]:  # exclude filename itself
            if part in VENDOR_DIRECTORIES:
                return FilterResult(should_index=False, reason=FilterReason.VENDOR_DEPENDENCY)

        # 4. Build output directory check
        for part in parts[:-1]:
            if part in BUILD_DIRECTORIES:
                return FilterResult(should_index=False, reason=FilterReason.BUILD_ARTIFACT)

        # 5. Known binary extension check
        ext = Path(rel_path).suffix
        if ext in BINARY_EXTENSIONS:
            return FilterResult(should_index=False, reason=FilterReason.BINARY_FILE)

        # 6. Maximum file size check
        if file.file_size > self.config.max_file_size_bytes:
            return FilterResult(should_index=False, reason=FilterReason.EXCEEDS_MAX_SIZE)

        # 7. File passes all filter checks -> include in index
        return FilterResult(should_index=True, reason=None)
