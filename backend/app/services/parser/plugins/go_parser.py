import re
from typing import List
from app.models.workspace import ASTSymbol
from app.services.parser.base import BaseLanguageParser

class GoParserPlugin(BaseLanguageParser):
    @property
    def supported_languages(self) -> List[str]:
        return ["Go"]

    def parse(self, repo_id: str, relative_path: str, code_content: str, language: str) -> List[ASTSymbol]:
        symbols: List[ASTSymbol] = []
        lines = code_content.splitlines()

        type_pattern = re.compile(r"type\s+(\w+)\s+(struct|interface)")
        method_pattern = re.compile(r"func\s+\((?:[*\w\s]+)\)\s+(\w+)\s*\(([^)]*)\)")
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
