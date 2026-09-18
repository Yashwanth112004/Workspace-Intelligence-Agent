"""Unit tests for IndexingService integrated multi-analyzer pipeline."""

import json
from pathlib import Path
from wia.services.indexing_service import IndexingService
from wia.services.init_service import InitService


def test_indexing_service_runs_all_analyzers(tmp_path: Path):
    # Initialize workspace
    init_res = InitService.initialize_workspace(tmp_path)
    assert init_res.success is True

    # Create dummy files: python file with secret, requirement file, package.json
    (tmp_path / "app.py").write_text("aws_key = 'AKIAIOSFODNN7EXAMPLE'", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("requests>=2.28.0\nflask==2.3.0", encoding="utf-8")
    (tmp_path / "package.json").write_text(json.dumps({"dependencies": {"express": "^4.18.0"}}), encoding="utf-8")

    # Execute indexing service
    res = IndexingService.index_workspace(tmp_path)
    assert res.success is True
    data = res.data

    assert "dependencies_count" in data
    assert data["dependencies_count"] >= 3  # requests, flask, express
    assert "security_findings_count" in data
    assert data["security_findings_count"] >= 1  # AWS key in app.py
    assert "git_hotspots_count" in data
    assert "dependency_conflicts_count" in data
