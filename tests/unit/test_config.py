"""Unit tests for WorkspaceConfig model."""

from pathlib import Path
from wia.core.config import WorkspaceConfig


def test_config_defaults():
    """Verify WorkspaceConfig initializes with correct defaults."""
    cfg = WorkspaceConfig(workspace_path="/path/to/repo")
    assert cfg.version == "1.0"
    assert cfg.workspace_path == "/path/to/repo"
    assert cfg.max_file_size_bytes == 10 * 1024 * 1024
    assert cfg.hash_algorithm == "sha256"
    assert cfg.exclude_patterns == []
    assert cfg.created_at is not None


def test_config_serialization(tmp_path: Path):
    """Verify WorkspaceConfig serialization to and from dictionary/disk."""
    cfg = WorkspaceConfig(
        workspace_path=str(tmp_path),
        exclude_patterns=["*.log", "tmp/"],
    )

    cfg.save_to_workspace(tmp_path)
    loaded_cfg = WorkspaceConfig.load_from_workspace(tmp_path)

    assert loaded_cfg.version == cfg.version
    assert loaded_cfg.workspace_path == cfg.workspace_path
    assert loaded_cfg.exclude_patterns == ["*.log", "tmp/"]
