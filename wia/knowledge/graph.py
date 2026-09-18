"""Workspace Knowledge Graph modeling code relationships and dependencies."""

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from wia.core.index_model import WorkspaceIndex


@dataclass
class GraphNode:
    """Represents an entity node in the workspace knowledge graph."""

    node_id: str
    node_type: str  # "file", "module", "class", "function", "package"
    name: str
    file_path: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert node to serializable dictionary."""
        return asdict(self)


@dataclass
class GraphEdge:
    """Represents a directional relationship edge between two knowledge nodes."""

    source_id: str
    target_id: str
    relation_type: str  # "IMPORTS", "CALLS", "DEFINES", "EXTENDS", "DEPENDS_ON", "TESTS"
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert edge to serializable dictionary."""
        return asdict(self)


class WorkspaceGraph:
    """In-memory and serializable relationship graph for workspace entities."""

    def __init__(self):
        self.nodes: dict[str, GraphNode] = {}
        self.edges: list[GraphEdge] = []
        self._adjacency: dict[str, list[GraphEdge]] = {}
        self._reverse_adjacency: dict[str, list[GraphEdge]] = {}

    def add_node(
        self, node_id: str, node_type: str, name: str, file_path: str = "", metadata: dict | None = None
    ) -> GraphNode:
        """Add or update a node in the graph."""
        node = GraphNode(
            node_id=node_id,
            node_type=node_type,
            name=name,
            file_path=file_path,
            metadata=metadata or {},
        )
        self.nodes[node_id] = node
        return node

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        confidence: float = 1.0,
        metadata: dict | None = None,
    ) -> None:
        """Add a directional relationship edge between two existing nodes without duplicate edges."""
        # Deduplicate edges between same source, target, and relation_type
        existing = self._adjacency.get(source_id, [])
        for e in existing:
            if e.target_id == target_id and e.relation_type == relation_type:
                if metadata and "imported_symbols" in metadata:
                    e_syms = e.metadata.setdefault("imported_symbols", [])
                    for s in metadata["imported_symbols"]:
                        if s not in e_syms:
                            e_syms.append(s)
                return

        edge = GraphEdge(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            confidence=confidence,
            metadata=metadata or {},
        )
        self.edges.append(edge)
        self._adjacency.setdefault(source_id, []).append(edge)
        self._reverse_adjacency.setdefault(target_id, []).append(edge)

    def build_from_index(self, index: WorkspaceIndex) -> None:
        """Build relationship graph from a WorkspaceIndex object."""
        self.nodes.clear()
        self.edges.clear()
        self._adjacency.clear()
        self._reverse_adjacency.clear()

        STD_LIB_MODULES = {
            "sys", "os", "time", "datetime", "pathlib", "json", "html", "dataclasses",
            "typing", "subprocess", "hashlib", "re", "math", "collections", "itertools",
            "functools", "enum", "copy", "tempfile", "shutil", "argparse", "sqlite3",
            "ast", "inspect", "logging"
        }

        # 1. Map file paths and defined symbols for fast module and symbol import resolution
        module_path_map: dict[str, str] = {}
        symbol_file_map: dict[str, list[tuple[str, str, str]]] = {}  # symbol_key -> list of (file_id, sym_id, qual_name)

        for rel_path, rec in index.files.items():
            if rec.indexing_status != "INDEXED":
                continue
            file_id = f"file:{rel_path}"
            self.add_node(file_id, node_type="file", name=Path(rel_path).name, file_path=rel_path)

            norm_p = rel_path.replace("\\", "/")
            stem_p = norm_p.rsplit(".", 1)[0]
            dot_p = stem_p.replace("/", ".")
            name_stem = Path(rel_path).stem

            module_path_map[dot_p] = file_id
            module_path_map[stem_p] = file_id
            module_path_map[norm_p] = file_id
            module_path_map[name_stem] = file_id
            module_path_map[Path(rel_path).name] = file_id

            # Register defined symbols
            symbols = rec.extra_metadata.get("symbols", [])
            for sym in symbols:
                sym_name = sym.get("name", "")
                sym_type = sym.get("symbol_type", "symbol")
                if sym_type != "import" and sym_name:
                    sym_id = f"symbol:{rel_path}:{sym_name}"
                    qual_name = f"{dot_p}.{sym_name}"
                    entry = (file_id, sym_id, qual_name)

                    symbol_file_map.setdefault(sym_name, []).append(entry)
                    symbol_file_map.setdefault(qual_name, []).append(entry)

                    self.add_node(
                        sym_id,
                        node_type=sym_type,
                        name=sym_name,
                        file_path=rel_path,
                        metadata={"line_number": sym.get("line_number", 0)},
                    )
                    self.add_edge(file_id, sym_id, relation_type="DEFINES")

        # 2. Process imports and build directional IMPORTS / CALLS edges
        for rel_path, rec in index.files.items():
            file_id = f"file:{rel_path}"
            symbols = rec.extra_metadata.get("symbols", [])
            raw_imports = set(rec.extra_metadata.get("imports", []))
            for sym in symbols:
                if sym.get("symbol_type") == "import" and sym.get("name"):
                    raw_imports.add(sym.get("name"))

            for imp_name in raw_imports:
                if not imp_name:
                    continue
                imp_clean = imp_name.strip()
                short_name = imp_clean.rsplit(".", 1)[-1]
                imp_dot = imp_clean.replace("/", ".")
                base_mod = imp_dot.split(".")[0]
                matched_symbol = False

                # Check if import matches a defined symbol
                for sym_key in (imp_clean, short_name):
                    if sym_key in symbol_file_map:
                        candidates = symbol_file_map[sym_key]
                        for target_file_id, target_sym_id, qual_n in candidates:
                            if target_file_id != file_id:
                                # Check if import prefix matches target file path
                                if imp_clean == short_name or imp_dot.startswith(qual_n.rsplit(".", 1)[0]):
                                    self.add_edge(
                                        file_id,
                                        target_file_id,
                                        relation_type="IMPORTS",
                                        metadata={"imported_symbols": [short_name]},
                                    )
                                    self.add_edge(
                                        file_id,
                                        target_sym_id,
                                        relation_type="CALLS",
                                        metadata={"imported_symbol": short_name},
                                    )
                                    matched_symbol = True
                        if matched_symbol:
                            break

                if matched_symbol:
                    continue

                # Check if import matches a workspace module/file
                target_file_id = None
                for mod_key, f_id in module_path_map.items():
                    if imp_dot == mod_key or imp_dot.startswith(mod_key + ".") or mod_key.endswith("." + imp_dot):
                        target_file_id = f_id
                        break

                if target_file_id and target_file_id != file_id:
                    self.add_edge(file_id, target_file_id, relation_type="IMPORTS")
                else:
                    node_t = "stdlib_module" if base_mod in STD_LIB_MODULES else "external_package"
                    import_id = f"external:{imp_clean}"
                    if import_id not in self.nodes:
                        self.add_node(import_id, node_type=node_t, name=imp_clean)
                    self.add_edge(file_id, import_id, relation_type="IMPORTS")

    def get_outgoing_edges(self, node_id: str) -> list[GraphEdge]:
        """Return all outgoing edges from target node."""
        return self._adjacency.get(node_id, [])

    def get_incoming_edges(self, node_id: str) -> list[GraphEdge]:
        """Return all incoming edges pointing to target node."""
        return self._reverse_adjacency.get(node_id, [])

    def find_nodes_by_name(self, name: str) -> list[GraphNode]:
        """Find graph nodes by exact or partial name match."""
        name_lower = name.lower()
        return [node for node in self.nodes.values() if name_lower in node.name.lower()]

    def to_dict(self) -> dict:
        """Serialize graph to dictionary payload."""
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
        }
