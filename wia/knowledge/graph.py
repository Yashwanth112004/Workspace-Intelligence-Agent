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
        self._edge_index: dict[tuple[str, str, str], GraphEdge] = {}

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
        edge_key = (source_id, target_id, relation_type)
        existing = self._edge_index.get(edge_key)
        if existing is not None:
            if metadata and "imported_symbols" in metadata:
                e_syms = existing.metadata.setdefault("imported_symbols", [])
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
        self._edge_index[edge_key] = edge
        self._adjacency.setdefault(source_id, []).append(edge)
        self._reverse_adjacency.setdefault(target_id, []).append(edge)

    def build_from_index(self, index: WorkspaceIndex) -> None:
        """Build relationship graph from a WorkspaceIndex object."""
        self.nodes.clear()
        self.edges.clear()
        self._adjacency.clear()
        self._reverse_adjacency.clear()
        self._edge_index.clear()

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

        # 2. Process symbol inheritance and internal calls
        for rel_path, rec in index.files.items():
            if rec.indexing_status != "INDEXED":
                continue
            file_id = f"file:{rel_path}"
            symbols = rec.extra_metadata.get("symbols", [])

            for sym in symbols:
                sym_name = sym.get("name", "")
                sym_type = sym.get("symbol_type", "symbol")
                if sym_type == "import" or not sym_name:
                    continue

                sym_id = f"symbol:{rel_path}:{sym_name}"

                # Inheritance edges (INHERITS)
                base_classes = sym.get("base_classes", [])
                for base in base_classes:
                    if base in symbol_file_map:
                        for tgt_fid, tgt_sid, _ in symbol_file_map[base]:
                            if tgt_sid != sym_id:
                                self.add_edge(sym_id, tgt_sid, relation_type="INHERITS")
                    else:
                        base_node_id = f"class:{base}"
                        if base_node_id not in self.nodes:
                            self.add_node(base_node_id, node_type="class", name=base)
                        self.add_edge(sym_id, base_node_id, relation_type="INHERITS")

                # Direct Call edges (CALLS)
                calls = sym.get("calls", [])
                for call_name in calls:
                    short_call = call_name.rsplit(".", 1)[-1]
                    if call_name in symbol_file_map:
                        for tgt_fid, tgt_sid, _ in symbol_file_map[call_name]:
                            if tgt_sid != sym_id:
                                self.add_edge(sym_id, tgt_sid, relation_type="CALLS")
                    elif short_call in symbol_file_map:
                        for tgt_fid, tgt_sid, _ in symbol_file_map[short_call]:
                            if tgt_sid != sym_id:
                                self.add_edge(sym_id, tgt_sid, relation_type="CALLS")

        # 3. Process imports and build directional IMPORTS / CALLS edges
        for rel_path, rec in index.files.items():
            if rec.indexing_status != "INDEXED":
                continue
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

        # 4. Build TESTS relationship edges (test_file -> target_file)
        for rel_path, rec in index.files.items():
            if rec.indexing_status != "INDEXED":
                continue
            is_test = (
                rec.file_type == "Test"
                or Path(rel_path).name.startswith("test_")
                or "test" in rel_path.lower()
            )
            if not is_test:
                continue

            test_file_id = f"file:{rel_path}"
            # Test file imports target file
            for edge in self.get_outgoing_edges(test_file_id):
                if edge.relation_type == "IMPORTS" and edge.target_id.startswith("file:"):
                    target_rec = index.files.get(edge.target_id.replace("file:", ""))
                    if target_rec and target_rec.file_type != "Test":
                        self.add_edge(test_file_id, edge.target_id, relation_type="TESTS")

            # Match naming convention: test_foo.py -> foo.py
            stem = Path(rel_path).stem
            if stem.startswith("test_"):
                target_stem = stem[5:]
                for mod_k, f_id in module_path_map.items():
                    if f_id != test_file_id and (mod_k == target_stem or mod_k.endswith("." + target_stem)):
                        self.add_edge(test_file_id, f_id, relation_type="TESTS")

    def remove_file(self, rel_path: str) -> None:
        """Remove file node and all its defined symbol nodes and connected edges."""
        file_id = f"file:{rel_path}"
        nodes_to_remove = {file_id}

        for node_id, node in list(self.nodes.items()):
            if node.file_path == rel_path or node_id.startswith(f"symbol:{rel_path}:"):
                nodes_to_remove.add(node_id)

        for nid in nodes_to_remove:
            self.nodes.pop(nid, None)
            self._adjacency.pop(nid, None)
            self._reverse_adjacency.pop(nid, None)

        # Clean edges list, edge index, and other adjacency entries
        self.edges = [
            e for e in self.edges
            if e.source_id not in nodes_to_remove and e.target_id not in nodes_to_remove
        ]
        self._edge_index = {
            (e.source_id, e.target_id, e.relation_type): e for e in self.edges
        }
        for src_id, edge_list in list(self._adjacency.items()):
            self._adjacency[src_id] = [e for e in edge_list if e.target_id not in nodes_to_remove]
        for tgt_id, edge_list in list(self._reverse_adjacency.items()):
            self._reverse_adjacency[tgt_id] = [e for e in edge_list if e.source_id not in nodes_to_remove]

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
