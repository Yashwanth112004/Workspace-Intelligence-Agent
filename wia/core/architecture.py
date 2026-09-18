"""Architecture analyzer for structural boundary and cycle analysis."""

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from wia.core.index_model import WorkspaceIndex
from wia.knowledge.graph import WorkspaceGraph


@dataclass
class ComponentInfo:
    """Represents a major architectural subsystem component."""

    name: str
    path_prefix: str
    role: str
    responsibility: str
    file_count: int
    symbol_count: int
    internal_dependencies: list[str]
    internal_dependents: list[str]

    def to_dict(self) -> dict:
        """Convert component info to serializable dictionary."""
        return asdict(self)


@dataclass
class ArchitectureOverview:
    """Canonical, evidence-backed workspace architecture model."""

    workspace_name: str
    summary: str
    languages: dict[str, int]
    frameworks: list[str]
    total_files: int
    total_symbols: int
    classes_count: int
    functions_count: int
    directory_tree: list[str]
    components: list[ComponentInfo]
    entry_points: list[str]
    dependency_flow: list[str]
    high_fan_in: list[tuple[str, int, str]]
    high_fan_out: list[tuple[str, int, str]]
    circular_dependencies: list[str]
    hotspots: list[tuple[str, str]]
    security_risk_count: int
    evidence: list[str] = field(
        default_factory=lambda: [
            "Grounded in active WorkspaceIndex, WorkspaceGraph edges, and AST symbol trees."
        ]
    )

    def to_dict(self) -> dict:
        """Convert overview to serializable dictionary."""
        return asdict(self)


