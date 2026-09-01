"""CLI unit tests for `wia analyze` command group."""

import json
from pathlib import Path
from click.testing import CliRunner
from wia.cli.app import main


def test_analyze_deps_cmd(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text('[project]\ndependencies = ["click>=8.0.0"]', encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, ["analyze", "deps", "--workspace", str(tmp_path)])
    assert result.exit_code == 0
    assert "Dependencies Analysis" in result.output
    assert "pyproject.toml" in result.output
    assert "click" in result.output


def test_analyze_git_cmd(tmp_path: Path):
    runner = CliRunner()
    result = runner.invoke(main, ["analyze", "git", "--workspace", str(tmp_path)])
    assert result.exit_code == 0
    assert "Git Intelligence" in result.output


def test_analyze_security_cmd(tmp_path: Path):
    (tmp_path / "secret.py").write_text("aws_key = 'AKIAIOSFODNN7EXAMPLE'", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, ["analyze", "security", "--workspace", str(tmp_path)])
    assert result.exit_code == 0
    assert "Security Scan" in result.output
    assert "SEC-001" in result.output
    assert "AKIAIOSFODNN7EXAMPLE" not in result.output
