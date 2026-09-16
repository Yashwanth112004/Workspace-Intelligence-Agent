import re
from typing import List
from app.models.workspace import ASTSymbol
from app.services.parser.base import BaseLanguageParser

class RustParserPlugin(BaseLanguageParser):
    @property
    def supported_languages(self) -> List[str]:
        return ["Rust"]

    def parse(self, repo_id: str, relative_path: str, code_content: str, language: str) -> List[ASTSymbol]:
        symbols: List[ASTSymbol] = []
        lines = code_content.splitlines()

        struct_pattern = re.compile(r"(?:pub\s+)?(struct|enum|trait)\s+(\w+)")
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

class CFamilyParserPlugin(BaseLanguageParser):
    @property
    def supported_languages(self) -> List[str]:
        return ["C", "C++", "Java", "C#", "C/C++ Header", "C++ Header"]

    def parse(self, repo_id: str, relative_path: str, code_content: str, language: str) -> List[ASTSymbol]:
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
