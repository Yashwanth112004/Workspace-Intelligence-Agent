"""Standalone HTML workspace report generator for WIA — Developer Intelligence Narrative Engine."""

import html
import json
from pathlib import Path
from typing import Any
from wia.analyzers.dependency.conflict_detector import ConflictDetector
from wia.analyzers.dependency.manifest_parser import ManifestParser
from wia.analyzers.git.git_analyzer import GitAnalyzer
from wia.analyzers.security.secret_scanner import SecretScanner
from wia.core.index_model import WorkspaceIndex
from wia.core.project_commands import ProjectCommandDetector
from wia.knowledge.graph import WorkspaceGraph
from wia.services.explanation_service import ExplanationService


def _safe_json_embed(obj: Any) -> str:
    """Safely serialize data to JSON for embedding inside HTML <script> tags."""
    raw = json.dumps(obj, default=str)
    # Prevent premature script tag termination and HTML injection
    return raw.replace("</script>", r"<\/script>").replace("<!--", r"<\!--")


class ReportGenerator:
    """Generates clean, developer-focused, batch-accumulating workspace intelligence narrative reports."""

    @classmethod
    def export_report_json(
        cls,
        index: WorkspaceIndex,
        output_path: str | Path | None = None,
        files_data: list[dict] | None = None,
        deps: list | None = None,
        git_hotspots: list | None = None,
        security_findings: list | None = None,
    ) -> Path:
        """Export structured workspace intelligence payload to JSON sidecar file."""
        ws_path = Path(index.workspace_path).resolve()
        target = (
            Path(output_path)
            if output_path
            else ws_path / ".wia" / "report_data.json"
        )
        target.parent.mkdir(parents=True, exist_ok=True)

        if files_data is None:
            graph = WorkspaceGraph()
            graph.build_from_index(index)
            files_data = []
            for rel_path, rec in index.files.items():
                if rec.indexing_status != "INDEXED":
                    continue
                expl = ExplanationService.explain_file_structured(rel_path, index, graph)
                files_data.append(expl)

        if deps is None:
            deps = ManifestParser.parse_workspace_manifests(ws_path)
        if git_hotspots is None:
            git_hotspots = GitAnalyzer.get_file_hotspots(ws_path, top_n=15)
        if security_findings is None:
            security_findings = SecretScanner.scan_workspace(ws_path)

        payload = {
            "workspace_name": ws_path.name,
            "workspace_path": str(ws_path),
            "indexed_at": index.indexed_at,
            "index_version": index.index_version,
            "wia_version": index.wia_version,
            "stats": index.stats,
            "languages": index.languages,
            "frameworks": index.frameworks,
            "batches": [b.to_dict() for b in index.batches],
            "files": files_data,
            "dependencies": [d.to_dict() for d in deps],
            "git_hotspots": [
                gh.to_dict() if hasattr(gh, "to_dict") else dict(gh)
                for gh in git_hotspots
            ],
            "security_findings": [s.to_dict() for s in security_findings],
        }
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return target

    @classmethod
    def _detect_project_commands(
        cls, ws_path: Path, index: WorkspaceIndex, files_data: list[dict]
    ) -> list[dict]:
        """Detect runnable developer commands (install, run, test, build, lint) from workspace manifests."""
        return ProjectCommandDetector.detect_commands(ws_path, index=index, files_data=files_data)

    @classmethod
    def _build_graph_payload(
        cls,
        index: WorkspaceIndex,
        graph: WorkspaceGraph | None = None,
        files_data: list[dict] | None = None,
        deps: list | None = None,
        conflicts: list | None = None,
    ) -> dict:
        """Construct a comprehensive graph payload with visualization ranking and cycle detection.

        NOTE: 'vis_rank' (0 to 4+) and 'vis_score' are computed strictly for UI layout
        hierarchy and visual density management. They are completely separate from WIA's
        semantic impact analysis and security risk calculations.
        """
        if graph is None:
            graph = WorkspaceGraph()
            graph.build_from_index(index)
        if files_data is None:
            files_data = []
        if deps is None:
            deps = []
        if conflicts is None:
            conflicts = []

        file_meta_map = {f["file_path"]: f for f in files_data}
        conflict_pkg_map = {c.package_name.lower(): c for c in conflicts}

        nodes_list: list[dict] = []
        edges_list: list[dict] = []
        node_id_set: set[str] = set()

        def add_node(nid: str, ntype: str, label: str, file_p: str = "", extra: dict | None = None):
            if nid in node_id_set:
                return
            node_id_set.add(nid)
            meta = extra or {}
            nodes_list.append({
                "id": nid,
                "type": ntype,
                "label": label,
                "file_path": file_p,
                "metadata": meta,
            })

        # 1. Identify Target / Primary Entrypoints
        entry_paths = {
            f["file_path"] for f in files_data
            if any(k in f.get("role", "").lower() for k in ("entry", "cli", "main", "app", "server", "controller", "router"))
        }
        if not entry_paths and files_data:
            entry_paths = {files_data[0]["file_path"]}

        # 2. Add File Nodes from indexed files
        for rel_p, rec in index.files.items():
            if rec.indexing_status != "INDEXED":
                continue
            fid = f"file:{rel_p}"
            fmeta = file_meta_map.get(rel_p, {})
            is_target = rel_p in entry_paths
            add_node(
                nid=fid,
                ntype="file",
                label=Path(rel_p).name,
                file_p=rel_p,
                extra={
                    "is_target": is_target,
                    "language": rec.language,
                    "role": fmeta.get("role", "Component"),
                    "purpose": fmeta.get("purpose", ""),
                    "risk": fmeta.get("impact_risk_level", "LOW"),
                    "risk_explanation": fmeta.get("impact_explanation", ""),
                    "symbol_count": len(rec.extra_metadata.get("symbols", [])),
                    "symbols": [
                        {"name": s.get("name", ""), "type": s.get("symbol_type", "symbol"), "line": s.get("line_number", 0), "doc": s.get("docstring", "")}
                        for s in rec.extra_metadata.get("symbols", []) if s.get("symbol_type") != "import"
                    ],
                    "direct_dependents": fmeta.get("impact_direct_dependents", []),
                },
            )

        # 3. Add Symbol Nodes and graph knowledge entities
        for g_nid, g_node in graph.nodes.items():
            if g_nid.startswith("file:"):
                continue  # already added
            ntype = g_node.node_type
            fpath = g_node.file_path
            fmeta = file_meta_map.get(fpath, {})
            add_node(
                nid=g_nid,
                ntype=ntype,
                label=g_node.name,
                file_p=fpath,
                extra={
                    "is_target": False,
                    "line_number": g_node.metadata.get("line_number", 0),
                    "parent_file": fpath,
                    "role": fmeta.get("role", ""),
                    "risk": fmeta.get("impact_risk_level", "LOW"),
                },
            )

        # 4. Add Manifest and External Package Nodes
        for d in deps:
            pkg_name = getattr(d, "name", getattr(d, "package_name", ""))
            m_path = getattr(d, "manifest_path", "manifest")
            eco = getattr(d, "ecosystem", "generic")
            dtype = getattr(d, "dependency_type", "runtime")
            has_conf = pkg_name.lower() in conflict_pkg_map
            conf_obj = conflict_pkg_map.get(pkg_name.lower())

            m_id = f"manifest:{m_path}"
            add_node(m_id, ntype="manifest", label=Path(m_path).name, file_p=m_path, extra={"is_target": False, "ecosystem": eco})

            pkg_id = f"pkg:{m_path}:{pkg_name}"
            add_node(
                pkg_id,
                ntype="package",
                label=pkg_name,
                file_p=m_path,
                extra={
                    "is_target": False,
                    "version": getattr(d, "version_spec", getattr(d, "specifier", "*")),
                    "ecosystem": eco,
                    "dep_type": dtype,
                    "has_conflict": has_conf,
                    "conflict_reason": conf_obj.reason if conf_obj else "",
                },
            )

        # 5. Populate Graph Edges from WorkspaceGraph
        for edge in graph.edges:
            src = edge.source_id
            tgt = edge.target_id
            rel = edge.relation_type
            if src in node_id_set and tgt in node_id_set:
                edges_list.append({
                    "source": src,
                    "target": tgt,
                    "relation": rel,
                    "confidence": edge.confidence,
                    "metadata": edge.metadata or {},
                })

        # 6. Add Manifest -> Package DEPENDS_ON edges
        for d in deps:
            pkg_name = getattr(d, "name", getattr(d, "package_name", ""))
            m_path = getattr(d, "manifest_path", "manifest")
            m_id = f"manifest:{m_path}"
            pkg_id = f"pkg:{m_path}:{pkg_name}"
            if m_id in node_id_set and pkg_id in node_id_set:
                edges_list.append({
                    "source": m_id,
                    "target": pkg_id,
                    "relation": "DEPENDS_ON",
                    "confidence": 1.0,
                    "metadata": {},
                })

        # 7. Adjacency, Degrees & Cycle Detection
        adj: dict[str, list[str]] = {n["id"]: [] for n in nodes_list}
        rev_adj: dict[str, list[str]] = {n["id"]: [] for n in nodes_list}
        node_rel_types: dict[str, set[str]] = {n["id"]: set() for n in nodes_list}

        for e in edges_list:
            s, t, r = e["source"], e["target"], e["relation"]
            if s in adj and t in adj:
                adj[s].append(t)
                rev_adj[t].append(s)
                node_rel_types[s].add(r)
                node_rel_types[t].add(r)

        visited: dict[str, int] = {}
        cycles_detected: list[list[str]] = []
        path_stack: list[str] = []

        def dfs_cycle(u: str):
            visited[u] = 1
            path_stack.append(u)
            for v in adj.get(u, []):
                if visited.get(v, 0) == 1:
                    try:
                        idx = path_stack.index(v)
                        cycle_path = path_stack[idx:] + [v]
                        cycles_detected.append(cycle_path)
                    except ValueError:
                        cycles_detected.append([u, v, u])
                elif visited.get(v, 0) == 0:
                    dfs_cycle(v)
            path_stack.pop()
            visited[u] = 2

        for node in nodes_list:
            nid = node["id"]
            if visited.get(nid, 0) == 0:
                dfs_cycle(nid)

        is_dag = len(cycles_detected) == 0

        # 8. Deterministic Visualization Ranking Algorithm
        # Target nodes: Rank 0
        # Direct dependencies/callers (1-hop): Rank 1
        # Secondary dependencies (2-hop): Rank 2
        # High-connectivity supporting nodes: Rank 3
        # Transitive / peripheral nodes: Rank 4
        target_ids = [n["id"] for n in nodes_list if n["metadata"].get("is_target")]
        if not target_ids and nodes_list:
            target_ids = [nodes_list[0]["id"]]
            nodes_list[0]["metadata"]["is_target"] = True

        # Compute shortest hop distance from target set
        distance_map: dict[str, int] = {}
        queue = []
        for tid in target_ids:
            distance_map[tid] = 0
            queue.append(tid)

        head = 0
        while head < len(queue):
            curr = queue[head]
            head += 1
            curr_dist = distance_map[curr]
            neighbors = adj.get(curr, []) + rev_adj.get(curr, [])
            for nxt in neighbors:
                if nxt not in distance_map:
                    distance_map[nxt] = curr_dist + 1
                    queue.append(nxt)

        for node in nodes_list:
            nid = node["id"]
            in_deg = len(rev_adj.get(nid, []))
            out_deg = len(adj.get(nid, []))
            tot_deg = in_deg + out_deg
            num_rels = len(node_rel_types.get(nid, set()))
            dist = distance_map.get(nid, 99)

            if node["metadata"].get("is_target"):
                v_rank = 0
                v_label = "TARGET"
                v_score = 1000 + tot_deg
            elif dist == 1:
                v_rank = 1
                v_label = "DIRECT"
                v_score = 500 + tot_deg * 5 + num_rels * 10
            elif dist == 2:
                v_rank = 2
                v_label = "SECONDARY"
                v_score = 250 + tot_deg * 3 + num_rels * 5
            elif tot_deg >= 4 or in_deg >= 3:
                v_rank = 3
                v_label = "CORE SUPPORT"
                v_score = 150 + tot_deg * 4
            else:
                v_rank = 4
                v_label = "PERIPHERAL"
                v_score = 50 + tot_deg

            node["vis_rank"] = v_rank
            node["vis_rank_label"] = v_label
            node["vis_score"] = v_score
            node["metadata"]["in_degree"] = in_deg
            node["metadata"]["out_degree"] = out_deg
            node["metadata"]["total_degree"] = tot_deg

        # Rank Edges for visual hierarchy
        node_rank_map = {n["id"]: n["vis_rank"] for n in nodes_list}
        for edge in edges_list:
            s_rank = node_rank_map.get(edge["source"], 4)
            t_rank = node_rank_map.get(edge["target"], 4)
            min_r = min(s_rank, t_rank)
            if min_r == 0:
                edge["edge_priority"] = 1  # Target - Direct
            elif min_r <= 2:
                edge["edge_priority"] = 2  # Secondary / Core
            else:
                edge["edge_priority"] = 3  # Peripheral

        direct_count = sum(1 for n in nodes_list if n["vis_rank"] == 1)
        indirect_count = sum(1 for n in nodes_list if n["vis_rank"] >= 2)
        high_conn_count = sum(1 for n in nodes_list if n["vis_rank"] == 3)
        peripheral_count = sum(1 for n in nodes_list if n["vis_rank"] >= 4)

        summary_dict = {
            "total_nodes": len(nodes_list),
            "total_edges": len(edges_list),
            "cycle_count": len(cycles_detected),
            "direct_count": direct_count,
            "indirect_count": indirect_count,
            "high_connectivity_count": high_conn_count,
            "peripheral_count": peripheral_count,
            "files_count": sum(1 for n in nodes_list if n["type"] == "file"),
            "symbols_count": sum(1 for n in nodes_list if n["type"] in ("class", "function", "method", "symbol")),
            "packages_count": sum(1 for n in nodes_list if n["type"] == "package"),
        }

        return {
            "is_dag": is_dag,
            "cycle_count": len(cycles_detected),
            "cycles": cycles_detected[:12],
            "nodes": nodes_list,
            "edges": edges_list,
            "summary": summary_dict,
            "metrics": summary_dict,
        }

    @classmethod
    def generate_html_report(
        cls, index: WorkspaceIndex, output_path: str | Path | None = None
    ) -> Path:
        """Generate a clean, developer-focused HTML narrative report file for the workspace index."""
        target_file = (
            Path(output_path)
            if output_path
            else Path(index.workspace_path) / "wia-report.html"
        )

        ws_path = Path(index.workspace_path).resolve()
        ws_name = html.escape(ws_path.name)
        version = html.escape(index.index_version)
        wia_ver = html.escape(index.wia_version)

        # Build WorkspaceGraph
        graph = WorkspaceGraph()
        graph.build_from_index(index)

        # Basic Counters
        total_discovered = index.stats.get("total_discovered", len(index.files))
        total_indexed = len(index.get_indexed_files())
        total_ignored = index.stats.get("total_ignored", len(index.files) - total_indexed)
        total_symbols = sum(
            len(f.extra_metadata.get("symbols", [])) for f in index.files.values()
        )

        # Batches
        batches = index.batches
        completed_batches = [b for b in batches if b.status == "COMPLETED"]
        running_batches = [b for b in batches if b.status == "RUNNING"]
        pending_batches = [b for b in batches if b.status == "PENDING"]
        failed_batches = [b for b in batches if b.status == "FAILED"]

        pct = int(len(completed_batches) / len(batches) * 100) if batches else 100

        # Analyzers
        deps = ManifestParser.parse_workspace_manifests(ws_path)
        git_hotspots = GitAnalyzer.get_file_hotspots(ws_path, top_n=10)
        security_findings = SecretScanner.scan_workspace(ws_path)

        # Structured File Intelligence
        files_data = []
        for rel_path, rec in index.files.items():
            if rec.indexing_status != "INDEXED":
                continue
            expl = ExplanationService.explain_file_structured(rel_path, index, graph)
            files_data.append(expl)

        # Export JSON payload sidecar file reusing computed data
        cls.export_report_json(
            index,
            ws_path / ".wia" / "report_data.json",
            files_data=files_data,
            deps=deps,
            git_hotspots=git_hotspots,
            security_findings=security_findings,
        )

        # High-Level Project Narrative Synthesis
        roles_summary = set(fd["role"].split(" — ")[0] for fd in files_data)
        roles_narrative = ", ".join(sorted(roles_summary)) if roles_summary else "Core Application Components"

        project_narrative_p1 = (
            f"<strong>{ws_name}</strong> is a software repository containing <strong>{total_indexed}</strong> indexed files "
            f"and <strong>{total_symbols}</strong> declared AST code symbols. Based on static analysis and graph dependency mapping, "
            f"the codebase implements functional roles across <em>{html.escape(roles_narrative)}</em>."
        )

        entry_files = [
            f["file_name"] for f in files_data
            if any(k in f["role"].lower() for k in ("entry", "cli", "route", "controller", "main", "app", "server", "router"))
        ]
        service_files = [
            f["file_name"] for f in files_data
            if any(k in f["role"].lower() for k in ("service", "core", "orchestrator", "workflow", "engine", "handler", "manager"))
        ]
        model_storage_files = [
            f["file_name"] for f in files_data
            if any(k in f["role"].lower() for k in ("model", "store", "database", "schema", "entity", "repository", "state"))
        ]

        flow_clauses = []
        if entry_files:
            entry_list_str = ", ".join(f"<code>{html.escape(ef)}</code>" for ef in entry_files[:4])
            flow_clauses.append(f"Execution originates at detected entrypoint modules ({entry_list_str})")
        else:
            flow_clauses.append("Workflows and operations are distributed across functional component tiers")

        if service_files:
            svc_list_str = ", ".join(f"<code>{html.escape(sf)}</code>" for sf in service_files[:4])
            flow_clauses.append(f"delegating domain business logic to core services ({svc_list_str})")

        if model_storage_files:
            storage_list_str = ", ".join(f"<code>{html.escape(mf)}</code>" for mf in model_storage_files[:3])
            flow_clauses.append(f"coordinated with state and data schema definitions ({storage_list_str})")

        if index.frameworks:
            fw_names = ", ".join(index.frameworks)
            flow_clauses.append(f"leveraging <strong>{html.escape(fw_names)}</strong> ecosystem tooling")

        project_narrative_p2 = ", ".join(flow_clauses) + "." if flow_clauses else (
            f"Static code intelligence has mapped dependencies and structural call graphs across all {total_indexed} files."
        )

        project_narrative_p3 = (
            f"Workspace intelligence has been accumulated across <strong>{len(completed_batches)}</strong> completed analysis batches "
            f"out of <strong>{len(batches)}</strong> total batches ({pct}% completed). Each batch inspects source files, parses AST syntax trees, "
            f"extracts code symbols, scans security rules, and computes component change impact risks."
        )

        # Risk Distribution Counts
        high_risk_count = sum(1 for f in files_data if f.get("impact_risk_level") == "HIGH")
        medium_risk_count = sum(1 for f in files_data if f.get("impact_risk_level") == "MEDIUM")
        low_risk_count = sum(1 for f in files_data if f.get("impact_risk_level") == "LOW")

        # Component Architecture Breakdown Cards
        components_map: dict[str, list[dict]] = {}
        for fd in files_data:
            role_category = fd["role"].split(" — ")[0]
            components_map.setdefault(role_category, []).append(fd)

        components_html = ""
        for comp_name, comp_files in sorted(components_map.items()):
            comp_name_esc = html.escape(comp_name)
            file_names_str = ", ".join([f"<code>{html.escape(f['file_name'])}</code>" for f in comp_files[:6]])
            if len(comp_files) > 6:
                file_names_str += f" and {len(comp_files)-6} more"

            total_syms = sum(len(f.get("symbols", [])) for f in comp_files)
            high_impact_cnt = sum(1 for f in comp_files if f.get("impact_risk_level") == "HIGH")

            components_html += f"""
            <div class="card component-card">
                <div class="card-header">
                    <h3 class="card-title">{comp_name_esc}</h3>
                    <span class="badge badge-info">{len(comp_files)} Files</span>
                </div>
                <p class="narrative-text">
                    Contains {len(comp_files)} workspace component(s) declaring {total_syms} AST code symbol(s).
                    Key modules include {file_names_str}.
                </p>
                <div class="card-meta">
                    Discovered Symbols: <strong>{total_syms}</strong> | High Impact Files: <strong>{high_impact_cnt}</strong>
                </div>
            </div>
            """

        if not components_html:
            components_html = '<div class="empty-state">No architectural component groupings identified.</div>'

        # Accumulated Batch Narratives HTML
        batch_narratives_html = ""
        for b in batches:
            b_id_esc = html.escape(b.batch_id)
            if not b.narrative_summary:
                b_files_list = ", ".join([f"<code>{html.escape(Path(p).name)}</code>" for p in b.file_paths[:4]])
                b_narr = (
                    f"<strong>{b_id_esc}</strong> evaluated {len(b.file_paths)} repository components ({b_files_list}). "
                    f"This batch established file metadata, content hashes, and structural symbol records in the workspace index."
                )
            else:
                b_narr = b.narrative_summary

            status_badge = (
                '<span class="badge badge-success">COMPLETED</span>'
                if b.status == "COMPLETED"
                else f'<span class="badge badge-danger">FAILED</span>'
                if b.status == "FAILED"
                else '<span class="badge badge-warning">IN PROGRESS</span>'
            )

            err_html = f'<div class="error-box">{html.escape(b.error_message)}</div>' if b.error_message else ""
            b_files_str = ", ".join([html.escape(p) for p in b.file_paths])

            batch_narratives_html += f"""
            <div class="card batch-card" id="batch-{b_id_esc.lower().replace(' ', '-')}">
                <div class="card-header">
                    <h3 class="card-title">
                        <a href="#batch-{b_id_esc.lower().replace(' ', '-')}" class="anchor-link">#</a> {b_id_esc} — Technical Narrative
                    </h3>
                    {status_badge}
                </div>
                <p class="narrative-text">{b_narr}</p>
                {err_html}
                <details class="collapsible-details">
                    <summary>View Batch File List ({len(b.file_paths)} files)</summary>
                    <div class="code-block" style="margin-top: 0.5rem;">{b_files_str}</div>
                </details>
                <div class="card-meta">
                    Processed: <strong>{len(b.file_paths)} files</strong> | Duration: <strong>{b.duration_seconds:.2f}s</strong> | Timestamp: <strong>{html.escape(b.started_at[:19].replace('T', ' '))}</strong>
                </div>
            </div>
            """

        if not batch_narratives_html:
            batch_narratives_html = '<div class="empty-state">No batch records logged in workspace index.</div>'

        # Group Files by Language
        files_by_language: dict[str, list[dict]] = {}
        for fd in files_data:
            lang = fd.get("language") or "Other"
            files_by_language.setdefault(lang, []).append(fd)

        def _lang_sort_key(item: tuple[str, list[dict]]) -> tuple[int, str]:
            lname = item[0]
            if lname == "Python":
                return (0, lname)
            if lname == "TypeScript":
                return (1, lname)
            if lname == "JavaScript":
                return (2, lname)
            if lname == "Other":
                return (99, lname)
            return (10, lname)

        sorted_lang_groups = sorted(files_by_language.items(), key=_lang_sort_key)

        # Build File Intelligence Cards HTML Grouped by Language with Anchors
        language_nav_items_html = ""
        language_select_options_html = (
            '                    <option value="" selected disabled>-- Select a Language to Filter Files --</option>\n'
        )
        grouped_files_html = ""

        for lang_name, lang_files in sorted_lang_groups:
            lang_slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in lang_name.lower())
            lang_id = f"lang-{lang_slug}"
            lang_name_esc = html.escape(lang_name)
            count = len(lang_files)

            icon = "🐍" if lang_name == "Python" else "📘" if lang_name == "TypeScript" else "📜" if lang_name == "JavaScript" else "⚙️" if lang_name in ("TOML", "JSON", "YAML") else "📄"

            language_nav_items_html += f"""
            <li class="nav-sub-item">
                <a href="#{lang_id}" onclick="onLanguageSelect('{lang_slug}')">
                    <span><span class="sub-bullet">•</span> {icon} {lang_name_esc}</span>
                    <span class="badge badge-neutral">{count}</span>
                </a>
            </li>
            """

            language_select_options_html += f'                    <option value="{lang_slug}">{icon} {lang_name_esc} ({count} files)</option>\n'

            group_cards_html = ""
            for fd in lang_files:
                rel_p = html.escape(fd["file_path"])
                file_slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in fd["file_path"].lower())
                file_anchor_id = f"file-{file_slug}"
                lang = html.escape(fd["language"])
                role = html.escape(fd["role"])
                purpose = html.escape(fd["purpose"])
                impact_level = fd.get("impact_risk_level", "LOW")
                batch_id = html.escape(fd.get("batch_id", "Batch-1"))

                risk_class = (
                    "badge-danger"
                    if impact_level == "HIGH"
                    else "badge-warning"
                    if impact_level == "MEDIUM"
                    else "badge-success"
                )

                symbols_html = ""
                for s in fd.get("symbols", []):
                    stype = s.get("symbol_type")
                    if stype == "import":
                        continue
                    sname = html.escape(s.get("name", ""))
                    doc_raw = s.get("docstring") or ""
                    doc = html.escape(doc_raw.strip())
                    doc_str = f" — <span class='doc-text'>{doc}</span>" if doc else ""
                    symbols_html += f'<li class="sym-item"><span class="sym-type">{stype}</span> <code class="sym-name">{sname}</code>{doc_str}</li>'

                if not symbols_html:
                    symbols_html = '<li class="text-muted" style="font-size:0.85rem; padding:0.25rem 0;">No top-level functions or classes declared.</li>'

                ws_deps = fd.get("workspace_dependencies", [])
                used_by = fd.get("used_by", [])
                ws_deps_str = ", ".join([f"<code>{html.escape(d)}</code>" for d in ws_deps]) if ws_deps else '<span class="text-muted">None</span>'
                used_by_str = ", ".join([f"<code>{html.escape(u)}</code>" for u in used_by]) if used_by else '<span class="text-muted">None</span>'
                cls_cnt = len([s for s in fd.get("symbols", []) if s.get("symbol_type") == "class"])
                func_cnt = len([s for s in fd.get("symbols", []) if s.get("symbol_type") in ("function", "method")])
                total_sym_cnt = len(fd.get("symbols", []))

                file_narrative_text = (
                    f"The file <code>{rel_p}</code> fulfills the architectural role of <strong>{role}</strong>. "
                    f"{purpose} Declares {cls_cnt} class(es) and {func_cnt} function(s). "
                    f"Imports {ws_deps_str} and is imported by {used_by_str}. "
                    f"Evaluated change impact risk: <strong>{impact_level}</strong>."
                )

                group_cards_html += f"""
                <div class="card file-card" id="{file_anchor_id}" data-filepath="{rel_p.lower()}" data-language="{lang_slug}" data-batch="{batch_id}">
                    <div class="file-card-header">
                        <div class="file-title-wrap">
                            <a href="#{file_anchor_id}" class="anchor-link" title="Direct link to {rel_p}">#</a>
                            <span class="file-title">{rel_p}</span>
                            <span class="badge badge-neutral">{lang}</span>
                            <span class="badge badge-neutral">{batch_id}</span>
                        </div>
                        <span class="badge {risk_class}">Impact: {impact_level}</span>
                    </div>
                    <p class="narrative-text" style="margin-top:0.4rem; margin-bottom:0.6rem;">{file_narrative_text}</p>

                    <details class="collapsible-details file-details">
                        <summary>View Declared Symbols ({total_sym_cnt}) & Direct Dependencies</summary>
                        <div class="details-content">
                            <ul class="sym-list">
                                {symbols_html}
                            </ul>
                            <div class="dep-links-grid">
                                <div>
                                    <span class="dep-label">Depends On:</span>
                                    <div class="dep-values">{ws_deps_str}</div>
                                </div>
                                <div>
                                    <span class="dep-label">Used By:</span>
                                    <div class="dep-values">{used_by_str}</div>
                                </div>
                            </div>
                        </div>
                    </details>
                </div>
                """

            grouped_files_html += f"""
            <details class="section-panel card" id="{lang_id}" data-language-group="{lang_slug}" open>
                <summary class="section-panel-header">
                    <div class="header-left">
                        <span class="dropdown-chevron">▶</span>
                        <a href="#{lang_id}" class="anchor-link" title="Direct link to {lang_name_esc} files" onclick="event.stopPropagation()">#</a>
                        <h3 class="panel-heading">{icon} {lang_name_esc} Files</h3>
                        <span class="badge badge-info">{count} File{'s' if count != 1 else ''}</span>
                    </div>
                    <div class="header-right">
                        <button class="btn btn-sm btn-secondary" onclick="event.stopPropagation(); toggleLanguageDetails('{lang_id}')">Toggle Symbols</button>
                    </div>
                </summary>
                <div class="panel-body">
                    {group_cards_html}
                </div>
            </details>
            """

        if not grouped_files_html:
            grouped_files_html = '<div class="empty-state">No source files indexed in workspace.</div>'

        # Frameworks HTML
        framework_items_html = ""
        for fw in index.frameworks:
            fw_esc = html.escape(fw)
            framework_items_html += f'<span class="badge badge-info">{fw_esc}</span> '
        if not framework_items_html:
            framework_items_html = '<span class="text-muted">None detected</span>'

        # Languages HTML
        lang_items_html = ""
        for lang, count in index.languages.items():
            lang_esc = html.escape(lang)
            lang_slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in lang.lower())
            lang_items_html += f'<a href="#lang-{lang_slug}" class="badge badge-neutral" style="text-decoration:none;">{lang_esc}: {count}</a> '
        if not lang_items_html:
            lang_items_html = '<span class="text-muted">No language data</span>'

        # Security Findings HTML
        security_html = ""
        for sec in security_findings:
            sev_class = "badge-danger" if sec.severity.upper() in ("CRITICAL", "HIGH") else "badge-warning" if sec.severity.upper() == "MEDIUM" else "badge-neutral"
            sec_type = getattr(sec, "finding_type", getattr(sec, "rule_id", "Secret"))
            evid = getattr(sec, "masked_evidence", getattr(sec, "match_snippet", ""))
            security_html += f"""
            <tr>
                <td><span class="badge {sev_class}">{html.escape(sec.severity)}</span></td>
                <td>{html.escape(sec_type)}</td>
                <td><code>{html.escape(sec.file_path)}:{sec.line_number}</code></td>
                <td><code>{html.escape(evid)}</code></td>
            </tr>
            """

        security_section_html = ""
        if security_findings:
            security_section_html = f"""
            <section class="report-section" id="security">
                <details class="section-panel card" open>
                    <summary class="section-panel-header">
                        <div class="header-left">
                            <span class="dropdown-chevron">▶</span>
                            <a href="#security" class="anchor-link" title="Direct link to Security Intelligence" onclick="event.stopPropagation()">#</a>
                            <h2 class="section-title">Security Intelligence Findings</h2>
                            <span class="badge badge-danger">{len(security_findings)} Findings</span>
                        </div>
                    </summary>
                    <div class="panel-body">
                        <div class="table-container">
                            <table class="data-table">
                                <thead>
                                    <tr><th>Severity</th><th>Type</th><th>Location</th><th>Evidence</th></tr>
                                </thead>
                                <tbody>
                                    {security_html}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </details>
            </section>
            """

        # Dependency Conflicts and Graph Payload
        conflicts = ConflictDetector.detect_conflicts(deps)
        conflict_pkg_map = {c.package_name.lower(): c for c in conflicts}

        eco_counts: dict[str, int] = {}
        for d in deps:
            eco = d.ecosystem.lower() if d.ecosystem else "other"
            eco_counts[eco] = eco_counts.get(eco, 0) + 1

        manifest_files = sorted(list(set(d.manifest_path for d in deps)))

        deps_data_for_table = []
        for d in deps:
            pkg_name = getattr(d, "name", getattr(d, "package_name", ""))
            ver_spec = getattr(d, "version_spec", getattr(d, "specifier", "*"))
            m_path = getattr(d, "manifest_path", "manifest")
            eco = getattr(d, "ecosystem", "generic")
            dtype = getattr(d, "dependency_type", "runtime")

            referencing_files = []
            for rel_p, frec in index.files.items():
                if frec.indexing_status != "INDEXED":
                    continue
                imports = frec.extra_metadata.get("imports", [])
                if any(
                    pkg_name.lower() == imp.lower().split(".")[0]
                    or (f" {pkg_name.lower()} " in f" {imp.lower()} ")
                    or pkg_name.lower() in imp.lower()
                    for imp in imports
                ):
                    referencing_files.append(rel_p)

            has_conflict = pkg_name.lower() in conflict_pkg_map
            conflict_obj = conflict_pkg_map.get(pkg_name.lower())
            conflict_reason = conflict_obj.reason if conflict_obj else ""

            deps_data_for_table.append({
                "name": pkg_name,
                "version": ver_spec or "*",
                "manifest": m_path,
                "ecosystem": eco,
                "type": dtype,
                "has_conflict": has_conflict,
                "conflict_reason": conflict_reason,
                "used_in": referencing_files[:6],
                "used_count": len(referencing_files),
            })

        conflicts_banner_html = ""
        if conflicts:
            conflict_items_html = ""
            for c in conflicts:
                affected_str = ", ".join(f"<code>{html.escape(m)}</code>" for m in c.affected_manifests)
                conflict_items_html += f"""
                <div class="conflict-item">
                    <div class="conflict-item-header">
                        <strong class="conflict-pkg-name">{html.escape(c.package_name)}</strong>
                        <span class="badge badge-danger">{html.escape(c.conflict_type)}</span>
                    </div>
                    <div class="conflict-desc">{html.escape(c.reason)}</div>
                    <div class="conflict-meta">Affected Manifests: {affected_str}</div>
                </div>
                """
            conflicts_banner_html = f"""
            <div class="card conflict-card">
                <div class="conflict-header">
                    <span class="conflict-icon">⚠️</span>
                    <h3 class="conflict-title">Detected Dependency Conflicts ({len(conflicts)})</h3>
                </div>
                {conflict_items_html}
            </div>
            """

        eco_filter_pills_html = f'<button class="btn btn-sm btn-secondary dep-filter-btn active" data-eco="all" onclick="filterDepEcosystem(\'all\', this)">All ({len(deps)})</button>'
        for eco_name, eco_cnt in sorted(eco_counts.items()):
            eco_filter_pills_html += f'<button class="btn btn-sm btn-secondary dep-filter-btn" data-eco="{html.escape(eco_name)}" onclick="filterDepEcosystem(\'{html.escape(eco_name)}\', this)">{html.escape(eco_name.capitalize())} ({eco_cnt})</button>'

        manifest_badges_html = " ".join(f'<span class="badge badge-neutral">📄 {html.escape(m)}</span>' for m in manifest_files)

        deps_rows_html = ""
        for d in deps_data_for_table:
            conf_badge = '<span class="badge badge-danger" style="margin-left:0.4rem;">Conflict</span>' if d["has_conflict"] else ""
            used_str = f'{d["used_count"]} file(s)' if d["used_count"] > 0 else '<span class="text-muted">Direct</span>'
            deps_rows_html += f"""
            <tr>
                <td><strong>{html.escape(d["name"])}</strong>{conf_badge}</td>
                <td><code>{html.escape(d["version"])}</code></td>
                <td><code>{html.escape(d["manifest"])}</code></td>
                <td><span class="badge badge-info">{html.escape(d["ecosystem"])}</span></td>
                <td><span class="badge badge-neutral">{html.escape(d["type"])}</span></td>
                <td>{used_str}</td>
            </tr>
            """

        deps_section_html = ""
        if deps:
            deps_section_html = f"""
            <section class="report-section" id="dependencies">
                <details class="section-panel card" open>
                    <summary class="section-panel-header">
                        <div class="header-left">
                            <span class="dropdown-chevron">▶</span>
                            <a href="#dependencies" class="anchor-link" title="Direct link to Manifest Dependencies" onclick="event.stopPropagation()">#</a>
                            <h2 class="section-title">Manifest Dependencies & Ecosystem Packages</h2>
                            <span class="badge badge-info">{len(deps)} Packages</span>
                            <span class="badge badge-neutral">{len(manifest_files)} Manifest{'s' if len(manifest_files) != 1 else ''}</span>
                            {f'<span class="badge badge-danger">{len(conflicts)} Conflicts</span>' if conflicts else ''}
                        </div>
                    </summary>

                    <div class="panel-body">
                        {conflicts_banner_html}

                        <div class="filter-toolbar">
                            <div class="filter-group">
                                <span class="filter-label">Ecosystems:</span>
                                {eco_filter_pills_html}
                            </div>
                            <div class="filter-group">
                                <span class="filter-label">Manifests:</span>
                                {manifest_badges_html}
                            </div>
                        </div>

                        <div class="table-container" style="margin-top: 1rem;">
                            <table class="data-table">
                                <thead>
                                    <tr><th>Package Name</th><th>Version Spec</th><th>Manifest</th><th>Ecosystem</th><th>Type</th><th>Workspace Usage</th></tr>
                                </thead>
                                <tbody>
                                    {deps_rows_html}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </details>
            </section>
            """

        # Graph Payload Construction
        graph_payload = cls._build_graph_payload(index, graph, files_data, deps, conflicts)
        is_dag = graph_payload["is_dag"]
        cycle_count = graph_payload["cycle_count"]

        graph_type_title = (
            "Dependency DAG (Acyclic Graph)"
            if is_dag
            else f"Dependency Graph (Directional Graph with {cycle_count} Cycle{'s' if cycle_count != 1 else ''})"
        )
        graph_type_badge = (
            '<span class="badge badge-success">Acyclic (DAG)</span>'
            if is_dag
            else f'<span class="badge badge-warning">{cycle_count} Cyclic Loops</span>'
        )

        # Dynamically determine sample impact analysis file from actual project
        sample_impact_file = ""
        for fd in files_data:
            if fd.get("workspace_dependencies") or fd.get("used_by"):
                sample_impact_file = fd["file_path"]
                break
        if not sample_impact_file and files_data:
            sample_impact_file = files_data[0]["file_path"]
        if not sample_impact_file:
            sample_impact_file = "src/main.py"

        # Dynamically detect all project-specific developer execution commands
        project_cmds = cls._detect_project_commands(ws_path, index, files_data)
        project_commands_html = ""
        for i, pcmd in enumerate(project_cmds, start=1):
            cat_badge = f'<span class="badge badge-info" style="margin-left:0.5rem;">{html.escape(pcmd["category"])}</span>'
            source_badge = f'<span class="badge badge-neutral" style="margin-left:0.4rem;">{html.escape(pcmd["source"])}</span>' if pcmd.get("source") else ""
            project_commands_html += f"""
                <div class="cmd-item">
                    <div class="cmd-desc">
                        <strong>{i}. {html.escape(pcmd["desc"])}</strong>
                        {cat_badge}
                        {source_badge}
                    </div>
                    <div class="cmd-box">
                        <span class="cmd-text">{html.escape(pcmd["command"])}</span>
                        <button class="btn btn-sm btn-secondary copy-btn" onclick="copyFromBox(this)">Copy</button>
                    </div>
                </div>
            """

        report_json_data = _safe_json_embed({
            "workspace_name": ws_name,
            "indexed_at": index.indexed_at,
            "index_version": index.index_version,
            "wia_version": index.wia_version,
            "stats": index.stats,
            "languages": index.languages,
            "frameworks": index.frameworks,
            "completed_batches": len(completed_batches),
            "total_batches": len(batches),
        })

        graph_json_data = _safe_json_embed(graph_payload)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WIA Workspace Intelligence Report — {ws_name}</title>
    <!-- Apache ECharts for High-Performance Interactive Graph Visualization -->
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
    <style>
        :root {{
            --bg: #f6f8fb;
            --surface: #ffffff;
            --surface-alt: #f1f5f9;
            --surface-subtle: #f8fafc;
            --border: #dbe2ea;
            --border-strong: #cbd5e1;
            --border-subtle: #edf2f7;

            --text: #172033;
            --text-secondary: #526071;
            --text-muted: #718096;

            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --primary-light: #eff6ff;
            --primary-border: #bfdbfe;
            --accent: #2563eb;
            --accent-hover: #1d4ed8;

            --info: #0284c7;
            --info-bg: #f0f9ff;
            --info-text: #0369a1;
            --info-border: #bae6fd;

            --success: #15803d;
            --success-bg: #f0fdf4;
            --success-text: #166534;
            --success-border: #bbf7d0;

            --warning: #b45309;
            --warning-bg: #fffbeb;
            --warning-text: #92400e;
            --warning-border: #fde68a;

            --danger: #b91c1c;
            --danger-bg: #fef2f2;
            --danger-text: #991b1b;
            --danger-border: #fecaca;

            --code-bg: #0f172a;
            --code-text: #f8fafc;
        }}

        *, *::before, *::after {{
            box-sizing: border-box;
        }}

        html {{
            scroll-behavior: smooth;
        }}

        body {{
            font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 0;
            line-height: 1.5;
            font-size: 0.9375rem;
            overflow-x: hidden;
            display: flex;
            min-height: 100vh;
        }}

        /* Sidebar Navigation */
        aside.report-sidebar {{
            width: 270px;
            background-color: var(--surface);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            padding: 1.25rem 0.85rem;
            flex-shrink: 0;
            position: sticky;
            top: 0;
            height: 100vh;
            overflow-y: auto;
            z-index: 100;
        }}

        .brand {{
            font-size: 1.15rem;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 1.25rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            letter-spacing: -0.02em;
            padding: 0 0.5rem;
        }}

        .nav-menu {{
            list-style: none;
            padding: 0;
            margin: 0;
            display: flex;
            flex-direction: column;
            gap: 0.2rem;
        }}

        .nav-item a {{
            color: var(--text-secondary);
            text-decoration: none;
            padding: 0.5rem 0.75rem;
            border-radius: 6px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.875rem;
            font-weight: 500;
            transition: background-color 0.15s ease, color 0.15s ease;
        }}

        .nav-item a:hover, .nav-item a.active {{
            background-color: var(--primary-light);
            color: var(--primary);
            font-weight: 600;
        }}

        .nav-sub-menu {{
            list-style: none;
            padding: 0.2rem 0 0.4rem 1.25rem;
            margin: 0;
            display: flex;
            flex-direction: column;
            gap: 0.15rem;
        }}

        .nav-sub-item a {{
            color: var(--text-muted);
            text-decoration: none;
            padding: 0.3rem 0.5rem;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 0.8125rem;
            transition: background-color 0.15s ease, color 0.15s ease;
        }}

        .nav-sub-item a:hover {{
            background-color: var(--surface-alt);
            color: var(--text);
        }}

        .sub-bullet {{
            margin-right: 0.4rem;
            color: var(--accent);
        }}

        /* Main Workspace Container */
        main.report-main {{
            flex: 1;
            min-width: 0;
            padding: 1.75rem 2.5rem;
            max-width: 1440px;
            margin: 0 auto;
            overflow-y: auto;
        }}

        header.report-header {{
            border-bottom: 1px solid var(--border);
            padding-bottom: 1.15rem;
            margin-bottom: 1.75rem;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            flex-wrap: wrap;
            gap: 1rem;
        }}

        h1.report-heading {{
            margin: 0;
            color: var(--text);
            font-size: 1.55rem;
            font-weight: 700;
            letter-spacing: -0.025em;
        }}

        .header-meta {{
            color: var(--text-muted);
            font-size: 0.85rem;
            margin-top: 0.3rem;
            word-break: break-all;
        }}

        .header-meta code {{
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 0.825rem;
            background: var(--surface);
            padding: 0.15rem 0.35rem;
            border-radius: 4px;
            border: 1px solid var(--border);
            color: var(--text-secondary);
        }}

        /* Section Layouts */
        .report-section {{
            margin-bottom: 2rem;
        }}

        .section-title {{
            font-size: 1.15rem;
            font-weight: 600;
            color: var(--text);
            margin: 0;
            letter-spacing: -0.015em;
        }}

        /* Cards and Panels */
        .card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.25rem;
            margin-bottom: 1.15rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
            min-width: 0;
        }}

        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}

        .card-title {{
            margin: 0;
            font-size: 1rem;
            font-weight: 600;
            color: var(--primary);
        }}

        .card-meta {{
            font-size: 0.8125rem;
            color: var(--text-muted);
            margin-top: 0.5rem;
            padding-top: 0.5rem;
            border-top: 1px solid var(--border-subtle);
        }}

        .narrative-card {{
            border-left: 4px solid var(--primary);
        }}

        .narrative-text {{
            font-size: 0.9375rem;
            line-height: 1.6;
            color: var(--text-secondary);
            margin: 0 0 0.75rem 0;
        }}

        .narrative-text:last-child {{
            margin-bottom: 0;
        }}

        /* Grid Utilities */
        .grid-4 {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 0.85rem;
            margin-bottom: 1.25rem;
        }}

        .grid-2 {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 0.85rem;
        }}

        .metric-card {{
            padding: 0.9rem 1.15rem;
        }}

        .metric-card h3 {{
            margin: 0 0 0.3rem 0;
            font-size: 0.75rem;
            text-transform: uppercase;
            color: var(--text-muted);
            font-weight: 600;
            letter-spacing: 0.05em;
        }}

        .metric-val {{
            font-size: 1.65rem;
            font-weight: 700;
            color: var(--text);
            line-height: 1.2;
        }}

        /* Badges */
        .badge {{
            display: inline-flex;
            align-items: center;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.03em;
            line-height: 1;
            white-space: nowrap;
        }}

        .badge-success {{
            background-color: var(--success-bg);
            color: var(--success-text);
            border: 1px solid var(--success-border);
        }}

        .badge-warning {{
            background-color: var(--warning-bg);
            color: var(--warning-text);
            border: 1px solid var(--warning-border);
        }}

        .badge-danger {{
            background-color: var(--danger-bg);
            color: var(--danger-text);
            border: 1px solid var(--danger-border);
        }}

        .badge-info {{
            background-color: var(--info-bg);
            color: var(--info-text);
            border: 1px solid var(--info-border);
        }}

        .badge-neutral {{
            background-color: var(--surface-alt);
            color: var(--text-secondary);
            border: 1px solid var(--border);
        }}

        /* Buttons */
        .btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-family: inherit;
            font-size: 0.8125rem;
            font-weight: 500;
            padding: 0.35rem 0.7rem;
            border-radius: 5px;
            border: 1px solid var(--border);
            background-color: var(--surface);
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.15s ease;
            white-space: nowrap;
        }}

        .btn:hover {{
            background-color: var(--surface-alt);
            color: var(--text);
            border-color: var(--border-strong);
        }}

        .btn-primary {{
            background-color: var(--primary);
            color: #ffffff;
            border-color: var(--primary);
        }}

        .btn-primary:hover {{
            background-color: var(--primary-dark);
            border-color: var(--primary-dark);
            color: #ffffff;
        }}

        .btn-sm {{
            padding: 0.25rem 0.5rem;
            font-size: 0.75rem;
        }}

        .btn.active {{
            background-color: var(--primary-light);
            color: var(--primary);
            border-color: var(--primary-border);
            font-weight: 600;
        }}

        /* Section Panels */
        .section-panel {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0;
            margin-bottom: 1.25rem;
            overflow: hidden;
        }}

        .section-panel-header {{
            padding: 0.9rem 1.15rem;
            background: var(--surface);
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            user-select: none;
            border-bottom: 1px solid transparent;
            transition: background-color 0.15s ease;
        }}

        .section-panel[open] > .section-panel-header {{
            border-bottom-color: var(--border);
            background-color: #fafbfc;
        }}

        .section-panel-header::-webkit-details-marker {{
            display: none;
        }}

        .header-left {{
            display: flex;
            align-items: center;
            gap: 0.6rem;
            flex-wrap: wrap;
        }}

        .header-right {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .panel-heading {{
            margin: 0;
            font-size: 1.05rem;
            font-weight: 600;
            color: var(--text);
        }}

        .panel-body {{
            padding: 1.15rem;
        }}

        .dropdown-chevron {{
            color: var(--text-muted);
            font-size: 0.75rem;
            transition: transform 0.2s ease;
            display: inline-block;
        }}

        details[open] > summary .dropdown-chevron {{
            transform: rotate(90deg);
        }}

        /* ================================================= */
        /* DEPENDENCY GRAPH PANEL & CONTROLS                 */
        /* ================================================= */
        .graph-panel {{
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--surface);
            overflow: hidden;
            margin-bottom: 1.75rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }}

        /* Graph Statistics Bar */
        .graph-stats-bar {{
            padding: 0.5rem 1rem;
            background: #f8fafc;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            gap: 1rem;
            flex-wrap: wrap;
            font-size: 0.8125rem;
        }}

        .stat-pill {{
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            color: var(--text-secondary);
        }}

        .stat-pill strong {{
            color: var(--text);
        }}

        .stat-pill.clickable {{
            cursor: pointer;
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            transition: background 0.15s ease;
        }}

        .stat-pill.clickable:hover {{
            background: var(--surface-alt);
        }}

        .graph-toolbar {{
            padding: 0.65rem 1rem;
            background: #ffffff;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.6rem;
        }}

        .graph-toolbar-left {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            flex-wrap: wrap;
            flex: 1;
            min-width: 260px;
        }}

        .graph-toolbar-right {{
            display: flex;
            align-items: center;
            gap: 0.35rem;
            flex-wrap: wrap;
        }}

        .search-input {{
            padding: 0.35rem 0.65rem;
            border-radius: 6px;
            border: 1px solid var(--border);
            background: var(--surface);
            color: var(--text);
            font-size: 0.8125rem;
            min-width: 200px;
            outline: none;
            transition: border-color 0.15s ease, box-shadow 0.15s ease;
        }}

        .search-input:focus {{
            border-color: var(--accent);
            box-shadow: 0 0 0 2px var(--primary-light);
        }}

        .graph-view-wrapper {{
            display: flex;
            width: 100%;
            height: 65vh;
            min-height: 520px;
            max-height: 800px;
            position: relative;
            background: #fbfcfe;
        }}

        .graph-viewport {{
            flex: 1;
            height: 100%;
            min-width: 0;
            position: relative;
        }}

        #depEchartsChart {{
            width: 100%;
            height: 100%;
        }}

        /* Graph Node Details Sidebar Panel */
        .graph-details-sidebar {{
            width: 320px;
            border-left: 1px solid var(--border);
            background: var(--surface);
            height: 100%;
            overflow-y: auto;
            padding: 1.15rem;
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
            font-size: 0.875rem;
        }}

        .details-panel-title {{
            font-size: 0.925rem;
            font-weight: 700;
            color: var(--text);
            margin: 0 0 0.75rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .node-detail-field {{
            margin-bottom: 0.65rem;
        }}

        .node-detail-label {{
            font-size: 0.72rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.15rem;
        }}

        .node-detail-value {{
            color: var(--text);
            font-size: 0.85rem;
            word-break: break-all;
        }}

        .node-detail-value code {{
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            background: var(--surface-alt);
            padding: 0.15rem 0.35rem;
            border-radius: 4px;
            font-size: 0.8125rem;
            border: 1px solid var(--border);
        }}

        .clickable-node-link {{
            color: var(--primary);
            cursor: pointer;
            text-decoration: underline;
            padding: 0.1rem 0;
            display: block;
        }}

        .clickable-node-link:hover {{
            color: var(--primary-dark);
        }}

        .graph-legend-bar {{
            padding: 0.55rem 1rem;
            background: #f8fafc;
            border-top: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 0.75rem;
            color: var(--text-muted);
            flex-wrap: wrap;
            gap: 0.65rem;
        }}

        .legend-items {{
            display: flex;
            align-items: center;
            gap: 0.85rem;
            flex-wrap: wrap;
        }}

        .legend-item {{
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
        }}

        .legend-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
        }}

        .legend-line {{
            width: 12px;
            height: 2px;
            display: inline-block;
        }}

        /* Tables */
        .table-container {{
            width: 100%;
            overflow-x: auto;
            border: 1px solid var(--border);
            border-radius: 6px;
        }}

        table.data-table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 0.875rem;
            white-space: nowrap;
        }}

        table.data-table th {{
            background-color: var(--surface-alt);
            padding: 0.6rem 0.8rem;
            border-bottom: 1px solid var(--border);
            color: var(--text-secondary);
            font-weight: 600;
            font-size: 0.8125rem;
        }}

        table.data-table td {{
            padding: 0.6rem 0.8rem;
            border-bottom: 1px solid var(--border-subtle);
            color: var(--text);
        }}

        table.data-table tr:last-child td {{
            border-bottom: none;
        }}

        table.data-table tr:hover td {{
            background-color: var(--surface-subtle);
        }}

        /* Code & Paths */
        code {{
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            background-color: var(--surface-alt);
            padding: 0.15rem 0.35rem;
            border-radius: 4px;
            font-size: 0.85em;
            color: var(--text-secondary);
            border: 1px solid var(--border);
        }}

        .code-block {{
            background: var(--code-bg);
            color: var(--code-text);
            padding: 0.75rem 1rem;
            border-radius: 6px;
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 0.8125rem;
            overflow-x: auto;
            white-space: pre-wrap;
            word-break: break-all;
        }}

        /* Commands Section */
        .cmd-item {{
            margin-bottom: 0.75rem;
        }}

        .cmd-desc {{
            color: var(--text-secondary);
            font-size: 0.85rem;
            margin-bottom: 0.3rem;
            display: flex;
            align-items: center;
            flex-wrap: wrap;
        }}

        .cmd-box {{
            background-color: #fafbfc;
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 0.45rem 0.75rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 0.85rem;
            gap: 0.75rem;
        }}

        .cmd-text {{
            color: var(--primary);
            overflow-x: auto;
            white-space: nowrap;
            flex: 1;
        }}

        /* File Cards */
        .file-card {{
            border-left: 3px solid var(--border);
            margin-bottom: 0.75rem;
            padding: 0.9rem 1.1rem;
            transition: border-color 0.15s ease;
        }}

        .file-card:hover {{
            border-left-color: var(--primary);
        }}

        .file-card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.35rem;
            flex-wrap: wrap;
            gap: 0.4rem;
        }}

        .file-title-wrap {{
            display: flex;
            align-items: center;
            gap: 0.35rem;
            flex-wrap: wrap;
        }}

        .file-title {{
            font-weight: 600;
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 0.875rem;
            color: var(--primary);
        }}

        .collapsible-details summary {{
            cursor: pointer;
            font-size: 0.8125rem;
            color: var(--primary);
            font-weight: 500;
            user-select: none;
        }}

        .collapsible-details summary:hover {{
            text-decoration: underline;
        }}

        .details-content {{
            margin-top: 0.5rem;
            padding-top: 0.5rem;
            border-top: 1px solid var(--border-subtle);
        }}

        .sym-list {{
            list-style: none;
            padding: 0;
            margin: 0.35rem 0 0.5rem 0;
            font-size: 0.8125rem;
        }}

        .sym-item {{
            padding: 0.2rem 0;
            border-bottom: 1px dashed var(--border-subtle);
        }}

        .sym-type {{
            font-size: 0.7rem;
            text-transform: uppercase;
            font-weight: 700;
            color: var(--text-muted);
            display: inline-block;
            width: 65px;
        }}

        .sym-name {{
            color: var(--text);
            font-weight: 600;
        }}

        .doc-text {{
            color: var(--text-muted);
            font-style: italic;
        }}

        .dep-links-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 0.65rem;
            font-size: 0.8125rem;
            margin-top: 0.5rem;
            background: var(--surface-alt);
            padding: 0.6rem 0.8rem;
            border-radius: 6px;
            border: 1px solid var(--border);
        }}

        .dep-label {{
            font-weight: 600;
            color: var(--text-secondary);
            display: block;
            margin-bottom: 0.2rem;
        }}

        .dep-values {{
            color: var(--text);
            word-break: break-all;
        }}

        /* Batch Cards & Progress */
        .batch-card {{
            border-left: 3px solid var(--primary);
        }}

        .progress-bar-bg {{
            height: 6px;
            background-color: var(--border);
            border-radius: 3px;
            overflow: hidden;
            margin: 0.5rem 0;
        }}

        .progress-bar-fill {{
            height: 100%;
            background-color: var(--primary);
            transition: width 0.3s ease;
        }}

        /* Conflict Banner */
        .conflict-card {{
            border: 1px solid var(--danger-border);
            background: var(--danger-bg);
            margin-bottom: 1.15rem;
            padding: 0.9rem 1.15rem;
        }}

        .conflict-header {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.65rem;
        }}

        .conflict-title {{
            margin: 0;
            color: var(--danger-text);
            font-size: 0.95rem;
            font-weight: 700;
        }}

        .conflict-item {{
            margin-bottom: 0.45rem;
            padding: 0.45rem 0.7rem;
            background: #ffffff;
            border: 1px solid var(--danger-border);
            border-radius: 6px;
        }}

        .conflict-item:last-child {{
            margin-bottom: 0;
        }}

        .conflict-item-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .conflict-pkg-name {{
            color: var(--danger-text);
        }}

        .conflict-desc {{
            font-size: 0.825rem;
            color: var(--text-secondary);
            margin-top: 0.15rem;
        }}

        .conflict-meta {{
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-top: 0.15rem;
        }}

        .filter-toolbar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.65rem;
            margin-bottom: 0.85rem;
            padding-bottom: 0.65rem;
            border-bottom: 1px solid var(--border-subtle);
        }}

        .filter-group {{
            display: flex;
            align-items: center;
            gap: 0.35rem;
            flex-wrap: wrap;
        }}

        .filter-label {{
            font-size: 0.8125rem;
            font-weight: 600;
            color: var(--text-muted);
            margin-right: 0.2rem;
        }}

        /* Anchor Links */
        .anchor-link {{
            color: var(--text-muted);
            text-decoration: none;
            font-size: 0.85em;
            margin-right: 0.3rem;
            opacity: 0.4;
            transition: opacity 0.15s ease, color 0.15s ease;
        }}

        .anchor-link:hover {{
            opacity: 1.0;
            color: var(--accent);
        }}

        .empty-state {{
            padding: 1.75rem 1.25rem;
            text-align: center;
            color: var(--text-muted);
            font-size: 0.875rem;
            background: var(--surface-alt);
            border: 1px dashed var(--border-strong);
            border-radius: 6px;
        }}

        .error-box {{
            background: var(--danger-bg);
            color: var(--danger-text);
            border: 1px solid var(--danger-border);
            padding: 0.55rem 0.75rem;
            border-radius: 6px;
            font-size: 0.825rem;
            margin-top: 0.45rem;
        }}

        .offline-notice {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            color: var(--text-muted);
            font-size: 0.875rem;
            background: var(--surface);
            padding: 1.25rem 1.75rem;
            border: 1px solid var(--border);
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            max-width: 420px;
        }}

        @media (max-width: 1024px) {{
            body {{
                flex-direction: column;
            }}
            aside.report-sidebar {{
                width: 100%;
                height: auto;
                position: relative;
                border-right: none;
                border-bottom: 1px solid var(--border);
            }}
            main.report-main {{
                padding: 1.25rem 1rem;
            }}
            .graph-view-wrapper {{
                flex-direction: column;
                height: auto;
            }}
            .graph-viewport {{
                height: 480px;
            }}
            .graph-details-sidebar {{
                width: 100%;
                height: 280px;
                border-left: none;
                border-top: 1px solid var(--border);
            }}
        }}
    </style>
