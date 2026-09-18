"""CLI integration tests for `wia status` command."""

from pathlib import Path
from click.testing import CliRunner
from wia.cli.app import main
from wia.services.indexing_service import IndexingService
from wia.services.init_service import InitService


def test_cli_status_uninitialized(tmp_path: Path):
    """Test `wia status` output on uninitialized workspace."""
    runner = CliRunner()
    result = runner.invoke(main, ["status", str(tmp_path)])

    assert result.exit_code == 0
    assert "WIA Workspace Status" in result.output
    assert "Not Initialized" in result.output
    assert "Run 'wia init' first." in result.output


def test_cli_status_initialized_unindexed(tmp_path: Path):
    """Test `wia status` output on initialized but unindexed workspace."""
    InitService.initialize_workspace(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["status", str(tmp_path)])

    assert result.exit_code == 0
    assert "WIA Workspace Status" in result.output
    assert "Initialized — Not Indexed" in result.output
    assert "Run 'wia index' to build the workspace index." in result.output


def test_cli_status_up_to_date(tmp_path: Path):
    """Test `wia status` output on up-to-date workspace."""
    (tmp_path / "app.py").write_text("v = 1", encoding="utf-8")
    IndexingService.index_workspace(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["status", str(tmp_path)])

    assert result.exit_code == 0
    assert "WIA Workspace Status" in result.output
    assert "Up to Date" in result.output
    assert "Indexed Files:" in result.output
    assert "Unchanged:" in result.output


def test_cli_status_changes_detected(tmp_path: Path):
    """Test `wia status` output when changes are detected."""
    app_file = tmp_path / "app.py"
    app_file.write_text("v = 1", encoding="utf-8")
    IndexingService.index_workspace(tmp_path)

    app_file.write_text("v = 2", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, ["status", str(tmp_path)])

    assert result.exit_code == 0
    assert "WIA Workspace Status" in result.output
    assert "Changes Detected" in result.output
    assert "Modified:" in result.output
    assert "Run 'wia index' to update the workspace intelligence." in result.output
