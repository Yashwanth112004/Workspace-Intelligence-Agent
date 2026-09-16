import logging
from typing import List, Dict, Optional
from app.models.workspace import ASTSymbol
from app.services.parser.base import BaseLanguageParser
from app.services.parser.plugins import ALL_PARSER_PLUGINS

logger = logging.getLogger("wia.parser")

class ASTParserEngine:
    """Multi-language AST and structural symbol parser routing through plugin registry."""

    _plugins: Dict[str, BaseLanguageParser] = {}

    @classmethod
    def _initialize_registry(cls):
        if not cls._plugins:
            for plugin in ALL_PARSER_PLUGINS:
                for lang in plugin.supported_languages:
                    cls._plugins[lang] = plugin

    @classmethod
    def parse_file(cls, repo_id: str, relative_path: str, code_content: str, language: str) -> List[ASTSymbol]:
        """Parses source file and extracts symbols using the matching language plugin."""
        if not code_content or not code_content.strip():
            return []

        cls._initialize_registry()
        parser = cls._plugins.get(language)
        if parser:
            try:
                return parser.parse(repo_id, relative_path, code_content, language)
            except Exception as e:
                logger.debug(f"Parser plugin failed for {relative_path} ({language}): {e}")

        # Fallback to C-like / generic matching if language is recognized
        c_family_parser = cls._plugins.get("C")
        if c_family_parser:
            return c_family_parser.parse(repo_id, relative_path, code_content, language)

        return []
