"""Unit tests for WorkspaceValidator core engine."""

import pytest
from pathlib import Path
from wia.core.validator import WorkspaceValidator
from wia.exceptions import WorkspaceValidationError


def test_validate_valid_directory(tmp_path: Path):
    """Test validating a normal directory."""
    (tmp_path / "main.py").write_text("print('hello')", encoding="utf-8")
    result = WorkspaceValidator.validate(tmp_path)

    assert result.is_valid is True
    assert result.is_git_repo is False
    assert result.is_empty is False
    assert result.is_readable is True
    assert result.error_message is None


def test_validate_empty_directory(tmp_path: Path):
    """Test validating an empty directory."""
    result = WorkspaceValidator.validate(tmp_path)

    assert result.is_valid is True
    assert result.is_empty is True


def test_validate_git_repository(tmp_path: Path):
    """Test validating a directory containing a .git folder."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    result = WorkspaceValidator.validate(tmp_path)

    assert result.is_valid is True
    assert result.is_git_repo is True


def test_validate_nonexistent_path(tmp_path: Path):
    """Test validating a path that does not exist."""
    fake_path = tmp_path / "nonexistent"
    result = WorkspaceValidator.validate(fake_path)

    assert result.is_valid is False
    assert "does not exist" in result.error_message


def test_validate_file_instead_of_directory(tmp_path: Path):
    """Test validating a path pointing to a file rather than a directory."""
    file_path = tmp_path / "sample.txt"
    file_path.write_text("data", encoding="utf-8")

    result = WorkspaceValidator.validate(file_path)
    assert result.is_valid is False
    assert "not a directory" in result.error_message


def test_validate_or_raise_exception(tmp_path: Path):
    """Test validate_or_raise raises WorkspaceValidationError for invalid paths."""
    fake_path = tmp_path / "nonexistent"
    with pytest.raises(WorkspaceValidationError):
        WorkspaceValidator.validate_or_raise(fake_path)
