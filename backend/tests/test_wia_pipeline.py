import pytest
import os
from sqlmodel import Session, SQLModel, create_engine
from app.models.workspace import Repository, FileNode, ASTSymbol, WorkspaceSummary
from app.services.ingestion import RepositoryCrawler
from app.services.parser import ASTParserEngine
from app.services.summarizer import HierarchicalSummarizerEngine
from app.services.rag import VectorSearchStore
from app.agent import WIACodeUnderstandingAgent

@pytest.fixture
def memory_db():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_crawler_scanner(memory_db):
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    nodes, stats = RepositoryCrawler.scan_repository("test_repo", current_dir)
    assert len(nodes) > 0
    assert stats["total_files"] > 0
    assert stats["total_loc"] > 0

def test_ast_python_parser():
    code = """
import os
import sys

class DataProcessor:
    \"\"\"Process data records.\"\"\"
    def process(self, items):
        return [self.transform(x) for x in items]

    def transform(self, item):
        return str(item).upper()

def main():
    dp = DataProcessor()
    dp.process([1, 2, 3])
"""
    symbols = ASTParserEngine.parse_file("repo1", "processor.py", code, "Python")
    fn_names = [s.name for s in symbols if s.symbol_type == "function"]
    class_names = [s.name for s in symbols if s.symbol_type == "class"]

    assert "DataProcessor" in class_names
    assert "process" in fn_names
    assert "transform" in fn_names
    assert "main" in fn_names

def test_hierarchical_summaries():
    repo = Repository(
        id="repo123",
        name="TestApp",
        source_type="local",
        source_path="./",
        local_path="./",
        total_files=2,
        total_loc=100,
        tech_stack={"Python": 100}
    )
    nodes = [
        FileNode(id="n1", repo_id="repo123", path="./app.py", relative_path="app.py", name="app.py", is_dir=False, loc_count=50, language="Python"),
    ]
    symbols = [
        ASTSymbol(id="s1", repo_id="repo123", file_path="app.py", symbol_type="function", name="main", signature="def main()", docstring="Main entry point")
    ]

    summaries = HierarchicalSummarizerEngine.generate_all_summaries(repo, nodes, symbols)
    levels = {s.level for s in summaries}
    
    assert "file" in levels
    assert "function" in levels
    assert "repository" in levels

def test_rag_and_nooa_agent():
    repo = Repository(
        id="repo123",
        name="TestApp",
        source_type="local",
        source_path="./",
        local_path="./",
        total_files=1,
        total_loc=50,
        tech_stack={"Python": 50}
    )
    summaries = [
        WorkspaceSummary(repo_id="repo123", level="repository", target_path="", name="TestApp", summary_text="Test app architecture summary.")
    ]
    symbols = [
        ASTSymbol(id="s1", repo_id="repo123", file_path="app.py", symbol_type="function", name="calculate_total", signature="def calculate_total(a, b)", docstring="Sums two numbers.")
    ]
    nodes = [
        FileNode(id="n1", repo_id="repo123", path="./app.py", relative_path="app.py", name="app.py", is_dir=False, loc_count=50, language="Python")
    ]

    chunks = VectorSearchStore.build_index("repo123", nodes, summaries, symbols)
    assert len(chunks) > 0

    agent = WIACodeUnderstandingAgent(repo, chunks, summaries)
    res = agent.answer_question("What function calculates totals?")

    assert "response" in res
    assert "citations" in res
    assert len(res["citations"]) > 0
