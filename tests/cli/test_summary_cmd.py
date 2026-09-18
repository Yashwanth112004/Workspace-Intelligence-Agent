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
