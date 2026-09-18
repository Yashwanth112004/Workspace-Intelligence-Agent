"""Workspace-aware developer-level code explanation service for files, notebooks, and symbols."""

import ast
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from wia.analyzers.code.notebook_parser import NotebookParser
from wia.core.impact import ImpactAnalyzer, ImpactReport
from wia.core.index_model import WorkspaceIndex
from wia.knowledge.graph import GraphNode, WorkspaceGraph

STD_LIB_MODULES = {
    "sys", "os", "time", "datetime", "pathlib", "json", "html", "dataclasses",
    "typing", "subprocess", "hashlib", "re", "math", "collections", "itertools",
    "functools", "enum", "copy", "tempfile", "shutil", "argparse", "sqlite3",
    "ast", "inspect", "logging", "unittest", "shlex", "concurrent", "queue",
    "urllib", "http", "socket", "traceback", "gc", "io", "csv", "tempfile",
}


@dataclass
class ExplanationModel:
    """Canonical workspace explanation data model."""

    target: str
    file_path: str
    file_name: str
    language: str
    file_size: int
    role: str
    purpose: str
    what_is: str
    what_does: str
    how_it_works: str
    why_exists: str
    role_in_project: str
    connects_to_codebase: str
    symbols: list[dict[str, Any]]
    std_dependencies: list[tuple[str, str]]
    external_dependencies: list[tuple[str, str]]
    workspace_dependencies: list[tuple[str, str]]
    used_by: list[tuple[str, str]]
    related_tests: list[tuple[str, str]]
    impact_report: ImpactReport
    developer_takeaway: str
    batch_id: str = "Batch 1"
    evidence: list[str] = field(
        default_factory=lambda: [
            "Grounded in AST symbol parsing, WorkspaceGraph relationship edges, and workspace metadata."
        ]
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert canonical explanation model to serializable dictionary."""
        return {
            "target": self.target,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "language": self.language,
            "file_size": self.file_size,
            "role": self.role,
            "purpose": self.purpose,
            "what_is": self.what_is,
            "what_does": self.what_does,
            "how_it_works": self.how_it_works,
            "why_exists": self.why_exists,
            "role_in_project": self.role_in_project,
            "connects_to_codebase": self.connects_to_codebase,
            "symbols": self.symbols,
            "classes_count": sum(1 for s in self.symbols if s.get("symbol_type") == "class"),
            "functions_count": sum(
                1 for s in self.symbols if s.get("symbol_type") in ("function", "method")
            ),
            "std_dependencies_items": self.std_dependencies,
            "std_dependencies": [s[0] for s in self.std_dependencies],
            "external_dependencies_items": self.external_dependencies,
            "external_dependencies": [e[0] for e in self.external_dependencies],
            "workspace_dependencies_items": self.workspace_dependencies,
            "workspace_dependencies": [w[0] for w in self.workspace_dependencies],
            "used_by_items": self.used_by,
            "used_by": [u[0] for u in self.used_by],
            "related_tests_items": self.related_tests,
            "related_tests": [t[0] for t in self.related_tests],
            "impact_risk_level": self.impact_report.risk_level,
            "impact_explanation": self.impact_report.explanation,
            "impact_direct_dependents": self.impact_report.direct_dependents,
            "developer_takeaway": self.developer_takeaway,
            "batch_id": self.batch_id,
            "evidence": self.evidence,
        }


class ExplanationService:
    """Generates grounded, developer-level explanations for workspace files, notebooks, and symbols."""

    @classmethod
    def _read_source_code(cls, rel_path: str, index: WorkspaceIndex) -> str | None:
        """Read source code content from workspace filesystem if available."""
        try:
            ws_root = Path(index.workspace_path).resolve()
            abs_p = ws_root / rel_path
            if abs_p.exists() and abs_p.is_file():
                return abs_p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            pass
        return None

    @classmethod
    def _analyze_function_ast(cls, func_name: str, source_code: str | None) -> dict[str, Any]:
        """Inspect AST of source code to extract parameters, docstrings, loops, conditionals, and calls."""
        if not source_code:
            return {}

        try:
            tree = ast.parse(source_code)
            for node in ast.walk(tree):
                if (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == func_name
                ):
                    docstring = ast.get_docstring(node) or ""
                    args = [arg.arg for arg in node.args.args]
                    has_if = any(isinstance(child, ast.If) for child in ast.walk(node))
                    has_loop = any(
                        isinstance(child, (ast.For, ast.While)) for child in ast.walk(node)
                    )
                    returns = [n for n in ast.walk(node) if isinstance(n, ast.Return)]
                    calls = []
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call):
                            if isinstance(child.func, ast.Name):
                                calls.append(child.func.id)
                            elif isinstance(child.func, ast.Attribute):
                                calls.append(child.func.attr)

                    return {
                        "docstring": docstring.strip(),
                        "params": args,
                        "has_conditionals": has_if,
                        "has_loops": has_loop,
                        "has_returns": len(returns) > 0,
                        "called_functions": sorted(set(calls[:8])),
                    }
        except Exception:
            pass
        return {}

    @classmethod
    def _analyze_test_file(cls, test_rel_path: str, index: WorkspaceIndex) -> str:
        """Extract test function names and test descriptions from Python test source code."""
        source = cls._read_source_code(test_rel_path, index)
        if not source:
            return "Contains automated test suite exercising target component."

        try:
            tree = ast.parse(source)
            test_funcs = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    doc = ast.get_docstring(node)
                    if doc:
                        test_funcs.append(f"`{node.name}` ({doc.strip()})")
                    else:
                        test_funcs.append(f"`{node.name}`")
            if test_funcs:
                return f"Contains test suite: {', '.join(test_funcs[:4])}."
        except Exception:
            pass
        return "Contains automated regression tests exercising this target component."

    @classmethod
    def _describe_symbol_implementation(
        cls, sym_name: str, stype: str, params: list[str], doc: str, rel_path: str, source_code: str | None
    ) -> str:
        """Generate concrete implementation breakdown for a symbol grounded strictly in AST evidence."""
        ast_info = cls._analyze_function_ast(sym_name, source_code)
        doc_clean = doc.strip() if doc else ast_info.get("docstring", "")
        param_str = f"({', '.join(params)})" if params else "()"

        calls = ast_info.get("called_functions", [])
        calls_str = f"`{', '.join(calls)}`" if calls else "None"
        cond_str = " Evaluates conditional logic (`if`)." if ast_info.get("has_conditionals") else ""
        loop_str = " Executes iterative operations (`for`/`while`)." if ast_info.get("has_loops") else ""

        purpose_line = doc_clean if doc_clean else f"Defines {stype} `{sym_name}` within `{rel_path}`."

        return (
            f"`{sym_name}{param_str}` [{stype.upper()}]\n"
            f"  * Purpose: {purpose_line}\n"
            f"  * Implementation: Accepts parameters {', '.join(params) if params else 'None'}.{cond_str}{loop_str}\n"
            f"  * Input: {', '.join(params) if params else 'None'}\n"
            f"  * Calls: {calls_str}"
        )

    @classmethod
    def infer_architectural_role(
        cls, rel_path: str, symbols: list[dict], imports: list[str]
    ) -> str:
        """Infer architectural role based on path, symbols, and imports."""
        p_lower = rel_path.replace("\\", "/").lower()

        if p_lower.startswith("tests/") or "test_" in p_lower or "_test." in p_lower:
            return "Test Module — Automated verification & test suite"
        elif p_lower.endswith(".ipynb"):
            return "Jupyter Notebook — Interactive workflow & experimentation"
        elif "cli/app.py" in p_lower or "main.py" in p_lower or "__main__.py" in p_lower:
            return "CLI / Application Entry Point — Root application entrypoint"
        elif "cli/commands/" in p_lower or "_cmd.py" in p_lower:
            return "CLI Command — Subcommand execution & terminal interface"
        elif "cli/formatting" in p_lower or "formatting" in p_lower:
            return "Presentation Layer — Terminal formatting & output helpers"
        elif "config" in p_lower or "constants.py" in p_lower:
            return "Configuration — Centralized defaults, settings & constants"
        elif "code/" in p_lower or "ast_parser" in p_lower or "parser" in p_lower:
            return "Code Analysis — Structural source parsing & AST extraction"
        elif "dependency" in p_lower or "manifest" in p_lower:
            return "Dependency Analysis — Manifest parsing & conflict detection"
        elif "git" in p_lower:
            return "Git Intelligence — Version control & history analysis"
        elif "security" in p_lower or "secret" in p_lower:
            return "Security Scanner — Credential & vulnerability detection"
        elif "storage" in p_lower or "sqlite" in p_lower or "db" in p_lower:
            return "Storage Layer — Relational database & persistence store"
        elif "retrieval" in p_lower or "retriever" in p_lower:
            return "Retrieval Layer — Context selection & evidence indexing"
        elif "llm" in p_lower or "provider" in p_lower or "reasoning" in p_lower:
            return "AI / Reasoning Layer — LLM provider abstraction & reasoning"
        elif "services" in p_lower:
            return "Service Layer — Application service logic & orchestration"
        elif "utils" in p_lower or "helpers" in p_lower:
            return "Utility — Helper functions and common utilities"
        elif "models" in p_lower or "schema" in p_lower or "index_model" in p_lower:
            return "Data Model — Domain dataclasses & schema definitions"

        return "Core Module — Application component"

    @classmethod
    def infer_purpose(
        cls, rel_path: str, symbols: list[dict], docstring: str | None = None
    ) -> str:
        """Infer plain technical purpose statement from workspace evidence."""
        if docstring and docstring.strip():
            return docstring.strip()

        fn_names = [
            s.get("name")
            for s in symbols
            if s.get("symbol_type") in ("function", "class")
        ]
        if fn_names:
            return f"Provides core functionality for `{Path(rel_path).stem}`, defining: {', '.join(fn_names[:5])}."

        return f"Source module `{Path(rel_path).name}` contributing to the `{Path(rel_path).parent}` component."

    @classmethod
    def find_related_tests(
        cls, target_name: str, index: WorkspaceIndex
    ) -> list[tuple[str, str]]:
        """Find test files and test rationale referencing target file or symbol."""
        stem = Path(target_name).stem.lower()
        related: list[tuple[str, str]] = []

        for rel_path, rec in index.files.items():
            norm_p = rel_path.replace("\\", "/").lower()
            if norm_p.endswith(".pyc") or "__pycache__" in norm_p or norm_p.endswith(".egg-info"):
                continue

            if norm_p.startswith("tests/") or "test_" in norm_p or "_test" in norm_p:
                imports = rec.extra_metadata.get("imports", [])

                matched = False
                if stem in norm_p:
                    matched = True
                else:
                    for imp in imports:
                        if stem in imp.lower():
                            matched = True
                            break

                if matched:
                    test_desc = cls._analyze_test_file(rel_path, index)
                    related.append((rel_path, test_desc))

        return related

    @classmethod
    def build_explanation_model(
        cls, rel_path: str, index: WorkspaceIndex, graph: WorkspaceGraph
    ) -> ExplanationModel:
        """Build canonical ExplanationModel from workspace index and relationship graph."""
        rec = index.files[rel_path]
        symbols = rec.extra_metadata.get("symbols", [])
        raw_imports = rec.extra_metadata.get("imports", [])
        file_name = Path(rel_path).name
        lang = rec.language
        source_code = cls._read_source_code(rel_path, index)

        # Extract module docstring
        module_doc = ""
        if source_code and lang == "Python":
            try:
                tree = ast.parse(source_code)
                module_doc = (ast.get_docstring(tree) or "").strip()
            except Exception:
                module_doc = ""

        purpose = cls.infer_purpose(rel_path, symbols, docstring=module_doc)
        role = cls.infer_architectural_role(rel_path, symbols, raw_imports)

        # 1. Identity & Overview
        class_cnt = sum(1 for s in symbols if s.get("symbol_type") == "class")
        func_cnt = sum(
            1 for s in symbols if s.get("symbol_type") in ("function", "method")
        )
        what_is_text = (
            f"This file `{rel_path}` is a {lang} module fulfilling the architectural role of {role}. "
            f"It declares {class_cnt} class(es) and {func_cnt} function/method definition(s) totaling {rec.file_size} bytes."
        )

        # 2. What it does
        if module_doc:
            what_does_text = f"{module_doc}\n\nThe module implements its declared symbols to fulfill its architectural role."
        elif symbols:
            top_syms = ", ".join(f"`{s.get('name')}`" for s in symbols[:4] if s.get("name"))
            what_does_text = f"The module provides implementations for symbols including {top_syms}, handling operations for the {Path(rel_path).parent} layer."
        else:
            what_does_text = f"The file `{file_name}` defines workspace configuration, structure, or utility rules."

        # 3. How it works
        if symbols:
            sym_summaries = []
            for s in symbols[:6]:
                sname = s.get("name", "")
                stype = s.get("symbol_type", "")
                params = s.get("parameters", [])
                doc = s.get("docstring") or ""
                p_str = f"({', '.join(params)})" if params else "()"
                desc = f"`{sname}{p_str}` ({stype})"
                if doc:
                    desc += f": {doc.splitlines()[0]}"
                sym_summaries.append(desc)

            how_works_text = (
                f"When imported or executed, `{file_name}` orchestrates the following components:\n"
                + "\n".join(f"  * {s}" for s in sym_summaries)
            )
        else:
            how_works_text = f"The file contains structural definitions and configurations evaluated during execution."

        # 4. Why it exists
        if symbols:
            why_exists_text = (
                f"The module exists to provide modular, testable implementations for `{file_name}` logic, "
                f"maintaining clear separation of concerns in the repository."
            )
        else:
            why_exists_text = f"This file exists to configure, test, or support the workspace build and execution environment."

        # 5. Role in Project
        role_in_project_text = (
            f"`{rel_path}` belongs to the {role.split(' — ')[0]} layer. It connects with related workspace modules "
            f"to perform required tasks."
        )

        # 6. Categorize Dependencies & Used By
        std_deps: list[tuple[str, str]] = []
        ext_deps: list[tuple[str, str]] = []
        ws_deps: list[tuple[str, str]] = []
        file_node_id = f"file:{rel_path}"

        for imp in raw_imports:
            if not imp:
                continue
            base_mod = imp.split(".")[0]
            if base_mod in STD_LIB_MODULES:
                std_deps.append((imp, f"Standard library module."))
            elif base_mod in index.files or any(base_mod in p for p in index.files):
                std_deps_desc = f"Workspace import."
                ws_deps.append((imp, std_deps_desc))
            else:
                ext_deps.append((imp, f"External package dependency."))

        for edge in graph.get_outgoing_edges(file_node_id):
            if edge.relation_type == "IMPORTS":
                target_node = graph.nodes.get(edge.target_id)
                if target_node and target_node.node_type == "file":
                    dep_p = target_node.file_path
                    dep_purpose = cls.infer_purpose(dep_p, index.files[dep_p].extra_metadata.get("symbols", [])) if dep_p in index.files else "Workspace dependency"
                    ws_deps.append((dep_p, dep_purpose))

        # Reverse Dependencies (Used By)
        used_by_items: list[tuple[str, str]] = []
        for edge in graph.get_incoming_edges(file_node_id):
            if edge.relation_type in ("IMPORTS", "CALLS"):
                source_node = graph.nodes.get(edge.source_id)
                if (
                    source_node
                    and source_node.file_path
                    and source_node.file_path != rel_path
                    and not source_node.file_path.endswith(".pyc")
                    and "__pycache__" not in source_node.file_path
                ):
                    usage_desc = f"Depends on `{file_name}` via {edge.relation_type} relationship."
                    used_by_items.append((source_node.file_path, usage_desc))

        sorted_used_by = sorted(set(used_by_items))

        # Connects to Codebase Text
        if sorted_used_by and ws_deps:
            connects_text = (
                f"`{rel_path}` is imported by {len(sorted_used_by)} workspace component(s) including "
                f"{', '.join([u[0] for u in sorted_used_by[:3]])}. It relies on workspace dependencies "
                f"({', '.join([w[0] for w in ws_deps[:3]])})."
            )
        elif sorted_used_by:
            connects_text = (
                f"`{rel_path}` is imported downstream by {len(sorted_used_by)} workspace component(s) "
                f"({', '.join([u[0] for u in sorted_used_by[:3]])})."
            )
        elif ws_deps:
            connects_text = (
                f"`{rel_path}` imports workspace modules ({', '.join([w[0] for w in ws_deps[:3]])})."
            )
        else:
            connects_text = f"`{rel_path}` operates as a self-contained module within the workspace."

        related_tests_list = cls.find_related_tests(rel_path, index)
        impact_report = ImpactAnalyzer.analyze_symbol_impact(rel_path, index, graph)

        # Actionable Developer Takeaway
        takeaway_text = (
            f"DEVELOPER TAKEAWAY:\n"
            f"Before modifying `{rel_path}`:\n"
            f"  * Risk Classification: {impact_report.risk_level} ({impact_report.explanation})\n"
            f"  * Downstream Dependents: {len(sorted_used_by)} direct consumer(s) identified.\n"
            f"  * Tests to Verify: {len(related_tests_list)} related test suite file(s)."
        )

        return ExplanationModel(
            target=rel_path,
            file_path=rel_path,
            file_name=file_name,
            language=lang,
            file_size=rec.file_size,
            role=role,
            purpose=purpose,
            what_is=what_is_text,
            what_does=what_does_text,
            how_it_works=how_works_text,
            why_exists=why_exists_text,
            role_in_project=role_in_project_text,
            connects_to_codebase=connects_text,
            symbols=symbols,
            std_dependencies=sorted(set(std_deps)),
            external_dependencies=sorted(set(ext_deps)),
            workspace_dependencies=sorted(set(ws_deps)),
            used_by=sorted_used_by,
            related_tests=related_tests_list,
            impact_report=impact_report,
            developer_takeaway=takeaway_text,
            batch_id=rec.extra_metadata.get("batch_id", "Batch 1"),
        )

    @classmethod
    def explain_notebook(cls, rel_path: str, index: WorkspaceIndex, graph: WorkspaceGraph) -> str:
        """Generate specialized developer explanation for a Jupyter Notebook (.ipynb)."""
        abs_p = Path(index.workspace_path) / rel_path
        nb = NotebookParser.parse_file(abs_p)

        headings_str = "\n".join(f"  * {h}" for h in nb.markdown_headings[:6]) if nb.markdown_headings else "  * No markdown section headers found"
        flow_str = "\n".join(f"  * {f}" for f in nb.execution_flow[:8]) if nb.execution_flow else "  * Sequential cell execution"
        syms_str = ", ".join(f"`{s.name}` ({s.symbol_type})" for s in nb.all_symbols[:6]) if nb.all_symbols else "None (executes script cells)"
        deps_str = ", ".join(nb.external_libraries[:8]) if nb.external_libraries else "None"
        refs_str = ", ".join(f"`{r}`" for r in nb.workspace_references[:6]) if nb.workspace_references else "None"

        # Check outputs
        outputs_found = sum(len(c.outputs_summary) for c in nb.cells)

        return f"""WIA Notebook Explanation
========================

Target: {rel_path}

1. NOTEBOOK OVERVIEW
--------------------
File: `{rel_path}` (Jupyter Notebook, Kernel: `{nb.kernel_name}`, Language: `{nb.language}`)
Total Cells: {nb.total_cells} (Markdown: {nb.markdown_cells_count}, Code: {nb.code_cells_count})

2. PURPOSE
----------
{nb.purpose_summary}

3. SECTION STRUCTURE
--------------------
{headings_str}

4. EXECUTION FLOW
-----------------
{flow_str}

5. IMPORTANT CODE & SYMBOLS
---------------------------
Symbols Defined: {syms_str}

6. DEPENDENCIES & LIBRARIES
---------------------------
External Libraries: {deps_str}

7. WORKSPACE REFERENCES
-----------------------
Referenced Workspace Artifacts: {refs_str}

8. OUTPUTS / RESULTS
--------------------
Computed Outputs: {outputs_found} cell(s) produced execution outputs/displays.

9. EVIDENCE
-----------
* Grounded in Jupyter Notebook JSON cell structure, AST code cell analysis, and workspace references.
"""

    @classmethod
    def explain_target(
        cls, target: str, index: WorkspaceIndex, graph: WorkspaceGraph | None = None
    ) -> str:
        """Main entrypoint for explaining a file, notebook, or code symbol."""
        if graph is None:
            graph = WorkspaceGraph()
            graph.build_from_index(index)

        target_norm = target.replace("\\", "/").strip()

        # 1. Check for Exact or File Path Match
        matched_files: list[str] = []
        for rel_path in index.files:
            norm_p = rel_path.replace("\\", "/")
            if (
                norm_p == target_norm
                or norm_p.endswith("/" + target_norm)
                or Path(norm_p).name == target_norm
            ):
                matched_files.append(rel_path)

        if len(matched_files) == 1:
            matched_f = matched_files[0]
            if matched_f.endswith(".ipynb") or index.files[matched_f].file_type == "Notebook":
                return cls.explain_notebook(matched_f, index, graph)
            return cls.explain_file(matched_f, index, graph)
        elif len(matched_files) > 1:
            candidates = "\n".join(
                [f"  {idx+1}. {f}" for idx, f in enumerate(matched_files)]
            )
            return (
                f"Multiple matching files found for target '{target}':\n\n"
                f"{candidates}\n\n"
                f"Please specify the full relative path."
            )

        # 2. Check for Symbol Match
        matching_symbols: list[tuple[str, dict]] = []
        for rel_path, rec in index.files.items():
            symbols = rec.extra_metadata.get("symbols", [])
            for sym in symbols:
                sname = sym.get("name", "")
                stype = sym.get("symbol_type", "")
                if stype != "import" and (
                    sname == target or sname.lower() == target.lower()
                ):
                    matching_symbols.append((rel_path, sym))

        if len(matching_symbols) == 1:
            rel_path, sym = matching_symbols[0]
            return cls.explain_symbol(target, rel_path, sym, index, graph)
        elif len(matching_symbols) > 1:
            candidates = "\n".join(
                [
                    f"  {idx+1}. {r} -> `{s.get('name')}` ({s.get('symbol_type')})"
                    for idx, (r, s) in enumerate(matching_symbols)
                ]
            )
            return (
                f"Multiple matching symbols found for target '{target}':\n\n"
                f"{candidates}\n\n"
                f"Please specify the file or fully qualified symbol name."
            )

        # 3. Target Not Found
        return (
            f"WIA could not determine target '{target}' reliably from the indexed workspace.\n"
            f"Make sure the file or symbol name is correct and run 'wia index' to update workspace state."
        )

    @classmethod
    def explain_file_structured(
        cls, rel_path: str, index: WorkspaceIndex, graph: WorkspaceGraph
    ) -> dict[str, Any]:
        """Generate structured dictionary payload for file explanation from canonical model."""
        model = cls.build_explanation_model(rel_path, index, graph)
        return model.to_dict()

    @classmethod
    def explain_file(
        cls, rel_path: str, index: WorkspaceIndex, graph: WorkspaceGraph
    ) -> str:
        """Generate comprehensive developer-level file explanation CLI output from canonical model."""
        model = cls.build_explanation_model(rel_path, index, graph)
        symbols = model.symbols
        source_code = cls._read_source_code(rel_path, index)

        sym_blocks: list[str] = []
        for s in symbols:
            stype = s.get("symbol_type")
            if stype == "import":
                continue
            sname = s.get("name", "")
            params = s.get("parameters", [])
            doc = (s.get("docstring") or "").strip()

            sym_desc = cls._describe_symbol_implementation(
                sname, stype, params, doc, rel_path, source_code
            )
            sym_blocks.append(sym_desc)

        symbol_section_text = (
            "\n\n".join(sym_blocks)
            if sym_blocks
            else "No top-level functions or classes declared."
        )

        std_dep_str = (
            "\n".join([f"  * {d[0]} — {d[1]}" for d in model.std_dependencies])
            if model.std_dependencies
            else "  * None"
        )
        ext_dep_str = (
            "\n".join([f"  * {d[0]} — {d[1]}" for d in model.external_dependencies])
            if model.external_dependencies
            else "  * None"
        )
        ws_dep_str = (
            "\n".join([f"  * {d[0]} — {d[1]}" for d in model.workspace_dependencies])
            if model.workspace_dependencies
            else "  * None"
        )

        used_by_str = (
            "\n".join([f"  * {u[0]} — {u[1]}" for u in model.used_by])
            if model.used_by
            else "  * None (No incoming workspace dependencies found)"
        )

        tests_str = (
            "\n".join([f"  * {t[0]} — {t[1]}" for t in model.related_tests])
            if model.related_tests
            else "  * None (No direct test references found)"
        )

        impact_level = model.impact_report.risk_level
        impact_exp = model.impact_report.explanation
        direct_deps = model.impact_report.direct_dependents

        return f"""WIA Code Explanation
====================

Target:
{model.file_path}

1. WHAT THIS CODE IS
--------------------
{model.what_is}

2. WHAT THIS CODE DOES
----------------------
{model.what_does}

3. HOW IT WORKS
---------------
{model.how_it_works}

4. WHY IT EXISTS
----------------
{model.why_exists}

5. ROLE IN THE PROJECT
----------------------
{model.role_in_project}

6. HOW IT CONNECTS TO THE CODEBASE
-----------------------------------
{model.connects_to_codebase}

7. SYMBOL / FUNCTION EXPLANATIONS
---------------------------------
{symbol_section_text}

8. DEPENDENCIES
---------------
Workspace Dependencies:
{ws_dep_str}

External Dependencies:
{ext_dep_str}

Standard Library Dependencies:
{std_dep_str}

9. USED BY
----------
{used_by_str}

10. RELATED TESTS
-----------------
{tests_str}

11. CHANGE IMPACT
-----------------
If this code changes:
  * Risk Level: {impact_level}
  * Rationale: {impact_exp}
  * Direct Dependents ({len(direct_deps)}): {', '.join(direct_deps[:5]) if direct_deps else 'None'}

12. DEVELOPER TAKEAWAY
----------------------
{model.developer_takeaway}

13. EVIDENCE
------------
* Grounded in AST parsing, WorkspaceGraph relationship edges, and workspace metadata.
"""

    @classmethod
    def explain_symbol(
        cls,
        symbol_name: str,
        rel_path: str,
        sym: dict,
        index: WorkspaceIndex,
        graph: WorkspaceGraph,
    ) -> str:
        """Generate comprehensive workspace-aware symbol explanation CLI output."""
        stype = sym.get("symbol_type", "symbol")
        params = sym.get("parameters", [])
        parent = sym.get("parent_symbol")
        doc = (sym.get("docstring") or "").strip()
        line_num = sym.get("line_number", 1)
        param_str = f"({', '.join(params)})" if params else "()"
        source_code = cls._read_source_code(rel_path, index)

        sym_desc = cls._describe_symbol_implementation(
            symbol_name, stype, params, doc, rel_path, source_code
        )

        sym_node_id = f"symbol:{rel_path}:{symbol_name}"
        file_node_id = f"file:{rel_path}"
        callers: list[str] = []

        for edge in graph.get_incoming_edges(sym_node_id) + graph.get_incoming_edges(file_node_id):
            if edge.relation_type in ("CALLS", "IMPORTS"):
                source_node = graph.nodes.get(edge.source_id)
                if (
                    source_node
                    and source_node.file_path
                    and source_node.file_path != rel_path
                    and not source_node.file_path.endswith(".pyc")
                    and "__pycache__" not in source_node.file_path
                ):
                    callers.append(f"{source_node.name} ({source_node.file_path})")

        callers_block = (
            "\n".join([f"  * {c}" for c in sorted(set(callers))])
            if callers
            else "  * No direct caller edges recorded in relationship graph"
        )

        related_tests = cls.find_related_tests(symbol_name, index)
        test_block = (
            "\n".join([f"  * {t[0]} — {t[1]}" for t in related_tests])
            if related_tests
            else "  * None (No direct test references found)"
        )

        impact_report = ImpactAnalyzer.analyze_symbol_impact(symbol_name, index, graph)

        return f"""WIA Symbol Explanation
======================

Target Symbol: {symbol_name}

1. WHAT THIS SYMBOL IS & TYPE
-----------------------------
Name: {symbol_name}
Type: {stype.capitalize()}
Signature: `{symbol_name}{param_str}`
Defined in: {rel_path}:{line_num}
Parent Symbol: {parent or 'None (Top-level)'}

2. WHAT IT DOES & HOW IT WORKS
------------------------------
{sym_desc}

3. WHY IT EXISTS
----------------
Provides reusable {stype} capabilities for `{symbol_name}` within `{rel_path}`.

4. DEPENDENCIES & CALLS
-----------------------
Executes logic relying on imports and helper methods in `{rel_path}`.

5. CALLED BY / USED BY
----------------------
{callers_block}

6. RELATED TESTS
----------------
{test_block}

7. POTENTIAL IMPACT
-------------------
Risk Level: {impact_report.risk_level}
Explanation: {impact_report.explanation}
Direct Dependents ({len(impact_report.direct_dependents)}): {', '.join(impact_report.direct_dependents[:5]) if impact_report.direct_dependents else 'None'}

8. DEVELOPER TAKEAWAY
---------------------
When modifying `{symbol_name}`, inspect signature compatibility across consuming modules and verify test assertions.

9. EVIDENCE
-----------
* Grounded in AST symbol node `{symbol_name}`, caller graph edges, and workspace index metadata.
"""
