import re
from typing import List
from app.models.workspace import ASTSymbol
from app.services.parser.base import BaseLanguageParser

class TypeScriptParserPlugin(BaseLanguageParser):
    @property
    def supported_languages(self) -> List[str]:
        return ["JavaScript", "TypeScript"]

    def parse(self, repo_id: str, relative_path: str, code_content: str, language: str) -> List[ASTSymbol]:
        symbols: List[ASTSymbol] = []
        lines = code_content.splitlines()

        # Imports pattern
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

        # Class / Interface / Type
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

        # Functions / Arrow functions
        func_pattern = re.compile(r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)|(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*=>")
        for idx, line in enumerate(lines, 1):
            m = func_pattern.search(line)
            if m:
                fn1, args1, fn2, args2 = m.groups()
                fn_name = fn1 or fn2
                args_str = args1 if fn1 else args2
                args = [a.strip().split(":")[0].strip() for a in (args_str or "").split(",") if a.strip()]
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
