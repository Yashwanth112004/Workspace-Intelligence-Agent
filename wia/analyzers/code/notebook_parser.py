"""Jupyter Notebook (.ipynb) structural parser and AST analyzer."""

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from wia.analyzers.code.ast_parser import ASTParser, SymbolNode


PATH_REF_PATTERN = re.compile(r"[\w\-\./]+\.(?:py|json|csv|txt|md|yml|yaml|png|jpg)")


@dataclass
class NotebookCell:
    """Represents a single cell in a Jupyter notebook."""

    cell_index: int
    cell_type: str  # "code", "markdown", "raw"
    source: str
    execution_count: int | None = None
    symbols: list[SymbolNode] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    outputs_summary: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert cell to dictionary."""
        return {
            "cell_index": self.cell_index,
            "cell_type": self.cell_type,
            "source": self.source,
            "execution_count": self.execution_count,
            "symbols": [s.to_dict() for s in self.symbols],
            "imports": self.imports,
            "outputs_summary": self.outputs_summary,
        }


@dataclass
class NotebookAnalysis:
    """Extracted technical analysis for a Jupyter Notebook."""

    file_path: str
    kernel_name: str = "python3"
    language: str = "python"
    total_cells: int = 0
    markdown_cells_count: int = 0
    code_cells_count: int = 0
    markdown_headings: list[str] = field(default_factory=list)
    purpose_summary: str = ""
    cells: list[NotebookCell] = field(default_factory=list)
    all_imports: list[str] = field(default_factory=list)
    all_symbols: list[SymbolNode] = field(default_factory=list)
    workspace_references: list[str] = field(default_factory=list)
    external_libraries: list[str] = field(default_factory=list)
    execution_flow: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert notebook analysis to dictionary."""
        return {
            "file_path": self.file_path,
            "kernel_name": self.kernel_name,
            "language": self.language,
            "total_cells": self.total_cells,
            "markdown_cells_count": self.markdown_cells_count,
            "code_cells_count": self.code_cells_count,
            "markdown_headings": self.markdown_headings,
            "purpose_summary": self.purpose_summary,
            "cells": [c.to_dict() for c in self.cells],
            "all_imports": self.all_imports,
            "all_symbols": [s.to_dict() for s in self.all_symbols],
            "workspace_references": self.workspace_references,
            "external_libraries": self.external_libraries,
            "execution_flow": self.execution_flow,
        }


