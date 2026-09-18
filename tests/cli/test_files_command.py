"""CLI integration tests for `wia files` command."""

from pathlib import Path
from click.testing import CliRunner
from wia.cli.app import main
from wia.services.indexing_service import IndexingService


def test_cli_files_unindexed(tmp_path: Path):
    """Test `wia files` output on unindexed workspace."""
    runner = CliRunner()
    result = runner.invoke(main, ["files", str(tmp_path)])

    assert result.exit_code == 1
    assert "Error:" in result.output
    assert "not indexed" in result.output


def test_cli_files_indexed(tmp_path: Path):
    """Test `wia files` output on indexed workspace."""
    (tmp_path / "app.py").write_text("v = 1", encoding="utf-8")
    IndexingService.index_workspace(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["files", str(tmp_path)])

    assert result.exit_code == 0
    assert "WIA Indexed Files" in result.output
    assert "app.py" in result.output


def test_cli_files_language_filter(tmp_path: Path):
    """Test `wia files --language python` filtering."""
    (tmp_path / "app.py").write_text("v = 1", encoding="utf-8")
    (tmp_path / "index.js").write_text("console.log()", encoding="utf-8")
    IndexingService.index_workspace(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["files", str(tmp_path), "--language", "python"])

    assert result.exit_code == 0
    assert "app.py" in result.output
    assert "index.js" not in result.output
