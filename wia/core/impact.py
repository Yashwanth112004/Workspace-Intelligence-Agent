"""Impact analysis engine evaluating refactoring and symbol change risks."""

from dataclasses import asdict, dataclass, field
from pathlib import Path
from wia.core.index_model import WorkspaceIndex
from wia.knowledge.graph import GraphNode, WorkspaceGraph


@dataclass
class ImpactReport:
    """Represents an impact classification report for a symbol or file change."""

    target_symbol: str
    target_type: str  # "symbol (function)", "file", "unknown"
    defining_file: str  # e.g. "wia/cli/formatting.py"
    risk_level: str  # "LOW", "MEDIUM", "HIGH", "NOT_FOUND"
    direct_dependents: list[str]  # Direct symbol callers with relation type
    file_dependents: list[str]  # File-level importing modules
    affected_files: list[str]
    explanation: str
    evidence: list[str] = field(
        default_factory=lambda: [
            "Tree-sitter AST symbol extraction",
            "WorkspaceGraph CALLS & IMPORTS edges",
            "Active WorkspaceIndex",
        ]
    )
    found: bool = True
    candidates: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert impact report to serializable dictionary."""
        return asdict(self)


class ImpactAnalyzer:
    """Calculates downstream dependencies and change impact classifications."""

    @classmethod
    def analyze_symbol_impact(
        cls, symbol_name: str, index: WorkspaceIndex, graph: WorkspaceGraph | None = None
    ) -> ImpactReport:
        """Analyze relationship graph to evaluate potential impact of modifying a symbol or file."""
        if graph is None:
            graph = WorkspaceGraph()
            graph.build_from_index(index)

        target_norm = symbol_name.replace("\\", "/").strip()
        file_node: GraphNode | None = None
        symbol_nodes: list[GraphNode] = []

        # 1. Exact file_id or exact file_path match
        for node in graph.nodes.values():
            if node.node_type == "file" and (
                node.file_path == target_norm or node.node_id == f"file:{target_norm}"
            ):
                file_node = node
                break

        # 2. File path ending or filename match
        if not file_node:
            for node in graph.nodes.values():
                if node.node_type == "file" and (
                    node.file_path.endswith("/" + target_norm)
                    or Path(node.file_path).name == target_norm
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

        # 4. Fallback search by substring if no exact match
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
                file_dependents=[],
                affected_files=[],
                explanation=f"Symbol '{symbol_name}' was not found in the indexed workspace. Run `wia search {symbol_name}` to find matching symbols.",
                found=False,
            )

        # 6. Evaluate File Target Impact
        if file_node:
            defining_file = file_node.file_path
            incoming_edges = graph.get_incoming_edges(file_node.node_id)

            file_dependents: list[str] = []
            affected_files: set[str] = set()

            for edge in incoming_edges:
                source_node = graph.nodes.get(edge.source_id)
                if source_node and source_node.node_type == "file":
                    if source_node.file_path and source_node.file_path != file_node.file_path:
                        file_dependents.append(source_node.file_path)
                        affected_files.add(source_node.file_path)

            dep_count = len(affected_files)
            p_lower = defining_file.lower()
            is_presentation = "formatting.py" in p_lower or "cli/formatting" in p_lower

            if dep_count >= 10:
                risk = "MEDIUM" if is_presentation else "HIGH"
            elif dep_count >= 3:
                risk = "MEDIUM"
            elif dep_count > 0:
                risk = "LOW"
            else:
                risk = "LOW"

            explanation = (
                f"Modifying file '{defining_file}' affects {dep_count} consuming workspace module(s). "
                f"Evaluated risk level: {risk}."
            )

            return ImpactReport(
                target_symbol=symbol_name,
                target_type="file",
                defining_file=defining_file,
                risk_level=risk,
                direct_dependents=[],
                file_dependents=sorted(file_dependents),
                affected_files=sorted(list(affected_files)),
                explanation=explanation,
                found=True,
            )

        # 7. Evaluate Symbol Target Impact
        candidates = [f"{s.file_path}::{s.name}" for s in symbol_nodes]
        target_sym = symbol_nodes[0]
        defining_file = target_sym.file_path

        direct_dependents: list[str] = []
        file_dependents: list[str] = []
        affected_files: set[str] = set()

        # Query direct symbol callers (CALLS edges to target symbol)
        sym_incoming = graph.get_incoming_edges(target_sym.node_id)
        for edge in sym_incoming:
            source_node = graph.nodes.get(edge.source_id)
            if source_node and source_node.file_path and source_node.file_path != defining_file:
                caller_str = f"{source_node.file_path} (CALLS {target_sym.name})"
                if caller_str not in direct_dependents:
                    direct_dependents.append(caller_str)
                affected_files.add(source_node.file_path)

        # Query file-level importers of defining file
        def_file_id = f"file:{defining_file}"
        file_incoming = graph.get_incoming_edges(def_file_id)
        for edge in file_incoming:
            source_node = graph.nodes.get(edge.source_id)
            if source_node and source_node.node_type == "file":
                if source_node.file_path and source_node.file_path != defining_file:
                    if source_node.file_path not in file_dependents:
                        file_dependents.append(source_node.file_path)
                    affected_files.add(source_node.file_path)

        dep_count = len(affected_files)
        p_lower = defining_file.lower()
        is_presentation = "formatting.py" in p_lower or "cli/formatting" in p_lower

        if dep_count >= 10:
            risk = "MEDIUM" if is_presentation else "HIGH"
        elif dep_count >= 3:
            risk = "MEDIUM"
        elif dep_count > 0:
            risk = "LOW"
        else:
            risk = "LOW"

        if dep_count > 0:
            if is_presentation:
                explanation = (
                    f"Modifying '{symbol_name}' (defined in '{defining_file}') affects terminal presentation across "
                    f"{dep_count} consuming CLI module(s). Evaluated risk level: {risk}."
                )
            else:
                explanation = (
                    f"Modifying '{symbol_name}' (defined in '{defining_file}') affects {dep_count} workspace "
                    f"component(s) across {len(affected_files)} file(s). Evaluated risk level: {risk}."
                )
        else:
            explanation = (
                f"The symbol '{symbol_name}' is defined in '{defining_file}' but no indexed downstream workspace "
                f"callers or referencing modules were identified. Evaluated risk level: LOW."
            )

        return ImpactReport(
            target_symbol=symbol_name,
            target_type=f"symbol ({target_sym.node_type})",
            defining_file=defining_file,
            risk_level=risk,
            direct_dependents=direct_dependents,
            file_dependents=sorted(file_dependents),
            affected_files=sorted(list(affected_files)),
            explanation=explanation,
            found=True,
            candidates=candidates if len(candidates) > 1 else [],
        )
