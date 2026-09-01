"""Service for initializing a WIA workspace."""

import json
from pathlib import Path
from wia.constants import WIA_DIR_NAME, WIA_CONFIG_FILE, CURRENT_CONFIG_SCHEMA_VERSION
from wia.core.config import WorkspaceConfig
from wia.exceptions import WorkspaceValidationError
from wia.services.base import BaseService, ServiceResult


class InitService(BaseService):
    """Orchestrates workspace initialization and WIA directory setup."""

    @staticmethod
    def initialize_workspace(
        target_path: str | Path | None = None, force: bool = False
    ) -> ServiceResult[dict]:
        """Initialize the `.wia/` metadata directory in target repository."""
        path = Path(target_path).resolve() if target_path else Path.cwd().resolve()

        if not path.exists():
            return ServiceResult.fail(
                f"Target path does not exist: {path}",
                error=WorkspaceValidationError(f"Path not found: {path}"),
            )

        if not path.is_dir():
            return ServiceResult.fail(
                f"Target path is not a directory: {path}",
                error=WorkspaceValidationError(f"Path is not a directory: {path}"),
            )

        wia_dir = path / WIA_DIR_NAME
        config_file = wia_dir / WIA_CONFIG_FILE

        if wia_dir.exists() and not force:
            return ServiceResult.fail(
                f"WIA workspace already initialized at {wia_dir}. Use --force to re-initialize."
            )

        try:
            config = WorkspaceConfig(workspace_path=str(path))
            config.save_to_workspace(path)

            gitignore_hint = False
            root_gitignore = path / ".gitignore"
            if root_gitignore.exists():
                try:
                    content = root_gitignore.read_text(encoding="utf-8")
                    if ".wia" not in content and f"{WIA_DIR_NAME}/" not in content:
                        gitignore_hint = True
                except Exception:
                    pass

            payload = {
                "workspace_path": str(path),
                "wia_dir": str(wia_dir),
                "config_file": str(config_file),
                "gitignore_hint": gitignore_hint,
            }

            return ServiceResult.ok(
                f"Initialized WIA workspace in {wia_dir}", data=payload
            )

        except Exception as err:
            return ServiceResult.fail(
                f"Failed to initialize WIA workspace: {err}", error=err
            )
