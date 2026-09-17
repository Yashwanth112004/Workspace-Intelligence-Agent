"""Embedding provider abstraction for vector generation."""

import math
import re
from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Abstract interface for generating vector embeddings."""

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Generate numerical vector embedding for input text."""
        pass

    @abstractmethod
    def dimension(self) -> int:
        """Return vector embedding dimension size."""
        pass


class HashEmbeddingProvider(EmbeddingProvider):
    """Deterministic local hash-based embedding provider (offline fallback)."""

    def __init__(self, dim: int = 64):
        self._dim = dim

    def dimension(self) -> int:
        return self._dim

    def embed_text(self, text: str) -> list[float]:
        """Generate normalized pseudo-vector based on character n-grams."""
        vec = [0.0] * self._dim
        tokens = re.findall(r"\w+", text.lower())
        if not tokens:
            return vec

        for token in tokens:
            for idx, char in enumerate(token):
                pos = (ord(char) * (idx + 1)) % self._dim
                vec[pos] += 1.0

        # L2 normalize vector
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec


class EmbeddingService:
    """Service wrapper for embedding generation across providers."""

    def __init__(self, provider: EmbeddingProvider | None = None):
        self.provider = provider or HashEmbeddingProvider()

    def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding vector using configured provider."""
        return self.provider.embed_text(text)
