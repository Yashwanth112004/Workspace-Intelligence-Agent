"""Git repository intelligence, commit history, and hotspot analyzer."""

import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class GitCommitInfo:
    """Represents metadata for a Git commit."""

    commit_hash: str
    author: str
    email: str
    timestamp: str
    message: str
    files_changed: list[str]

    def to_dict(self) -> dict:
        """Convert commit info to serializable dictionary."""
        return asdict(self)


@dataclass
class GitFileStats:
    """Represents Git commit activity and hotspot metrics for a single file."""

    path: str
    commit_count: int
    authors: list[str]

    def to_dict(self) -> dict:
        """Convert file stats to serializable dictionary."""
        return asdict(self)


class GitAnalyzer:
    """Extracts commit history, author statistics, and hotspot activity from Git repositories."""

    @classmethod
    def is_git_repository(cls, repo_path: str | Path) -> bool:
        """Check if the given directory path is a valid Git repository."""
        path = Path(repo_path)
        if not path.is_dir():
            return False
        git_dir = path / ".git"
        return git_dir.exists()

    @classmethod
    def get_commit_history(
        cls, repo_path: str | Path, max_commits: int = 50
    ) -> list[GitCommitInfo]:
        """Extract recent commit history using `git log`."""
        path = Path(repo_path)
        if not cls.is_git_repository(path):
            return []

        try:
            # Format: HASH|AUTHOR|EMAIL|DATE|SUBJECT
            delimiter = "---COMMIT_SEP---"
            field_sep = "|||"
            fmt = f"{delimiter}%H{field_sep}%an{field_sep}%ae{field_sep}%ad{field_sep}%s"

            cmd = [
                "git",
                "-C",
                str(path),
                "log",
                f"-n{max_commits}",
                f"--pretty=format:{fmt}",
                "--name-only",
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, encoding="utf-8", errors="ignore"
            )

            raw_output = result.stdout.strip()
            if not raw_output:
                return []

            commits: list[GitCommitInfo] = []
            raw_blocks = raw_output.split(delimiter)

            for block in raw_blocks:
                block = block.strip()
                if not block:
                    continue

                lines = block.splitlines()
                header = lines[0]
                changed_files = [line.strip() for line in lines[1:] if line.strip()]

                parts = header.split(field_sep)
                if len(parts) >= 5:
                    commits.append(
                        GitCommitInfo(
                            commit_hash=parts[0],
                            author=parts[1],
                            email=parts[2],
                            timestamp=parts[3],
                            message=parts[4],
                            files_changed=changed_files,
                        )
                    )

            return commits
        except (subprocess.SubprocessError, FileNotFoundError):
            return []

    @classmethod
    def get_file_hotspots(
        cls, repo_path: str | Path, top_n: int = 10, max_commits: int = 100
    ) -> list[GitFileStats]:
        """Analyze commit activity to identify high-churn file hotspots in the repository."""
        commits = cls.get_commit_history(repo_path, max_commits=max_commits)
        if not commits:
            return []

        counts: dict[str, int] = {}
        authors_map: dict[str, set[str]] = {}

        for commit in commits:
            for file_path in commit.files_changed:
                counts[file_path] = counts.get(file_path, 0) + 1
                if file_path not in authors_map:
                    authors_map[file_path] = set()
                if commit.author:
                    authors_map[file_path].add(commit.author)

        sorted_files = sorted(counts.items(), key=lambda item: item[1], reverse=True)[:top_n]

        hotspots: list[GitFileStats] = []
        for file_path, count in sorted_files:
            hotspots.append(
                GitFileStats(
                    path=file_path,
                    commit_count=count,
                    authors=sorted(list(authors_map.get(file_path, set()))),
                )
            )

        return hotspots
