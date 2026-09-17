"""Tests for WIA CLI help system."""

from click.testing import CliRunner
from wia.cli.app import main


def test_cli_help_flag():
    """Test `wia --help` displays global help guidance."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "WIA — Workspace Intelligence Agent" in result.output
    assert "Common Commands:" in result.output
    assert "init" in result.output
    assert "index" in result.output


def test_cli_short_help_flag():
    """Test `wia -h` displays global help guidance."""
    runner = CliRunner()
    result = runner.invoke(main, ["-h"])
    assert result.exit_code == 0
    assert "WIA — Workspace Intelligence Agent" in result.output
    assert "epilog" not in result.output.lower()  # ensures clean help display
    assert "For detailed command usage" in result.output
