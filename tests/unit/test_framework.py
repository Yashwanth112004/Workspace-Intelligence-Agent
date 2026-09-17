"""Unit tests for FrameworkDetector core engine."""

import json
from pathlib import Path
from wia.core.framework import FrameworkDetector


def test_detect_js_frameworks(tmp_path: Path):
    """Verify JS/TS framework detection via package.json."""
    pkg = {
        "name": "my-app",
        "dependencies": {
            "react": "^18.0.0",
            "next": "^14.0.0",
        },
    }
    (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")

    detected = FrameworkDetector.detect_frameworks(tmp_path)
    names = [f.name for f in detected]

    assert "Node.js" in names
    assert "Next.js" in names
    assert "React" in names


def test_detect_python_frameworks(tmp_path: Path):
    """Verify Python framework detection via pyproject.toml."""
    pyproject = """
    [project]
    dependencies = [
        "fastapi>=0.100.0",
        "pytest>=7.0.0",
    ]
    """
    (tmp_path / "pyproject.toml").write_text(pyproject, encoding="utf-8")

    detected = FrameworkDetector.detect_frameworks(tmp_path)
    names = [f.name for f in detected]

    assert "FastAPI" in names
    assert "pytest" in names


def test_detect_docker_tooling(tmp_path: Path):
    """Verify Docker tool detection via Dockerfile presence."""
    (tmp_path / "Dockerfile").write_text("FROM python:3.11", encoding="utf-8")

    detected = FrameworkDetector.detect_frameworks(tmp_path)
    names = [f.name for f in detected]

    assert "Docker" in names
