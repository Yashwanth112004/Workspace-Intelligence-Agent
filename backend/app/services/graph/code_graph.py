import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict, deque
from sqlmodel import Session, select
from app.models.knowledge import KnowledgeEntity, KnowledgeRelationship, EntityType, RelationshipType, ProvenanceType
from app.models.workspace import FileNode, ASTSymbol

logger = logging.getLogger("wia.graph")

class CodeKnowledgeGraph:
    """
    WIA-Native Code Knowledge Graph.
    Maintains graph entities (nodes) and explicit relationships (edges)
    with algorithms for caller/callee traversal, dependency mapping,
    impact analysis, and architecture exploration.
    """

    def __init__(self, repo_id: str, session: Optional[Session] = None):
        self.repo_id = repo_id
        self.session = session
        
        # In-memory graph indices
        self.entities_by_id: Dict[str, KnowledgeEntity] = {}
        self.entities_by_name: Dict[str, List[KnowledgeEntity]] = defaultdict(list)
        self.entities_by_file: Dict[str, List[KnowledgeEntity]] = defaultdict(list)
        
        # Adjacency lists: source_id -> list of (rel, target_id)
        self.outgoing_edges: Dict[str, List[KnowledgeRelationship]] = defaultdict(list)
        self.incoming_edges: Dict[str, List[KnowledgeRelationship]] = defaultdict(list)

    def add_entity(self, entity: KnowledgeEntity):
        self.entities_by_id[entity.id] = entity
        self.entities_by_name[entity.name].append(entity)
        if entity.file_path:
            self.entities_by_file[entity.file_path].append(entity)
        if self.session:
            self.session.add(entity)

    def add_relationship(self, rel: KnowledgeRelationship):
        self.outgoing_edges[rel.source_id].append(rel)
        self.incoming_edges[rel.target_id].append(rel)
        if self.session:
            self.session.add(rel)

    def build_from_ast_and_files(self, nodes: List[FileNode], symbols: List[ASTSymbol]):
        """Populates the knowledge graph from ingested file nodes and AST symbols."""
        file_entity_map: Dict[str, KnowledgeEntity] = {}

        # 1. Add Directory & File entities
        for n in nodes:
            e_type = EntityType.DIRECTORY.value if n.is_dir else EntityType.FILE.value
            fe = KnowledgeEntity(
                repo_id=self.repo_id,
                entity_type=e_type,
                name=n.name,
                qualified_name=n.relative_path,
                file_path=n.relative_path,
                loc=n.loc_count,
                language=n.language
            )
            self.add_entity(fe)
            file_entity_map[n.relative_path] = fe

        # 2. Add Parent -> Child directory containment relationships
        for n in nodes:
            if n.parent_path and n.parent_path in file_entity_map:
                parent_ent = file_entity_map[n.parent_path]
                child_ent = file_entity_map.get(n.relative_path)
                if child_ent:
                    self.add_relationship(KnowledgeRelationship(
                        repo_id=self.repo_id,
                        source_id=parent_ent.id,
                        target_id=child_ent.id,
                        source_name=parent_ent.name,
                        target_name=child_ent.name,
                        relationship_type=RelationshipType.CONTAINS.value
                    ))

        # 3. Add Symbol entities (Classes, Functions, Methods, Imports)
        symbol_entity_map: Dict[str, KnowledgeEntity] = {}
        for s in symbols:
            e_type = EntityType.CLASS.value if s.symbol_type == "class" else (
                EntityType.FUNCTION.value if s.symbol_type == "function" else EntityType.MODULE.value
            )
            se = KnowledgeEntity(
                repo_id=self.repo_id,
                entity_type=e_type,
                name=s.name,
                qualified_name=f"{s.file_path}::{s.name}",
                file_path=s.file_path,
                start_line=s.start_line,
                end_line=s.end_line,
                signature=s.signature,
                docstring=s.docstring,
                properties={
                    "calls": s.calls,
                    "parameters": s.parameters,
                    "imported_symbols": s.imported_symbols
                }
            )
            self.add_entity(se)
            symbol_entity_map[f"{s.file_path}::{s.name}"] = se

            # Link File -> DEFINES -> Symbol
            if s.file_path in file_entity_map:
                fe = file_entity_map[s.file_path]
                self.add_relationship(KnowledgeRelationship(
                    repo_id=self.repo_id,
                    source_id=fe.id,
                    target_id=se.id,
                    source_name=fe.name,
                    target_name=se.name,
                    relationship_type=RelationshipType.DEFINES.value,
                    source_location=f"{s.file_path}:{s.start_line}-{s.end_line}"
                ))

        # 4. Resolve Function Calls & Import references
        for s in symbols:
            caller_ent = symbol_entity_map.get(f"{s.file_path}::{s.name}")
            if not caller_ent:
                continue

            for call_name in s.calls:
                # Find matching target symbol entities across repo
                matches = self.entities_by_name.get(call_name, [])
                for target_ent in matches:
                    if target_ent.id != caller_ent.id:
                        self.add_relationship(KnowledgeRelationship(
                            repo_id=self.repo_id,
                            source_id=caller_ent.id,
                            target_id=target_ent.id,
                            source_name=caller_ent.name,
                            target_name=target_ent.name,
                            relationship_type=RelationshipType.CALLS.value,
                            source_location=f"{s.file_path}:{s.start_line}-{s.end_line}"
                        ))

            # Imports: File -> IMPORTS -> Module/Symbol
            if s.symbol_type == "import":
                fe = file_entity_map.get(s.file_path)
                if fe:
                    for imp in s.imported_symbols:
                        targets = self.entities_by_name.get(imp, [])
                        for t in targets:
                            self.add_relationship(KnowledgeRelationship(
                                repo_id=self.repo_id,
                                source_id=fe.id,
                                target_id=t.id,
                                source_name=fe.name,
                                target_name=t.name,
                                relationship_type=RelationshipType.IMPORTS.value,
                                source_location=f"{s.file_path}:{s.start_line}-{s.end_line}"
                            ))

    def find_symbol(self, name: str) -> List[KnowledgeEntity]:
        """Finds entity by symbol name or partial match."""
        if name in self.entities_by_name:
            return self.entities_by_name[name]
        return [e for e in self.entities_by_id.values() if name.lower() in e.name.lower()]

    def find_callers(self, entity_name: str) -> List[Tuple[KnowledgeEntity, KnowledgeRelationship]]:
        """Finds all functions/classes that call this entity."""
        targets = self.find_symbol(entity_name)
        callers = []
        for target in targets:
            for rel in self.incoming_edges.get(target.id, []):
                if rel.relationship_type == RelationshipType.CALLS.value:
                    source_ent = self.entities_by_id.get(rel.source_id)
                    if source_ent:
                        callers.append((source_ent, rel))
        return callers

    def find_callees(self, entity_name: str) -> List[Tuple[KnowledgeEntity, KnowledgeRelationship]]:
        """Finds all functions called by this entity."""
        sources = self.find_symbol(entity_name)
        callees = []
        for source in sources:
            for rel in self.outgoing_edges.get(source.id, []):
                if rel.relationship_type == RelationshipType.CALLS.value:
                    target_ent = self.entities_by_id.get(rel.target_id)
                    if target_ent:
                        callees.append((target_ent, rel))
        return callees

    def find_dependencies(self, file_path: str) -> List[KnowledgeEntity]:
        """Returns direct dependencies imported by a given file."""
        file_ent = next((e for e in self.entities_by_id.values() if e.file_path == file_path and e.entity_type == EntityType.FILE.value), None)
        if not file_ent:
            return []
        deps = []
        for rel in self.outgoing_edges.get(file_ent.id, []):
            if rel.relationship_type in (RelationshipType.IMPORTS.value, RelationshipType.DEPENDS_ON.value):
                target = self.entities_by_id.get(rel.target_id)
                if target:
                    deps.append(target)
        return deps

    def find_dependents(self, file_path: str) -> List[KnowledgeEntity]:
        """Returns all files that import or depend on a given file."""
        file_ent = next((e for e in self.entities_by_id.values() if e.file_path == file_path and e.entity_type == EntityType.FILE.value), None)
        if not file_ent:
            return []
        dependents = []
        for rel in self.incoming_edges.get(file_ent.id, []):
            if rel.relationship_type in (RelationshipType.IMPORTS.value, RelationshipType.DEPENDS_ON.value):
                source = self.entities_by_id.get(rel.source_id)
                if source:
                    dependents.append(source)
        return dependents

    def trace_flow(self, entry_symbol_name: str, max_depth: int = 5) -> List[Dict[str, Any]]:
        """Traces execution call flow starting from an entry point."""
        entries = self.find_symbol(entry_symbol_name)
        if not entries:
            return []

        flow = []
        visited = set()
        queue = deque([(entries[0], 0, "Root Entry")])

        while queue and len(flow) < 50:
            current, depth, reason = queue.popleft()
            if current.id in visited or depth > max_depth:
                continue
            visited.add(current.id)

            flow.append({
                "step": len(flow) + 1,
                "depth": depth,
                "symbol": current.name,
                "type": current.entity_type,
                "file": current.file_path,
                "line": current.start_line,
                "signature": current.signature,
                "reason": reason
            })

            # Traverse outgoing calls
            for rel in self.outgoing_edges.get(current.id, []):
                if rel.relationship_type == RelationshipType.CALLS.value:
                    target = self.entities_by_id.get(rel.target_id)
                    if target and target.id not in visited:
                        queue.append((target, depth + 1, f"Called by {current.name}"))

        return flow

    def analyze_impact(self, symbol_or_file: str) -> Dict[str, Any]:
        """Calculates ripple change impact for a symbol or file."""
        targets = self.find_symbol(symbol_or_file)
        if not targets:
            # Check if matching file
            targets = [e for e in self.entities_by_id.values() if e.file_path and symbol_or_file in e.file_path]

        direct_dependents = set()
        indirect_dependents = set()
        affected_files = set()
        affected_callers = set()

        for t in targets:
            affected_files.add(t.file_path)
            for rel in self.incoming_edges.get(t.id, []):
                src = self.entities_by_id.get(rel.source_id)
                if src:
                    direct_dependents.add(src.qualified_name or src.name)
                    if src.file_path:
                        affected_files.add(src.file_path)
                    if rel.relationship_type == RelationshipType.CALLS.value:
                        affected_callers.add(f"{src.name} ({src.file_path}:{src.start_line})")

                    # 2nd hop indirect
                    for ind_rel in self.incoming_edges.get(src.id, []):
                        ind_src = self.entities_by_id.get(ind_rel.source_id)
                        if ind_src:
                            indirect_dependents.add(ind_src.qualified_name or ind_src.name)
                            if ind_src.file_path:
                                affected_files.add(ind_src.file_path)

        return {
            "target": symbol_or_file,
            "matched_entities": [t.name for t in targets],
            "direct_impact_count": len(direct_dependents),
            "indirect_impact_count": len(indirect_dependents),
            "affected_files_count": len(affected_files),
            "direct_dependents": list(direct_dependents)[:20],
            "indirect_dependents": list(indirect_dependents)[:20],
            "affected_callers": list(affected_callers)[:20],
            "affected_files": list(affected_files)
        }

    def get_architecture_graph(self) -> Dict[str, Any]:
        """Returns complete node and edge summary of repository architecture."""
        nodes = []
        for e in self.entities_by_id.values():
            if e.entity_type in (EntityType.DIRECTORY.value, EntityType.FILE.value, EntityType.CLASS.value, EntityType.ENDPOINT.value):
                nodes.append({
                    "id": e.id,
                    "name": e.name,
                    "type": e.entity_type,
                    "file": e.file_path,
                    "loc": e.loc
                })

        edges = []
        for source_id, rels in self.outgoing_edges.items():
            for r in rels:
                edges.append({
                    "source": r.source_id,
                    "target": r.target_id,
                    "type": r.relationship_type,
                    "source_name": r.source_name,
                    "target_name": r.target_name
                })

        return {
            "repo_id": self.repo_id,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "nodes": nodes,
            "edges": edges
        }
