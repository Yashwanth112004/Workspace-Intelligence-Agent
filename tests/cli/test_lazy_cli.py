"""Tests verifying CLI version, help, and lazy initialization performance."""

import sys
import subprocess
from unittest.mock import MagicMock
import pytest
import wia


def test_cli_version_output():
    """Verify wia --version outputs exact version 0.1.2."""
    res = subprocess.run([sys.executable, "-m", "wia", "--version"], capture_output=True, text=True)
    assert res.returncode == 0
    assert f"wia version {wia.__version__}" in res.stdout.strip()
    assert wia.__version__ == "0.1.2"


def test_cli_version_no_hf_model_loading(monkeypatch):
    """Ensure `wia --version` does not instantiate or download SentenceTransformer embedding models."""
    mock_st = MagicMock()
    def fail_on_init(*args, **kwargs):
        raise RuntimeError("SentenceTransformer should not be instantiated during wia --version!")

    mock_st.SentenceTransformer = fail_on_init
    monkeypatch.setitem(sys.modules, "sentence_transformers", mock_st)

    from click.testing import CliRunner
    from wia.cli.app import main

    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert f"wia version {wia.__version__}" in result.output.strip()


def test_cli_help_no_hf_model_loading(monkeypatch):
    """Ensure `wia --help` does not instantiate or download SentenceTransformer embedding models."""
    mock_st = MagicMock()
    def fail_on_init(*args, **kwargs):
        raise RuntimeError("SentenceTransformer should not be instantiated during wia --help!")

    mock_st.SentenceTransformer = fail_on_init
    monkeypatch.setitem(sys.modules, "sentence_transformers", mock_st)

    from click.testing import CliRunner
    from wia.cli.app import main

    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "WIA" in result.output

