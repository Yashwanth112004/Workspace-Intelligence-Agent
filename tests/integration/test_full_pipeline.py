"""Comprehensive end-to-end integration test suite for complete WIA CLI workflow."""

import json
from pathlib import Path
from click.testing import CliRunner
from wia.cli.app import main


def test_full_wia_end_to_end_pipeline(tmp_path: Path):
    runner = CliRunner()

    # 1. Test `wia init`
    res_init = runner.invoke(main, ["init", str(tmp_path)])
    assert res_init.exit_code == 0
    assert (tmp_path / ".wia").exists()

    # 2. Populate synthetic multi-language project files
    (tmp_path / "app.py").write_text("import os\n\ndef main():\n    print('WIA Agent')", encoding="utf-8")
    (tmp_path / "index.js").write_text("const express = require('express');", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("requests>=2.28.0\nflask==2.3.0", encoding="utf-8")
    (tmp_path / "package.json").write_text(json.dumps({"dependencies": {"express": "^4.18.0"}}), encoding="utf-8")
    (tmp_path / "credentials.py").write_text("aws_key = 'AKIAIOSFODNN7EXAMPLE'", encoding="utf-8")

    # 3. Test `wia index`
    res_index = runner.invoke(main, ["index", str(tmp_path)])
    assert res_index.exit_code == 0
    assert "WIA Repository Indexing" in res_index.output
    assert (tmp_path / ".wia" / "index.json").exists()

    # 4. Test `wia status`
    res_status = runner.invoke(main, ["status", str(tmp_path)])
    assert res_status.exit_code == 0
    assert "WIA Workspace Status" in res_status.output

    # 5. Test `wia files`
    res_files = runner.invoke(main, ["files", str(tmp_path)])
    assert res_files.exit_code == 0
    assert "app.py" in res_files.output

    # 6. Test `wia info`
    res_info = runner.invoke(main, ["info", str(tmp_path)])
    assert res_info.exit_code == 0
    assert "Language Distribution" in res_info.output

    # 7. Test `wia analyze deps`
    res_deps = runner.invoke(main, ["analyze", "deps", "--workspace", str(tmp_path)])
    assert res_deps.exit_code == 0
    assert "Dependencies Analysis" in res_deps.output

    # 8. Test `wia analyze security`
    res_sec = runner.invoke(main, ["analyze", "security", "--workspace", str(tmp_path)])
    assert res_sec.exit_code == 0
    assert "SEC-001" in res_sec.output

    # 9. Test `wia report`
    res_report = runner.invoke(main, ["report", "--workspace", str(tmp_path)])
    assert res_report.exit_code == 0
    assert (tmp_path / "wia-report.html").exists()

    # 10. Test `wia search`
    res_search = runner.invoke(main, ["search", "main", "--workspace", str(tmp_path)])
    assert res_search.exit_code == 0
    assert "app.py" in res_search.output

    # 11. Test `wia summary`
    res_summary = runner.invoke(main, ["summary", "--workspace", str(tmp_path)])
    assert res_summary.exit_code == 0
    assert "Workspace Intelligence Summary" in res_summary.output
    assert "Repository Facts" in res_summary.output