</head>
<body>
    <aside class="report-sidebar">
        <div class="brand">
            ⚡ WIA Intelligence
        </div>
        <ul class="nav-menu" id="sidebarMenu">
            <li class="nav-item"><a href="#executive-overview" class="active">Executive Overview</a></li>
            <li class="nav-item"><a href="#dependency-graph">Dependency Graph</a></li>
            <li class="nav-item"><a href="#installation">Developer Commands</a></li>
            <li class="nav-item"><a href="#components">System Architecture</a></li>
            <li class="nav-item"><a href="#batch-narratives">Batch Log ({len(batches)})</a></li>
            <li class="nav-item">
                <a href="#file-narratives">File Intelligence ({len(files_data)})</a>
            </li>
            <ul class="nav-sub-menu">
                {language_nav_items_html}
            </ul>
            {f'<li class="nav-item"><a href="#security">Security ({len(security_findings)})</a></li>' if security_findings else ''}
            {f'<li class="nav-item"><a href="#dependencies">Manifest Dependencies ({len(deps)})</a></li>' if deps else ''}
        </ul>
    </aside>

    <main class="report-main" id="mainContainer">
        <header class="report-header">
            <div>
                <h1 class="report-heading">WIA Workspace Intelligence Report</h1>
                <div class="header-meta">
                    Repository: <code>{ws_path}</code> | Schema: <strong>{version}</strong> | WIA Engine: <strong>{wia_ver}</strong>
                </div>
            </div>
            <div>
                <span class="badge badge-neutral">Developer Intelligence Dashboard</span>
            </div>
        </header>

        <!-- Executive Project Overview -->
        <section class="report-section" id="executive-overview">
            <div class="card narrative-card">
                <div class="card-header">
                    <h2 class="section-title"><a href="#executive-overview" class="anchor-link">#</a> Executive Repository Summary</h2>
                    <span class="badge badge-info">{total_indexed} Files Indexed</span>
                </div>
                <p class="narrative-text">{project_narrative_p1}</p>
                <p class="narrative-text">{project_narrative_p2}</p>
                <p class="narrative-text">{project_narrative_p3}</p>
            </div>

            <!-- Overview Metrics Grid -->
            <div class="grid-4">
                <div class="card metric-card">
                    <h3>Indexed Files</h3>
                    <div class="metric-val">{total_indexed}</div>
                    <div class="card-meta">Discovered: {total_discovered} | Ignored: {total_ignored}</div>
                </div>
                <div class="card metric-card">
                    <h3>Declared Symbols</h3>
                    <div class="metric-val">{total_symbols}</div>
                    <div class="card-meta">Classes, Functions, Methods</div>
                </div>
                <div class="card metric-card">
                    <h3>Completed Batches</h3>
                    <div class="metric-val">{len(completed_batches)} / {len(batches)}</div>
                    <div class="card-meta">{pct}% Coverage Completed</div>
                </div>
                <div class="card metric-card">
                    <h3>Risk Classification</h3>
                    <div style="margin-top: 0.35rem; display: flex; gap: 0.3rem; flex-wrap: wrap;">
                        <span class="badge badge-danger">High: {high_risk_count}</span>
                        <span class="badge badge-warning">Med: {medium_risk_count}</span>
                        <span class="badge badge-success">Low: {low_risk_count}</span>
                    </div>
                    <div class="card-meta">{framework_items_html}</div>
                </div>
            </div>
        </section>

        <!-- ========================================== -->
        <!-- INTERACTIVE DEPENDENCY GRAPH PANEL         -->
        <!-- ========================================== -->
        <section class="report-section" id="dependency-graph">
            <div class="graph-panel">
                <!-- Statistics Strip -->
                <div class="graph-stats-bar">
                    <div class="stat-pill"><span class="stat-label">Nodes:</span> <strong>{graph_payload['summary']['total_nodes']}</strong></div>
                    <div class="stat-pill"><span class="stat-label">Edges:</span> <strong>{graph_payload['summary']['total_edges']}</strong></div>
                    <div class="stat-pill"><span class="stat-label">Direct (Rank 1):</span> <strong>{graph_payload['summary']['direct_count']}</strong></div>
                    <div class="stat-pill"><span class="stat-label">Indirect / Transitive:</span> <strong>{graph_payload['summary']['indirect_count']}</strong></div>
                    <div class="stat-pill clickable" onclick="toggleHighlightCycles()" title="Click to highlight/filter cyclic loops">
                        <span class="stat-label">Cycles:</span>
                        {f'<span class="badge badge-warning">{cycle_count} cycles detected</span>' if cycle_count else '<span class="badge badge-success">0 (Acyclic)</span>'}
                    </div>
                </div>

                <div class="graph-toolbar">
                    <div class="graph-toolbar-left">
                        <input type="text" id="graphSearchInput" class="search-input" placeholder="Search files, symbols, packages..." onkeyup="onGraphSearchChange()">
                        <div class="btn-group" style="display:inline-flex; gap:0.25rem;">
                            <button class="btn btn-sm btn-secondary active" id="btnViewArch" onclick="switchGraphView('arch', this)" title="Show File and Module architecture">Architecture</button>
                            <button class="btn btn-sm btn-secondary" id="btnViewDetailed" onclick="switchGraphView('detailed', this)" title="Show all symbols and call edges">Symbols</button>
                            <button class="btn btn-sm btn-secondary" id="btnViewDeps" onclick="switchGraphView('deps', this)" title="Show packages and manifests">Packages</button>
                            <button class="btn btn-sm btn-secondary" id="btnViewFull" onclick="switchGraphView('full', this)" title="Show complete graph">Full Graph</button>
                        </div>
                    </div>
                    <div class="graph-toolbar-right">
                        <button class="btn btn-sm btn-secondary" id="btnDensityToggle" onclick="togglePeripheralCollapse()" title="Toggle collapsing peripheral low-ranked nodes">➖ Collapse Peripheral</button>
                        <button class="btn btn-sm btn-secondary" id="btnLabelMode" onclick="toggleLabelMode()" title="Toggle smart ranked labels vs all labels">🏷️ Smart Labels</button>
                        <button class="btn btn-sm btn-secondary" id="btnToggleLayout" onclick="toggleLayoutMode()" title="Toggle Top-to-Bottom / Left-to-Right / Force Layout">DAG: Top-Down</button>
                        <button class="btn btn-sm btn-secondary" onclick="echartsFitView()" title="Fit View">⛶ Fit</button>
                        <button class="btn btn-sm btn-secondary" onclick="echartsResetView()" title="Reset Graph">⟲ Reset</button>
                    </div>
                </div>

                <div class="graph-view-wrapper" id="graphContainerWrapper">
                    <div class="graph-viewport" id="graphViewport">
                        <div id="depEchartsChart"></div>
                    </div>
                    <div class="graph-details-sidebar" id="graphDetailsSidebar">
                        <div class="details-panel-title">
                            <span>Selected Entity</span>
                            <span class="badge badge-neutral" id="sideNodeType">Info</span>
                        </div>
                        <div id="sidebarContentPlaceholder" class="empty-state" style="margin-top:1rem; padding:1.25rem 0.85rem;">
                            Select a node to inspect its dependency relationships.
                        </div>
                        <div id="sidebarContentActive" style="display:none;">
                            <div class="node-detail-field">
                                <div class="node-detail-label">Entity Name</div>
                                <div class="node-detail-value"><strong id="sideNodeName" style="color:var(--primary); font-size:0.95rem;">-</strong></div>
                            </div>
                            <div class="node-detail-field">
                                <div class="node-detail-label">Visualization Priority</div>
                                <div class="node-detail-value" id="sideNodeRank">-</div>
                            </div>
                            <div class="node-detail-field">
                                <div class="node-detail-label">File / Path</div>
                                <div class="node-detail-value"><code id="sideNodePath">-</code></div>
                            </div>
                            <div class="node-detail-field">
                                <div class="node-detail-label">Impact Risk Classification</div>
                                <div class="node-detail-value" id="sideNodeRisk">-</div>
                            </div>
                            <div class="node-detail-field" id="sideRoleField">
                                <div class="node-detail-label">Architectural Role</div>
                                <div class="node-detail-value" id="sideNodeRole">-</div>
                            </div>
                            <div class="node-detail-field" id="sidePurposeField">
                                <div class="node-detail-label">Functional Purpose</div>
                                <div class="node-detail-value" id="sideNodePurpose" style="font-size:0.8125rem; color:var(--text-secondary);">-</div>
                            </div>
                            <div class="node-detail-field" id="sideOutgoingField">
                                <div class="node-detail-label">Dependencies (<span id="sideOutCount">0</span>)</div>
                                <div class="node-detail-value" id="sideOutgoingList" style="font-size:0.8125rem;">-</div>
                            </div>
                            <div class="node-detail-field" id="sideIncomingField">
                                <div class="node-detail-label">Dependents / Callers (<span id="sideInCount">0</span>)</div>
                                <div class="node-detail-value" id="sideIncomingList" style="font-size:0.8125rem;">-</div>
                            </div>
                            <div class="node-detail-field" id="sideSymbolsField">
                                <div class="node-detail-label">Declared AST Symbols (<span id="sideSymCount">0</span>)</div>
                                <div class="node-detail-value" id="sideSymbolsList" style="font-size:0.8125rem;">-</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="graph-legend-bar">
                    <div class="legend-items">
                        <span class="legend-item"><span class="legend-dot" style="background:#1d4ed8;"></span> Target Entity</span>
                        <span class="legend-item"><span class="legend-dot" style="background:#3b82f6;"></span> Direct (Rank 1)</span>
                        <span class="legend-item"><span class="legend-dot" style="background:#0d9488;"></span> Core / High-Connectivity</span>
                        <span class="legend-item"><span class="legend-dot" style="background:#94a3b8;"></span> Peripheral / Transitive</span>
                        <span class="legend-item"><span class="legend-dot" style="background:#d97706;"></span> Manifest / Package</span>
                        <span class="legend-item"><span class="legend-line" style="background:#3b82f6;"></span> Imports</span>
                        <span class="legend-item"><span class="legend-line" style="background:#6366f1;"></span> Calls</span>
                        <span class="legend-item"><span class="legend-line" style="background:#64748b; border-top:1px dashed #64748b; height:0;"></span> Defines</span>
                        <span class="legend-item"><span class="legend-line" style="background:#8b5cf6;"></span> Inherits</span>
                    </div>
                    <div>
                        <span>💡 Scroll to Zoom • Drag to Pan • Click Node to Focus</span>
                    </div>
                </div>
            </div>
        </section>

        <!-- Project Execution & Developer Commands Guide -->
        <section class="report-section" id="installation">
            <details class="section-panel card" open>
                <summary class="section-panel-header">
                    <div class="header-left">
                        <span class="dropdown-chevron">▶</span>
                        <a href="#installation" class="anchor-link" title="Direct link to Developer Commands" onclick="event.stopPropagation()">#</a>
                        <h2 class="section-title">Project Execution & Developer Commands</h2>
                        <span class="badge badge-neutral">{len(project_cmds)} Detected</span>
                    </div>
                </summary>
                <div class="panel-body">
                    <p class="narrative-text" style="margin-bottom: 1rem;">
                        Verified setup, installation, build, test, and runtime commands detected from workspace manifests:
                    </p>

                    {project_commands_html}

                    <details class="collapsible-details" style="margin-top: 1.25rem; padding-top: 0.75rem; border-top: 1px solid var(--border-subtle);">
                        <summary>⚡ WIA Workspace Inspection & Agent Commands</summary>
                        <div style="margin-top: 0.75rem;">
                            <div class="cmd-item">
                                <div class="cmd-desc">Query repository architecture, data flow, and components:</div>
                                <div class="cmd-box">
                                    <span class="cmd-text">wia ask "Explain the system architecture, entrypoints, and data flow of {ws_name}"</span>
                                    <button class="btn btn-sm btn-secondary copy-btn" onclick="copyFromBox(this)">Copy</button>
                                </div>
                            </div>
                            <div class="cmd-item">
                                <div class="cmd-desc">Perform refactoring blast-radius and impact analysis on project files:</div>
                                <div class="cmd-box">
                                    <span class="cmd-text">wia impact {sample_impact_file}</span>
                                    <button class="btn btn-sm btn-secondary copy-btn" onclick="copyFromBox(this)">Copy</button>
                                </div>
                            </div>
                            <div class="cmd-item">
                                <div class="cmd-desc">Regenerate this standalone interactive HTML report:</div>
                                <div class="cmd-box">
                                    <span class="cmd-text">wia report --output wia-report.html</span>
                                    <button class="btn btn-sm btn-secondary copy-btn" onclick="copyFromBox(this)">Copy</button>
                                </div>
                            </div>
                        </div>
                    </details>
                </div>
            </details>
        </section>

        <!-- Component Architecture Breakdown -->
        <section class="report-section" id="components">
            <details class="section-panel card" open>
                <summary class="section-panel-header">
                    <div class="header-left">
                        <span class="dropdown-chevron">▶</span>
                        <a href="#components" class="anchor-link" title="Direct link to Component Architecture" onclick="event.stopPropagation()">#</a>
                        <h2 class="section-title">System Component Architecture</h2>
                        <span class="badge badge-info">{len(components_map)} Component Roles</span>
                    </div>
                </summary>
                <div class="panel-body">
                    <div class="grid-2">
                        {components_html}
                    </div>
                </div>
            </details>
        </section>

        <!-- Accumulated Batch Intelligence Log -->
        <section class="report-section" id="batch-narratives">
            <details class="section-panel card" open>
                <summary class="section-panel-header">
                    <div class="header-left">
                        <span class="dropdown-chevron">▶</span>
                        <a href="#batch-narratives" class="anchor-link" title="Direct link to Batch Analysis Log" onclick="event.stopPropagation()">#</a>
                        <h2 class="section-title">Accumulated Batch Analysis Log</h2>
                        <span class="badge badge-info">{len(batches)} Batches</span>
                        <span class="badge badge-success">{pct}% Coverage</span>
                    </div>
                </summary>
                <div class="panel-body">
                    <div class="card" style="background: var(--surface-alt); margin-bottom: 1.25rem;">
                        <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.875rem;">
                            <span>Accumulated Progress ({len(completed_batches)} of {len(batches)} Batches Completed)</span>
                            <strong>{pct}%</strong>
                        </div>
                        <div class="progress-bar-bg">
                            <div class="progress-bar-fill" style="width: {pct}%;"></div>
                        </div>
                        <div style="display:flex; gap:0.5rem; margin-top:0.75rem; flex-wrap:wrap;">
                            <span class="badge badge-success">Completed: {len(completed_batches)}</span>
                            <span class="badge badge-warning">Running: {len(running_batches)}</span>
                            <span class="badge badge-neutral">Pending: {len(pending_batches)}</span>
                            {f'<span class="badge badge-danger">Failed: {len(failed_batches)}</span>' if failed_batches else ''}
                        </div>
                    </div>

                    <div>
                        {batch_narratives_html}
                    </div>
                </div>
            </details>
        </section>

        <!-- File-by-File Technical Intelligence Narratives -->
        <section class="report-section" id="file-narratives">
            <details class="section-panel card" open>
                <summary class="section-panel-header">
                    <div class="header-left">
                        <span class="dropdown-chevron">▶</span>
                        <a href="#file-narratives" class="anchor-link" title="Direct link to File Intelligence" onclick="event.stopPropagation()">#</a>
                        <h2 class="section-title">File-by-File Codebase Intelligence</h2>
                        <span class="badge badge-info">{len(files_data)} Files</span>
                    </div>
                </summary>
                <div class="panel-body">
                    <div style="margin-bottom: 1rem; display:flex; gap:0.75rem; flex-wrap:wrap;">
                        <input type="text" id="fileSearch" class="search-input" style="flex:1;" placeholder="Filter files by path, symbol, module role..." onkeyup="filterFiles()">
                        <select id="languageSelect" class="search-input" style="min-width:200px;" onchange="onLanguageSelect(this.value)">
                            {language_select_options_html}
                        </select>
                    </div>

                    <div id="fileList">
                        {grouped_files_html}
                    </div>
                </div>
            </details>
        </section>

        <!-- Security Findings (if present) -->
        {security_section_html}

        <!-- Manifest Dependencies (if present) -->
        {deps_section_html}
    </main>

    <script>
        window.WIA_REPORT_DATA = {report_json_data};
        window.WIA_GRAPH_DATA = {graph_json_data};

        function copyFromBox(btn) {{
            const box = btn.closest('.cmd-box');
            if (!box) return;
            const textEl = box.querySelector('.cmd-text');
            const text = textEl ? textEl.innerText.trim() : '';
            if (!text) return;

            navigator.clipboard.writeText(text).then(() => {{
                const originalText = btn.innerText;
                btn.innerText = 'Copied!';
                btn.classList.add('btn-primary');
                setTimeout(() => {{
                    btn.innerText = originalText;
                    btn.classList.remove('btn-primary');
                }}, 2000);
            }}).catch(() => {{
                const el = document.createElement('textarea');
                el.value = text;
                document.body.appendChild(el);
                el.select();
                document.execCommand('copy');
                document.body.removeChild(el);
                btn.innerText = 'Copied!';
                setTimeout(() => {{ btn.innerText = 'Copy'; }}, 2000);
            }});
        }}

        function onLanguageSelect(langSlug) {{
            const selectEl = document.getElementById('languageSelect');
            if (selectEl && selectEl.value !== langSlug) {{
                selectEl.value = langSlug;
            }}

            if (!langSlug) return;

            const parentSection = document.getElementById('file-narratives');
            if (parentSection) {{
                const details = parentSection.querySelector('details');
                if (details) details.open = true;
            }}

            const targetPanel = document.getElementById('lang-' + langSlug);
            if (targetPanel) {{
                targetPanel.open = true;
                targetPanel.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
            }}
        }}

        function toggleLanguageDetails(langSectionId) {{
            const sec = document.getElementById(langSectionId);
            if (!sec) return;
            const detailsList = sec.querySelectorAll('.file-details');
            if (!detailsList.length) return;
            const anyClosed = Array.from(detailsList).some(d => !d.open);
            detailsList.forEach(d => d.open = anyClosed);
        }}

        function filterFiles() {{
            const input = document.getElementById('fileSearch').value.toLowerCase().trim();
            const cards = document.querySelectorAll('.file-card');
            const panels = document.querySelectorAll('[data-language-group]');

            if (!input) {{
                cards.forEach(c => c.style.display = 'block');
                panels.forEach(p => p.style.display = 'block');
                return;
            }}

            cards.forEach(card => {{
                const path = card.getAttribute('data-filepath') || '';
                const text = card.innerText.toLowerCase();
                if (path.includes(input) || text.includes(input)) {{
                    card.style.display = 'block';
                }} else {{
                    card.style.display = 'none';
                }}
            }});

            panels.forEach(panel => {{
                const hasVisible = Array.from(panel.querySelectorAll('.file-card')).some(c => c.style.display !== 'none');
                if (hasVisible) {{
                    panel.style.display = 'block';
                    panel.open = true;
                }} else {{
                    panel.style.display = 'none';
                }}
            }});
        }}

        function filterDepEcosystem(eco, btn) {{
            document.querySelectorAll('.dep-filter-btn').forEach(b => b.classList.remove('active'));
            if (btn) btn.classList.add('active');

            const rows = document.querySelectorAll('#dependencies table tbody tr');
            rows.forEach(r => {{
                if (eco === 'all') {{
                    r.style.display = '';
                }} else {{
                    const ecoBadge = r.querySelector('.badge-info');
                    const text = ecoBadge ? ecoBadge.innerText.toLowerCase() : '';
                    r.style.display = (text === eco.toLowerCase()) ? '' : 'none';
                }}
            }});
        }}

        // Smooth navigation & automatic details expansion
        function openTargetDetails(targetId) {{
            if (!targetId) return;
            const el = document.getElementById(targetId);
            if (!el) return;

            if (el.tagName && el.tagName.toLowerCase() === 'details') {{
                el.open = true;
            }}
            let p = el.parentElement;
            while (p) {{
                if (p.tagName && p.tagName.toLowerCase() === 'details') {{
                    p.open = true;
                }}
                p = p.parentElement;
            }}
            el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        }}

        document.querySelectorAll('a[href^="#"]').forEach(a => {{
            a.addEventListener('click', function(e) {{
                const id = this.getAttribute('href').substring(1);
                if (id) {{
                    openTargetDetails(id);
                }}
            }});
        }});

        window.addEventListener('hashchange', () => {{
            const hash = window.location.hash.replace('#', '');
            if (hash) openTargetDetails(hash);
        }});

        // Scrollspy for sidebar menu
        function initScrollSpy() {{
            const sections = document.querySelectorAll('section[id]');
            const navLinks = document.querySelectorAll('.nav-menu .nav-item a');
            const mainEl = document.getElementById('mainContainer');
            if (!mainEl) return;

            mainEl.addEventListener('scroll', () => {{
                let current = '';
                const scrollPos = mainEl.scrollTop + 140;
                sections.forEach(sec => {{
                    const top = sec.offsetTop;
                    const height = sec.offsetHeight;
                    if (scrollPos >= top && scrollPos < top + height) {{
                        current = sec.getAttribute('id');
                    }}
                }});

                if (current) {{
                    navLinks.forEach(link => {{
                        link.classList.remove('active');
                        if (link.getAttribute('href') === '#' + current) {{
                            link.classList.add('active');
                        }}
                    }});
                }}
            }});
        }}

        // =========================================================
        // Advanced Ranked Interactive Dependency Graph Engine
        // =========================================================
        let graphChart = null;
        const MAX_INITIAL_NODES = 50;

        const graphState = {{
            viewMode: 'arch',       // 'arch', 'detailed', 'deps', 'full'
            layoutMode: 'dag-tb',    // 'dag-tb' (top-down), 'dag-lr' (left-right), 'force'
            collapsePeripheral: true, // Collapse Rank 4+ nodes when count > 30
            smartLabels: true,       // Only render labels on Target, Direct, Core
            searchTerm: '',
            selectedNodeId: null,
            highlightCycles: false,
            expandedGroups: new Set(),
            rawNodes: [],
            rawEdges: []
        }};

        function initGraphEngine() {{
            const container = document.getElementById('depEchartsChart');
            if (!container) return;

            const graphData = window.WIA_GRAPH_DATA || {{}};
            const nodes = graphData.nodes || [];
            const edges = graphData.edges || [];

            if (nodes.length === 0) {{
                container.innerHTML = '<div class="empty-state" style="margin:2rem;">Dependency graph unavailable<br><span style="font-size:0.8rem; color:#718096;">No graph relationships were returned for this analysis.</span></div>';
                return;
            }}

            if (typeof echarts === 'undefined') {{
                const wrapper = document.getElementById('graphContainerWrapper');
                if (wrapper && !wrapper.querySelector('.offline-notice')) {{
                    const notice = document.createElement('div');
                    notice.className = 'offline-notice';
                    notice.innerHTML = '<p><strong>Dependency Graph Renderer Notice</strong></p><p style="color:#718096; font-size:0.825rem;">Interactive canvas chart is loading or operating in offline fallback mode.</p>';
                    wrapper.appendChild(notice);
                }}
                return;
            }}

            if (!graphChart) {{
                graphChart = echarts.init(container, null, {{ renderer: 'canvas' }});
                window.addEventListener('resize', () => {{
                    if (graphChart) graphChart.resize();
                }});
                if (window.ResizeObserver) {{
                    const ro = new ResizeObserver(() => {{
                        if (graphChart) graphChart.resize();
                    }});
                    ro.observe(container);
                }}

                graphChart.on('click', function(params) {{
                    if (params.dataType === 'node') {{
                        if (params.data.isGroupNode) {{
                            toggleGroupExpansion(params.data.groupId);
                        }} else {{
                            selectGraphNode(params.data.id);
                        }}
                    }}
                }});
            }}

            graphState.rawNodes = nodes;
            graphState.rawEdges = edges;

            // Auto-select Target node if present
            const targetNode = nodes.find(n => n.vis_rank === 0);
            if (targetNode) {{
                selectGraphNode(targetNode.id);
            }}

            renderGraphView();
        }}

        function toggleGroupExpansion(groupId) {{
            if (graphState.expandedGroups.has(groupId)) {{
                graphState.expandedGroups.delete(groupId);
            }} else {{
                graphState.expandedGroups.add(groupId);
            }}
            renderGraphView();
        }}

        function togglePeripheralCollapse() {{
            graphState.collapsePeripheral = !graphState.collapsePeripheral;
            const btn = document.getElementById('btnDensityToggle');
            if (btn) {{
                btn.innerText = graphState.collapsePeripheral ? '➖ Collapse Peripheral' : '➕ Expand All';
            }}
            renderGraphView();
        }}

        function toggleLabelMode() {{
            graphState.smartLabels = !graphState.smartLabels;
            const btn = document.getElementById('btnLabelMode');
            if (btn) {{
                btn.innerText = graphState.smartLabels ? '🏷️ Smart Labels' : '🏷️ All Labels';
            }}
            renderGraphView();
        }}

        function toggleHighlightCycles() {{
            graphState.highlightCycles = !graphState.highlightCycles;
            renderGraphView();
        }}

        function computeHierarchicalLayout(nodes, edges, direction) {{
            // Direction: 'tb' (Top-to-Bottom) or 'lr' (Left-to-Right)
            // Group nodes by visual hierarchy rank (Layer 0 = Target, Layer 1 = Direct, Layer 2 = Secondary, Layer 3 = Core, Layer 4 = Peripheral/Groups)
            const layers = {{ 0: [], 1: [], 2: [], 3: [], 4: [] }};

            nodes.forEach(n => {{
                const r = Math.min(4, Math.max(0, n.vis_rank !== undefined ? n.vis_rank : 4));
                layers[r].push(n);
            }});

            const layerSpacing = direction === 'tb' ? 170 : 250;
            const nodeSpacing = direction === 'tb' ? 200 : 54;

            Object.keys(layers).forEach(layerKey => {{
                const layerIdx = Number(layerKey);
                const group = layers[layerIdx];
                if (!group.length) return;

                const totalBreadth = (group.length - 1) * nodeSpacing;
                const startBreadth = -(totalBreadth / 2);

                group.forEach((node, idx) => {{
                    const breadthPos = startBreadth + (idx * nodeSpacing);
                    const depthPos = layerIdx * layerSpacing;

                    if (direction === 'tb') {{
                        node.x = breadthPos;
                        node.y = depthPos;
                    }} else {{
                        node.x = depthPos;
                        node.y = breadthPos;
                    }}
                }});
            }});
        }}

        function renderGraphView() {{
            if (!graphChart) return;

            const mode = graphState.viewMode;
            const search = graphState.searchTerm.toLowerCase();
            const doCollapse = graphState.collapsePeripheral && graphState.rawNodes.length > 30;

            // 1. Filter Nodes based on viewMode
            let filteredNodes = graphState.rawNodes.filter(n => {{
                if (mode === 'arch') {{
                    return n.type === 'file' || n.type === 'manifest';
                }} else if (mode === 'deps') {{
                    return n.type === 'file' || n.type === 'manifest' || n.type === 'package';
                }} else if (mode === 'detailed') {{
                    return n.type === 'file' || n.type === 'class' || n.type === 'function' || n.type === 'method';
                }}
                return true; // 'full'
            }});

            // 2. Peripheral Node Grouping / Collapsing
            let displayNodes = [];
            let displayEdges = [];
            let collapsedPeripheralNodes = [];

            if (doCollapse) {{
                filteredNodes.forEach(n => {{
                    // If peripheral rank (>= 4) and not target/direct and not expanded
                    const isExpanded = graphState.expandedGroups.has('group-peripheral');
                    if (n.vis_rank >= 4 && !isExpanded && !search) {{
                        collapsedPeripheralNodes.push(n);
                    }} else {{
                        displayNodes.push(n);
                    }}
                }});

                if (collapsedPeripheralNodes.length > 0) {{
                    const groupNode = {{
                        id: 'group-peripheral',
                        isGroupNode: true,
                        groupId: 'group-peripheral',
                        label: `+ ${{collapsedPeripheralNodes.length}} Peripheral Entities (Click to Expand)`,
                        type: 'cluster',
                        vis_rank: 4,
                        vis_rank_label: 'COLLAPSED GROUP',
                        metadata: {{
                            role: 'Grouped Peripheral Components',
                            purpose: 'Contains transitive and low-connectivity peripheral modules.'
                        }}
                    }};
                    displayNodes.push(groupNode);
                }}
            }} else {{
                displayNodes = filteredNodes;
            }}

            const activeNodeSet = new Set(displayNodes.map(n => n.id));

            // Map edges to active/group nodes
            graphState.rawEdges.forEach(e => {{
                let s = e.source;
                let t = e.target;

                if (!activeNodeSet.has(s) && doCollapse && collapsedPeripheralNodes.some(n => n.id === s)) {{
                    s = 'group-peripheral';
                }}
                if (!activeNodeSet.has(t) && doCollapse && collapsedPeripheralNodes.some(n => n.id === t)) {{
                    t = 'group-peripheral';
                }}

                if (activeNodeSet.has(s) && activeNodeSet.has(t) && s !== t) {{
                    displayEdges.push({{
                        source: s,
                        target: t,
                        relation: e.relation,
                        edge_priority: e.edge_priority || 2,
                        edgeData: e
                    }});
                }}
            }});

            // Layout coordinates
            if (graphState.layoutMode === 'dag-tb') {{
                computeHierarchicalLayout(displayNodes, displayEdges, 'tb');
            }} else if (graphState.layoutMode === 'dag-lr') {{
                computeHierarchicalLayout(displayNodes, displayEdges, 'lr');
            }}

            // Convert to ECharts options
            const echartsNodes = displayNodes.map(n => {{
                const isSelected = (n.id === graphState.selectedNodeId);
                const isSearchMatch = search && (
                    (n.label && n.label.toLowerCase().includes(search)) ||
                    (n.file_path && n.file_path.toLowerCase().includes(search)) ||
                    (n.id && n.id.toLowerCase().includes(search))
                );

                let size = 18;
                let color = '#2563eb';
                let borderColor = '#1d4ed8';

                if (n.isGroupNode) {{
                    size = 26;
                    color = '#475569';
                    borderColor = '#334155';
                }} else if (n.vis_rank === 0) {{
                    size = 32;
                    color = '#1d4ed8';
                    borderColor = '#172554';
                }} else if (n.vis_rank === 1) {{
                    size = 22;
                    color = '#3b82f6';
                    borderColor = '#1d4ed8';
                }} else if (n.vis_rank === 2) {{
                    size = 17;
                    color = '#60a5fa';
                    borderColor = '#3b82f6';
                }} else if (n.vis_rank === 3) {{
                    size = 19;
                    color = '#0d9488';
                    borderColor = '#0f766e';
                }} else if (n.vis_rank >= 4) {{
                    size = 12;
                    color = '#94a3b8';
                    borderColor = '#cbd5e1';
                }}

                if (n.type === 'package' || n.type === 'manifest') {{
                    color = '#d97706';
                    borderColor = '#b45309';
                }}

                // Smart Labeling
                let showLabel = false;
                if (!graphState.smartLabels || isSelected || isSearchMatch || n.vis_rank <= 1 || n.isGroupNode) {{
                    showLabel = true;
                }}

                const opacity = (search && !isSearchMatch) ? 0.25 : 1.0;

                return {{
                    id: n.id,
                    name: n.id,
                    value: n.label,
                    symbolSize: isSelected ? (size + 8) : size,
                    x: n.x,
                    y: n.y,
                    draggable: true,
                    itemStyle: {{
                        color: color,
                        borderColor: isSelected ? '#172033' : borderColor,
                        borderWidth: isSelected ? 3 : (n.isGroupNode ? 2 : 1.5),
                        borderType: n.isGroupNode ? 'dashed' : 'solid',
                        opacity: opacity,
                        shadowBlur: isSelected ? 10 : 0,
                        shadowColor: 'rgba(0,0,0,0.25)'
                    }},
                    label: {{
                        show: showLabel,
                        position: graphState.layoutMode === 'dag-tb' ? 'bottom' : 'right',
                        formatter: function() {{
                            return n.label.length > 22 ? n.label.substring(0, 20) + '…' : n.label;
                        }},
                        color: '#172033',
                        fontSize: (n.vis_rank === 0 || isSelected) ? 12 : 11,
                        fontWeight: (n.vis_rank === 0 || isSelected) ? 700 : 500
                    }},
                    nodeData: n
                }};
            }});

            const echartsLinks = displayEdges.map(e => {{
                let lineColor = '#cbd5e1';
                let width = 1.0;
                let opacity = 0.4;

                if (e.edge_priority === 1) {{
                    lineColor = '#2563eb';
                    width = 2.2;
                    opacity = 0.85;
                }} else if (e.edge_priority === 2) {{
                    lineColor = '#64748b';
                    width = 1.4;
                    opacity = 0.6;
                }}

                if (e.relation === 'CALLS') {{
                    lineColor = '#6366f1';
                }} else if (e.relation === 'INHERITS') {{
                    lineColor = '#8b5cf6';
                }} else if (e.relation === 'DEFINES') {{
                    lineColor = '#94a3b8';
                }}

                return {{
                    source: e.source,
                    target: e.target,
                    lineStyle: {{
                        color: lineColor,
                        width: width,
                        curveness: 0.18,
                        opacity: opacity
                    }},
                    edgeData: e
                }};
            }});

            const option = {{
                backgroundColor: 'transparent',
                tooltip: {{
                    trigger: 'item',
                    backgroundColor: '#172033',
                    borderColor: '#334155',
                    borderWidth: 1,
                    padding: [8, 12],
                    textStyle: {{ color: '#f8fafc', fontSize: 12 }},
                    formatter: function(params) {{
                        if (params.dataType === 'edge') {{
                            const e = params.data.edgeData;
                            return `<div style="font-size:11px; color:#94a3b8;">Relationship Edge: <strong>${{htmlEscape(e.relation)}}</strong></div>`;
                        }}
                        const n = params.data.nodeData;
                        if (!n) return params.name;
                        if (n.isGroupNode) {{
                            return `<strong>${{htmlEscape(n.label)}}</strong><div style="font-size:11px; color:#94a3b8; margin-top:3px;">Click node to expand all grouped items</div>`;
                        }}
                        const rankTag = `<span style="font-size:10px; background:#2563eb; color:#fff; padding:1px 5px; border-radius:3px; font-weight:bold;">${{n.vis_rank_label || 'NODE'}}</span>`;
                        return `<div style="display:flex; justify-content:space-between; gap:10px; align-items:center;">
                                    <strong style="color:#60a5fa;">${{htmlEscape(n.label)}}</strong>
                                    ${{rankTag}}
                                </div>
                                <div style="font-size:11px; color:#cbd5e1; margin-top:3px;">Type: <strong>${{htmlEscape(n.type)}}</strong></div>
                                ${{n.file_path ? `<div style="font-size:10.5px; color:#94a3b8;">Path: ${{htmlEscape(n.file_path)}}</div>` : ''}}`;
                    }}
                }},
                series: [{{
                    type: 'graph',
                    layout: graphState.layoutMode === 'force' ? 'force' : 'none',
                    data: echartsNodes,
                    links: echartsLinks,
                    roam: true,
                    draggable: true,
                    edgeSymbol: ['none', 'arrow'],
                    edgeSymbolSize: [4, 7],
                    scaleLimit: {{ min: 0.15, max: 4.0 }},
                    force: {{
                        repulsion: 240,
                        edgeLength: [60, 150],
                        gravity: 0.08,
                        friction: 0.6
                    }},
                    emphasis: {{
                        focus: 'adjacency',
                        lineStyle: {{ width: 3, opacity: 1 }}
                    }}
                }}]
            }};

            graphChart.setOption(option, true);
        }}

        function selectGraphNode(nodeId) {{
            graphState.selectedNodeId = nodeId;
            const node = graphState.rawNodes.find(n => n.id === nodeId);
            if (!node) return;

            const placeholder = document.getElementById('sidebarContentPlaceholder');
            const active = document.getElementById('sidebarContentActive');
            if (placeholder) placeholder.style.display = 'none';
            if (active) active.style.display = 'block';

            const nameEl = document.getElementById('sideNodeName');
            const rankEl = document.getElementById('sideNodeRank');
            const pathEl = document.getElementById('sideNodePath');
            const typeEl = document.getElementById('sideNodeType');
            const riskEl = document.getElementById('sideNodeRisk');
            const roleEl = document.getElementById('sideNodeRole');
            const purposeEl = document.getElementById('sideNodePurpose');

            if (nameEl) nameEl.innerText = node.label;
            if (pathEl) pathEl.innerText = node.file_path || 'Workspace Root';
            if (typeEl) typeEl.innerText = node.type.toUpperCase();

            if (rankEl) {{
                const rLabel = node.vis_rank_label || 'Rank ' + node.vis_rank;
                const rColor = node.vis_rank === 0 ? 'badge-info' : node.vis_rank === 1 ? 'badge-primary' : 'badge-neutral';
                rankEl.innerHTML = `<span class="badge ${{rColor}}">${{rLabel}} (Priority Score: ${{node.vis_score || '-'}})</span>`;
            }}

            const risk = (node.metadata && node.metadata.risk) ? node.metadata.risk : 'LOW';
            const riskBadgeClass = risk === 'HIGH' ? 'badge-danger' : risk === 'MEDIUM' ? 'badge-warning' : 'badge-success';
            if (riskEl) {{
                riskEl.innerHTML = `<span class="badge ${{riskBadgeClass}}">${{risk}} RISK</span>`;
            }}

            if (roleEl) roleEl.innerText = (node.metadata && node.metadata.role) ? node.metadata.role : 'Application Component';
            if (purposeEl) purposeEl.innerText = (node.metadata && node.metadata.purpose) ? node.metadata.purpose : 'Static code analysis entity in workspace dependency tree.';

            // Outgoing edges
            const outgoing = graphState.rawEdges.filter(e => e.source === nodeId);
            const outCount = document.getElementById('sideOutCount');
            const outList = document.getElementById('sideOutgoingList');
            if (outCount) outCount.innerText = outgoing.length;
            if (outList) {{
                if (outgoing.length === 0) {{
                    outList.innerHTML = '<span class="text-muted">None</span>';
                }} else {{
                    outList.innerHTML = outgoing.slice(0, 10).map(e => {{
                        const targetLabel = e.target.split(':').pop();
                        return `<a class="clickable-node-link" onclick="selectGraphNode('${{e.target}}')">→ <strong>${{htmlEscape(e.relation)}}</strong>: <code>${{htmlEscape(targetLabel)}}</code></a>`;
                    }}).join('');
                }}
            }}

            // Incoming edges
            const incoming = graphState.rawEdges.filter(e => e.target === nodeId);
            const inCount = document.getElementById('sideInCount');
            const inList = document.getElementById('sideIncomingList');
            if (inCount) inCount.innerText = incoming.length;
            if (inList) {{
                if (incoming.length === 0) {{
                    inList.innerHTML = '<span class="text-muted">None</span>';
                }} else {{
                    inList.innerHTML = incoming.slice(0, 10).map(e => {{
                        const sourceLabel = e.source.split(':').pop();
                        return `<a class="clickable-node-link" onclick="selectGraphNode('${{e.source}}')">← <strong>${{htmlEscape(e.relation)}}</strong> from: <code>${{htmlEscape(sourceLabel)}}</code></a>`;
                    }}).join('');
                }}
            }}

            // Declared symbols
            const syms = (node.metadata && node.metadata.symbols) ? node.metadata.symbols : [];
            const symCount = document.getElementById('sideSymCount');
            const symList = document.getElementById('sideSymbolsList');
            const symField = document.getElementById('sideSymbolsField');
            if (symCount) symCount.innerText = syms.length;
            if (symField) symField.style.display = syms.length ? 'block' : 'none';
            if (symList && syms.length) {{
                symList.innerHTML = syms.slice(0, 8).map(s => `<div><span class="badge badge-neutral" style="font-size:0.65rem;">${{htmlEscape(s.type)}}</span> <code>${{htmlEscape(s.name)}}</code> (L${{s.line}})</div>`).join('');
            }}

            renderGraphView();
        }}

        function switchGraphView(mode, btn) {{
            graphState.viewMode = mode;
            document.querySelectorAll('.graph-toolbar .btn-group button').forEach(b => {{
                if (b.id && b.id.startsWith('btnView')) b.classList.remove('active');
            }});
            if (btn) btn.classList.add('active');
            renderGraphView();
        }}

        function toggleLayoutMode() {{
            const btn = document.getElementById('btnToggleLayout');
            if (graphState.layoutMode === 'dag-tb') {{
                graphState.layoutMode = 'dag-lr';
                if (btn) btn.innerText = 'DAG: Left-Right';
            }} else if (graphState.layoutMode === 'dag-lr') {{
                graphState.layoutMode = 'force';
                if (btn) btn.innerText = 'Force-Directed';
            }} else {{
                graphState.layoutMode = 'dag-tb';
                if (btn) btn.innerText = 'DAG: Top-Down';
            }}
            renderGraphView();
        }}

        function echartsFitView() {{
            if (!graphChart) return;
            graphChart.dispatchAction({{ type: 'restore' }});
        }}

        function echartsResetView() {{
            graphState.searchTerm = '';
            graphState.selectedNodeId = null;
            graphState.expandedGroups.clear();
            const input = document.getElementById('graphSearchInput');
            if (input) input.value = '';
            renderGraphView();
            echartsFitView();
        }}

        function onGraphSearchChange() {{
            const input = document.getElementById('graphSearchInput');
            graphState.searchTerm = input ? input.value : '';
            renderGraphView();

            if (graphState.searchTerm) {{
                const match = graphState.rawNodes.find(n =>
                    (n.label && n.label.toLowerCase().includes(graphState.searchTerm.toLowerCase())) ||
                    (n.id && n.id.toLowerCase().includes(graphState.searchTerm.toLowerCase()))
                );
                if (match) {{
                    selectGraphNode(match.id);
                }}
            }}
        }}

        function htmlEscape(str) {{
            if (!str) return '';
            return String(str)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;');
        }}

        // Auto-refresh dynamic updates
        async function checkForDynamicUpdates() {{
            try {{
                const res = await fetch('.wia/report_data.json?t=' + Date.now());
                if (res.ok) {{
                    const fresh = await res.json();
                    if (fresh && fresh.indexed_at !== window.WIA_REPORT_DATA.indexed_at) {{
                        window.location.reload();
                    }}
                }}
            }} catch(e) {{}}
        }}

        window.addEventListener('DOMContentLoaded', () => {{
            checkForDynamicUpdates();
            setInterval(checkForDynamicUpdates, 3000);
            initScrollSpy();
            setTimeout(initGraphEngine, 40);
        }});
    </script>
</body>
</html>
"""
        target_file.write_text(html_content, encoding="utf-8")
        return target_file

