import ast
import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from app.models.workspace import ASTSymbol

logger = logging.getLogger("wia.parser")

class ASTParserEngine:
    """Multi-language AST and structural code symbol parser engine."""

    @staticmethod
    def parse_file(repo_id: str, relative_path: str, code_content: str, language: str) -> List[ASTSymbol]:
        """Parses source file and extracts symbols based on file language."""
        if not code_content or not code_content.strip():
            return []

        symbols: List[ASTSymbol] = []

        if language == "Python":
            symbols = ASTParserEngine._parse_python(repo_id, relative_path, code_content)
        elif language in ("JavaScript", "TypeScript"):
            symbols = ASTParserEngine._parse_js_ts(repo_id, relative_path, code_content)
        elif language == "Go":
            symbols = ASTParserEngine._parse_go(repo_id, relative_path, code_content)
        elif language == "Rust":
            symbols = ASTParserEngine._parse_rust(repo_id, relative_path, code_content)
        elif language in ("Java", "C#", "C", "C++", "C/C++ Header", "C++ Header"):
            symbols = ASTParserEngine._parse_c_like(repo_id, relative_path, code_content, language)
        else:
            symbols = ASTParserEngine._parse_generic(repo_id, relative_path, code_content)

        return symbols

    @staticmethod
    def _parse_python(repo_id: str, relative_path: str, code_content: str) -> List[ASTSymbol]:
        symbols: List[ASTSymbol] = []
        try:
            tree = ast.parse(code_content)
        except Exception as e:
            logger.debug(f"Python AST parse failed for {relative_path}: {e}")
            return ASTParserEngine._parse_generic(repo_id, relative_path, code_content)

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

    @staticmethod
    def _parse_js_ts(repo_id: str, relative_path: str, code_content: str) -> List[ASTSymbol]:
        symbols: List[ASTSymbol] = []
        lines = code_content.splitlines()

        # Imports pattern: import { a, b } from 'module' or import x from 'module' or require('module')
        import_pattern = re.compile(r"import\s+(?:\{([^}]+)\}|(\w+))\s+from\s+['\"]([^'\"]+)['\"]|const\s+(\{?[^=]+\}?)\s*=\s*require\(['\"]([^'\"]+)['\"]\)")
        for idx, line in enumerate(lines, 1):
            m = import_pattern.search(line)
            if m:
                dest, single, mod1, req_dest, mod2 = m.groups()
                mod = mod1 or mod2 or ""
                imports = []
                if dest:
                    imports = [i.strip() for i in dest.split(",") if i.strip()]
                elif single:
                    imports = [single.strip()]
                elif req_dest:
                    imports = [r.strip() for r in req_dest.replace("{", "").replace("}", "").split(",") if r.strip()]
                symbols.append(ASTSymbol(
                    repo_id=repo_id,
                    file_path=relative_path,
                    symbol_type="import",
                    name=mod,
                    start_line=idx,
                    end_line=idx,
                    imported_symbols=imports
                ))

        # Class / Interface / Type pattern
        class_pattern = re.compile(r"(?:export\s+)?(?:default\s+)?(?:class|interface|type)\s+(\w+)(?:\s+extends\s+(\w+))?")
        for idx, line in enumerate(lines, 1):
            m = class_pattern.search(line)
            if m:
                cname, base = m.groups()
                symbols.append(ASTSymbol(
                    repo_id=repo_id,
                    file_path=relative_path,
                    symbol_type="class",
                    name=cname,
                    signature=f"class/interface {cname}" + (f" extends {base}" if base else ""),
                    start_line=idx,
                    end_line=idx,
                    parameters=[base] if base else []
                ))

        # Function pattern: function myFunc(a, b) or const myFunc = (a, b) => or async function
        func_pattern = re.compile(r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)|(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*=>")
        for idx, line in enumerate(lines, 1):
            m = func_pattern.search(line)
            if m:
                fn1, args1, fn2, args2 = m.groups()
                fn_name = fn1 or fn2
                args_str = args1 if fn1 else args2
                args = [a.strip().split(":")[0].strip() for a in (args_str or "").split(",") if a.strip()]
                
                # Extract calls inside line context
                calls = [c for c in re.findall(r"\b(\w+)\(", line) if c not in {fn_name, "if", "for", "while", "switch", "catch", "require", "import"}]
                
                symbols.append(ASTSymbol(
                    repo_id=repo_id,
                    file_path=relative_path,
                    symbol_type="function",
                    name=fn_name,
                    signature=f"function {fn_name}({', '.join(args)})",
                    start_line=idx,
                    end_line=idx,
                    parameters=args,
                    calls=calls
                ))

        return symbols

    @staticmethod
    def _parse_go(repo_id: str, relative_path: str, code_content: str) -> List[ASTSymbol]:
        symbols: List[ASTSymbol] = []
        lines = code_content.splitlines()

        # Structs / Interfaces: type MyStruct struct / interface
        type_pattern = re.compile(r"type\s+(\w+)\s+(struct|interface)")
        # Methods: func (r *Receiver) Method(args) returns
        method_pattern = re.compile(r"func\s+\((?:[*\w\s]+)\)\s+(\w+)\s*\(([^)]*)\)")
        # Standalone Functions: func FunctionName(args)
        func_pattern = re.compile(r"func\s+(\w+)\s*\(([^)]*)\)")

        for idx, line in enumerate(lines, 1):
            t_match = type_pattern.search(line)
            if t_match:
                name, kind = t_match.groups()
                symbols.append(ASTSymbol(
                    repo_id=repo_id,
                    file_path=relative_path,
                    symbol_type="class" if kind == "struct" else "interface",
                    name=name,
                    signature=f"type {name} {kind}",
                    start_line=idx,
                    end_line=idx
                ))
                continue

            m_match = method_pattern.search(line)
            if m_match:
                name, args = m_match.groups()
                symbols.append(ASTSymbol(
                    repo_id=repo_id,
                    file_path=relative_path,
                    symbol_type="function",
                    name=name,
                    signature=f"func (receiver) {name}({args})",
                    start_line=idx,
                    end_line=idx,
                    parameters=[a.strip() for a in args.split(",") if a.strip()]
                ))
                continue

            f_match = func_pattern.search(line)
            if f_match:
                name, args = f_match.groups()
                if name not in {"if", "for", "switch"}:
                    symbols.append(ASTSymbol(
                        repo_id=repo_id,
                        file_path=relative_path,
                        symbol_type="function",
                        name=name,
                        signature=f"func {name}({args})",
                        start_line=idx,
                        end_line=idx,
                        parameters=[a.strip() for a in args.split(",") if a.strip()]
                    ))

        return symbols

    @staticmethod
    def _parse_rust(repo_id: str, relative_path: str, code_content: str) -> List[ASTSymbol]:
        symbols: List[ASTSymbol] = []
        lines = code_content.splitlines()

        # Struct / Enum / Trait
        struct_pattern = re.compile(r"(?:pub\s+)?(struct|enum|trait)\s+(\w+)")
        # Functions / Methods
        fn_pattern = re.compile(r"(?:pub\s+)?(?:async\s+)?fn\s+(\w+)\s*(?:<[^>]+>)?\s*\(([^)]*)\)")

        for idx, line in enumerate(lines, 1):
            s_match = struct_pattern.search(line)
            if s_match:
                kind, name = s_match.groups()
                symbols.append(ASTSymbol(
                    repo_id=repo_id,
                    file_path=relative_path,
                    symbol_type="class",
                    name=name,
                    signature=f"{kind} {name}",
                    start_line=idx,
                    end_line=idx
                ))
                continue

            f_match = fn_pattern.search(line)
            if f_match:
                name, args = f_match.groups()
                symbols.append(ASTSymbol(
                    repo_id=repo_id,
                    file_path=relative_path,
                    symbol_type="function",
                    name=name,
                    signature=f"fn {name}({args})",
                    start_line=idx,
                    end_line=idx,
                    parameters=[a.strip() for a in args.split(",") if a.strip()]
                ))

        return symbols

    @staticmethod
    def _parse_c_like(repo_id: str, relative_path: str, code_content: str, lang: str) -> List[ASTSymbol]:
        symbols: List[ASTSymbol] = []
        lines = code_content.splitlines()

        class_pattern = re.compile(r"(?:public\s+|private\s+|protected\s+)?(?:class|interface|struct)\s+(\w+)")
        func_pattern = re.compile(r"(?:public|private|protected|static|void|int|string|bool|float|double|auto|virtual)\s+(\w+)\s*\(([^)]*)\)")

        for idx, line in enumerate(lines, 1):
            c_match = class_pattern.search(line)
            if c_match:
                cname = c_match.group(1)
                symbols.append(ASTSymbol(
                    repo_id=repo_id,
                    file_path=relative_path,
                    symbol_type="class",
                    name=cname,
                    signature=f"class {cname}",
                    start_line=idx,
                    end_line=idx
                ))
                continue

            m = func_pattern.search(line)
            if m:
                name, args_str = m.groups()
                if name not in {"if", "while", "for", "switch", "catch", "return"}:
                    args = [a.strip() for a in args_str.split(",") if a.strip()]
                    symbols.append(ASTSymbol(
                        repo_id=repo_id,
                        file_path=relative_path,
                        symbol_type="function",
                        name=name,
                        signature=f"{name}({', '.join(args)})",
                        start_line=idx,
                        end_line=idx,
                        parameters=args
                    ))

        return symbols

    @staticmethod
    def _parse_generic(repo_id: str, relative_path: str, code_content: str) -> List[ASTSymbol]:
        return []
