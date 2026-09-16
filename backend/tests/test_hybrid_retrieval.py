import pytest
from app.models.workspace import VectorChunk, WorkspaceSummary, ASTSymbol
from app.services.retrieval.hybrid_retriever import HybridRetriever
from app.services.retrieval.query_planner import QueryPlanner
from app.services.intelligence.secret_safety import SecretSafetyService
from app.services.export.okf_exporter import OKFExporter
from app.models.workspace import Repository, FileNode
import tempfile
import os

def test_query_planner_intents():
    p1 = QueryPlanner.plan_query("Explain this architecture")
    assert p1["intent"] == "ARCHITECTURE"

    p2 = QueryPlanner.plan_query("Trace execution flow for login")
    assert p2["intent"] == "CODE_FLOW"

    p3 = QueryPlanner.plan_query("What happens if I modify UserService?")
    assert p3["intent"] == "DEPENDENCY_IMPACT"

def test_secret_safety_redaction():
    assert SecretSafetyService.is_sensitive_file(".env") is True
    assert SecretSafetyService.is_sensitive_file("id_rsa") is True
    assert SecretSafetyService.is_sensitive_file("main.py") is False

    code_with_secret = 'api_key = "sk-1234567890abcdef1234567890abcdef"'
    sanitized = SecretSafetyService.sanitize_content(code_with_secret)
    assert "sk-1234567890abcdef" not in sanitized
    assert "[REDACTED" in sanitized

def test_okf_exporter():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Repository(id="repo_okf", name="OKFTest", source_type="local", source_path=tmpdir, local_path=tmpdir)
        nodes = [FileNode(id="n1", repo_id="repo_okf", path=os.path.join(tmpdir, "main.py"), relative_path="main.py", name="main.py", is_dir=False, loc_count=20)]
        symbols = [ASTSymbol(id="s1", repo_id="repo_okf", file_path="main.py", symbol_type="function", name="main")]
        summaries = [WorkspaceSummary(repo_id="repo_okf", level="repository", target_path="", name="OKFTest", summary_text="OKF overview")]

        out_path = OKFExporter.export_okf_tree(repo, nodes, symbols, summaries, tmpdir)
        assert os.path.exists(os.path.join(out_path, "index.md"))
        assert os.path.exists(os.path.join(out_path, "repository.md"))
        assert os.path.exists(os.path.join(out_path, "architecture.md"))
