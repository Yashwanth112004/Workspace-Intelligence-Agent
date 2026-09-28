"""Multi-tier impact analysis engine evaluating direct, indirect, test, and example ripple effects."""

from collections import deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from wia.core.index_model import WorkspaceIndex
from wia.knowledge.graph import GraphNode, WorkspaceGraph


@dataclass
class ImpactReport:
    """Represents an evidence-grounded impact classification report for a symbol or file change."""

    target_symbol: str
    target_type: str  # "file", "symbol (function)", "symbol (class)"
    defining_file: str
    risk_level: str  # "LOW", "MEDIUM", "HIGH", "NOT_FOUND"
    direct_dependents: list[str] = field(default_factory=list)
    indirect_dependents: list[str] = field(default_factory=list)
    file_dependents: list[str] = field(default_factory=list)
    affected_files: list[str] = field(default_factory=list)
    affected_tests: list[str] = field(default_factory=list)
    affected_examples: list[str] = field(default_factory=list)
    dependency_paths: list[str] = field(default_factory=list)
    change_implications: list[str] = field(default_factory=list)
    explanation: str = ""
    evidence: list[str] = field(default_factory=list)
    found: bool = True
    candidates: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert impact report to serializable dictionary."""
        return asdict(self)


class ImpactAnalyzer:
    """Calculates multi-tier downstream dependencies, affected tests/examples, and change implications."""

    @classmethod
    def analyze_symbol_impact(
        cls, symbol_name: str, index: WorkspaceIndex, graph: WorkspaceGraph | None = None
    ) -> ImpactReport:
        """Analyze relationship graph to evaluate direct and indirect impact of modifying a symbol or file."""
        if graph is None:
            graph = WorkspaceGraph()
            graph.build_from_index(index)

        target_norm = symbol_name.replace("\\", "/").strip()
        file_node: GraphNode | None = None
        symbol_nodes: list[GraphNode] = []

        # 1. Direct O(1) file_id lookup
        direct_file_id = f"file:{target_norm}"
        if direct_file_id in graph.nodes and graph.nodes[direct_file_id].node_type == "file":
            file_node = graph.nodes[direct_file_id]

        # 2. File path ending or filename/stem match
        if not file_node:
            for node in graph.nodes.values():
                if node.node_type == "file" and (
                    node.file_path == target_norm
                    or node.file_path.endswith("/" + target_norm)
                    or Path(node.file_path).name.lower() == target_norm.lower()
                    or Path(node.file_path).stem.lower() == target_norm.lower()
                ):
                    file_node = node
                    break

        # 3. Search for matching symbol nodes if not a file
        if not file_node:
            for node in graph.nodes.values():
                if node.node_type != "file" and (
                    node.name == symbol_name or f":{symbol_name}" in node.node_id
                ):
                    symbol_nodes.append(node)

        # 3. Fallback search by substring if no exact match
        if not file_node and not symbol_nodes:
            matches = graph.find_nodes_by_name(symbol_name)
            for m in matches:
                if m.node_type != "file":
                    symbol_nodes.append(m)

        # 5. Handle Unknown Target
        if not file_node and not symbol_nodes:
            return ImpactReport(
                target_symbol=symbol_name,
                target_type="unknown",
                defining_file="",
                risk_level="NOT_FOUND",
                direct_dependents=[],
                indirect_dependents=[],
                file_dependents=[],
                affected_files=[],
                affected_tests=[],
                affected_examples=[],
                dependency_paths=[],
                change_implications=["Symbol was not identified in workspace index."],
                explanation=f"Target '{symbol_name}' was not found in the indexed workspace.",
                evidence=["WorkspaceIndex search yielded 0 matching records."],
                found=False,
            )

        # 6. Evaluate Target Node & Dependents Traversal
        target_node = file_node or symbol_nodes[0]
        defining_file = target_node.file_path
        target_type = "file" if file_node else f"symbol ({target_node.node_type})"

        direct_dependents: list[str] = []
        direct_files: set[str] = set()
        indirect_files: set[str] = set()
        affected_tests: set[str] = set()
        affected_examples: set[str] = set()
        dep_paths: list[str] = []
        evidence: list[str] = []

        # Find direct callers/importers
        incoming = graph.get_incoming_edges(target_node.node_id)
        if file_node:
            # 6a. Direct file-to-file incoming edges
            for edge in incoming:
                src = graph.nodes.get(edge.source_id)
                if src and src.file_path and src.file_path != defining_file:
                    direct_files.add(src.file_path)
                    direct_dependents.append(f"{src.file_path} ({edge.relation_type})")
                    evidence.append(f"`{src.file_path}` has `{edge.relation_type}` relationship to `{defining_file}`")

            # 6b. Check incoming edges to ANY symbol defined inside this file
            for node in graph.nodes.values():
                if node.file_path == defining_file and node.node_id != file_node.node_id:
                    for sym_edge in graph.get_incoming_edges(node.node_id):
                        src = graph.nodes.get(sym_edge.source_id)
                        if src and src.file_path and src.file_path != defining_file:
                            direct_files.add(src.file_path)
                            lbl = f"{src.file_path} (references {node.name})"
                            if lbl not in direct_dependents:
                                direct_dependents.append(lbl)
                                evidence.append(f"`{src.file_path}` {sym_edge.relation_type.lower()}s `{node.name}` defined in `{defining_file}`")

            # 6c. Cross-reference index file import declarations
            def_stem = Path(defining_file).stem
            def_name = Path(defining_file).name
            def_syms = set()
            if defining_file in index.files:
                def_syms = {s.get("name") for s in index.files[defining_file].extra_metadata.get("symbols", []) if s.get("name")}

            for o_path, o_rec in index.files.items():
                if o_path == defining_file:
                    continue
                o_imports = set(o_rec.extra_metadata.get("imports", []))
                for s in o_rec.extra_metadata.get("symbols", []):
                    if s.get("symbol_type") == "import":
                        if s.get("name"):
                            o_imports.add(s.get("name"))
                        if s.get("parent_symbol"):
                            o_imports.add(s.get("parent_symbol"))

                for imp in o_imports:
                    if not imp:
                        continue
                    clean_imp = imp.strip().replace("\\", "/")
                    if (
                        clean_imp == def_stem
                        or clean_imp == def_name
                        or clean_imp.endswith("/" + def_stem)
                        or clean_imp.endswith("/" + def_name)
                        or clean_imp in def_syms
                    ):
                        if o_path not in direct_files:
                            direct_files.add(o_path)
                            lbl = f"{o_path} (imports {def_name})"
                            if lbl not in direct_dependents:
                                direct_dependents.append(lbl)
                                evidence.append(f"`{o_path}` imports `{imp}` from `{defining_file}`")
        else:
            for edge in incoming:
                src = graph.nodes.get(edge.source_id)
                if src and src.file_path and src.file_path != defining_file:
                    direct_files.add(src.file_path)
                    caller_label = f"{src.file_path}::{src.name}" if src.node_type != "file" else src.file_path
                    direct_dependents.append(f"{caller_label} ({edge.relation_type})")
                    evidence.append(f"`{caller_label}` has `{edge.relation_type}` edge to `{target_node.name}`")

            # Also check file-level imports of defining file
            def_file_id = f"file:{defining_file}"
            for edge in graph.get_incoming_edges(def_file_id):
                src = graph.nodes.get(edge.source_id)
                if src and src.file_path and src.file_path != defining_file:
                    direct_files.add(src.file_path)

        # Transitive BFS traversal for indirect dependents
        visited_nodes: set[str] = {target_node.node_id}
        if not file_node:
            visited_nodes.add(f"file:{defining_file}")

        queue: deque[tuple[str, list[str]]] = deque()
        for f in direct_files:
            fid = f"file:{f}"
            visited_nodes.add(fid)
            queue.append((fid, [defining_file, f]))

        while queue:
            curr_id, path_so_far = queue.popleft()
            if len(path_so_far) > 4:  # Depth limit
                continue

            for edge in graph.get_incoming_edges(curr_id):
                src = graph.nodes.get(edge.source_id)
                if src and src.file_path and src.file_path != defining_file and src.file_path not in direct_files:
                    if src.file_path not in indirect_files:
                        indirect_files.add(src.file_path)
                        new_path = path_so_far + [src.file_path]
                        dep_paths.append(" -> ".join(new_path))
                        if len(queue) < 50:
                            queue.append((f"file:{src.file_path}", new_path))

        all_affected = sorted(list(direct_files | indirect_files))

        # Categorize affected tests and examples
        for p in all_affected:
            p_lower = p.lower()
            rec = index.files.get(p)
            f_type = rec.file_type if rec else ""

            if f_type == "Test" or "test" in p_lower or Path(p).name.startswith("test_"):
                affected_tests.add(p)
            elif any(part in p_lower for part in ("example", "examples", "demo", "sample", "tutorial", ".ipynb")):
                affected_examples.add(p)

        # Build Change Implications
        implications: list[str] = []
        if not all_affected:
            implications.append("Evidence indicates isolated impact: no downstream workspace consumers were found.")
        else:
            implications.append(f"Modifying target directly affects {len(direct_files)} workspace component(s).")
            if indirect_files:
                implications.append(f"Transitive ripple reaches {len(indirect_files)} secondary downstream module(s).")
            if affected_tests:
                implications.append(f"Verification required across {len(affected_tests)} test suite file(s).")
            if affected_examples:
                implications.append(f"Example/notebook workflows in {len(affected_examples)} file(s) may be affected.")

        # Evidence-derived risk classification
        total_consumers = len(all_affected)
        if total_consumers >= 10 or len(affected_tests) >= 5:
            risk = "HIGH"
            explanation = f"High blast radius: {total_consumers} total downstream file(s) and {len(affected_tests)} test file(s) depend on this entity."
        elif total_consumers >= 3:
            risk = "MEDIUM"
            explanation = f"Moderate blast radius: {total_consumers} downstream file(s) depend directly or transitively on this entity."
        elif total_consumers > 0:
            risk = "LOW"
            explanation = f"Localized impact: {total_consumers} consuming workspace file(s) identified."
        else:
            risk = "LOW"
            explanation = f"Evidence indicates isolated impact with 0 identified downstream callers or referencing files."

        candidates = [f"{s.file_path}::{s.name}" for s in symbol_nodes] if symbol_nodes else []

        return ImpactReport(
            target_symbol=symbol_name,
            target_type=target_type,
            defining_file=defining_file,
            risk_level=risk,
            direct_dependents=direct_dependents,
            indirect_dependents=sorted(list(indirect_files)),
            file_dependents=sorted(list(direct_files)),
            affected_files=all_affected,
            affected_tests=sorted(list(affected_tests)),
            affected_examples=sorted(list(affected_examples)),
            dependency_paths=dep_paths[:8],
            change_implications=implications,
            explanation=explanation,
            evidence=evidence[:10],
            found=True,
            candidates=candidates if len(candidates) > 1 else [],
        )
