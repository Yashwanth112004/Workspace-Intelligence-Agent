import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool
from app.main import app
from app.core.database import get_session
from app.models.workspace import Repository, FileNode, ASTSymbol, WorkspaceSummary

@pytest.fixture(name="client")
def client_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    # Seed test repository
    with Session(engine) as session:
        repo = Repository(
            id="test-repo-123",
            name="TestRepository",
            source_type="local",
            source_path="./backend",
            local_path="./backend",
            status="completed",
            progress_pct=100,
            total_files=5,
            total_loc=350,
            tech_stack={"Python": 350},
            dependencies=["fastapi", "pydantic"],
            entry_points=["main.py"]
        )
        session.add(repo)

        node = FileNode(
            id="node-1",
            repo_id="test-repo-123",
            path="./backend/main.py",
            relative_path="main.py",
            name="main.py",
            is_dir=False,
            language="Python",
            loc_count=50,
            size_bytes=1200
        )
        session.add(node)

        sym = ASTSymbol(
            id="sym-1",
            repo_id="test-repo-123",
            file_path="main.py",
            symbol_type="function",
            name="start_server",
            signature="def start_server(port: int)",
            start_line=10,
            end_line=20
        )
        session.add(sym)

        imp_sym = ASTSymbol(
            id="sym-2",
            repo_id="test-repo-123",
            file_path="main.py",
            symbol_type="import",
            name="fastapi",
            start_line=1,
            end_line=1,
            imported_symbols=["FastAPI"]
        )
        session.add(imp_sym)

        summary = WorkspaceSummary(
            id="sum-1",
            repo_id="test-repo-123",
            level="repository",
            target_path="",
            name="TestRepository",
            summary_text="Architecture overview of test repository."
        )
        session.add(summary)
        session.commit()

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_root_and_health(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "online"

    r_health = client.get("/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "healthy"

def test_list_repositories(client):
    r = client.get("/api/v1/repos")
    assert r.status_code == 200
    data = r.json()
    assert "repositories" in data
    assert len(data["repositories"]) >= 1
    assert data["repositories"][0]["id"] == "test-repo-123"

def test_get_repo_status(client):
    r = client.get("/api/v1/repos/test-repo-123/status")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "TestRepository"
    assert data["status"] == "completed"

def test_get_repo_tree(client):
    r = client.get("/api/v1/repos/test-repo-123/tree")
    assert r.status_code == 200
    data = r.json()
    assert len(data["nodes"]) >= 1

def test_get_file_details(client):
    r = client.get("/api/v1/repos/test-repo-123/file?path=main.py")
    assert r.status_code == 200
    data = r.json()
    assert "file" in data
    assert "symbols" in data

def test_search_symbols(client):
    r = client.get("/api/v1/repos/test-repo-123/symbols/search?q=start_server")
    assert r.status_code == 200
    data = r.json()
    assert data["total_matches"] == 1
    assert data["symbols"][0]["name"] == "start_server"

def test_get_metrics(client):
    r = client.get("/api/v1/repos/test-repo-123/metrics")
    assert r.status_code == 200
    data = r.json()
    assert data["total_loc"] == 50
    assert data["symbol_counts"]["functions"] == 1

def test_get_dependency_graph(client):
    r = client.get("/api/v1/repos/test-repo-123/dependencies/graph")
    assert r.status_code == 200
    data = r.json()
    assert data["total_import_statements"] == 1
    assert data["import_graph"][0]["imported_module"] == "fastapi"

def test_export_report_markdown_and_json(client):
    r_md = client.get("/api/v1/repos/test-repo-123/export?format=markdown")
    assert r_md.status_code == 200
    assert "Architecture & Intelligence Report" in r_md.text

    r_json = client.get("/api/v1/repos/test-repo-123/export?format=json")
    assert r_json.status_code == 200
    assert "repository" in r_json.json()

def test_delete_repository(client):
    r = client.delete("/api/v1/repos/test-repo-123")
    assert r.status_code == 200
    
    # Verify 404 after deletion
    r_check = client.get("/api/v1/repos/test-repo-123/status")
    assert r_check.status_code == 404
