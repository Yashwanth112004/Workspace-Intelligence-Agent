"""Unit tests for HTML ReportGenerator."""

from pathlib import Path
from wia.core.index_model import FileRecord, WorkspaceIndex, BatchRecord
from wia.utils.report_generator import ReportGenerator, _safe_json_embed


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
    assert "box-sizing: border-box" in content
    assert "var(--bg)" in content


def test_report_generator_empty_graph(tmp_path: Path):
    index = WorkspaceIndex(
        workspace_path=str(tmp_path),
        files={},
        languages={},
        frameworks=[],
        stats={},
    )
    output_html = tmp_path / "empty-report.html"
    report_file = ReportGenerator.generate_html_report(index, output_path=output_html)
    assert report_file.exists()
    content = report_file.read_text(encoding="utf-8")
    assert "No source files indexed in workspace" in content
    assert "WIA_GRAPH_DATA" in content


def test_report_generator_cyclic_graph(tmp_path: Path):
    # Simulate a cyclic dependency: a.py -> b.py -> a.py
    f1 = FileRecord(
        relative_path="src/module_a.py",
        file_size=100,
        modified_time=1000.0,
        extension=".py",
        language="Python",
        file_type="Source",
        indexing_status="INDEXED",
        extra_metadata={"imports": ["src.module_b"], "symbols": [{"name": "FuncA", "symbol_type": "function", "line_number": 5}]},
    )
    f2 = FileRecord(
        relative_path="src/module_b.py",
        file_size=100,
        modified_time=1000.0,
        extension=".py",
        language="Python",
        file_type="Source",
        indexing_status="INDEXED",
        extra_metadata={"imports": ["src.module_a"], "symbols": [{"name": "FuncB", "symbol_type": "function", "line_number": 5}]},
    )

    index = WorkspaceIndex(
        workspace_path=str(tmp_path),
        files={"src/module_a.py": f1, "src/module_b.py": f2},
        languages={"Python": 2},
        frameworks=[],
        stats={"total_discovered": 2, "total_indexed": 2},
    )

    output_html = tmp_path / "cyclic-report.html"
    report_file = ReportGenerator.generate_html_report(index, output_path=output_html)
    content = report_file.read_text(encoding="utf-8")

    assert report_file.exists()
    assert "module_a.py" in content
    assert "module_b.py" in content
    assert "Cyclic" in content or "Dependency Graph" in content


def test_report_generator_long_paths_and_escaping(tmp_path: Path):
    long_path = "nested/deeply/embedded/subsystems/enterprise/controller/v2/authentication_and_session_management_handler_provider.ts"
    f = FileRecord(
        relative_path=long_path,
        file_size=5000,
        modified_time=1000.0,
        extension=".ts",
        language="TypeScript",
        file_type="Source",
        indexing_status="INDEXED",
        extra_metadata={
            "imports": ["<script>alert('xss')</script>"],
            "symbols": [
                {
                    "name": "AuthManager<T>",
                    "symbol_type": "class",
                    "line_number": 42,
                    "docstring": "Handles session token verification with special characters & < > ' \"",
                }
            ],
        },
    )

    index = WorkspaceIndex(
        workspace_path=str(tmp_path),
        files={long_path: f},
        languages={"TypeScript": 1},
        frameworks=["NestJS"],
        stats={"total_discovered": 1, "total_indexed": 1},
    )

    output_html = tmp_path / "escaping-report.html"
    report_file = ReportGenerator.generate_html_report(index, output_path=output_html)
    content = report_file.read_text(encoding="utf-8")

    assert report_file.exists()
    assert "authentication_and_session_management_handler_provider.ts" in content
    assert "<script>alert('xss')</script>" not in content  # safely escaped in raw HTML
    assert "AuthManager" in content


