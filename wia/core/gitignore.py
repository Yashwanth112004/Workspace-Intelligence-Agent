"""Gitignore pattern processing engine using pathspec with caching."""

from pathlib import Path
import pathspec


class GitignoreProcessor:
    """Parses root and nested `.gitignore` files to test file paths against Git ignore rules."""

    def __init__(self, root_path: str | Path):
        self.root_path = Path(root_path).resolve()
        self.spec: pathspec.PathSpec | None = None
        self._file_cache: dict[str, bool] = {}
        self._dir_cache: dict[str, bool] = {}
        self._load_ignore_rules()

    def _load_ignore_rules(self) -> None:
        """Scan repository for root and nested .gitignore files and compile PathSpec matcher."""
        patterns: list[str] = [".git/", ".wia/"]  # Default metadata excludes

        if not self.root_path.exists() or not self.root_path.is_dir():
            self.spec = pathspec.PathSpec.from_lines("gitignore", patterns)
            return

        # 1. Root .gitignore
        root_gitignore = self.root_path / ".gitignore"
        if root_gitignore.exists() and root_gitignore.is_file():
            try:
                patterns.extend(root_gitignore.read_text(encoding="utf-8").splitlines())
            except Exception:
                pass

        # 2. Git info exclude (.git/info/exclude) if present
        git_exclude = self.root_path / ".git" / "info" / "exclude"
        if git_exclude.exists() and git_exclude.is_file():
            try:
                patterns.extend(git_exclude.read_text(encoding="utf-8").splitlines())
            except Exception:
                pass

        # 3. Nested .gitignore files
        for gitignore_file in self.root_path.rglob(".gitignore"):
            if gitignore_file == root_gitignore:
                continue
            try:
                rel_dir = gitignore_file.parent.relative_to(self.root_path).as_posix()
                lines = gitignore_file.read_text(encoding="utf-8").splitlines()
                for line in lines:
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#"):
                        continue
                    # Prefix nested rules with relative subfolder path
                    if stripped.startswith("!"):
                        patterns.append(f"!{rel_dir}/{stripped[1:]}")
                    else:
                        patterns.append(f"{rel_dir}/{stripped}")
            except Exception:
                pass

        self.spec = pathspec.PathSpec.from_lines("gitignore", patterns)

    def is_ignored(self, relative_path: str) -> bool:
        """Check if a relative POSIX file path matches `.gitignore` patterns."""
        if not self.spec:
            return False

        posix_path = relative_path.replace("\\", "/")
        if posix_path in self._file_cache:
            return self._file_cache[posix_path]

        # Fast parent directory check
        parts = posix_path.split("/")
        for i in range(1, len(parts)):
            parent_dir = "/".join(parts[:i])
            if parent_dir in self._dir_cache:
                if self._dir_cache[parent_dir]:
                    self._file_cache[posix_path] = True
                    return True
            else:
                is_dir_ign = bool(
                    self.spec.match_file(parent_dir + "/")
                    or self.spec.match_file(parent_dir)
                )
                self._dir_cache[parent_dir] = is_dir_ign
                if is_dir_ign:
                    self._file_cache[posix_path] = True
                    return True

        res = bool(self.spec.match_file(posix_path))
        self._file_cache[posix_path] = res
        return res
