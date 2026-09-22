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
    base_classes: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    calls: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert SymbolNode to serializable dictionary."""
        return asdict(self)


# Precompiled regular expressions for multi-language fallback parsing
CLASS_PATTERN = re.compile(
    r"^\s*(?:export\s+|public\s+|private\s+|protected\s+)?(?:class|struct|interface|trait|type)\s+([A-Za-z0-9_]+)(?:\s+(?:extends|implements|<|:)\s*([A-Za-z0-9_\.]+))?"
)
FUNC_PATTERN = re.compile(
    r"^\s*(?:async\s+)?(?:export\s+|public\s+|private\s+|protected\s+|static\s+)*(?:def|function|fn|func|const|let|var)\s+([A-Za-z0-9_]+)"
)
IMPORT_PATTERN = re.compile(
    r"^\s*(?:import|from|use|require|include)\s+([A-Za-z0-9_\./\-]+)"
)


class ASTParser:
    """Parses source files into structural AST symbol nodes."""

    @classmethod
    def _extract_decorator_name(cls, dec_node: ast.AST) -> str:
        """Extract name string from decorator node."""
        if isinstance(dec_node, ast.Name):
            return dec_node.id
        elif isinstance(dec_node, ast.Attribute):
            val = cls._extract_decorator_name(dec_node.value)
            return f"{val}.{dec_node.attr}" if val else dec_node.attr
        elif isinstance(dec_node, ast.Call):
            return cls._extract_decorator_name(dec_node.func)
        return ""

    @classmethod
    def _extract_base_name(cls, base_node: ast.AST) -> str:
        """Extract name string from class base node."""
        if isinstance(base_node, ast.Name):
            return base_node.id
        elif isinstance(base_node, ast.Attribute):
            val = cls._extract_base_name(base_node.value)
            return f"{val}.{base_node.attr}" if val else base_node.attr
        return ""

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
                bases = [cls._extract_base_name(b) for b in node.bases if cls._extract_base_name(b)]
                decs = [cls._extract_decorator_name(d) for d in node.decorator_list if cls._extract_decorator_name(d)]

                symbols.append(
                    SymbolNode(
                        name=node.name,
                        symbol_type="class",
                        line_number=node.lineno,
                        end_line_number=getattr(node, "end_lineno", node.lineno),
                        docstring=doc,
                        parent_symbol=self.current_parent,
                        base_classes=bases,
                        decorators=decs,
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
                decs = [cls._extract_decorator_name(d) for d in node.decorator_list if cls._extract_decorator_name(d)]

                calls: list[str] = []
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Call):
                        cname = cls._extract_base_name(sub.func)
                        if cname and cname not in calls:
                            calls.append(cname)

                symbols.append(
                    SymbolNode(
                        name=node.name,
                        symbol_type=stype,
                        line_number=node.lineno,
                        end_line_number=getattr(node, "end_lineno", node.lineno),
                        docstring=doc,
                        parameters=params,
                        parent_symbol=self.current_parent,
                        decorators=decs,
                        calls=calls[:30],
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

        for idx, line in enumerate(lines, start=1):
            class_match = CLASS_PATTERN.search(line)
            if class_match:
                bases = [class_match.group(2)] if class_match.group(2) else []
                symbols.append(
                    SymbolNode(
                        name=class_match.group(1),
                        symbol_type="class",
                        line_number=idx,
                        end_line_number=idx,
                        base_classes=bases,
                    )
                )
                continue

            func_match = FUNC_PATTERN.search(line)
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

            import_match = IMPORT_PATTERN.search(line)
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

        ext = path.suffix.lower()
        if ext == ".ipynb":
            from wia.analyzers.code.notebook_parser import NotebookParser
            return NotebookParser.parse_file(path).all_symbols

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return []

        if ext == ".py":
            return cls.parse_python_content(content)
        else:
            return cls.parse_regex_fallback(content)
