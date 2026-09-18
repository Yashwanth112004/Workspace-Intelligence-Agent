"""Unit tests for HTML ReportGenerator."""

from pathlib import Path
from wia.core.index_model import WorkspaceIndex
from wia.utils.report_generator import ReportGenerator


def test_report_generator_output(tmp_path: Path):
    index = WorkspaceIndex(
        workspace_path=str(tmp_path),
        files={},
        languages={"Python": 10, "JavaScript": 5},
        frameworks=["Django", "React"],
        stats={
            "total_discovered": 15,
            "total_indexed": 15,
            "total_ignored": 0,
            "dependencies_count": 8,
            "dependency_conflicts_count": 1,
            "git_hotspots_count": 2,
            "security_findings_count": 0,
        },
    )

    output_html = tmp_path / "custom-report.html"
    report_file = ReportGenerator.generate_html_report(index, output_path=output_html)

    assert report_file.exists()
    content = report_file.read_text(encoding="utf-8")

    assert "WIA Workspace Intelligence Report" in content
    assert "Django" in content
    assert "React" in content
    assert "Python" in content
    assert "JavaScript" in content
