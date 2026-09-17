"""Unit tests for Git Intelligence & Hotspot Analyzer."""

from pathlib import Path
from wia.analyzers.git.git_analyzer import GitAnalyzer, GitCommitInfo, GitFileStats


def test_git_commit_info_to_dict():
    commit = GitCommitInfo(
        commit_hash="abc1234",
        author="John Doe",
        email="john@example.com",
        timestamp="2026-09-01",
        message="Initial commit",
        files_changed=["main.py", "README.md"],
    )
    data = commit.to_dict()
    assert data["commit_hash"] == "abc1234"
    assert data["files_changed"] == ["main.py", "README.md"]


def test_git_file_stats_to_dict():
    stats = GitFileStats(
        path="wia/cli/app.py",
        commit_count=12,
        authors=["Alice", "Bob"],
    )
    data = stats.to_dict()
    assert data["path"] == "wia/cli/app.py"
    assert data["commit_count"] == 12
    assert data["authors"] == ["Alice", "Bob"]


def test_is_git_repository_non_git(tmp_path: Path):
    assert GitAnalyzer.is_git_repository(tmp_path) is False


def test_is_git_repository_valid(tmp_path: Path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    assert GitAnalyzer.is_git_repository(tmp_path) is True


def test_get_commit_history_current_repo():
    repo_root = Path(__file__).parents[2]
    if GitAnalyzer.is_git_repository(repo_root):
        commits = GitAnalyzer.get_commit_history(repo_root, max_commits=5)
        assert isinstance(commits, list)
        if commits:
            assert len(commits[0].commit_hash) > 0
            assert isinstance(commits[0].files_changed, list)


def test_get_file_hotspots_current_repo():
    repo_root = Path(__file__).parents[2]
    if GitAnalyzer.is_git_repository(repo_root):
        hotspots = GitAnalyzer.get_file_hotspots(repo_root, top_n=5, max_commits=20)
        assert isinstance(hotspots, list)
        if hotspots:
            assert hotspots[0].commit_count >= 1
            assert len(hotspots[0].authors) >= 1
