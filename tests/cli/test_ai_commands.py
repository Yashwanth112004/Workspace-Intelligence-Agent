"""CLI unit tests for architecture, impact, ask, explain, and doctor commands."""

from pathlib import Path
from click.testing import CliRunner
from wia.cli.app import main
from wia.services.indexing_service import IndexingService
from wia.services.init_service import InitService


def test_cli_new_commands(tmp_path: Path):
    InitService.initialize_workspace(tmp_path)
    (tmp_path / "app.py").write_text("class CoreApp:\n    pass", encoding="utf-8")
    IndexingService.index_workspace(tmp_path)

    runner = CliRunner()

    # 1. test `wia architecture`
    res_arch = runner.invoke(main, ["architecture", "-w", str(tmp_path)])
    assert res_arch.exit_code == 0
    assert "Architecture Intelligence" in res_arch.output

    # 2. test `wia impact`
    res_imp = runner.invoke(main, ["impact", "CoreApp", "-w", str(tmp_path)])
    assert res_imp.exit_code == 0
    assert "Impact Analysis" in res_imp.output

    # 3. test `wia ask`
    res_ask = runner.invoke(main, ["ask", "Explain CoreApp", "-w", str(tmp_path)])
    assert res_ask.exit_code == 0
    assert "Workspace Reasoning" in res_ask.output

    # 4. test `wia explain`
    res_exp = runner.invoke(main, ["explain", "app.py", "-w", str(tmp_path)])
    assert res_exp.exit_code == 0
    assert "Code Explanation" in res_exp.output

    # 5. test `wia doctor`
    res_doc = runner.invoke(main, ["doctor", "-w", str(tmp_path)])
    assert res_doc.exit_code == 0
    assert "System Diagnostics" in res_doc.output
