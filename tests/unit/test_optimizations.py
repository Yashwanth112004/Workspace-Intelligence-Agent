"""Unit and regression tests verifying all codebase optimizations and performance fast-paths."""

from pathlib import Path
import math
import sqlite3
import pytest

from wia.core.hashing import FileHasher
from wia.core.change_detector import ChangeDetector
from wia.core.metadata import FileRecord, IndexingStatus
from wia.core.language import LanguageDetector, FileType
from wia.analyzers.security.secret_scanner import SecretScanner
from wia.analyzers.code.ast_parser import ASTParser
from wia.knowledge.graph import WorkspaceGraph
from wia.knowledge.vector_store import VectorStore
from wia.storage.sqlite_store import SQLiteStore
from wia.core.index_model import WorkspaceIndex


def test_file_hasher_optimizations(tmp_path: Path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("performance optimization test content", encoding="utf-8")

    h1 = FileHasher.hash_file(test_file)
    h2 = FileHasher.hash_text("performance optimization test content")
    assert h1 == h2
    assert len(h1) == 64


def test_change_detector_has_changes(tmp_path: Path):
    rec1 = FileRecord(
        relative_path="a.py",
        file_size=10,
        modified_time=1.0,
        extension=".py",
        language="Python",
        content_hash="hash1",
        indexing_status=IndexingStatus.INDEXED,
    )
    rec2 = FileRecord(
        relative_path="a.py",
        file_size=10,
        modified_time=2.0,
        extension=".py",
        language="Python",
        content_hash="hash2",
        indexing_status=IndexingStatus.INDEXED,
    )

    prev = {"a.py": rec1}
    curr_same = {"a.py": rec1}
    curr_diff = {"a.py": rec2}

    assert not ChangeDetector.has_changes(prev, curr_same)
    assert ChangeDetector.has_changes(prev, curr_diff)


def test_language_detector_static_sets():
    assert LanguageDetector.detect_file_type("package-lock.json") == FileType.DEPENDENCY_LOCK
    assert LanguageDetector.detect_file_type("pyproject.toml") == FileType.BUILD
    assert LanguageDetector.detect_file_type(".env.example") == FileType.CONFIGURATION
    assert LanguageDetector.detect_file_type("docs/guide.md") == FileType.DOCUMENTATION


def test_secret_scanner_heuristic_fast_path():
    clean_code = "def add(a, b):\n    return a + b\n"
    findings_clean = SecretScanner.scan_content(clean_code, file_path="clean.py")
    assert len(findings_clean) == 0

    secret_code = "AWS_KEY = 'AKIA1234567890123456'\n"
    findings_secret = SecretScanner.scan_content(secret_code, file_path="aws.py")
    assert len(findings_secret) == 1
    assert findings_secret[0].rule_id == "SEC-001"


def test_ast_parser_precompiled_patterns():
    code = """
class DataProcessor:
    def process(self, data):
        self.clean(data)
        return self.transform(data)
"""
    symbols = ASTParser.parse_python_content(code)
    class_sym = [s for s in symbols if s.symbol_type == "class"]
    func_sym = [s for s in symbols if s.symbol_type == "method"]
    assert len(class_sym) == 1
    assert len(func_sym) == 1
    assert "clean" in func_sym[0].calls or "self.clean" in func_sym[0].calls or "transform" in func_sym[0].calls


def test_workspace_graph_edge_indexing():
    graph = WorkspaceGraph()
    graph.add_node("n1", "file", "a.py", "a.py")
    graph.add_node("n2", "file", "b.py", "b.py")

    # Add duplicate edges
    graph.add_edge("n1", "n2", "IMPORTS")
    graph.add_edge("n1", "n2", "IMPORTS")

    assert len(graph.edges) == 1
    assert len(graph.get_outgoing_edges("n1")) == 1


def test_sqlite_store_pragma_tuning(tmp_path: Path):
    db_file = tmp_path / "test.db"
    index = WorkspaceIndex(
        workspace_path=str(tmp_path),
        files={},
        languages={"Python": 1},
        frameworks=["FastAPI"],
    )
    SQLiteStore.save_index(db_file, index)

    conn = SQLiteStore.get_connection(db_file)
    journal_mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
    conn.close()
    assert journal_mode.upper() == "WAL"
