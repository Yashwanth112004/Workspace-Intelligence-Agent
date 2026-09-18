"""Workspace repository validation engine."""

import os
from dataclasses import dataclass
from pathlib import Path
from wia.exceptions import WorkspaceValidationError


@dataclass
class WorkspaceValidationResult:
    """Encapsulates workspace inspection and validation state."""

    path: Path
    is_valid: bool
    is_git_repo: bool
    is_empty: bool
    is_readable: bool
    error_message: str | None = None


class WorkspaceValidator:
    """Validates local directories before WIA indexing operations."""

    @staticmethod
    def validate(target_path: str | Path) -> WorkspaceValidationResult:
        """Inspect and validate target workspace path.

        Raises WorkspaceValidationError if validation fails catastrophically.
        """
        raw_path = Path(target_path)

        # 1. Path existence check
        if not raw_path.exists():
            msg = f"Workspace path does not exist: '{raw_path}'"
            return WorkspaceValidationResult(
                path=raw_path,
                is_valid=False,
                is_git_repo=False,
                is_empty=True,
                is_readable=False,
                error_message=msg,
            )

        resolved_path = raw_path.resolve()

        # 2. Directory check
        if not resolved_path.is_dir():
            msg = f"Workspace path is a file, not a directory: '{resolved_path}'"
            return WorkspaceValidationResult(
                path=resolved_path,
                is_valid=False,
                is_git_repo=False,
                is_empty=False,
                is_readable=False,
                error_message=msg,
            )

        # 3. Accessibility & read permissions check
        if not os.access(resolved_path, os.R_OK):
            msg = f"Workspace directory is not readable (Permission Denied): '{resolved_path}'"
            return WorkspaceValidationResult(
                path=resolved_path,
                is_valid=False,
                is_git_repo=False,
                is_empty=False,
                is_readable=False,
                error_message=msg,
            )

        # 4. Check contents & empty status
        try:
            entries = list(resolved_path.iterdir())
            is_empty = len(entries) == 0
            is_readable = True
        except PermissionError:
            msg = f"Permission denied while reading contents of '{resolved_path}'"
            return WorkspaceValidationResult(
                path=resolved_path,
                is_valid=False,
                is_git_repo=False,
                is_empty=False,
                is_readable=False,
                error_message=msg,
            )

        # 5. Git repository check
        git_dir = resolved_path / ".git"
        is_git_repo = git_dir.exists()

        return WorkspaceValidationResult(
            path=resolved_path,
            is_valid=True,
            is_git_repo=is_git_repo,
            is_empty=is_empty,
            is_readable=is_readable,
            error_message=None,
        )

    @classmethod
    def validate_or_raise(cls, target_path: str | Path) -> WorkspaceValidationResult:
        """Validate workspace path and raise WorkspaceValidationError if invalid."""
        result = cls.validate(target_path)
        if not result.is_valid:
            raise WorkspaceValidationError(result.error_message)
        return result
