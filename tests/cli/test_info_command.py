"""CLI integration tests for `wia info` command."""

from pathlib import Path
from click.testing import CliRunner
from wia.cli.app import main
from wia.services.indexing_service import IndexingService


def test_cli_info_unindexed(tmp_path: Path):
    """Test `wia info` output on unindexed workspace."""
    runner = CliRunner()
    result = runner.invoke(main, ["info", str(tmp_path)])

    assert result.exit_code == 1
    assert "Error:" in result.output
    assert "not indexed" in result.output


def test_cli_info_indexed(tmp_path: Path):
    """Test `wia info` output on indexed workspace."""
    (tmp_path / "app.py").write_text("v = 1", encoding="utf-8")
    IndexingService.index_workspace(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["info", str(tmp_path)])

    assert result.exit_code == 0
    assert "WIA Workspace Information" in result.output
    assert "WIA Version:" in result.output
    assert "File Statistics:" in result.output
    assert "Language Distribution:" in result.output
    assert "Python" in result.output
