"""Project runnable command detector for software workspaces."""

import json
from pathlib import Path
from wia.core.index_model import WorkspaceIndex


class ProjectCommandDetector:
    """Detect runnable developer commands (install, run, dev, test, build, lint, docker, make) from workspace manifests."""

    @classmethod
    def detect_commands(
        cls,
        ws_path: Path,
        index: WorkspaceIndex | None = None,
        files_data: list[dict] | None = None,
    ) -> list[dict]:
        """Inspect manifests, scripts, entrypoints, and configurations to extract runnable project commands."""
        ws_path = Path(ws_path).resolve()
        cmds: list[dict] = []
        seen_cmds: set[str] = set()
        frameworks = index.frameworks if index else []
        files = files_data or []

        def add_cmd(category: str, desc: str, cmd: str, source: str = ""):
            if cmd and cmd not in seen_cmds:
                seen_cmds.add(cmd)
                cmds.append({
                    "category": category,
                    "desc": desc,
                    "command": cmd,
                    "source": source,
                })

        # 1. Node / TypeScript / JavaScript ecosystem
        pkg_candidates = [
            ws_path / "package.json",
            ws_path / "vscode-extension" / "package.json",
            ws_path / "frontend" / "package.json",
            ws_path / "client" / "package.json",
            ws_path / "web" / "package.json",
            ws_path / "ui" / "package.json",
            ws_path / "server" / "package.json",
        ]
        for pkg_candidate in pkg_candidates:
            if pkg_candidate.exists():
                try:
                    pkg_data = json.loads(pkg_candidate.read_text(encoding="utf-8", errors="ignore"))
                    rel_dir = pkg_candidate.parent.relative_to(ws_path)
                    prefix = f"cd {rel_dir} && " if str(rel_dir) != "." else ""
                    pkg_name = pkg_data.get("name") or (str(rel_dir) if str(rel_dir) != "." else ws_path.name)
                    pm = (
                        "pnpm" if (pkg_candidate.parent / "pnpm-lock.yaml").exists()
                        else "yarn" if (pkg_candidate.parent / "yarn.lock").exists()
                        else "bun" if (pkg_candidate.parent / "bun.lockb").exists() or (pkg_candidate.parent / "bun.lock").exists()
                        else "npm"
                    )

                    scripts = pkg_data.get("scripts", {})
                    add_cmd("Installation & Setup", f"Install {pkg_name} dependencies ({pm}):", f"{prefix}{pm} install", str(pkg_candidate.relative_to(ws_path)))

                    if "dev" in scripts:
                        add_cmd("Run & Development", f"Launch {pkg_name} development server:", f"{prefix}{pm} run dev", str(pkg_candidate.relative_to(ws_path)))
                    elif "start" in scripts:
                        add_cmd("Run & Development", f"Start {pkg_name} application:", f"{prefix}{pm} start", str(pkg_candidate.relative_to(ws_path)))

                    if "build" in scripts:
                        add_cmd("Build & Bundle", f"Build {pkg_name} production bundle:", f"{prefix}{pm} run build", str(pkg_candidate.relative_to(ws_path)))
                    elif "compile" in scripts:
                        add_cmd("Build & Bundle", f"Compile TypeScript / assets for {pkg_name}:", f"{prefix}{pm} run compile", str(pkg_candidate.relative_to(ws_path)))

                    if "test" in scripts:
                        add_cmd("Testing & Verification", f"Run {pkg_name} automated test suite:", f"{prefix}{pm} test", str(pkg_candidate.relative_to(ws_path)))
                    if "lint" in scripts:
                        add_cmd("Code Quality & Linting", f"Run linter checks for {pkg_name}:", f"{prefix}{pm} run lint", str(pkg_candidate.relative_to(ws_path)))
                    if "format" in scripts:
                        add_cmd("Code Quality & Linting", f"Format source code for {pkg_name}:", f"{prefix}{pm} run format", str(pkg_candidate.relative_to(ws_path)))
                except Exception:
                    pass

        # 2. Python ecosystem
        pyproject_path = ws_path / "pyproject.toml"
        setup_py_path = ws_path / "setup.py"
        req_txt_path = ws_path / "requirements.txt"
        poetry_lock = ws_path / "poetry.lock"
        pipfile = ws_path / "Pipfile"

        if pyproject_path.exists() or setup_py_path.exists():
            add_cmd("Installation & Setup", "Install Python package in editable development mode:", "pip install -e .", "pyproject.toml" if pyproject_path.exists() else "setup.py")
        elif poetry_lock.exists():
            add_cmd("Installation & Setup", "Install project dependencies using Poetry:", "poetry install", "poetry.lock")
        elif pipfile.exists():
            add_cmd("Installation & Setup", "Install dependencies with Pipenv:", "pipenv install --dev", "Pipfile")
        elif req_txt_path.exists():
            add_cmd("Installation & Setup", "Install Python dependencies from requirements file:", "pip install -r requirements.txt", "requirements.txt")

        # 3. Python Runtime / Execution entry points
        if (ws_path / "run_dev.py").exists():
            add_cmd("Run & Development", "Start local development runner / backend daemon:", "python run_dev.py", "run_dev.py")
        elif (ws_path / "manage.py").exists() or "Django" in frameworks:
            add_cmd("Run & Development", "Launch Django development server:", "python manage.py runserver", "manage.py")
        elif (ws_path / "backend" / "app" / "main.py").exists():
            add_cmd("Run & Development", "Launch FastAPI application server with hot-reload:", "uvicorn backend.app.main:app --reload --port 8000", "backend/app/main.py")
        elif "FastAPI" in frameworks:
            add_cmd("Run & Development", "Launch FastAPI application server:", "uvicorn app.main:app --reload --port 8000", "app/main.py")
        elif "Flask" in frameworks:
            add_cmd("Run & Development", "Launch Flask development server:", "flask run", "Flask")
        elif (ws_path / "app.py").exists():
            add_cmd("Run & Development", "Execute application entrypoint:", "python app.py", "app.py")
        elif (ws_path / "main.py").exists():
            add_cmd("Run & Development", "Execute main entrypoint script:", "python main.py", "main.py")
        elif (ws_path / "run.py").exists():
            add_cmd("Run & Development", "Execute project runtime runner:", "python run.py", "run.py")

        # 4. Python Testing
        test_files = [f.get("file_path", "") for f in files if "test" in f.get("file_path", "").lower()]
        if (ws_path / "tests").exists() or (ws_path / "pytest.ini").exists() or any(test_files):
            add_cmd("Testing & Verification", "Run unit and integration test suite with Pytest:", "pytest -v", "tests/")

        # 5. Rust ecosystem
        if (ws_path / "Cargo.toml").exists():
            add_cmd("Installation & Setup", "Fetch Rust dependencies via Cargo:", "cargo fetch", "Cargo.toml")
            add_cmd("Run & Development", "Run Rust binary executable:", "cargo run", "Cargo.toml")
            add_cmd("Build & Bundle", "Compile optimized release binary:", "cargo build --release", "Cargo.toml")
            add_cmd("Testing & Verification", "Execute Rust cargo test suite:", "cargo test", "Cargo.toml")
            add_cmd("Code Quality & Linting", "Run Clippy linter checks:", "cargo clippy", "Cargo.toml")

        # 6. Go ecosystem
        if (ws_path / "go.mod").exists():
            add_cmd("Installation & Setup", "Download Go module dependencies:", "go mod download", "go.mod")
            add_cmd("Run & Development", "Run main Go application:", "go run .", "go.mod")
            add_cmd("Testing & Verification", "Run all Go package tests:", "go test ./...", "go.mod")
            add_cmd("Build & Bundle", "Build Go project binaries:", "go build ./...", "go.mod")

        # 7. Makefile targets
        makefile_path = ws_path / "Makefile"
        if makefile_path.exists():
            try:
                lines = makefile_path.read_text(encoding="utf-8", errors="ignore").splitlines()
                for line in lines:
                    if line and not line.startswith(("#", "\t", " ")) and ":" in line:
                        target = line.split(":")[0].strip()
                        if target in ("all", "build", "test", "dev", "run", "lint", "start", "clean", "docker"):
                            add_cmd("Makefile Workflow", f"Execute Makefile '{target}' target:", f"make {target}", "Makefile")
            except Exception:
                pass

        # 8. Docker / Containerization
        if (ws_path / "docker-compose.yml").exists() or (ws_path / "compose.yaml").exists():
            add_cmd("Containerization", "Launch multi-container services with Docker Compose:", "docker compose up --build", "docker-compose.yml")
        elif (ws_path / "Dockerfile").exists():
            add_cmd("Containerization", f"Build container image for {ws_path.name.lower()}:", f"docker build -t {ws_path.name.lower()} .", "Dockerfile")

        # 9. Fallback if no specific manifests were detected
        if not cmds:
            add_cmd("Run & Development", "Inspect workspace structure and files:", "ls -la", "workspace")

        return cmds
