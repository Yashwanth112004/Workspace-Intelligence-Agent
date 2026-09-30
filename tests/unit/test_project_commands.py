"""Unit tests for ProjectCommandDetector and `wia commands` CLI command."""

from pathlib import Path
from click.testing import CliRunner
from wia.cli.app import main
from wia.core.index_model import WorkspaceIndex
from wia.core.project_commands import ProjectCommandDetector


def test_project_command_detector_python(tmp_path: Path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname = 'demo'", encoding="utf-8")
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()

    index = WorkspaceIndex(
        workspace_path=str(tmp_path),
        files={},
        languages={"Python": 1},
        frameworks=["FastAPI"],
        stats={},
    )

    cmds = ProjectCommandDetector.detect_commands(tmp_path, index=index)
    assert len(cmds) > 0
    cmd_strings = [c["command"] for c in cmds]
    assert any("pip install" in c for c in cmd_strings)
    assert any("pytest" in c for c in cmd_strings)


def test_project_command_detector_node(tmp_path: Path):
    pkg_json = tmp_path / "package.json"
    pkg_json.write_text('{"name": "frontend", "scripts": {"dev": "vite", "build": "vite build", "test": "vitest"}}', encoding="utf-8")

    cmds = ProjectCommandDetector.detect_commands(tmp_path)
    assert len(cmds) >= 3
    cmd_strings = [c["command"] for c in cmds]
    assert any("npm install" in c for c in cmd_strings)
    assert any("npm run dev" in c for c in cmd_strings)
    assert any("npm run build" in c for c in cmd_strings)
    assert any("npm test" in c for c in cmd_strings)


def test_cli_commands_output(tmp_path: Path):
    runner = CliRunner()
    res = runner.invoke(main, ["commands", "--workspace", str(tmp_path)])
    assert res.exit_code == 0
    assert "Runnable Project Commands" in res.output

    res_json = runner.invoke(main, ["commands", "--workspace", str(tmp_path), "--json"])
    assert res_json.exit_code == 0
    assert "[" in res_json.output