def test_report_generator_many_nodes(tmp_path: Path):
    files = {}
    for i in range(50):
        p = f"src/services/service_{i}.py"
        files[p] = FileRecord(
            relative_path=p,
            file_size=200,
            modified_time=1000.0,
            extension=".py",
            language="Python",
            file_type="Source",
            indexing_status="INDEXED",
            extra_metadata={
                "imports": [f"src.services.service_{(i+1)%50}"],
                "symbols": [{"name": f"execute_{i}", "symbol_type": "function", "line_number": 10}],
            },
        )

    index = WorkspaceIndex(
        workspace_path=str(tmp_path),
        files=files,
        languages={"Python": 50},
        frameworks=[],
        stats={"total_discovered": 50, "total_indexed": 50},
    )

    output_html = tmp_path / "large-report.html"
    report_file = ReportGenerator.generate_html_report(index, output_path=output_html)
    content = report_file.read_text(encoding="utf-8")

    assert report_file.exists()
    assert "service_0.py" in content
    assert "service_49.py" in content


def test_safe_json_embed():
    payload = {"tag": "</script><script>alert(1)</script>", "comment": "<!-- sensitive -->"}
    embedded = _safe_json_embed(payload)
    assert "</script>" not in embedded
    assert r"<\/script>" in embedded
    assert "<!--" not in embedded


def test_build_graph_payload_ranking_and_metrics(tmp_path: Path):
    """Test deterministic visualization ranking: Target, Direct, Secondary, Core, Peripheral."""
    # Build a graph structure:
    # entrypoint.py (Target) -> service_a.py (Direct) -> db.py (Secondary / High-connectivity)
    # entrypoint.py -> service_b.py (Direct) -> db.py
    # entrypoint.py -> service_c.py (Direct) -> db.py
    # util_isolated.py (Peripheral/Isolated)
    files = {
        "src/entrypoint.py": FileRecord(
            relative_path="src/entrypoint.py",
            file_size=500,
            modified_time=1000.0,
            extension=".py",
            language="Python",
            file_type="Source",
            indexing_status="INDEXED",
            extra_metadata={"imports": ["src.service_a", "src.service_b", "src.service_c"]},
        ),
        "src/service_a.py": FileRecord(
            relative_path="src/service_a.py",
            file_size=300,
            modified_time=1000.0,
            extension=".py",
            language="Python",
            file_type="Source",
            indexing_status="INDEXED",
            extra_metadata={"imports": ["src.db"]},
        ),
        "src/service_b.py": FileRecord(
            relative_path="src/service_b.py",
            file_size=300,
            modified_time=1000.0,
            extension=".py",
            language="Python",
            file_type="Source",
            indexing_status="INDEXED",
            extra_metadata={"imports": ["src.db"]},
        ),
        "src/service_c.py": FileRecord(
            relative_path="src/service_c.py",
            file_size=300,
            modified_time=1000.0,
            extension=".py",
            language="Python",
            file_type="Source",
            indexing_status="INDEXED",
            extra_metadata={"imports": ["src.db"]},
        ),
        "src/db.py": FileRecord(
            relative_path="src/db.py",
            file_size=800,
            modified_time=1000.0,
            extension=".py",
            language="Python",
            file_type="Source",
            indexing_status="INDEXED",
            extra_metadata={"imports": []},
        ),
        "src/util_isolated.py": FileRecord(
            relative_path="src/util_isolated.py",
            file_size=100,
            modified_time=1000.0,
            extension=".py",
            language="Python",
            file_type="Source",
            indexing_status="INDEXED",
            extra_metadata={},
        ),
    }

    index = WorkspaceIndex(
        workspace_path=str(tmp_path),
        files=files,
        languages={"Python": 6},
        frameworks=[],
        stats={"total_discovered": 6, "total_indexed": 6},
    )

    payload = ReportGenerator._build_graph_payload(index)

    assert "nodes" in payload
    assert "edges" in payload
    assert "metrics" in payload

    nodes_by_id = {n["id"]: n for n in payload["nodes"]}
    assert "file:src/entrypoint.py" in nodes_by_id
    assert "file:src/db.py" in nodes_by_id
    assert "file:src/util_isolated.py" in nodes_by_id

    # Check metrics
    metrics = payload["metrics"]
    assert metrics["total_nodes"] == 6
    assert metrics["total_edges"] > 0
    assert metrics["direct_count"] >= 1
    assert metrics["cycle_count"] == 0

    # Entrypoint (main entry) or highest priority entity has rank 0 or 1
    entry_node = nodes_by_id["file:src/entrypoint.py"]
    assert entry_node["vis_rank"] in (0, 1)

    # Edge priority checks
    for edge in payload["edges"]:
        assert "edge_priority" in edge
        assert edge["edge_priority"] in (1, 2, 3)


