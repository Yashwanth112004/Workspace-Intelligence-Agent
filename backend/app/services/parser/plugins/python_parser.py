import ast
import logging
from typing import List
from app.models.workspace import ASTSymbol
from app.services.parser.base import BaseLanguageParser

logger = logging.getLogger("wia.parser.python")

class PythonParserPlugin(BaseLanguageParser):
    @property
    def supported_languages(self) -> List[str]:
        return ["Python"]

    def parse(self, repo_id: str, relative_path: str, code_content: str, language: str) -> List[ASTSymbol]:
        symbols: List[ASTSymbol] = []
        try:
            tree = ast.parse(code_content)
        except Exception as e:
            logger.debug(f"Python AST parse failed for {relative_path}: {e}")
            return []

        class FunctionCallVisitor(ast.NodeVisitor):
            def __init__(self):
                self.calls = []

            def visit_Call(self, node):
                if isinstance(node.func, ast.Name):
                    self.calls.append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    self.calls.append(node.func.attr)
                self.generic_visit(node)

        for node in ast.walk(tree):
            # Imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    symbols.append(ASTSymbol(
                        repo_id=repo_id,
                        file_path=relative_path,
                        symbol_type="import",
                        name=alias.name,
                        start_line=getattr(node, 'lineno', 1),
                        end_line=getattr(node, 'end_lineno', getattr(node, 'lineno', 1)),
                        imported_symbols=[alias.asname or alias.name]
                    ))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                imported = [n.name for n in node.names]
                symbols.append(ASTSymbol(
                    repo_id=repo_id,
                    file_path=relative_path,
                    symbol_type="import",
                    name=module,
                    start_line=getattr(node, 'lineno', 1),
                    end_line=getattr(node, 'end_lineno', getattr(node, 'lineno', 1)),
                    imported_symbols=imported
                ))
            # Classes
            elif isinstance(node, ast.ClassDef):
                docstring = ast.get_docstring(node)
                bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
                symbols.append(ASTSymbol(
                    repo_id=repo_id,
                    file_path=relative_path,
                    symbol_type="class",
                    name=node.name,
                    signature=f"class {node.name}({', '.join(bases)})" if bases else f"class {node.name}",
                    start_line=node.lineno,
                    end_line=getattr(node, 'end_lineno', node.lineno),
                    docstring=docstring,
                    parameters=bases
                ))
            # Functions / Methods
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                docstring = ast.get_docstring(node)
                args = [a.arg for a in node.args.args]
                
                visitor = FunctionCallVisitor()
                visitor.visit(node)
                calls = list(set(visitor.calls))

                prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
                sig = f"{prefix} {node.name}({', '.join(args)})"

                symbols.append(ASTSymbol(
                    repo_id=repo_id,
                    file_path=relative_path,
                    symbol_type="function",
                    name=node.name,
                    signature=sig,
                    start_line=node.lineno,
                    end_line=getattr(node, 'end_lineno', node.lineno),
                    docstring=docstring,
                    parameters=args,
                    calls=calls
                ))

        return symbols
