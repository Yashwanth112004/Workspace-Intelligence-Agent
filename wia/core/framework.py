"""Framework and software development tool detector engine."""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FrameworkEvidence:
    """Represents detected framework or development tool with evidence source."""

    name: str
    category: str
    evidence_source: str


class FrameworkDetector:
    """Scans repository manifests and config files to detect frameworks and tools."""

    @classmethod
    def detect_frameworks(cls, workspace_path: str | Path) -> list[FrameworkEvidence]:
        """Detect frameworks and development tools present in workspace."""
        root = Path(workspace_path).resolve()
        evidence_list: list[FrameworkEvidence] = []

        if not root.exists() or not root.is_dir():
            return evidence_list

        # 1. Node.js & JavaScript/TypeScript Ecosystem (package.json)
        package_json = root / "package.json"
        if package_json.exists() and package_json.is_file():
            cls._inspect_package_json(package_json, evidence_list)

        # 2. Python Ecosystem (pyproject.toml & requirements.txt)
        pyproject_toml = root / "pyproject.toml"
        if pyproject_toml.exists() and pyproject_toml.is_file():
            cls._inspect_pyproject_toml(pyproject_toml, evidence_list)

        requirements_txt = root / "requirements.txt"
        if requirements_txt.exists() and requirements_txt.is_file():
            cls._inspect_requirements_txt(requirements_txt, evidence_list)

        # 3. Docker & Infrastructure (Dockerfile, docker-compose.yml, *.tf)
        if (root / "Dockerfile").exists() or (root / "docker-compose.yml").exists() or (root / "docker-compose.yaml").exists():
            evidence_list.append(
                FrameworkEvidence(
                    name="Docker",
                    category="Containerization / DevOps",
                    evidence_source="Dockerfile or docker-compose file",
                )
            )

        if list(root.glob("*.tf")):
            evidence_list.append(
                FrameworkEvidence(
                    name="Terraform",
                    category="Infrastructure as Code",
                    evidence_source="*.tf configuration files",
                )
            )

        # Deduplicate results by framework name
        unique_map: dict[str, FrameworkEvidence] = {}
        for ev in evidence_list:
            if ev.name not in unique_map:
                unique_map[ev.name] = ev

        return sorted(unique_map.values(), key=lambda e: e.name)

    @staticmethod
    def _inspect_package_json(
        package_json_path: Path, evidence_list: list[FrameworkEvidence]
    ) -> None:
        """Inspect package.json dependencies for JS/TS frameworks."""
        try:
            with open(package_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            deps = {}
            deps.update(data.get("dependencies", {}))
            deps.update(data.get("devDependencies", {}))

            evidence_list.append(
                FrameworkEvidence(
                    name="Node.js",
                    category="Runtime",
                    evidence_source="package.json",
                )
            )

            if "next" in deps:
                evidence_list.append(
                    FrameworkEvidence(name="Next.js", category="Full-stack Web Framework", evidence_source="package.json dependency: 'next'")
                )
            if "react" in deps:
                evidence_list.append(
                    FrameworkEvidence(name="React", category="Frontend UI Framework", evidence_source="package.json dependency: 'react'")
                )
            if "vue" in deps:
                evidence_list.append(
                    FrameworkEvidence(name="Vue.js", category="Frontend UI Framework", evidence_source="package.json dependency: 'vue'")
                )
            if "@angular/core" in deps:
                evidence_list.append(
                    FrameworkEvidence(name="Angular", category="Frontend Web Framework", evidence_source="package.json dependency: '@angular/core'")
                )
            if "express" in deps:
                evidence_list.append(
                    FrameworkEvidence(name="Express", category="Backend Web Framework", evidence_source="package.json dependency: 'express'")
                )
        except Exception:
            pass

    @staticmethod
    def _inspect_pyproject_toml(
        pyproject_path: Path, evidence_list: list[FrameworkEvidence]
    ) -> None:
        """Inspect pyproject.toml for Python web frameworks."""
        try:
            content = pyproject_path.read_text(encoding="utf-8").lower()
            if "fastapi" in content:
                evidence_list.append(
                    FrameworkEvidence(name="FastAPI", category="Backend Web Framework", evidence_source="pyproject.toml dependency: 'fastapi'")
                )
            if "django" in content:
                evidence_list.append(
                    FrameworkEvidence(name="Django", category="Backend Web Framework", evidence_source="pyproject.toml dependency: 'django'")
                )
            if "flask" in content:
                evidence_list.append(
                    FrameworkEvidence(name="Flask", category="Backend Web Framework", evidence_source="pyproject.toml dependency: 'flask'")
                )
            if "pytest" in content:
                evidence_list.append(
                    FrameworkEvidence(name="pytest", category="Testing Framework", evidence_source="pyproject.toml dependency: 'pytest'")
                )
        except Exception:
            pass

    @staticmethod
    def _inspect_requirements_txt(
        req_path: Path, evidence_list: list[FrameworkEvidence]
    ) -> None:
        """Inspect requirements.txt for Python frameworks."""
        try:
            content = req_path.read_text(encoding="utf-8").lower()
            if "fastapi" in content:
                evidence_list.append(
                    FrameworkEvidence(name="FastAPI", category="Backend Web Framework", evidence_source="requirements.txt")
                )
            if "django" in content:
                evidence_list.append(
                    FrameworkEvidence(name="Django", category="Backend Web Framework", evidence_source="requirements.txt")
                )
            if "flask" in content:
                evidence_list.append(
                    FrameworkEvidence(name="Flask", category="Backend Web Framework", evidence_source="requirements.txt")
                )
        except Exception:
            pass
