"""Integration tests for AST symbol extraction within IndexingService."""

from pathlib import Path
from wia.services.indexing_service import IndexingService
from wia.storage.repository import IndexRepository


def test_indexing_pipeline_extracts_symbols(tmp_path: Path):
    """Verify IndexingService attaches AST symbols and imports to FileRecord.extra_metadata."""
    py_content = """
import sys
from os import path

class Service:
    def process(self):
        pass

def run():
    s = Service()
    s.process()
"""
    (tmp_path / "service.py").write_text(py_content, encoding="utf-8")

    res = IndexingService.index_workspace(tmp_path)
    assert res.success is True

    index = IndexRepository.load_index(tmp_path)
    assert index is not None

    rec = index.files["service.py"]
    assert "symbols" in rec.extra_metadata
    assert "imports" in rec.extra_metadata

    symbol_names = [s["name"] for s in rec.extra_metadata["symbols"]]
    assert "Service" in symbol_names
    assert "process" in symbol_names
    assert "run" in symbol_names

    imports = rec.extra_metadata["imports"]
    assert "sys" in imports
    assert "os.path" in imports
