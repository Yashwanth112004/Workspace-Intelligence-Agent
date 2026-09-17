"""CLI unit tests for `wia search` command."""

from pathlib import Path
from click.testing import CliRunner
from wia.cli.app import main
from wia.services.indexing_service import IndexingService
from wia.services.init_service import InitService


def test_search_cmd(tmp_path: Path):
    InitService.initialize_workspace(tmp_path)
    (tmp_path / "service.py").write_text("class MyService:\n    pass", encoding="utf-8")
    IndexingService.index_workspace(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["search", "MyService", "--workspace", str(tmp_path)])
    assert result.exit_code == 0
    assert "Workspace Search" in result.output
    assert "service.py" in result.output
