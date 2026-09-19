"""CLI unit tests for `wia summary` command."""

from pathlib import Path
from click.testing import CliRunner
from wia.cli.app import main
from wia.services.indexing_service import IndexingService
from wia.services.init_service import InitService


def test_summary_cmd(tmp_path: Path):
    InitService.initialize_workspace(tmp_path)
    (tmp_path / "main.py").write_text("print('hello')", encoding="utf-8")
    IndexingService.index_workspace(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["summary", "--workspace", str(tmp_path)])
    assert result.exit_code == 0
    assert "Workspace Intelligence Summary" in result.output
    assert "Repository Facts" in result.output
    assert "main.py" in result.output


def test_summary_cmd_with_components(tmp_path: Path):
    InitService.initialize_workspace(tmp_path)
    cli_dir = tmp_path / "wia" / "cli"
    cli_dir.mkdir(parents=True)
    (cli_dir / "app.py").write_text("def cli_entrypoint(): pass", encoding="utf-8")
    IndexingService.index_workspace(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["summary", "--workspace", str(tmp_path)])
    assert result.exit_code == 0
    assert "Workspace Intelligence Summary" in result.output
    assert "Architecture & Subsystems" in result.output
    assert "CLI Presentation & Commands" in result.output


def test_main_summary_flag(tmp_path: Path, monkeypatch):
    InitService.initialize_workspace(tmp_path)
    (tmp_path / "main.py").write_text("print('hello')", encoding="utf-8")
    IndexingService.index_workspace(tmp_path)

    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(main, ["--summary"])
    assert result.exit_code == 0
    assert "Workspace Intelligence Summary" in result.output
    assert "Repository Facts" in result.output
