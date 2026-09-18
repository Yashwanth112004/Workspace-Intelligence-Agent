"""Tests for WIA version flag and version command."""

from click.testing import CliRunner
import wia
from wia.cli.app import main


def test_version_flag():
    """Test `wia --version` outputs version string."""
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert f"wia version {wia.__version__}" in result.output.strip()


def test_version_command():
    """Test `wia version` subcommand outputs version string."""
    runner = CliRunner()
    result = runner.invoke(main, ["version"])
    assert result.exit_code == 0
    assert f"wia version {wia.__version__}" in result.output.strip()