class NotebookParser:
    """Parses Jupyter Notebook JSON, extracting markdown sections, code cells, AST symbols, and outputs."""

    @classmethod
    def parse_content(cls, content: str, file_path: str = "") -> NotebookAnalysis:
        """Parse notebook raw JSON string into structural NotebookAnalysis."""
        try:
            data = json.loads(content)
        except Exception:
            return NotebookAnalysis(file_path=file_path)

        metadata = data.get("metadata", {})
        language_info = metadata.get("language_info", {})
        lang_name = language_info.get("name", "python")
        kernel_spec = metadata.get("kernelspec", {})
        kernel_name = kernel_spec.get("name", "python3")

        raw_cells = data.get("cells", [])
        parsed_cells: list[NotebookCell] = []
        all_symbols: list[SymbolNode] = []
        all_imports: list[str] = []
        markdown_headings: list[str] = []
        first_markdown_text: list[str] = []
        exec_flow: list[str] = []
        ws_refs: set[str] = set()

        line_offset = 1
        for idx, cell in enumerate(raw_cells, start=1):
            c_type = cell.get("cell_type", "raw")
            raw_source = cell.get("source", [])
            source_text = "".join(raw_source) if isinstance(raw_source, list) else str(raw_source)
            exec_cnt = cell.get("execution_count")

            cell_symbols: list[SymbolNode] = []
            cell_imports: list[str] = []
            outputs_summary: list[str] = []

            if c_type == "markdown":
                for line in source_text.splitlines():
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        markdown_headings.append(stripped)
                    elif stripped and len(first_markdown_text) < 3:
                        first_markdown_text.append(stripped)

            elif c_type == "code":
                # Parse Python AST for code cell
                if lang_name.lower() in ("python", "python3", "ipython"):
                    extracted = ASTParser.parse_python_content(source_text)
                    for s in extracted:
                        s.line_number += (line_offset - 1)
                        s.end_line_number += (line_offset - 1)
                        if s.symbol_type == "import":
                            cell_imports.append(s.name)
                            if s.name not in all_imports:
                                all_imports.append(s.name)
                        else:
                            cell_symbols.append(s)
                            all_symbols.append(s)

                # Process outputs summary
                outputs = cell.get("outputs", [])
                for out in outputs:
                    out_type = out.get("output_type", "")
                    if out_type == "stream":
                        txt = "".join(out.get("text", []))[:100].strip()
                        if txt:
                            outputs_summary.append(f"stdout: {txt}")
                    elif out_type in ("execute_result", "display_data"):
                        data_dict = out.get("data", {})
                        if "text/plain" in data_dict:
                            txt = "".join(data_dict.get("text/plain", []))[:100].strip()
                            outputs_summary.append(f"result: {txt}")
                    elif out_type == "error":
                        ename = out.get("ename", "Error")
                        outputs_summary.append(f"error: {ename}")

                step_label = f"Cell #{idx} [In {exec_cnt or ' '}]"
                if cell_symbols:
                    sym_names = ", ".join(s.name for s in cell_symbols[:3])
                    step_label += f" -> defines ({sym_names})"
                elif cell_imports:
                    imp_names = ", ".join(cell_imports[:3])
                    step_label += f" -> imports ({imp_names})"
                exec_flow.append(step_label)

            # Check for file path references in code or markdown
            for match in PATH_REF_PATTERN.findall(source_text):
                if not match.startswith("http") and "/" in match or "." in match:
                    ws_refs.add(match)

            parsed_cells.append(
                NotebookCell(
                    cell_index=idx,
                    cell_type=c_type,
                    source=source_text,
                    execution_count=exec_cnt,
                    symbols=cell_symbols,
                    imports=cell_imports,
                    outputs_summary=outputs_summary,
                )
            )
            line_offset += max(1, len(source_text.splitlines()))

        purpose = ""
        if markdown_headings:
            purpose = markdown_headings[0].lstrip("#").strip()
            if first_markdown_text:
                purpose += f" — {first_markdown_text[0]}"
        elif first_markdown_text:
            purpose = first_markdown_text[0]
        else:
            purpose = f"Interactive Jupyter Notebook ({len(parsed_cells)} cells)"

        md_count = sum(1 for c in parsed_cells if c.cell_type == "markdown")
        code_count = sum(1 for c in parsed_cells if c.cell_type == "code")

        ext_libs = [imp.split(".")[0] for imp in all_imports if not imp.startswith(".")]

        return NotebookAnalysis(
            file_path=file_path,
            kernel_name=kernel_name,
            language=lang_name,
            total_cells=len(parsed_cells),
            markdown_cells_count=md_count,
            code_cells_count=code_count,
            markdown_headings=markdown_headings,
            purpose_summary=purpose,
            cells=parsed_cells,
            all_imports=all_imports,
            all_symbols=all_symbols,
            workspace_references=sorted(list(ws_refs)),
            external_libraries=sorted(list(set(ext_libs))),
            execution_flow=exec_flow,
        )

    @classmethod
    def parse_file(cls, file_path: str | Path) -> NotebookAnalysis:
        """Read and parse a .ipynb file from filesystem."""
        path = Path(file_path)
        if not path.is_file():
            return NotebookAnalysis(file_path=str(file_path))
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            return cls.parse_content(content, file_path=str(file_path))
        except Exception:
            return NotebookAnalysis(file_path=str(file_path))
