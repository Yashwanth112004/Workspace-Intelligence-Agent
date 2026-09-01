"""CLI integration tests for `wia index` command shell."""

from pathlib import Path
from click.testing import CliRunner
from wia.cli.app import main


def test_cli_index_command_success(tmp_path: Path):
    """Test `wia index <path>` executes cleanly on valid workspace."""
    (tmp_path / "main.py").write_text("print('hello')", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(main, ["index", str(tmp_path)])

    assert result.exit_code == 0
    assert "WIA Repository Indexing" in result.output
    assert "Files Discovered:" in result.output
    assert "Files Indexed:" in result.output
    assert "Changes:" in result.output
    assert "Python:" in result.output


def test_cli_index_command_invalid_path(tmp_path: Path):
    """Test `wia index` returns error exit code on invalid path."""
    fake_path = tmp_path / "nonexistent"
    runner = CliRunner()
    result = runner.invoke(main, ["index", str(fake_path)])

    assert result.exit_code == 1
    assert "Error:" in result.output
