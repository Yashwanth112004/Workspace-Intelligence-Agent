"""Standalone HTML workspace report generator for WIA — Developer Intelligence Narrative Engine."""

import html
import json
from pathlib import Path
from wia.analyzers.dependency.conflict_detector import ConflictDetector
from wia.analyzers.dependency.manifest_parser import ManifestParser
from wia.analyzers.git.git_analyzer import GitAnalyzer
from wia.analyzers.security.secret_scanner import SecretScanner
from wia.core.index_model import WorkspaceIndex
from wia.knowledge.graph import WorkspaceGraph
from wia.services.explanation_service import ExplanationService


class ReportGenerator:
    """Generates clean, developer-focused, batch-accumulating workspace intelligence narrative reports."""

    @classmethod
    def export_report_json(
        cls, index: WorkspaceIndex, output_path: str | Path | None = None
    ) -> Path:
        """Export structured workspace intelligence payload to JSON sidecar file."""
        ws_path = Path(index.workspace_path).resolve()
        target = (
            Path(output_path)
            if output_path
            else ws_path / ".wia" / "report_data.json"
        )
        target.parent.mkdir(parents=True, exist_ok=True)

        graph = WorkspaceGraph()
        graph.build_from_index(index)

        files_data = []
        for rel_path, rec in index.files.items():
            if rec.indexing_status != "INDEXED":
                continue
            expl = ExplanationService.explain_file_structured(rel_path, index, graph)
            files_data.append(expl)

        deps = ManifestParser.parse_workspace_manifests(ws_path)
        git_hotspots = GitAnalyzer.get_file_hotspots(ws_path, top_n=15)
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

        # Export JSON payload sidecar file
        cls.export_report_json(index, ws_path / ".wia" / "report_data.json")

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

        # High-Level Project Narrative Synthesis
        roles_summary = set(fd["role"].split(" — ")[0] for fd in files_data)
        roles_narrative = ", ".join(sorted(roles_summary)) if roles_summary else "Core Application Components"

        project_narrative_p1 = (
            f"<strong>{ws_name}</strong> is a software repository containing <strong>{total_indexed}</strong> indexed files "
            f"and <strong>{total_symbols}</strong> declared AST code symbols. Based on static analysis and graph dependency mapping, "
            f"the codebase implements functional roles across <em>{html.escape(roles_narrative)}</em>."
        )

        project_narrative_p2 = (
            f"Execution originates at entrypoints and CLI command modules, delegating core orchestration to service layers. "
            f"These services interact with storage engines (SQLite store, vector stores, and relationship graphs) to maintain "
            f"persistent workspace knowledge and generate architectural explanations."
        )

        project_narrative_p3 = (
            f"Workspace intelligence has been accumulated across <strong>{len(completed_batches)}</strong> completed analysis batches "
            f"out of <strong>{len(batches)}</strong> total batches ({pct}% completed). Each batch inspects source files, parses AST syntax trees, "
            f"extracts code symbols, scans security rules, and computes component change impact risks."
        )        # Component Architecture Breakdown Cards
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
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 0.5rem;">
                    <h3 style="margin:0; color:var(--accent-color); font-size:1.1rem;">{comp_name_esc}</h3>
                    <span class="badge badge-info">{len(comp_files)} Files</span>
                </div>
                <p class="narrative-text" style="font-size:0.9rem;">
                    Contains {len(comp_files)} workspace component(s) declaring {total_syms} AST code symbol(s).
                    Key modules include {file_names_str}.
                </p>
                <div class="header-meta">
                    Discovered Symbols: <strong>{total_syms}</strong> | High Impact Files: <strong>{high_impact_cnt}</strong>
                </div>
            </div>
            """

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

            err_html = f'<div class="error-msg">{html.escape(b.error_message)}</div>' if b.error_message else ""
            b_files_str = ", ".join([html.escape(p) for p in b.file_paths])

            batch_narratives_html += f"""
            <div class="card batch-card" id="batch-{b_id_esc.lower().replace(' ', '-')}">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 0.5rem;">
                    <h3 style="margin:0; color:var(--accent-color); font-size: 1.05rem;">
                        <a href="#batch-{b_id_esc.lower().replace(' ', '-')}" class="anchor-link">#</a> {b_id_esc} — Technical Narrative
                    </h3>
                    {status_badge}
                </div>
                <p class="narrative-text" style="font-size:0.9rem; margin-bottom: 0.5rem;">{b_narr}</p>
                {err_html}
                <details style="margin-top: 0.4rem;">
                    <summary style="font-size:0.8rem; color:var(--muted-color); cursor:pointer;">View Batch File List ({len(b.file_paths)} files)</summary>
                    <div style="margin-top:0.4rem; font-size:0.8rem; font-family:monospace; background:var(--code-bg); padding:0.5rem; border-radius:0.375rem; color:var(--text-color);">
                        {b_files_str}
                    </div>
                </details>
                <div class="header-meta" style="margin-top:0.4rem;">
                    Processed: <strong>{len(b.file_paths)} files</strong> | Duration: <strong>{b.duration_seconds:.2f}s</strong> | Timestamp: <strong>{html.escape(b.started_at[:19].replace('T', ' '))}</strong>
                </div>
            </div>
            """

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
            f'                    <option value="" selected disabled>-- Select a Language to View Files --</option>\n'
            f'                    <option value="all">🌐 All Languages ({len(files_data)} files)</option>\n'
        )
        grouped_files_html = ""

        for lang_name, lang_files in sorted_lang_groups:
            lang_slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in lang_name.lower())
            lang_id = f"lang-{lang_slug}"
            lang_name_esc = html.escape(lang_name)
            count = len(lang_files)

            # Language Icon
            icon = "🐍" if lang_name == "Python" else "📘" if lang_name == "TypeScript" else "📜" if lang_name == "JavaScript" else "⚙️" if lang_name in ("TOML", "JSON", "YAML") else "📄"

            language_nav_items_html += f"""
            <li class="nav-sub-item">
                <a href="#{lang_id}" onclick="onLanguageSelect('{lang_slug}')">
                    <span><span class="sub-bullet">•</span> {icon} {lang_name_esc}</span>
                    <span class="badge badge-outline" style="font-size:0.7rem; padding:0.1rem 0.4rem;">{count}</span>
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
                impact_level = fd["impact_risk_level"]
                batch_id = html.escape(fd["batch_id"])

                risk_class = (
                    "badge-danger"
                    if impact_level == "HIGH"
                    else "badge-warning"
                    if impact_level == "MEDIUM"
                    else "badge-success"
                )

                symbols_html = ""
                for s in fd["symbols"]:
                    stype = s.get("symbol_type")
                    if stype == "import":
                        continue
                    sname = html.escape(s.get("name", ""))
                    doc_raw = s.get("docstring") or ""
                    doc = html.escape(doc_raw.strip())
                    doc_str = f" — <span class='doc-text'>{doc}</span>" if doc else ""
                    symbols_html += f'<li class="sym-item"><span class="sym-type">{stype}</span> <code>{sname}</code>{doc_str}</li>'

                if not symbols_html:
                    symbols_html = '<li class="text-muted">No top-level functions or classes declared</li>'

                ws_deps_str = ", ".join([html.escape(d) for d in fd["workspace_dependencies"]]) if fd["workspace_dependencies"] else "None"
                used_by_str = ", ".join([html.escape(u) for u in fd["used_by"]]) if fd["used_by"] else "None"
                cls_cnt = len([s for s in fd.get("symbols", []) if s.get("symbol_type") == "class"])
                func_cnt = len([s for s in fd.get("symbols", []) if s.get("symbol_type") in ("function", "method")])
                total_sym_cnt = len(fd.get("symbols", []))

                file_narrative_text = (
                    f"The file <code>{rel_p}</code> fulfills the architectural role of <strong>{role}</strong>. "
                    f"{purpose} Declares {cls_cnt} class(es) and {func_cnt} function(s). "
                    f"Imports <em>{ws_deps_str}</em> and is imported by <em>{used_by_str}</em>. "
                    f"Evaluated change impact risk: <strong>{impact_level}</strong>."
                )

                group_cards_html += f"""
                <div class="card file-card" id="{file_anchor_id}" data-filepath="{rel_p.lower()}" data-language="{lang_slug}" data-batch="{batch_id}">
                    <div class="file-card-header">
                        <div>
                            <a href="#{file_anchor_id}" class="anchor-link" title="Direct link to {rel_p}">#</a>
                            <span class="file-title">{rel_p}</span>
                            <span class="badge badge-info">{lang}</span>
                            <span class="badge badge-outline">{batch_id}</span>
                        </div>
                        <span class="badge {risk_class}">Impact: {impact_level}</span>
                    </div>
                    <p class="narrative-text" style="font-size:0.9rem; margin-top: 0.4rem; margin-bottom: 0.5rem;">{file_narrative_text}</p>

                    <details class="file-details">
                        <summary>View Declared Symbols ({total_sym_cnt}) & Dependencies</summary>
                        <div class="details-content">
                            <ul class="sym-list">
                                {symbols_html}
                            </ul>
                            <div class="grid-2" style="font-size:0.85rem;">
                                <div>
                                    <strong>Depends On:</strong> {ws_deps_str}
                                </div>
                                <div>
                                    <strong>Used By:</strong> {used_by_str}
                                </div>
                            </div>
                        </div>
                    </details>
                </div>
                """

            grouped_files_html += f"""
            <div class="language-section" id="{lang_id}" data-language-group="{lang_slug}" style="display:none;">
                <div class="language-section-header">
                    <div style="display:flex; align-items:center; gap:0.6rem;">
                        <a href="#{lang_id}" class="anchor-link" style="font-size:1.2rem;" title="Direct link to {lang_name_esc} files">#</a>
                        <h3 style="margin:0; font-size:1.2rem; color:var(--text-color);">{lang_name_esc} Files</h3>
                        <span class="badge badge-info">{count} File{'s' if count != 1 else ''}</span>
                    </div>
                    <button class="toggle-btn" onclick="toggleLanguageDetails('{lang_id}')">Toggle All Details</button>
                </div>
                <div class="language-file-list">
                    {group_cards_html}
                </div>
            </div>
            """

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
            lang_items_html += f'<a href="#lang-{lang_slug}" class="badge badge-outline" style="text-decoration:none;">{lang_esc}: {count} files</a> '
        if not lang_items_html:
            lang_items_html = '<span class="text-muted">No language data</span>'

        # Security Findings HTML
        security_html = ""
        for sec in security_findings:
            sev_class = "badge-danger" if sec.severity.upper() in ("CRITICAL", "HIGH") else "badge-warning"
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
            <section id="security">
                <h2 class="section-heading"><a href="#security" class="anchor-link">#</a> Security Intelligence ({len(security_findings)} Findings)</h2>
                <div class="card">
                    <table>
                        <thead>
                            <tr><th>Severity</th><th>Type</th><th>Location</th><th>Evidence</th></tr>
                        </thead>
                        <tbody>
                            {security_html}
                        </tbody>
                    </table>
                </div>
            </section>
            """

        # Dependencies Section HTML (only if dependencies present)
        deps_section_html = ""
        if deps:
            deps_rows_html = ""
            for d in deps:
                pkg_name = getattr(d, "name", getattr(d, "package_name", ""))
                ver_spec = getattr(d, "version_spec", getattr(d, "specifier", "Any"))
                deps_rows_html += f"""
                <tr>
                    <td><strong>{html.escape(pkg_name)}</strong></td>
                    <td>{html.escape(ver_spec or 'Any')}</td>
                    <td><code>{html.escape(d.manifest_path)}</code></td>
                    <td>{html.escape(d.ecosystem)}</td>
                </tr>
                """
            deps_section_html = f"""
            <section id="dependencies">
                <h2 class="section-heading"><a href="#dependencies" class="anchor-link">#</a> Manifest Dependencies ({len(deps)})</h2>
                <div class="card">
                    <table>
                        <thead>
                            <tr><th>Package Name</th><th>Version</th><th>Manifest</th><th>Ecosystem</th></tr>
                        </thead>
                        <tbody>
                            {deps_rows_html}
                        </tbody>
                    </table>
                </div>
            </section>
            """

        report_json_data = json.dumps({
            "indexed_at": index.indexed_at,
            "index_version": index.index_version,
            "wia_version": index.wia_version,
            "stats": index.stats,
            "languages": index.languages,
            "frameworks": index.frameworks,
            "completed_batches": len(completed_batches),
            "total_batches": len(batches),
        })

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WIA Workspace Intelligence Report — {ws_name}</title>
    <style>
        :root {{
            --bg-color: #0b0f19;
            --sidebar-bg: #111827;
            --card-bg: #1f2937;
            --card-hover: #374151;
            --text-color: #f9fafb;
            --muted-color: #9ca3af;
            --accent-color: #38bdf8;
            --accent-glow: rgba(56, 189, 248, 0.25);
            --border-color: #374151;
            --danger-color: #f43f5e;
            --warning-color: #fbbf24;
            --success-color: #34d399;
            --code-bg: #111827;
        }}
        * {{ box-sizing: border-box; }}
        html {{ scroll-behavior: smooth; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 0;
            display: flex;
            height: 100vh;
            overflow: hidden;
        }}
        /* Sidebar */
        aside {{
            width: 270px;
            background-color: var(--sidebar-bg);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            padding: 1.25rem 1rem;
            flex-shrink: 0;
        }}
        .brand {{
            font-size: 1.2rem;
            font-weight: bold;
            color: var(--accent-color);
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .nav-menu {{
            list-style: none;
            padding: 0;
            margin: 0;
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
            overflow-y: auto;
        }}
        .nav-item a {{
            color: var(--muted-color);
            text-decoration: none;
            padding: 0.6rem 0.8rem;
            border-radius: 0.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.88rem;
            font-weight: 500;
            transition: all 0.15s ease;
        }}
        .nav-item a:hover, .nav-item a.active {{
            background-color: rgba(56, 189, 248, 0.12);
            color: var(--accent-color);
        }}
        .nav-sub-menu {{
            list-style: none;
            padding: 0.2rem 0 0.4rem 1rem;
            margin: 0;
            display: flex;
            flex-direction: column;
            gap: 0.2rem;
        }}
        .nav-sub-item a {{
            color: var(--muted-color);
            text-decoration: none;
            padding: 0.35rem 0.6rem;
            border-radius: 0.375rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 0.8rem;
            transition: all 0.15s ease;
        }}
        .nav-sub-item a:hover {{
            background-color: rgba(56, 189, 248, 0.08);
            color: var(--accent-color);
        }}
        .sub-bullet {{ margin-right: 0.35rem; color: var(--accent-color); font-size: 0.9rem; }}

        /* Main Content */
        main {{
            flex: 1;
            overflow-y: auto;
            padding: 2rem 2.5rem;
        }}
        header {{
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 1rem;
            margin-bottom: 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        h1 {{ margin: 0; color: var(--text-color); font-size: 1.75rem; }}
        .header-meta {{ color: var(--muted-color); font-size: 0.85rem; margin-top: 0.3rem; }}

        /* Anchor Links */
        .anchor-link {{
            color: var(--muted-color);
            text-decoration: none;
            font-size: 0.85em;
            margin-right: 0.35rem;
            opacity: 0.4;
            transition: opacity 0.2s ease, color 0.2s ease;
        }}
        .anchor-link:hover {{
            opacity: 1.0;
            color: var(--accent-color);
        }}
        :target {{
            animation: highlight-pulse 2s ease-out;
        }}
        @keyframes highlight-pulse {{
            0% {{ background-color: rgba(56, 189, 248, 0.2); outline: 2px solid var(--accent-color); }}
            100% {{ background-color: var(--card-bg); outline: none; }}
        }}

        /* Prose & Narratives */
        .narrative-card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-left: 4px solid var(--accent-color);
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}
        .narrative-card h2 {{
            margin-top: 0;
            margin-bottom: 0.75rem;
            font-size: 1.3rem;
            color: var(--accent-color);
        }}
        .narrative-text {{
            font-size: 0.95rem;
            line-height: 1.65;
            color: #e2e8f0;
            margin-bottom: 0.75rem;
        }}
        .narrative-text:last-child {{ margin-bottom: 0; }}

        /* Installation Commands Guide */
        .install-card {{
            background: linear-gradient(145deg, #162032, #1f2937);
            border: 1px solid rgba(56, 189, 248, 0.3);
            border-left: 4px solid var(--accent-color);
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}
        .cmd-box {{
            background-color: var(--code-bg);
            border: 1px solid var(--border-color);
            border-radius: 0.5rem;
            padding: 0.75rem 1rem;
            margin-bottom: 0.75rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-family: "JetBrains Mono", Consolas, "Courier New", monospace;
            font-size: 0.88rem;
        }}
        .cmd-text {{ color: #38bdf8; }}
        .cmd-desc {{ color: var(--muted-color); font-size: 0.8rem; margin-bottom: 0.3rem; }}
        .copy-btn {{
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid var(--border-color);
            color: var(--text-color);
            padding: 0.3rem 0.6rem;
            border-radius: 0.375rem;
            font-size: 0.75rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .copy-btn:hover {{
            background: var(--accent-color);
            color: #0b0f19;
            font-weight: bold;
        }}

        .batch-card {{
            border-left: 4px solid var(--success-color);
            margin-bottom: 0.85rem;
        }}

        /* Grid & Cards */
        .grid-4 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }}
        .grid-2 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1rem; }}
        .card {{ background-color: var(--card-bg); border: 1px solid var(--border-color); border-radius: 0.75rem; padding: 1.25rem; margin-bottom: 1.1rem; }}
        .metric-card h3 {{ margin: 0 0 0.4rem 0; font-size: 0.78rem; text-transform: uppercase; color: var(--muted-color); letter-spacing: 0.05em; }}
        .metric-val {{ font-size: 1.75rem; font-weight: bold; color: var(--text-color); }}

        /* Badges */
        .badge {{ display: inline-block; padding: 0.2rem 0.55rem; border-radius: 0.375rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }}
        .badge-success {{ background-color: rgba(52, 211, 153, 0.15); color: var(--success-color); border: 1px solid rgba(52, 211, 153, 0.3); }}
        .badge-warning {{ background-color: rgba(251, 191, 36, 0.15); color: var(--warning-color); border: 1px solid rgba(251, 191, 36, 0.3); }}
        .badge-danger {{ background-color: rgba(244, 63, 94, 0.15); color: var(--danger-color); border: 1px solid rgba(244, 63, 94, 0.3); }}
        .badge-info {{ background-color: rgba(56, 189, 248, 0.15); color: var(--accent-color); border: 1px solid rgba(56, 189, 248, 0.3); }}
        .badge-outline {{ border: 1px solid var(--border-color); color: var(--muted-color); }}

        /* Language Sections */
        .language-section {{
            margin-bottom: 2rem;
            padding-top: 0.5rem;
        }}
        .language-section-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 0.6rem;
            margin-bottom: 1rem;
        }}
        .toggle-btn {{
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid var(--border-color);
            color: var(--muted-color);
            padding: 0.35rem 0.75rem;
            border-radius: 0.375rem;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .toggle-btn:hover {{
            background: rgba(56, 189, 248, 0.15);
            color: var(--accent-color);
        }}

        /* Filter Pills */
        /* Filter Toolbar & Language Dropdown */
        .filter-toolbar {{
            display: flex;
            gap: 1rem;
            align-items: center;
            margin-bottom: 1.25rem;
            flex-wrap: wrap;
        }}
        .search-input-wrapper {{
            flex: 1;
            min-width: 280px;
        }}
        .lang-dropdown-wrapper {{
            min-width: 240px;
        }}
        .lang-select {{
            width: 100%;
            padding: 0.7rem 1rem;
            border-radius: 0.5rem;
            border: 1px solid var(--border-color);
            background-color: var(--sidebar-bg);
            color: var(--text-color);
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            outline: none;
            transition: all 0.2s ease;
        }}
        .lang-select:focus {{
            border-color: var(--accent-color);
            box-shadow: 0 0 0 2px var(--accent-glow);
        }}
        .lang-select option {{
            background-color: var(--sidebar-bg);
            color: var(--text-color);
            padding: 0.5rem;
        }}

        /* Tables */
        table {{ width: 100%; border-collapse: collapse; margin-top: 0.5rem; text-align: left; font-size: 0.88rem; }}
        th {{ background-color: rgba(0, 0, 0, 0.2); padding: 0.65rem; border-bottom: 1px solid var(--border-color); color: var(--muted-color); font-weight: 600; }}
        td {{ padding: 0.65rem; border-bottom: 1px solid var(--border-color); }}

        /* File Card Details */
        .file-card {{ border-left: 3px solid var(--border-color); margin-bottom: 0.85rem; transition: border-color 0.2s ease; }}
        .file-card:hover {{ border-left-color: var(--accent-color); }}
        .file-card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem; }}
        .file-title {{ font-weight: 600; font-family: monospace; font-size: 0.92rem; color: var(--accent-color); margin-right: 0.5rem; }}
        .file-details summary {{ cursor: pointer; font-size: 0.8rem; color: var(--accent-color); font-weight: 500; }}
        .details-content {{ margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid var(--border-color); }}
        .sym-list {{ list-style: none; padding: 0; margin: 0.4rem 0 0.6rem 0; font-size: 0.83rem; }}
        .sym-item {{ padding: 0.2rem 0; border-bottom: 1px dashed rgba(255,255,255,0.05); }}
        .sym-type {{ font-size: 0.7rem; text-transform: uppercase; font-weight: bold; color: var(--muted-color); display: inline-block; width: 60px; }}
        .doc-text {{ color: var(--muted-color); font-style: italic; }}

        /* Progress Bar */
        .progress-bar-bg {{ height: 8px; background-color: var(--border-color); border-radius: 4px; overflow: hidden; margin: 0.5rem 0; }}
        .progress-bar-fill {{ height: 100%; background-color: var(--accent-color); transition: width 0.3s ease; }}

        /* Search Box */
        .search-input {{ width: 100%; padding: 0.7rem 1rem; border-radius: 0.5rem; border: 1px solid var(--border-color); background-color: var(--sidebar-bg); color: var(--text-color); font-size: 0.9rem; }}
        .search-input:focus {{ outline: 2px solid var(--accent-color); }}

        .section-heading {{ font-size: 1.25rem; font-weight: bold; margin: 1.75rem 0 1rem 0; color: var(--text-color); border-left: 4px solid var(--accent-color); padding-left: 0.6rem; display: flex; align-items: center; }}
        code {{ background-color: var(--code-bg); padding: 0.15rem 0.35rem; border-radius: 0.25rem; font-family: monospace; font-size: 0.85em; }}
        .text-muted {{ color: var(--muted-color); }}
    </style>
</head>
<body>
    <aside>
        <div class="brand">
            ⚡ WIA Intelligence
        </div>
        <ul class="nav-menu">
            <li class="nav-item"><a href="#executive-overview" class="active">Executive Overview</a></li>
            <li class="nav-item"><a href="#installation">Installation & Commands</a></li>
            <li class="nav-item"><a href="#components">System Architecture</a></li>
            <li class="nav-item"><a href="#batch-narratives">Batch Analysis Log ({len(batches)})</a></li>
            <li class="nav-item">
                <a href="#file-narratives">File Intelligence ({len(files_data)})</a>
            </li>
            <ul class="nav-sub-menu">
                {language_nav_items_html}
            </ul>
            {f'<li class="nav-item"><a href="#security">Security ({len(security_findings)})</a></li>' if security_findings else ''}
            {f'<li class="nav-item"><a href="#dependencies">Dependencies ({len(deps)})</a></li>' if deps else ''}
        </ul>
    </aside>

    <main>
        <header>
            <div>
                <h1>WIA Workspace Intelligence Report</h1>
                <div class="header-meta">
                    Repository: <code>{ws_path}</code> | Schema Version: <strong>{version}</strong> | WIA Engine: <strong>{wia_ver}</strong>
                </div>
            </div>
            <div>
                <span class="badge badge-info">Developer Intelligence Report</span>
            </div>
        </header>

        <!-- Executive Project Overview -->
        <section id="executive-overview">
            <div class="narrative-card">
                <h2><a href="#executive-overview" class="anchor-link">#</a> Executive Repository Summary</h2>
                <p class="narrative-text">{project_narrative_p1}</p>
                <p class="narrative-text">{project_narrative_p2}</p>
                <p class="narrative-text">{project_narrative_p3}</p>
            </div>

            <!-- Overview Metrics Grid -->
            <div class="grid-4">
                <div class="card metric-card">
                    <h3>Indexed Files</h3>
                    <div class="metric-val">{total_indexed}</div>
                    <div class="header-meta">Discovered: {total_discovered} | Ignored: {total_ignored}</div>
                </div>
                <div class="card metric-card">
                    <h3>Declared Symbols</h3>
                    <div class="metric-val">{total_symbols}</div>
                    <div class="header-meta">Classes, Functions, Methods</div>
                </div>
                <div class="card metric-card">
                    <h3>Completed Batches</h3>
                    <div class="metric-val">{len(completed_batches)} / {len(batches)}</div>
                    <div class="header-meta">{pct}% Complete</div>
                </div>
                <div class="card metric-card">
                    <h3>Frameworks & Languages</h3>
                    <div style="margin-top: 0.35rem; font-size: 0.85rem;">{framework_items_html}</div>
                    <div style="margin-top: 0.25rem; font-size: 0.8rem;">{lang_items_html}</div>
                </div>
            </div>
        </section>

        <!-- Installation & Usage Guide -->
        <section id="installation">
            <h2 class="section-heading"><a href="#installation" class="anchor-link">#</a> Installation & CLI Usage Commands</h2>
            <div class="install-card">
                <p class="narrative-text" style="margin-top:0;">
                    Follow these commands to install, index, query, and run intelligence workflows on this workspace:
                </p>

                <div class="cmd-desc">1. Display WIA CLI help and available commands:</div>
                <div class="cmd-box">
                    <span class="cmd-text">wia --help</span>
                    <button class="copy-btn" onclick="copyFromBox(this)">Copy</button>
                </div>

                <div class="cmd-desc">2. Install WIA CLI toolchain (Editable Mode or Pip):</div>
                <div class="cmd-box">
                    <span class="cmd-text">pip install -e .</span>
                    <button class="copy-btn" onclick="copyFromBox(this)">Copy</button>
                </div>

                <div class="cmd-desc">3. Initialize and perform full workspace indexation:</div>
                <div class="cmd-box">
                    <span class="cmd-text">wia init && wia index</span>
                    <button class="copy-btn" onclick="copyFromBox(this)">Copy</button>
                </div>

                <div class="cmd-desc">4. Check workspace indexing status, batch health, and cache statistics:</div>
                <div class="cmd-box">
                    <span class="cmd-text">wia status</span>
                    <button class="copy-btn" onclick="copyFromBox(this)">Copy</button>
                </div>

                <div class="cmd-desc">5. Query codebase intelligence and retrieve grounded evidence:</div>
                <div class="cmd-box">
                    <span class="cmd-text">wia ask "Explain the system architecture, entrypoints, and data flow"</span>
                    <button class="copy-btn" onclick="copyFromBox(this)">Copy</button>
                </div>

                <div class="cmd-desc">6. Perform Blast-Radius / Impact Analysis before modifying a file:</div>
                <div class="cmd-box">
                    <span class="cmd-text">wia impact wia/core/retrieval.py</span>
                    <button class="copy-btn" onclick="copyFromBox(this)">Copy</button>
                </div>

                <div class="cmd-desc">7. Regenerate standalone interactive HTML report:</div>
                <div class="cmd-box">
                    <span class="cmd-text">wia report --output wia-report.html</span>
                    <button class="copy-btn" onclick="copyFromBox(this)">Copy</button>
                </div>

                <div class="cmd-desc">8. Launch backend FastAPI server / REST intelligence API:</div>
                <div class="cmd-box">
                    <span class="cmd-text">uvicorn backend.app.main:app --reload --port 8000</span>
                    <button class="copy-btn" onclick="copyFromBox(this)">Copy</button>
                </div>
            </div>
        </section>

        <!-- Component Architecture Breakdown -->
        <section id="components">
            <h2 class="section-heading"><a href="#components" class="anchor-link">#</a> System Component Architecture</h2>
            <div class="grid-2">
                {components_html}
            </div>
        </section>

        <!-- Accumulated Batch Intelligence Log -->
        <section id="batch-narratives">
            <h2 class="section-heading"><a href="#batch-narratives" class="anchor-link">#</a> Accumulated Batch Analysis Log ({len(batches)} Batches)</h2>
            <div class="card" style="margin-bottom: 1.25rem;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span>Accumulated Batch Progress ({len(completed_batches)} of {len(batches)} Batches Completed)</span>
                    <strong>{pct}%</strong>
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width: {pct}%;"></div>
                </div>
                <div class="grid-4" style="margin-top: 0.75rem; margin-bottom: 0;">
                    <div><span class="badge badge-success">Completed: {len(completed_batches)}</span></div>
                    <div><span class="badge badge-warning">Running: {len(running_batches)}</span></div>
                    <div><span class="badge badge-outline">Pending: {len(pending_batches)}</span></div>
                    <div><span class="badge badge-danger">Failed: {len(failed_batches)}</span></div>
                </div>
            </div>

            <div>
                {batch_narratives_html}
            </div>
        </section>

        <!-- File-by-File Technical Intelligence Narratives -->
        <section id="file-narratives">
            <h2 class="section-heading"><a href="#file-narratives" class="anchor-link">#</a> File-by-File Codebase Intelligence ({len(files_data)} Files)</h2>
            
            <div class="filter-toolbar">
                <div class="search-input-wrapper">
                    <input type="text" id="fileSearch" class="search-input" placeholder="Search repository files, symbols, modules, architectural roles..." onkeyup="filterFiles()">
                </div>
                <div class="lang-dropdown-wrapper">
                    <select id="languageSelect" class="lang-select" onchange="onLanguageSelect(this.value)">
                        {language_select_options_html}
                    </select>
                </div>
            </div>

            <div id="fileList">
                <div id="noLangPlaceholder" class="card" style="text-align:center; padding:3.5rem 1.5rem; color:var(--muted-color); border:1px dashed var(--border-color); margin-top:0.5rem; background:rgba(31, 41, 55, 0.4);">
                    <div style="font-size:2.8rem; margin-bottom:0.75rem;">📂</div>
                    <h3 style="margin:0 0 0.5rem 0; color:var(--text-color); font-size:1.15rem;">Select a Language to View Files</h3>
                    <p style="margin:0 auto; font-size:0.9rem; max-width:480px; line-height:1.5;">
                        Choose a programming language from the dropdown selector above to inspect its indexed source files, declared AST symbols, and dependency relationships.
                    </p>
                </div>
                {grouped_files_html}
            </div>
        </section>

        <!-- Security Findings (if present) -->
        {security_section_html}

        <!-- Manifest Dependencies (if present) -->
        {deps_section_html}
    </main>

    <script>
        window.WIA_REPORT_DATA = {report_json_data};

        function copyFromBox(btn) {{
            const box = btn.closest('.cmd-box');
            if (!box) return;
            const textEl = box.querySelector('.cmd-text');
            const text = textEl ? textEl.innerText.trim() : '';
            if (!text) return;

            navigator.clipboard.writeText(text).then(() => {{
                const originalText = btn.innerText;
                btn.innerText = 'Copied!';
                btn.style.background = '#34d399';
                btn.style.color = '#0b0f19';
                setTimeout(() => {{
                    btn.innerText = originalText;
                    btn.style.background = '';
                    btn.style.color = '';
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

            const placeholder = document.getElementById('noLangPlaceholder');
            const sections = document.querySelectorAll('.language-section');

            if (!langSlug) {{
                if (placeholder) placeholder.style.display = 'block';
                sections.forEach(s => s.style.display = 'none');
                return;
            }}

            if (placeholder) placeholder.style.display = 'none';

            if (langSlug === 'all') {{
                sections.forEach(s => s.style.display = 'block');
            }} else {{
                sections.forEach(s => {{
                    if (s.getAttribute('data-language-group') === langSlug) {{
                        s.style.display = 'block';
                    }} else {{
                        s.style.display = 'none';
                    }}
                }});
            }}
            filterFiles();
        }}

        function toggleLanguageDetails(langSectionId) {{
            const sec = document.getElementById(langSectionId);
            if (!sec) return;
            const detailsList = sec.querySelectorAll('details');
            if (!detailsList.length) return;
            const anyClosed = Array.from(detailsList).some(d => !d.open);
            detailsList.forEach(d => d.open = anyClosed);
        }}

        function filterFiles() {{
            const input = document.getElementById('fileSearch').value.toLowerCase().trim();
            const selectEl = document.getElementById('languageSelect');
            let currentLang = selectEl ? selectEl.value : '';
            const placeholder = document.getElementById('noLangPlaceholder');

            if (input && !currentLang) {{
                currentLang = 'all';
                if (placeholder) placeholder.style.display = 'none';
            }} else if (!input && !currentLang) {{
                if (placeholder) placeholder.style.display = 'block';
                document.querySelectorAll('.language-section').forEach(s => s.style.display = 'none');
                return;
            }}

            const cards = document.querySelectorAll('.file-card');
            cards.forEach(card => {{
                const path = card.getAttribute('data-filepath') || '';
                const cardLang = card.getAttribute('data-language') || '';
                const text = card.innerText.toLowerCase();

                const matchesLang = (currentLang === 'all' || cardLang === currentLang);
                const matchesSearch = (!input || path.includes(input) || text.includes(input));

                if (matchesLang && matchesSearch) {{
                    card.style.display = 'block';
                }} else {{
                    card.style.display = 'none';
                }}
            }});

            // Hide empty language sections when searching or filtering
            document.querySelectorAll('.language-section').forEach(sec => {{
                const secLang = sec.getAttribute('data-language-group') || '';
                if (currentLang !== 'all' && secLang !== currentLang) {{
                    sec.style.display = 'none';
                }} else {{
                    const hasVisible = Array.from(sec.querySelectorAll('.file-card')).some(c => c.style.display !== 'none');
                    sec.style.display = hasVisible ? 'block' : 'none';
                }}
            }});
        }}

        // Auto-refresh on data update
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
        }});
    </script>
</body>
</html>
"""
        target_file.write_text(html_content, encoding="utf-8")
        return target_file
