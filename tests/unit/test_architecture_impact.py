"""Unit tests for ArchitectureAnalyzer and ImpactAnalyzer."""

from pathlib import Path
from wia.core.architecture import ArchitectureAnalyzer
from wia.core.impact import ImpactAnalyzer
from wia.core.index_model import WorkspaceIndex
from wia.core.metadata import FileRecord, IndexingStatus
from wia.knowledge.graph import WorkspaceGraph


def test_architecture_analyzer():
    index = WorkspaceIndex(
        workspace_path="/app",
        files={
            "wia/cli/app.py": FileRecord("wia/cli/app.py", 100, 1.0, ".py", language="Python", indexing_status=IndexingStatus.INDEXED),
            "wia/services/service.py": FileRecord("wia/services/service.py", 100, 1.0, ".py", language="Python", indexing_status=IndexingStatus.INDEXED),
        },
        languages={"Python": 2},
        frameworks=["pytest"],
    )

    overview = ArchitectureAnalyzer.analyze_workspace(index)
    assert overview.total_files == 2
    assert "pytest" in overview.frameworks
    assert overview.summary is not None
    assert len(overview.components) > 0


def test_architecture_controlled_repository_relationships():
    """Verify controlled repo (cli -> service -> storage) components and relationship flow."""
    index = WorkspaceIndex(
        workspace_path="/app",
        files={
            "wia/cli/app.py": FileRecord(
                "wia/cli/app.py",
                500,
                1.0,
                ".py",
                language="Python",
                indexing_status=IndexingStatus.INDEXED,
                extra_metadata={"imports": ["wia.services.service"], "symbols": [{"name": "main", "symbol_type": "function"}]},
            ),
            "wia/services/service.py": FileRecord(
                "wia/services/service.py",
                500,
                1.0,
                ".py",
                language="Python",
                indexing_status=IndexingStatus.INDEXED,
                extra_metadata={"imports": ["wia.storage.repository"], "symbols": [{"name": "run", "symbol_type": "function"}]},
            ),
            "wia/storage/repository.py": FileRecord(
                "wia/storage/repository.py",
                500,
                1.0,
                ".py",
                language="Python",
                indexing_status=IndexingStatus.INDEXED,
                extra_metadata={"symbols": [{"name": "load", "symbol_type": "function"}]},
            ),
        },
    )

    graph = WorkspaceGraph()
    graph.build_from_index(index)

    overview = ArchitectureAnalyzer.analyze_workspace(index, graph)
    assert overview.total_files == 3
    assert len(overview.circular_dependencies) == 0

    cli_comp = next(c for c in overview.components if c.path_prefix == "wia/cli")
    assert cli_comp.file_count == 1
    assert "Service & Workflow Orchestration" in cli_comp.internal_dependencies


def test_architecture_cycle_detection():
    """Verify directed cycle detection on workspace IMPORTS edges."""
    index = WorkspaceIndex(
        workspace_path="/app",
        files={
            "mod_a.py": FileRecord("mod_a.py", 100, 1.0, ".py", indexing_status=IndexingStatus.INDEXED, extra_metadata={"imports": ["mod_b"]}),
            "mod_b.py": FileRecord("mod_b.py", 100, 1.0, ".py", indexing_status=IndexingStatus.INDEXED, extra_metadata={"imports": ["mod_a"]}),
        },
    )

    graph = WorkspaceGraph()
    graph.build_from_index(index)

    cycles = ArchitectureAnalyzer._detect_cycles(graph)
    assert len(cycles) >= 1
    assert "mod_a.py" in cycles[0]
    assert "mod_b.py" in cycles[0]


def test_impact_analyzer_symbol_with_callers():
    index = WorkspaceIndex(
        workspace_path="/app",
        files={
            "wia/cli/formatting.py": FileRecord(
                "wia/cli/formatting.py",
                100,
                1.0,
                ".py",
                language="Python",
                indexing_status=IndexingStatus.INDEXED,
                extra_metadata={"symbols": [{"name": "format_bytes", "symbol_type": "function"}]},
            ),
            "wia/cli/commands/status_cmd.py": FileRecord(
                "wia/cli/commands/status_cmd.py",
                100,
                1.0,
                ".py",
                language="Python",
                indexing_status=IndexingStatus.INDEXED,
                extra_metadata={"imports": ["wia.cli.formatting.format_bytes"]},
            ),
        },
    )

    graph = WorkspaceGraph()
    graph.build_from_index(index)

    report = ImpactAnalyzer.analyze_symbol_impact("format_bytes", index, graph)
    assert report.found is True
    assert report.target_symbol == "format_bytes"
    assert report.defining_file == "wia/cli/formatting.py"
    assert len(report.affected_files) == 1
    assert "wia/cli/commands/status_cmd.py" in report.affected_files


def test_impact_analyzer_file_target():
    index = WorkspaceIndex(
        workspace_path="/app",
        files={
            "formatting.py": FileRecord("formatting.py", 100, 1.0, ".py", language="Python", indexing_status=IndexingStatus.INDEXED),
            "app.py": FileRecord("app.py", 100, 1.0, ".py", language="Python", indexing_status=IndexingStatus.INDEXED, extra_metadata={"imports": ["formatting"]}),
        },
    )

    graph = WorkspaceGraph()
    graph.build_from_index(index)

    report = ImpactAnalyzer.analyze_symbol_impact("formatting.py", index, graph)
    assert report.found is True
    assert report.target_type == "file"
    assert report.defining_file == "formatting.py"
    assert "app.py" in report.affected_files


def test_impact_analyzer_unknown_symbol():
    index = WorkspaceIndex(workspace_path="/app", files={})
    report = ImpactAnalyzer.analyze_symbol_impact("NonExistentSymbol", index)
    assert report.found is False
    assert report.risk_level == "NOT_FOUND"
    assert "was not found" in report.explanation

def test_architecture_entry_points_from_pyproject(tmp_path):
    """Verify console scripts are extracted from pyproject.toml."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project.scripts]
wia = "wia.cli.app:main"
""",
        encoding="utf-8",
    )

    index = WorkspaceIndex(
        workspace_path=str(tmp_path),
        files={
            "pyproject.toml": FileRecord(
                "pyproject.toml",
                100,
                1.0,
                ".toml",
                indexing_status=IndexingStatus.INDEXED,
            )
        },
    )

    result = ArchitectureAnalyzer._detect_entry_points(index)

    assert "`wia` -> `wia.cli.app:main`" in result


def test_architecture_entry_points_fallback():
    """Verify the default CLI entry point is returned when no source entry point exists."""
    index = WorkspaceIndex(
        workspace_path="/app",
        files={},
    )

def test_architecture_entry_points_from_cli_source():
    """Verify CLI source entry points are detected as a fallback."""
    index = WorkspaceIndex(
        workspace_path="/app",
        files={
            "wia/cli/app.py": FileRecord(
                "wia/cli/app.py",
                100,
                1.0,
                ".py",
                indexing_status=IndexingStatus.INDEXED,
            )
        },
    )
    result = ArchitectureAnalyzer._detect_entry_points(index)
    assert result == ["`wia` CLI -> `wia/cli/app.py`"]
