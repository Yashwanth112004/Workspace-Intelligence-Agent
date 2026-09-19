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
    """Scans repository manifests, workflows, and config files to detect tech stacks."""

    @classmethod
    def detect_frameworks(cls, workspace_path: str | Path) -> list[FrameworkEvidence]:
        """Detect frameworks, libraries, build tools, testing suites, and DevOps configurations."""
        root = Path(workspace_path).resolve()
        evidence_list: list[FrameworkEvidence] = []

        if not root.exists() or not root.is_dir():
            return evidence_list

        # 1. CI / CD Workflows
        gh_workflows = root / ".github" / "workflows"
        if gh_workflows.exists() and any(gh_workflows.glob("*.yml")) or any(gh_workflows.glob("*.yaml")):
            evidence_list.append(
                FrameworkEvidence(name="GitHub Actions", category="CI/CD", evidence_source=".github/workflows")
            )
        if (root / ".gitlab-ci.yml").exists():
            evidence_list.append(
                FrameworkEvidence(name="GitLab CI", category="CI/CD", evidence_source=".gitlab-ci.yml")
            )
        if (root / "Jenkinsfile").exists():
            evidence_list.append(
                FrameworkEvidence(name="Jenkins", category="CI/CD", evidence_source="Jenkinsfile")
            )

        # 2. Node.js & JavaScript/TypeScript Ecosystem
        package_json = root / "package.json"
        if package_json.exists() and package_json.is_file():
            cls._inspect_package_json(package_json, evidence_list)

        # 3. Python Ecosystem
        pyproject_toml = root / "pyproject.toml"
        if pyproject_toml.exists() and pyproject_toml.is_file():
            cls._inspect_pyproject_toml(pyproject_toml, evidence_list)

        requirements_txt = root / "requirements.txt"
        if requirements_txt.exists() and requirements_txt.is_file():
            cls._inspect_requirements_txt(requirements_txt, evidence_list)

        # 4. Rust Ecosystem
        cargo_toml = root / "Cargo.toml"
        if cargo_toml.exists() and cargo_toml.is_file():
            evidence_list.append(
                FrameworkEvidence(name="Cargo", category="Build Tools", evidence_source="Cargo.toml")
            )

        # 5. Docker & Infrastructure
        if (root / "Dockerfile").exists() or list(root.glob("Dockerfile.*")):
            evidence_list.append(
                FrameworkEvidence(
                    name="Docker",
                    category="Containerization",
                    evidence_source="Dockerfile",
                )
            )
        if (root / "docker-compose.yml").exists() or (root / "docker-compose.yaml").exists():
            evidence_list.append(
                FrameworkEvidence(
                    name="Docker Compose",
                    category="Containerization",
                    evidence_source="docker-compose.yml",
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

        return sorted(unique_map.values(), key=lambda e: (e.category, e.name))

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
                    category="Package Managers",
                    evidence_source="package.json",
                )
            )

            framework_map = {
                "next": ("Next.js", "Frontend Frameworks"),
                "react": ("React", "Frontend Frameworks"),
                "vue": ("Vue.js", "Frontend Frameworks"),
                "nuxt": ("Nuxt", "Frontend Frameworks"),
                "svelte": ("Svelte", "Frontend Frameworks"),
                "@angular/core": ("Angular", "Frontend Frameworks"),
                "express": ("Express", "Frameworks"),
                "nestjs": ("NestJS", "Frameworks"),
                "tailwindcss": ("Tailwind CSS", "Libraries"),
                "jest": ("Jest", "Testing Tools"),
                "vitest": ("Vitest", "Testing Tools"),
                "playwright": ("Playwright", "Testing Tools"),
                "cypress": ("Cypress", "Testing Tools"),
                "typescript": ("TypeScript", "Build Tools"),
                "vite": ("Vite", "Build Tools"),
                "webpack": ("Webpack", "Build Tools"),
            }

            for dep_name, (fw_name, category) in framework_map.items():
                if dep_name in deps:
                    evidence_list.append(
                        FrameworkEvidence(name=fw_name, category=category, evidence_source=f"package.json dependency: '{dep_name}'")
                    )
        except Exception:
            pass

    @staticmethod
    def _inspect_pyproject_toml(
        pyproject_path: Path, evidence_list: list[FrameworkEvidence]
    ) -> None:
        """Inspect pyproject.toml for Python frameworks and build tools."""
        try:
            content = pyproject_path.read_text(encoding="utf-8").lower()
            checks = {
                "hatchling": ("Hatch", "Build Tools"),
                "poetry": ("Poetry", "Build Tools"),
                "flit": ("Flit", "Build Tools"),
                "setuptools": ("Setuptools", "Build Tools"),
                "fastapi": ("FastAPI", "Frameworks"),
                "django": ("Django", "Frameworks"),
                "flask": ("Flask", "Frameworks"),
                "starlette": ("Starlette", "Frameworks"),
                "pytest": ("pytest", "Testing Tools"),
                "tree-sitter": ("Tree-sitter", "Libraries"),
                "torch": ("PyTorch", "Libraries"),
                "tensorflow": ("TensorFlow", "Libraries"),
                "scikit-learn": ("Scikit-learn", "Libraries"),
                "pandas": ("Pandas", "Libraries"),
                "numpy": ("NumPy", "Libraries"),
                "openai": ("OpenAI SDK", "Libraries"),
            }
            for key, (fw_name, category) in checks.items():
                if key in content:
                    evidence_list.append(
                        FrameworkEvidence(name=fw_name, category=category, evidence_source=f"pyproject.toml: '{key}'")
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
            checks = {
                "fastapi": ("FastAPI", "Frameworks"),
                "django": ("Django", "Frameworks"),
                "flask": ("Flask", "Frameworks"),
                "pytest": ("pytest", "Testing Tools"),
                "torch": ("PyTorch", "Libraries"),
                "tensorflow": ("TensorFlow", "Libraries"),
                "pandas": ("Pandas", "Libraries"),
                "numpy": ("NumPy", "Libraries"),
            }
            for key, (fw_name, category) in checks.items():
                if key in content:
                    evidence_list.append(
                        FrameworkEvidence(name=fw_name, category=category, evidence_source=f"requirements.txt: '{key}'")
                    )
        except Exception:
            pass
