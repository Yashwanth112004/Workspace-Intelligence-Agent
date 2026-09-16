import pytest
from app.models.workspace import FileNode, ASTSymbol
from app.services.graph.code_graph import CodeKnowledgeGraph

def test_code_knowledge_graph_build_and_query():
    graph = CodeKnowledgeGraph("repo_test")

    nodes = [
        FileNode(id="n1", repo_id="repo_test", path="./main.py", relative_path="main.py", name="main.py", is_dir=False, loc_count=30),
        FileNode(id="n2", repo_id="repo_test", path="./auth.py", relative_path="auth.py", name="auth.py", is_dir=False, loc_count=50)
    ]

    symbols = [
        ASTSymbol(id="s1", repo_id="repo_test", file_path="main.py", symbol_type="function", name="main", signature="def main()", start_line=1, end_line=10, calls=["authenticate"]),
        ASTSymbol(id="s2", repo_id="repo_test", file_path="auth.py", symbol_type="function", name="authenticate", signature="def authenticate(user)", start_line=1, end_line=20, calls=[])
    ]

    graph.build_from_ast_and_files(nodes, symbols)

    # Test find_symbol
    syms = graph.find_symbol("authenticate")
    assert len(syms) >= 1
    assert syms[0].name == "authenticate"

    # Test find_callers
    callers = graph.find_callers("authenticate")
    assert len(callers) >= 1
    assert callers[0][0].name == "main"

    # Test find_callees
    callees = graph.find_callees("main")
    assert len(callees) >= 1
    assert callees[0][0].name == "authenticate"

    # Test trace_flow
    flow = graph.trace_flow("main")
    assert len(flow) == 2
    assert flow[0]["symbol"] == "main"
    assert flow[1]["symbol"] == "authenticate"

    # Test impact analysis
    impact = graph.analyze_impact("authenticate")
    assert impact["direct_impact_count"] >= 1
    assert "main" in [c.split()[0] for c in impact["affected_callers"]]
