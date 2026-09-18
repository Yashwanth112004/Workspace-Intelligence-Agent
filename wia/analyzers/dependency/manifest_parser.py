"""Manifest parser for multi-ecosystem package dependencies."""

import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None


@dataclass
class DependencyItem:
    """Represents a package dependency entry extracted from a manifest file."""

    name: str
    version_spec: str
    ecosystem: str  # "python", "npm", "cargo", "go"
    manifest_path: str
    dependency_type: str = "runtime"  # "runtime", "optional", "dev", "build"

    def to_dict(self) -> dict:
        """Convert DependencyItem to serializable dictionary."""
        return asdict(self)


class ManifestParser:
    """Parses project manifests for dependencies across Python, Node, Cargo, and Go."""

    @classmethod
    def _parse_requirement_spec(cls, spec_str: str) -> tuple[str, str]:
        """Extract normalized package name and version constraint from a dependency spec string."""
        clean_str = spec_str.split(";")[0].strip()  # Strip environment markers
        pattern = re.compile(r"^\s*([A-Za-z0-9_\-\.]+)\s*([<>=!~^].*)?")
        match = pattern.match(clean_str)
        if match:
            pkg_name = match.group(1).lower()
            ver_spec = match.group(2).strip() if match.group(2) else "*"
            return pkg_name, ver_spec
        return clean_str.lower(), "*"

    @classmethod
    def parse_pyproject_toml(
        cls, content: str, manifest_path: str = "pyproject.toml"
    ) -> list[DependencyItem]:
        """Parse Python `pyproject.toml` file (PEP 621, Poetry, or build-system)."""
        items: list[DependencyItem] = []
        if not tomllib:
            # Simple fallback regex parser for dependencies if tomllib unavailable
            for line in content.splitlines():
                if "=" in line or ":" in line:
                    continue
                line_str = line.strip().strip('"').strip("'").strip(",")
                if line_str and not line_str.startswith("[") and not line_str.startswith("#"):
                    name, ver = cls._parse_requirement_spec(line_str)
                    if name:
                        items.append(
                            DependencyItem(
                                name=name,
                                version_spec=ver,
                                ecosystem="python",
                                manifest_path=manifest_path,
                                dependency_type="runtime",
                            )
                        )
            return items

        try:
            data = tomllib.loads(content)
        except Exception:
            return items

        # 1. Standard PEP 621 dependencies
        project_table = data.get("project", {})
        if isinstance(project_table, dict):
            # Runtime dependencies list
            raw_deps = project_table.get("dependencies", [])
            if isinstance(raw_deps, list):
                for req in raw_deps:
                    if isinstance(req, str):
                        name, ver = cls._parse_requirement_spec(req)
                        if name:
                            items.append(
                                DependencyItem(
                                    name=name,
                                    version_spec=ver,
                                    ecosystem="python",
                                    manifest_path=manifest_path,
                                    dependency_type="runtime",
                                )
                            )

            # Optional / Dev dependencies table
            opt_deps = project_table.get("optional-dependencies", {})
            if isinstance(opt_deps, dict):
                for group_name, group_reqs in opt_deps.items():
                    if isinstance(group_reqs, list):
                        for req in group_reqs:
                            if isinstance(req, str):
                                name, ver = cls._parse_requirement_spec(req)
                                if name:
                                    items.append(
                                        DependencyItem(
                                            name=name,
                                            version_spec=ver,
                                            ecosystem="python",
                                            manifest_path=manifest_path,
                                            dependency_type=f"optional ({group_name})",
                                        )
                                    )

        # 2. Poetry dependencies table
        poetry_table = data.get("tool", {}).get("poetry", {})
        if isinstance(poetry_table, dict):
            p_deps = poetry_table.get("dependencies", {})
            if isinstance(p_deps, dict):
                for pkg, spec in p_deps.items():
                    if pkg.lower() != "python":
                        ver = str(spec) if isinstance(spec, (str, int, float)) else "*"
                        items.append(
                            DependencyItem(
                                name=pkg.lower(),
                                version_spec=ver,
                                ecosystem="python",
                                manifest_path=manifest_path,
                                dependency_type="runtime",
                            )
                        )

        # 3. Build-system requires
        build_requires = data.get("build-system", {}).get("requires", [])
        if isinstance(build_requires, list):
            for req in build_requires:
                if isinstance(req, str):
                    name, ver = cls._parse_requirement_spec(req)
                    if name:
                        items.append(
                            DependencyItem(
                                name=name,
                                version_spec=ver,
                                ecosystem="python",
                                manifest_path=manifest_path,
                                dependency_type="build",
                            )
                        )

        # Deduplicate identical items
        seen = set()
        deduped: list[DependencyItem] = []
        for item in items:
            key = (item.name, item.version_spec, item.manifest_path, item.dependency_type)
            if key not in seen:
                seen.add(key)
                deduped.append(item)

        return deduped

    @classmethod
    def parse_requirements_txt(
        cls, content: str, manifest_path: str = "requirements.txt"
    ) -> list[DependencyItem]:
        """Parse Python `requirements.txt` file."""
        items: list[DependencyItem] = []
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue

            pkg_name, ver_spec = cls._parse_requirement_spec(line)
            if pkg_name:
                items.append(
                    DependencyItem(
                        name=pkg_name,
                        version_spec=ver_spec,
                        ecosystem="python",
                        manifest_path=manifest_path,
                        dependency_type="runtime",
                    )
                )
        return items

    @classmethod
    def parse_package_json(
        cls, content: str, manifest_path: str = "package.json"
    ) -> list[DependencyItem]:
        """Parse Node.js `package.json` file."""
        items: list[DependencyItem] = []
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return items

        for key, dep_type in (
            ("dependencies", "runtime"),
            ("devDependencies", "dev"),
            ("peerDependencies", "peer"),
        ):
            deps = data.get(key, {})
            if isinstance(deps, dict):
                for pkg_name, ver_spec in deps.items():
                    items.append(
                        DependencyItem(
                            name=pkg_name.lower(),
                            version_spec=str(ver_spec),
                            ecosystem="npm",
                            manifest_path=manifest_path,
                            dependency_type=dep_type,
                        )
                    )
        return items

    @classmethod
    def parse_workspace_manifests(cls, workspace_path: str | Path) -> list[DependencyItem]:
        """Discover and parse all project manifest files in workspace."""
        path = Path(workspace_path)
        items: list[DependencyItem] = []
        ignored_parts = {".wia", ".git", "node_modules", "venv", ".venv", ".pytest_cache", "__pycache__", "build", "dist"}

        # 1. Look for pyproject.toml
        for pyproj_file in path.rglob("pyproject.toml"):
            if any(part in ignored_parts or part.endswith(".egg-info") or part.endswith(".dist-info") for part in pyproj_file.parts):
                continue
            try:
                content = pyproj_file.read_text(encoding="utf-8", errors="ignore")
                rel_p = str(pyproj_file.relative_to(path)).replace("\\", "/")
                items.extend(cls.parse_pyproject_toml(content, manifest_path=rel_p))
            except Exception:
                pass

        # 2. Look for requirements.txt
        for req_file in path.rglob("requirements*.txt"):
            if any(part in ignored_parts or part.endswith(".egg-info") or part.endswith(".dist-info") for part in req_file.parts):
                continue
            try:
                content = req_file.read_text(encoding="utf-8", errors="ignore")
                rel_p = str(req_file.relative_to(path)).replace("\\", "/")
                items.extend(cls.parse_requirements_txt(content, manifest_path=rel_p))
            except Exception:
                pass

        # 3. Look for package.json
        for pkg_file in path.rglob("package.json"):
            if any(part in ignored_parts for part in pkg_file.parts):
                continue
            try:
                content = pkg_file.read_text(encoding="utf-8", errors="ignore")
                rel_p = str(pkg_file.relative_to(path)).replace("\\", "/")
                items.extend(cls.parse_package_json(content, manifest_path=rel_p))
            except Exception:
                pass

        return items
