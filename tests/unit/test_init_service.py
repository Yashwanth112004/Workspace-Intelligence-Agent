"""Unit tests for InitService."""

import json
from pathlib import Path
from wia.constants import WIA_DIR_NAME, WIA_CONFIG_FILE
from wia.services.init_service import InitService


def test_init_service_creates_wia_directory(tmp_path: Path):
    """Verify InitService creates .wia directory and config.json."""
    result = InitService.initialize_workspace(tmp_path)
    assert result.success is True

    wia_dir = tmp_path / WIA_DIR_NAME
    config_file = wia_dir / WIA_CONFIG_FILE

    assert wia_dir.exists() and wia_dir.is_dir()
    assert config_file.exists() and config_file.is_file()

    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)
    assert config["workspace_path"] == str(tmp_path.resolve())


def test_init_service_existing_without_force(tmp_path: Path):
    """Verify InitService fails if .wia exists and force=False."""
    InitService.initialize_workspace(tmp_path)

    # Second initialization attempt should fail without force
    result2 = InitService.initialize_workspace(tmp_path, force=False)
    assert result2.success is False
    assert "already initialized" in result2.message


def test_init_service_existing_with_force(tmp_path: Path):
    """Verify InitService succeeds if force=True."""
    InitService.initialize_workspace(tmp_path)

    # Second attempt with force=True should succeed
    result2 = InitService.initialize_workspace(tmp_path, force=True)
    assert result2.success is True


def test_init_service_nonexistent_path(tmp_path: Path):
    """Verify InitService fails on nonexistent target path."""
    fake_path = tmp_path / "does_not_exist"
    result = InitService.initialize_workspace(fake_path)
    assert result.success is False
    assert "Target path does not exist" in result.message