def test_build_graph_payload_large_500_nodes(tmp_path: Path):
    """Test graph builder with 500+ nodes to ensure ranking and stability."""
    files = {}
    for i in range(520):
        p = f"src/pkg/mod_{i}.py"
        imports = []
        if i > 0:
            imports.append(f"src.pkg.mod_{i-1}")
        if i % 10 == 0 and i > 20:
            imports.append("src.pkg.mod_0")
        files[p] = FileRecord(
            relative_path=p,
            file_size=150,
            modified_time=1000.0,
            extension=".py",
            language="Python",
            file_type="Source",
            indexing_status="INDEXED",
            extra_metadata={"imports": imports},
        )

    index = WorkspaceIndex(
        workspace_path=str(tmp_path),
        files=files,
        languages={"Python": 520},
        frameworks=[],
        stats={"total_discovered": 520, "total_indexed": 520},
    )

    payload = ReportGenerator._build_graph_payload(index)
    assert len(payload["nodes"]) == 520
    assert payload["metrics"]["total_nodes"] == 520

    # Ensure peripheral count is captured
    assert payload["metrics"]["peripheral_count"] > 0

    # Generate HTML and verify no errors
    output_html = tmp_path / "large-500-report.html"
    report_file = ReportGenerator.generate_html_report(index, output_path=output_html)
    assert report_file.exists()


def test_build_graph_payload_many_cycles_24(tmp_path: Path):
    """Test cycle detection with 24 cyclic dependencies."""
    files = {}
    # Create pairs and triangles of mutual dependencies:
    for i in range(24):
        p_a = f"src/cycles/cycle_{i}_a.py"
        p_b = f"src/cycles/cycle_{i}_b.py"
        files[p_a] = FileRecord(
            relative_path=p_a,
            file_size=200,
            modified_time=1000.0,
            extension=".py",
            language="Python",
            file_type="Source",
            indexing_status="INDEXED",
            extra_metadata={"imports": [f"src.cycles.cycle_{i}_b"]},
        )
        files[p_b] = FileRecord(
            relative_path=p_b,
            file_size=200,
            modified_time=1000.0,
            extension=".py",
            language="Python",
            file_type="Source",
            indexing_status="INDEXED",
            extra_metadata={"imports": [f"src.cycles.cycle_{i}_a"]},
        )

    index = WorkspaceIndex(
        workspace_path=str(tmp_path),
        files=files,
        languages={"Python": 48},
        frameworks=[],
        stats={"total_discovered": 48, "total_indexed": 48},
    )

    payload = ReportGenerator._build_graph_payload(index)
    assert payload["is_dag"] is False
    assert payload["cycle_count"] >= 24
    assert payload["metrics"]["cycle_count"] >= 24

    output_html = tmp_path / "24-cycles-report.html"
    report_file = ReportGenerator.generate_html_report(index, output_path=output_html)
    assert report_file.exists()
    content = report_file.read_text(encoding="utf-8")
    assert "cycles detected" in content


def test_build_graph_payload_missing_metadata(tmp_path: Path):
    """Test robustness against missing or empty metadata."""
    files = {
        "src/none_meta.py": FileRecord(
            relative_path="src/none_meta.py",
            file_size=10,
            modified_time=1000.0,
            extension=".py",
            language="Python",
            file_type="Source",
            indexing_status="INDEXED",
            extra_metadata={},
        )
    }

    index = WorkspaceIndex(
        workspace_path=str(tmp_path),
        files=files,
        languages={"Python": 1},
        frameworks=[],
        stats={"total_discovered": 1, "total_indexed": 1},
    )

    payload = ReportGenerator._build_graph_payload(index)
    assert len(payload["nodes"]) == 1
    output_html = tmp_path / "missing-meta-report.html"
    report_file = ReportGenerator.generate_html_report(index, output_path=output_html)
    assert report_file.exists()


