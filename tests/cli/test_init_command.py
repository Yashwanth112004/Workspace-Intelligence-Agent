"""CLI integration tests for `wia init` command."""

from pathlib import Path
from click.testing import CliRunner
from wia.cli.app import main
from wia.constants import WIA_DIR_NAME


def test_cli_init_command_success(tmp_path: Path):
    """Test `wia init <path>` creates workspace directory."""
    runner = CliRunner()
    result = runner.invoke(main, ["init", str(tmp_path)])

    assert result.exit_code == 0
    assert "WIA Initialization" in result.output
    assert (tmp_path / WIA_DIR_NAME).exists()


def test_cli_init_command_already_initialized(tmp_path: Path):
    """Test `wia init <path>` returns error code 1 when already initialized."""
    runner = CliRunner()
    runner.invoke(main, ["init", str(tmp_path)])

    # Second invocation without --force
    result2 = runner.invoke(main, ["init", str(tmp_path)])
    assert result2.exit_code == 1
    assert "Error:" in result2.output
    assert "already initialized" in result2.output


def test_cli_init_command_with_force(tmp_path: Path):
    """Test `wia init <path> --force` succeeds even when already initialized."""
    runner = CliRunner()
    runner.invoke(main, ["init", str(tmp_path)])

    result2 = runner.invoke(main, ["init", str(tmp_path), "--force"])
    assert result2.exit_code == 0
    assert "WIA Initialization" in result2.output
