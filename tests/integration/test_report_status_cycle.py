"""Integration tests for WIA report generation and status immutability."""

from pathlib import Path
from click.testing import CliRunner
from wia.cli.app import main
from wia.services.indexing_service import IndexingService
from wia.services.init_service import InitService
from wia.services.status_service import StatusService


def test_report_does_not_mutate_workspace_status(tmp_path: Path):
    """Verify generating wia-report.html does not trigger pending changes in wia status."""
    InitService.initialize_workspace(tmp_path)
    (tmp_path / "app.py").write_text("def main(): pass", encoding="utf-8")
    IndexingService.index_workspace(tmp_path)

    runner = CliRunner()

    # 1. Initial status check -> Up to Date
    res_status1 = runner.invoke(main, ["status", str(tmp_path)])
    assert res_status1.exit_code == 0
    assert "Up to Date" in res_status1.output

    # 2. Run wia report to generate wia-report.html
    res_report = runner.invoke(main, ["report", "--workspace", str(tmp_path)])
    assert res_report.exit_code == 0
    assert (tmp_path / "wia-report.html").exists()

    # 3. Status check must remain Up to Date and NOT report modified/added files
    res_status2 = runner.invoke(main, ["status", str(tmp_path)])
    assert res_status2.exit_code == 0
    assert "Up to Date" in res_status2.output
    assert "Modified: 0" in res_status2.output
    assert "Added: 0" in res_status2.output

    # 4. Files command must NOT list wia-report.html
    res_files = runner.invoke(main, ["files", str(tmp_path)])
    assert res_files.exit_code == 0
    assert "wia-report.html" not in res_files.output
