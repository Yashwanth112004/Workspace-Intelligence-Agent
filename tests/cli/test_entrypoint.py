"""Tests for WIA CLI entrypoint and execution."""

from click.testing import CliRunner
import wia
from wia.cli.app import main


def test_cli_bare_invocation():
    """Test invoking wia without subcommands displays root welcome message."""
    runner = CliRunner()
    result = runner.invoke(main)
    assert result.exit_code == 0
    assert "WIA — Workspace Intelligence Agent" in result.output
    assert wia.__version__ in result.output


def test_python_module_invocation():
    """Verify wia.cli.app:main function is callable as click command."""
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 0