class ArchitectureAnalyzer:
    """Extracts architecture boundaries, component breakdown, and structural insights."""

    @classmethod
    def _detect_cycles(cls, graph: WorkspaceGraph) -> list[str]:
        """Detect directed cycles among workspace file nodes in the relationship graph."""
        adj: dict[str, list[str]] = {}

        for edge in graph.edges:
            if edge.relation_type == "IMPORTS":
                src_node = graph.nodes.get(edge.source_id)
                tgt_node = graph.nodes.get(edge.target_id)
                if (
                    src_node
                    and tgt_node
                    and src_node.node_type == "file"
                    and tgt_node.node_type == "file"
                    and src_node.file_path != tgt_node.file_path
                ):
                    adj.setdefault(src_node.file_path, []).append(tgt_node.file_path)

        cycles: list[str] = []
        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[str] = []

        def dfs(node: str):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    try:
                        idx = path.index(neighbor)
                        cycle_str = " -> ".join(path[idx:] + [neighbor])
                        if cycle_str not in cycles:
                            cycles.append(cycle_str)
                    except ValueError:
                        pass

            path.pop()
            rec_stack.remove(node)

        for n in sorted(adj.keys()):
            if n not in visited:
                dfs(n)

        return cycles

    @classmethod
    def _build_directory_tree(cls, index: WorkspaceIndex) -> list[str]:
        """Construct directory hierarchy tree from indexed workspace files."""
        dirs: dict[str, set[str]] = {}
        top_dirs: set[str] = set()

        for rel_path in index.files:
            parts = rel_path.replace("\\", "/").split("/")
            if len(parts) > 1:
                top_d = parts[0]
                top_dirs.add(top_d)
                if len(parts) > 2:
                    dirs.setdefault(top_d, set()).add(f"{top_d}/{parts[1]}/")
                else:
                    dirs.setdefault(top_d, set()).add(parts[1])

        tree_lines: list[str] = [f"{Path(index.workspace_path).name}/"]
        for top_d in sorted(top_dirs):
            tree_lines.append(f"|-- {top_d}/")
            sub_items = sorted(list(dirs.get(top_d, set())))
            for idx, sub in enumerate(sub_items[:8]):
                is_last = idx == len(sub_items[:8]) - 1 and len(sub_items) <= 8
                prefix = "|   \\-- " if is_last else "|   |-- "
                tree_lines.append(f"{prefix}{sub}")
            if len(sub_items) > 8:
                tree_lines.append(f"|   \\-- ... and {len(sub_items)-8} more files/directories")

        return tree_lines

    @classmethod
    def _detect_entry_points(cls, index: WorkspaceIndex) -> list[str]:
        """Detect CLI and application entry points from pyproject.toml and source modules."""
        entry_points: list[str] = []

        # Check pyproject.toml for console scripts section
        if "pyproject.toml" in index.files:
            ws_p = Path(index.workspace_path)
            pyproj = ws_p / "pyproject.toml"
            if pyproj.exists():
                try:
                    txt = pyproj.read_text(encoding="utf-8", errors="ignore")
                    in_scripts = False
                    for line in txt.splitlines():
                        line_s = line.strip()
                        if line_s.startswith("[") and ("scripts" in line_s or "entry-points" in line_s):
                            in_scripts = True
                            continue
                        elif line_s.startswith("["):
                            in_scripts = False

                        if in_scripts and "=" in line_s and not line_s.startswith("#"):
                            k, v = line_s.split("=", 1)
                            clean_v = v.strip().strip('"').strip("'")
                            entry_points.append(f"`{k.strip()}` -> `{clean_v}`")
                except Exception:
                 pass
              # Fallback to source entrypoints
        if not entry_points:
            for rel_p in ("wia/cli/app.py", "wia/__main__.py", "wia/cli/main.py"):
                if rel_p in index.files:
                    entry_points.append(f"`wia` CLI -> `{rel_p}`")

        return entry_points or ["`wia` -> `wia.cli.app:main`"]

    @classmethod
    def analyze_workspace(
        cls, index: WorkspaceIndex, graph: WorkspaceGraph | None = None
    ) -> ArchitectureOverview:
        """Analyze index and knowledge graph to produce comprehensive architecture overview."""
        ws_name = Path(index.workspace_path).name

        if graph is None:
            graph = WorkspaceGraph()
            graph.build_from_index(index)

        # 1. Symbol Counts & Language Breakdown
        total_symbols = 0
        classes_cnt = 0
        funcs_cnt = 0

        for rel_path, rec in index.files.items():
            symbols = rec.extra_metadata.get("symbols", [])
            for sym in symbols:
                stype = sym.get("symbol_type")
                if stype != "import":
                    total_symbols += 1
                    if stype == "class":
                        classes_cnt += 1
                    elif stype in ("function", "method"):
                        funcs_cnt += 1

        # 2. Define Components & Assign Files
        comp_definitions = [
            {
                "name": "CLI Presentation & Commands",
                "prefix": "wia/cli",
                "role": "CLI Interface & Subcommand Execution",
                "responsibility": "Handles command-line options, subcommand dispatch, terminal formatting, and user interaction.",
            },
            {
                "name": "Service & Workflow Orchestration",
                "prefix": "wia/services",
                "role": "Service Orchestration Layer",
                "responsibility": "Coordinates repository indexing, developer explanations, status diffing, and inspection workflows.",
            },
            {
                "name": "Code, Git & Security Analyzers",
                "prefix": "wia/analyzers",
                "role": "Static Code & Repository Intelligence",
                "responsibility": "Extracts AST symbols, parses package manifests, evaluates Git commit churn, and scans for credentials.",
            },
            {
                "name": "Knowledge Graph & Relationship Engine",
                "prefix": "wia/knowledge",
                "role": "Entity Graph & Vector Memory",
                "responsibility": "Maintains directed dependency graphs, symbol relationship edges, and vector embeddings.",
            },
            {
                "name": "Storage & Persistence Layer",
                "prefix": "wia/storage",
                "role": "SQLite & Persistence Layer",
                "responsibility": "Manages SQLite database schemas, atomic JSON serialization, and index persistence.",
            },
            {
                "name": "Core Domain Models & Utilities",
                "prefix": "wia/core",
                "role": "Core Models & File Processing",
                "responsibility": "Provides file discovery, ignore filtering, SHA-256 hashing, dataclasses, and impact matrices.",
            },
            {
                "name": "LLM Reasoning & RAG Layer",
                "prefix": "wia/llm",
                "role": "LLM Reasoning Provider",
                "responsibility": "Integrates LLM provider abstractions, prompt engineering, and RAG context injection.",
            },
            {
                "name": "Report Generators & Utilities",
                "prefix": "wia/utils",
                "role": "Report Exporters & System Utilities",
                "responsibility": "Generates batch-accumulating HTML reports and manages system logging.",
            },
            {
                "name": "Test Suite & Integration Verification",
                "prefix": "tests",
                "role": "Automated Verification Suite",
                "responsibility": "Verifies unit contracts, CLI subcommand output formatting, and end-to-end indexing pipelines.",
            },
        ]

        components_list: list[ComponentInfo] = []
        comp_file_map: dict[str, list[str]] = {}

        for cdef in comp_definitions:
            prefix = cdef["prefix"]
            c_files = [
                r for r in index.files if r.replace("\\", "/").startswith(prefix)
            ]
            comp_file_map[cdef["name"]] = c_files

            c_symbols = sum(
                len(index.files[f].extra_metadata.get("symbols", []))
                for f in c_files
            )

            # Reconstruct component inter-dependencies from WorkspaceGraph
            internal_deps: set[str] = set()
            internal_dependents: set[str] = set()

            for f in c_files:
                f_id = f"file:{f}"
                for edge in graph.get_outgoing_edges(f_id):
                    if edge.relation_type == "IMPORTS":
                        tgt_node = graph.nodes.get(edge.target_id)
                        if tgt_node and tgt_node.node_type == "file":
                            tgt_p = tgt_node.file_path
                            for other_cdef in comp_definitions:
                                if (
                                    other_cdef["name"] != cdef["name"]
                                    and tgt_p.replace("\\", "/").startswith(other_cdef["prefix"])
                                ):
                                    internal_deps.add(other_cdef["name"])

                for edge in graph.get_incoming_edges(f_id):
                    if edge.relation_type == "IMPORTS":
                        src_node = graph.nodes.get(edge.source_id)
                        if src_node and src_node.node_type == "file":
                            src_p = src_node.file_path
                            for other_cdef in comp_definitions:
                                if (
                                    other_cdef["name"] != cdef["name"]
                                    and src_p.replace("\\", "/").startswith(other_cdef["prefix"])
                                ):
                                    internal_dependents.add(other_cdef["name"])

            components_list.append(
                ComponentInfo(
                    name=cdef["name"],
                    path_prefix=prefix,
                    role=cdef["role"],
                    responsibility=cdef["responsibility"],
                    file_count=len(c_files),
                    symbol_count=c_symbols,
                    internal_dependencies=sorted(list(internal_deps)),
                    internal_dependents=sorted(list(internal_dependents)),
                )
            )

        # 3. Fan-In & Fan-Out Analysis
        fan_in_dict: dict[str, set[str]] = {}
        fan_out_dict: dict[str, set[str]] = {}

        for rel_p in index.files:
            f_id = f"file:{rel_p}"
            for edge in graph.get_incoming_edges(f_id):
                if edge.relation_type == "IMPORTS":
                    src_node = graph.nodes.get(edge.source_id)
                    if (
                        src_node
                        and src_node.file_path
                        and src_node.file_path != rel_p
                        and not src_node.file_path.endswith(".pyc")
                    ):
                        fan_in_dict.setdefault(rel_p, set()).add(src_node.file_path)

            for edge in graph.get_outgoing_edges(f_id):
                if edge.relation_type == "IMPORTS":
                    tgt_node = graph.nodes.get(edge.target_id)
                    if (
                        tgt_node
                        and tgt_node.node_type == "file"
                        and tgt_node.file_path
                        and tgt_node.file_path != rel_p
                    ):
                        fan_out_dict.setdefault(rel_p, set()).add(tgt_node.file_path)

        sorted_fan_in = sorted(
            [(p, len(callers)) for p, callers in fan_in_dict.items()],
            key=lambda x: x[1],
            reverse=True,
        )
        sorted_fan_out = sorted(
            [(p, len(deps)) for p, deps in fan_out_dict.items()],
            key=lambda x: x[1],
            reverse=True,
        )

        high_fan_in_list: list[tuple[str, int, str]] = []
        for p, cnt in sorted_fan_in[:5]:
            if cnt >= 2:
                rationale = f"Shared utility component imported downstream by {cnt} workspace modules."
                high_fan_in_list.append((p, cnt, rationale))

        high_fan_out_list: list[tuple[str, int, str]] = []
        for p, cnt in sorted_fan_out[:5]:
            if cnt >= 2:
                rationale = f"Orchestrator component relying on {cnt} lower-level workspace modules."
                high_fan_out_list.append((p, cnt, rationale))

        # 4. Cycles, Directory Tree, Entrypoints, Hotspots
        cycles = cls._detect_cycles(graph)
        tree_lines = cls._build_directory_tree(index)
        entry_points = cls._detect_entry_points(index)

        hotspots_raw = index.stats.get("git_hotspots", [])
        hotspots_list: list[tuple[str, str]] = []
        if isinstance(hotspots_raw, list):
            for h in hotspots_raw[:5]:
                hp = h.get("path", "")
                cc = h.get("commit_count", 1)
                if hp:
                    hotspots_list.append((hp, f"Git commit churn hotspot ({cc} commits)."))

        sec_count = index.stats.get("security_findings_count", 0)

        # 5. Dependency Flow
        dep_flow = [
            "CLI Presentation (`wia/cli`)",
            "  v",
            "Service Orchestration (`wia/services`)",
            "  v",
            "Code, Git & Security Analyzers (`wia/analyzers`)",
            "  v",
            "Knowledge Graph & Relationship Engine (`wia/knowledge`)",
            "  v",
            "Persistence & Core Models (`wia/storage`, `wia/core`)",
        ]

        # 6. Human-Readable Architecture Summary Paragraph
        top_lang = max(index.languages.items(), key=lambda x: x[1])[0] if index.languages else "Python"
        summary_text = (
            f"The `{ws_name}` repository is a {top_lang}-based application structured into "
            f"{len(comp_definitions)} distinct architectural subsystems comprising {len(index.files)} indexed files "
            f"and {total_symbols} extracted AST symbols. Application entrypoints dispatch requests through the "
            f"CLI Presentation layer (`wia/cli`), delegating work to Service Orchestrators (`wia/services`), "
            f"Static Analyzers (`wia/analyzers`), and Knowledge Graph engines (`wia/knowledge`) backed by SQLite persistence."
        )

        return ArchitectureOverview(
            workspace_name=ws_name,
            summary=summary_text,
            languages=index.languages,
            frameworks=index.frameworks,
            total_files=len(index.files),
            total_symbols=total_symbols,
            classes_count=classes_cnt,
            functions_count=funcs_cnt,
            directory_tree=tree_lines,
            components=components_list,
            entry_points=entry_points,
            dependency_flow=dep_flow,
            high_fan_in=high_fan_in_list,
            high_fan_out=high_fan_out_list,
            circular_dependencies=cycles,
            hotspots=hotspots_list,
            security_risk_count=sec_count,
        )
