from abc import ABC, abstractmethod
from typing import List
from app.models.workspace import ASTSymbol

class BaseLanguageParser(ABC):
    """Abstract base class for language parser plugins."""

    @property
    @abstractmethod
    def supported_languages(self) -> List[str]:
        """List of language names handled by this parser."""
        pass

    @abstractmethod
    def parse(self, repo_id: str, relative_path: str, code_content: str, language: str) -> List[ASTSymbol]:
        """Parses source code into ASTSymbol entities."""
        pass
