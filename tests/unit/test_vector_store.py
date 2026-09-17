"""Unit tests for WorkspaceChunker, EmbeddingService, and VectorStore."""

from pathlib import Path
from wia.core.chunker import WorkspaceChunker
from wia.knowledge.embeddings import EmbeddingService, HashEmbeddingProvider
from wia.knowledge.vector_store import VectorStore


def test_chunker_extracts_functions_and_classes():
    content = """
class UserService:
    def get_user(self, user_id):
        return {"id": user_id}

def main():
    service = UserService()
    print(service.get_user(1))
"""
    chunks = WorkspaceChunker.chunk_file("user_service.py", content)
    assert len(chunks) >= 2
    symbols = {c.symbol_name for c in chunks}
    assert "UserService" in symbols
    assert "main" in symbols


def test_embedding_service_dimension():
    service = EmbeddingService(HashEmbeddingProvider(dim=32))
    vec = service.generate_embedding("def login(username, password): pass")
    assert len(vec) == 32


def test_vector_store_save_and_search(tmp_path: Path):
    db_file = tmp_path / "vectors.json"
    store = VectorStore(storage_path=db_file)

    chunks = WorkspaceChunker.chunk_file(
        "auth.py", "def authenticate_user(): return True\ndef revoke_token(): pass"
    )
    for c in chunks:
        store.add_chunk(c)

    store.save()
    assert db_file.exists()

    # Test load
    new_store = VectorStore(storage_path=db_file)
    results = new_store.search_similarity("authenticate", top_k=2)
    assert len(results) >= 1
    assert results[0][0].symbol_name == "authenticate_user"
