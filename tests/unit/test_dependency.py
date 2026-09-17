"""Unit tests for Dependency Manifest Parser and Conflict Detector."""

import json
from pathlib import Path
from wia.analyzers.dependency.manifest_parser import DependencyItem, ManifestParser
from wia.analyzers.dependency.conflict_detector import DependencyConflict, ConflictDetector


def test_dependency_item_to_dict():
    item = DependencyItem(
        name="requests",
        version_spec=">=2.25.0",
        ecosystem="python",
        manifest_path="requirements.txt",
        dependency_type="runtime",
    )
    data = item.to_dict()
    assert data == {
        "name": "requests",
        "version_spec": ">=2.25.0",
        "ecosystem": "python",
        "manifest_path": "requirements.txt",
        "dependency_type": "runtime",
    }


def test_parse_requirements_txt():
    content = """
    # Comment line
    requests>=2.28.0
    flask==2.3.0
    pytest
    -e .
    """
    items = ManifestParser.parse_requirements_txt(content, "requirements.txt")
    assert len(items) == 3

    assert items[0].name == "requests"
    assert items[0].version_spec == ">=2.28.0"
    assert items[0].ecosystem == "python"

    assert items[1].name == "flask"
    assert items[1].version_spec == "==2.3.0"

    assert items[2].name == "pytest"
    assert items[2].version_spec == "*"


def test_parse_pyproject_toml():
    content = """
[project]
name = "Workspace-Intelligence-Agent"
version = "0.1.0"
dependencies = [
    "click>=8.0.0",
    "pytest>=7.0.0; python_version >= '3.8'",
]

[project.optional-dependencies]
dev = [
    "black>=23.0.0",
]
"""
    items = ManifestParser.parse_pyproject_toml(content, "pyproject.toml")
    assert len(items) == 3

    names = {item.name for item in items}
    assert "click" in names
    assert "pytest" in names
    assert "black" in names

    click_item = next(i for i in items if i.name == "click")
    assert click_item.version_spec == ">=8.0.0"
    assert click_item.dependency_type == "runtime"

    black_item = next(i for i in items if i.name == "black")
    assert black_item.dependency_type == "optional (dev)"


def test_parse_package_json():
    content = json.dumps({
        "name": "my-app",
        "dependencies": {
            "react": "^18.2.0",
            "lodash": "4.17.21"
        },
        "devDependencies": {
            "typescript": "^5.0.0"
        }
    })
    items = ManifestParser.parse_package_json(content, "package.json")
    assert len(items) == 3
    names = {item.name for item in items}
    assert names == {"react", "lodash", "typescript"}

    react_item = next(item for item in items if item.name == "react")
    assert react_item.version_spec == "^18.2.0"
    assert react_item.ecosystem == "npm"


def test_parse_workspace_manifests(tmp_path: Path):
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("numpy>=1.20.0\nscipy==1.7.0", encoding="utf-8")

    pkg_file = tmp_path / "package.json"
    pkg_file.write_text(json.dumps({"dependencies": {"express": "^4.18.0"}}), encoding="utf-8")

    pyproj_file = tmp_path / "pyproject.toml"
    pyproj_file.write_text('[project]\ndependencies = ["click>=8.0"]', encoding="utf-8")

    ignored_dir = tmp_path / "node_modules" / "subpackage"
    ignored_dir.mkdir(parents=True)
    (ignored_dir / "package.json").write_text(json.dumps({"dependencies": {"bad": "1.0"}}), encoding="utf-8")

    items = ManifestParser.parse_workspace_manifests(tmp_path)
    assert len(items) == 4
    names = {item.name for item in items}
    assert "numpy" in names
    assert "scipy" in names
    assert "express" in names
    assert "click" in names
    assert "bad" not in names


def test_conflict_detector_version_mismatch():
    items = [
        DependencyItem("requests", ">=2.25.0", "python", "requirements.txt"),
        DependencyItem("requests", "==2.30.0", "python", "services/requirements.txt"),
    ]
    conflicts = ConflictDetector.detect_conflicts(items)
    assert len(conflicts) == 1
    assert conflicts[0].package_name == "requests"
    assert conflicts[0].conflict_type == "version_mismatch"
    assert "requirements.txt" in conflicts[0].affected_manifests
    assert "services/requirements.txt" in conflicts[0].affected_manifests


def test_conflict_detector_duplicate_entry():
    items = [
        DependencyItem("express", "^4.18.0", "npm", "package.json"),
        DependencyItem("express", "^4.18.0", "npm", "api/package.json"),
    ]
    conflicts = ConflictDetector.detect_conflicts(items)
    assert len(conflicts) == 1
    assert conflicts[0].package_name == "express"
    assert conflicts[0].conflict_type == "duplicate_entry"


def test_conflict_detector_no_conflicts():
    items = [
        DependencyItem("requests", ">=2.25.0", "python", "requirements.txt"),
        DependencyItem("express", "^4.18.0", "npm", "package.json"),
    ]
    conflicts = ConflictDetector.detect_conflicts(items)
    assert len(conflicts) == 0
