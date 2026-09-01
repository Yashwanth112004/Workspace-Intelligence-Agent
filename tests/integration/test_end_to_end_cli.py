"""End-to-end CLI workflow integration test suite."""

from pathlib import Path
from click.testing import CliRunner
from wia.cli.app import main


def test_complete_developer_cli_workflow(tmp_path: Path):
    """Test full developer lifecycle: init -> index -> status -> modify -> reindex -> files -> info."""
    runner = CliRunner()

    # 1. Setup mock multi-language repository
    (tmp_path / "main.py").write_text("print('hello')", encoding="utf-8")
    (tmp_path / "app.ts").write_text("console.log('hi')", encoding="utf-8")
    (tmp_path / "build.log").write_text("log data", encoding="utf-8")
    (tmp_path / ".gitignore").write_text("*.log\n", encoding="utf-8")

    # 2. Run `wia init`
    res_init = runner.invoke(main, ["init", str(tmp_path)])
    assert res_init.exit_code == 0
    assert "WIA Initialization" in res_init.output

    # 3. Check status before indexing
    res_status_unindexed = runner.invoke(main, ["status", str(tmp_path)])
    assert res_status_unindexed.exit_code == 0
    assert "Initialized — Not Indexed" in res_status_unindexed.output

    # 4. Run `wia index`
    res_index1 = runner.invoke(main, ["index", str(tmp_path)])
    assert res_index1.exit_code == 0
    assert "Files Discovered: 4" in res_index1.output
    assert "Files Indexed: 3" in res_index1.output
    assert "Files Ignored: 1" in res_index1.output

    # 5. Check `wia status` after indexing
    res_status1 = runner.invoke(main, ["status", str(tmp_path)])
    assert res_status1.exit_code == 0
    assert "Indexed Files: 3" in res_status1.output
    assert "Unchanged: 3" in res_status1.output

    # 6. Modify main.py and add helper.py
    (tmp_path / "main.py").write_text("print('hello v2')", encoding="utf-8")
    (tmp_path / "helper.py").write_text("x = 42", encoding="utf-8")

    # 7. Check `wia status` detects modifications
    res_status2 = runner.invoke(main, ["status", str(tmp_path)])
    assert res_status2.exit_code == 0
    assert "Added: 1" in res_status2.output
    assert "Modified: 1" in res_status2.output
    assert "Unchanged: 2" in res_status2.output

    # 8. Re-index workspace
    res_index2 = runner.invoke(main, ["index", str(tmp_path)])
    assert res_index2.exit_code == 0
    assert "Added: 1" in res_index2.output
    assert "Modified: 1" in res_index2.output

    # 9. Query `wia files --language python`
    res_files = runner.invoke(main, ["files", str(tmp_path), "--language", "python"])
    assert res_files.exit_code == 0
    assert "main.py" in res_files.output
    assert "helper.py" in res_files.output
    assert "app.ts" not in res_files.output

    # 10. Inspect `wia info`
    res_info = runner.invoke(main, ["info", str(tmp_path)])
    assert res_info.exit_code == 0
    assert "WIA Workspace Information" in res_info.output
    assert "Python:" in res_info.output
    assert "TypeScript:" in res_info.output
