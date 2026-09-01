"""AST and symbol parser for structural code analysis."""

import ast
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class SymbolNode:
    """Represents a code symbol (class, function, method, import)."""

    name: str
    symbol_type: str  # "class", "function", "method", "import"
    line_number: int = 1
    end_line_number: int = 1
    docstring: str | None = None
    parameters: list[str] = field(default_factory=list)
    parent_symbol: str | None = None

    def to_dict(self) -> dict:
        """Convert SymbolNode to serializable dictionary."""
        return asdict(self)


class ASTParser:
    """Parses source files into structural AST symbol nodes."""

    @classmethod
    def parse_python_content(cls, content: str) -> list[SymbolNode]:
        """Parse Python source code using built-in `ast` module."""
        symbols: list[SymbolNode] = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return cls.parse_regex_fallback(content)

        class Visitor(ast.NodeVisitor):
            def __init__(self):
                self.current_parent: str | None = None

            def visit_ClassDef(self, node: ast.ClassDef):
                doc = ast.get_docstring(node)
                symbols.append(
                    SymbolNode(
                        name=node.name,
                        symbol_type="class",
                        line_number=node.lineno,
                        end_line_number=getattr(node, "end_lineno", node.lineno),
                        docstring=doc,
                        parent_symbol=self.current_parent,
                    )
                )
                prev_parent = self.current_parent
                self.current_parent = node.name
                self.generic_visit(node)
                self.current_parent = prev_parent

            def visit_FunctionDef(self, node: ast.FunctionDef):
                self._visit_func(node)

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
                self._visit_func(node)

            def _visit_func(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
                params = [arg.arg for arg in node.args.args]
                doc = ast.get_docstring(node)
                stype = "method" if self.current_parent else "function"

                symbols.append(
                    SymbolNode(
                        name=node.name,
                        symbol_type=stype,
                        line_number=node.lineno,
                        end_line_number=getattr(node, "end_lineno", node.lineno),
                        docstring=doc,
                        parameters=params,
                        parent_symbol=self.current_parent,
                    )
                )
                prev_parent = self.current_parent
                self.current_parent = node.name
                self.generic_visit(node)
                self.current_parent = prev_parent

            def visit_Import(self, node: ast.Import):
                for alias in node.names:
                    symbols.append(
                        SymbolNode(
                            name=alias.name,
                            symbol_type="import",
                            line_number=node.lineno,
                            end_line_number=node.lineno,
                        )
                    )

            def visit_ImportFrom(self, node: ast.ImportFrom):
                mod = node.module or ""
                for alias in node.names:
                    full_name = f"{mod}.{alias.name}" if mod else alias.name
                    symbols.append(
                        SymbolNode(
                            name=full_name,
                            symbol_type="import",
                            line_number=node.lineno,
                            end_line_number=node.lineno,
                        )
                    )

        Visitor().visit(tree)
        return symbols

    @classmethod
    def parse_regex_fallback(cls, content: str) -> list[SymbolNode]:
        """Regex-based fallback symbol parser for multi-language or non-standard syntax."""
        symbols: list[SymbolNode] = []
        lines = content.splitlines()

        class_pattern = re.compile(r"^\s*(?:export\s+)?class\s+([A-Za-z0-9_]+)")
        func_pattern = re.compile(
            r"^\s*(?:async\s+)?(?:export\s+)?(?:def|function|const|let|var)\s+([A-Za-z0-9_]+)"
        )
        import_pattern = re.compile(r"^\s*(?:import|from)\s+([A-Za-z0-9_\./\-]+)")

        for idx, line in enumerate(lines, start=1):
            class_match = class_pattern.search(line)
            if class_match:
                symbols.append(
                    SymbolNode(
                        name=class_match.group(1),
                        symbol_type="class",
                        line_number=idx,
                        end_line_number=idx,
                    )
                )
                continue

            func_match = func_pattern.search(line)
            if func_match:
                symbols.append(
                    SymbolNode(
                        name=func_match.group(1),
                        symbol_type="function",
                        line_number=idx,
                        end_line_number=idx,
                    )
                )
                continue

            import_match = import_pattern.search(line)
            if import_match:
                symbols.append(
                    SymbolNode(
                        name=import_match.group(1),
                        symbol_type="import",
                        line_number=idx,
                        end_line_number=idx,
                    )
                )

        return symbols

    @classmethod
    def parse_file(cls, file_path: str | Path) -> list[SymbolNode]:
        """Parse source file into symbol nodes based on extension."""
        path = Path(file_path)
        if not path.is_file():
            return []

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return []

        if path.suffix.lower() == ".py":
            return cls.parse_python_content(content)
        else:
            return cls.parse_regex_fallback(content)
