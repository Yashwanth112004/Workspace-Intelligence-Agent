import os
import sys
import time
import argparse
import logging
from typing import Optional, List, Dict
from sqlmodel import Session, select

# Ensure UTF-8 output on Windows consoles
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.core.database import init_db, engine
from app.models.workspace import Repository, FileNode, ASTSymbol, WorkspaceSummary, VectorChunk
from app.services.ingestion import RepositoryCrawler
from app.services.parser import ASTParserEngine
from app.services.summarizer import HierarchicalSummarizerEngine
from app.services.rag import VectorSearchStore
from app.agent.nooa_agent import WIACodeUnderstandingAgent
from app.services.pipeline import run_ingestion_pipeline, IN_MEMORY_CHUNKS, IN_MEMORY_SUMMARIES
from app.services.graph.code_graph import CodeKnowledgeGraph
from app.services.export.okf_exporter import OKFExporter
from app.services.intelligence.incremental_indexer import IncrementalIndexer
from app.services.intelligence.git_intel import GitIntelligence

logging.basicConfig(level=logging.WARNING, format="%(message)s")
logger = logging.getLogger("wia.cli")

def get_db_session():
    init_db()
    return Session(engine)

def get_repo(session: Session, target: str) -> Optional[Repository]:
    repo = session.get(Repository, target)
    if not repo:
        repo = session.exec(select(Repository).where(Repository.name == target)).first()
    if not repo:
        repo = session.exec(select(Repository).where(Repository.source_path == target)).first()
    return repo

def cmd_scan(args):
    """Scan and ingest a repository directly from CLI."""
    source_path = args.path.strip()
    name = args.name or os.path.basename(source_path.rstrip("/\\")) or "Workspace Repo"
    
    print(f"\n🚀 [WIA CLI] Ingesting repository: {source_path}")
    
    with get_db_session() as session:
        repo = Repository(
            name=name,
            source_type="github" if source_path.startswith("http") else "local",
            source_path=source_path,
            local_path="",
            status="pending",
            progress_pct=0,
            status_message="Ingestion initialized from CLI"
        )
        session.add(repo)
        session.commit()
        session.refresh(repo)

        print(f"📦 Repository ID: {repo.id}")
        print("⏳ Running ingestion, knowledge graph build & intelligence pipeline...\n")
        
        try:
            run_ingestion_pipeline(repo.id, source_path)
            session.refresh(repo)
            print("✅ Ingestion & Analysis Completed Successfully!")
            print(f"   - Name:         {repo.name}")
            print(f"   - Total Files:  {repo.total_files}")
            print(f"   - Total LOC:    {repo.total_loc}")
            print(f"   - Tech Stack:   {repo.tech_stack}")
            print(f"   - Entry Points: {repo.entry_points}")
            print(f"   - Dependencies: {len(repo.dependencies or [])} detected\n")
            print(f"💡 Query with: wia query \"{repo.name}\" \"Explain architecture\"\n")
        except Exception as e:
            print(f"❌ Ingestion failed: {e}")
            sys.exit(1)

def cmd_query(args):
    """Ask technical questions about a codebase."""
    target = args.target.strip()
    question = args.question.strip()

    with get_db_session() as session:
        repo = get_repo(session, target)
        if not repo:
            print(f"❌ Repository '{target}' not found. Run 'wia list' to see available repositories.")
            return

        chunks = IN_MEMORY_CHUNKS.get(repo.id, [])
        summaries = IN_MEMORY_SUMMARIES.get(repo.id, [])
        if not summaries:
            summaries = session.exec(select(WorkspaceSummary).where(WorkspaceSummary.repo_id == repo.id)).all()

        symbols = session.exec(select(ASTSymbol).where(ASTSymbol.repo_id == repo.id)).all()
        nodes = session.exec(select(FileNode).where(FileNode.repo_id == repo.id)).all()
        graph = CodeKnowledgeGraph(repo.id, session=session)
        graph.build_from_ast_and_files(nodes, symbols)

        agent = WIACodeUnderstandingAgent(
            repo=repo,
            chunks=chunks,
            summaries=summaries,
            symbols=symbols,
            graph=graph
        )

        print(f"\n🧠 [WIA Code Understanding Agent] Processing query for '{repo.name}'...")
        print(f"❓ Question: {question}\n")
        
        try:
            result = agent.answer_question(question)
            print("=" * 70)
            print(result.get("response", "No response generated."))
            print("=" * 70)

            citations = result.get("citations", [])
            if citations:
                print("\n📌 Exact Source Citations & Provenance:")
                for idx, c in enumerate(citations[:6], 1):
                    file_p = c.get("file_path", "unknown")
                    s_line = c.get("start_line", 1)
                    e_line = c.get("end_line", 1)
                    c_type = c.get("chunk_type", "reference")
                    score = c.get("score", 0.0)
                    print(f"   [{idx}] {file_p} (lines {s_line}-{e_line}) [{c_type}] - relevance: {score:.2f}")
            print()
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

def cmd_architecture(args):
    """View architecture overview, subsystems, and knowledge graph."""
    target = args.target.strip()
    with get_db_session() as session:
        repo = get_repo(session, target)
        if not repo:
            print(f"❌ Repository '{target}' not found.")
            return

        summaries = session.exec(select(WorkspaceSummary).where(WorkspaceSummary.repo_id == repo.id)).all()
        repo_summary = next((s.summary_text for s in summaries if s.level == "repository"), "Architecture summary available.")
        folder_summaries = [s for s in summaries if s.level in ("parent_folder", "child_folder")]

        nodes = session.exec(select(FileNode).where(FileNode.repo_id == repo.id)).all()
        symbols = session.exec(select(ASTSymbol).where(ASTSymbol.repo_id == repo.id)).all()
        graph = CodeKnowledgeGraph(repo.id, session=session)
        graph.build_from_ast_and_files(nodes, symbols)
        graph_data = graph.to_json()

        print(f"\n🏛️ Architecture Overview for '{repo.name}':")
        print(f"   - Nodes in Graph: {len(graph_data['nodes'])} (Files & Classes)")
        print(f"   - Edges in Graph: {len(graph_data['edges'])} (Contains, Calls, Defines, Imports)")
        print(f"\n📖 High-Level Summary:\n{repo_summary}\n")

        print("📁 Subsystems:")
        for f in folder_summaries:
            print(f"   • [{f.name}] ({f.target_path}): {f.summary_text}")
        print()

def cmd_flow(args):
    """Trace code execution flow starting from a symbol or entry point."""
    target = args.target.strip()
    entry = (args.entry or args.entry_pos or "").strip()

    if not entry:
        print(f"❌ Please provide an entry symbol to trace. Example: wia flow {target} handle_login")
        return

    with get_db_session() as session:
        repo = get_repo(session, target)
        if not repo:
            print(f"❌ Repository '{target}' not found.")
            return

        nodes = session.exec(select(FileNode).where(FileNode.repo_id == repo.id)).all()
        symbols = session.exec(select(ASTSymbol).where(ASTSymbol.repo_id == repo.id)).all()
        graph = CodeKnowledgeGraph(repo.id, session=session)
        graph.build_from_ast_and_files(nodes, symbols)

        flow = graph.trace_flow(entry)
        if not flow:
            print(f"❌ No execution flow path found starting from '{entry}'.")
            return

        print(f"\n🔄 Execution Flow starting from '{entry}' ({len(flow)} steps):\n")
        for step in flow:
            indent = "  " * step["depth"]
            print(f"{indent}Step {step['step']}: {step['symbol']} ({step['file']}:{step['line']}) - {step['reason']}")
        print()

def cmd_impact(args):
    """Analyze change impact for a symbol or file."""
    target = args.target.strip()

    with get_db_session() as session:
        repo = get_repo(session, target)
        if not repo:
            print(f"❌ Repository '{target}' not found.")
            return

        nodes = session.exec(select(FileNode).where(FileNode.repo_id == repo.id)).all()
        symbols = session.exec(select(ASTSymbol).where(ASTSymbol.repo_id == repo.id)).all()
        graph = CodeKnowledgeGraph(repo.id, session=session)
        graph.build_from_ast_and_files(nodes, symbols)

        if args.diff:
            # Impact from git diff
            diff_status = GitIntelligence.get_git_diff_status(repo.source_path or ".")
            changed = diff_status["modified_files"] + diff_status["added_files"]
            print(f"\n💥 Git Diff Blast Radius Analysis for '{repo.name}':")
            print(f"   - Changed Files: {len(changed)}")
            for cf in changed:
                impact = graph.analyze_impact(cf)
                print(f"   • {cf} -> {impact['direct_impact_count']} direct dependents, {impact['affected_files_count']} affected files")
            print()
            return

        symbol = (args.symbol or args.symbol_pos or "").strip()
        if not symbol:
            print(f"❌ Please provide a symbol or file to analyze. Example: wia impact {target} AuthService")
            return

        impact = graph.analyze_impact(symbol)
        print(f"\n💥 Change Impact Analysis for '{symbol}' in '{repo.name}':")
        print(f"   - Direct Dependents:   {impact['direct_impact_count']}")
        print(f"   - Indirect Dependents: {impact['indirect_impact_count']}")
        print(f"   - Total Affected Files:{impact['affected_files_count']}\n")
        
        if impact['affected_callers']:
            print("   📞 Affected Callers:")
            for c in impact['affected_callers'][:10]:
                print(f"      • {c}")
        if impact['affected_files']:
            print("   📄 Affected Files:")
            for f in impact['affected_files'][:10]:
                print(f"      • {f}")
        print()

def cmd_diff(args):
    """Analyze git diff changes and modified symbols in the workspace."""
    target = (args.target or ".").strip()
    with get_db_session() as session:
        repo = get_repo(session, target)
        repo_path = repo.source_path if repo else (target if os.path.exists(target) else ".")

        diff_data = GitIntelligence.get_git_diff_status(repo_path)
        print(f"\n📊 Git Diff Analysis for '{repo.name if repo else repo_path}':")
        print(f"   - Git Repository:   {'Yes' if diff_data['is_git_repo'] else 'No'}")
        print(f"   - Modified Files:   {len(diff_data['modified_files'])}")
        print(f"   - Added Files:      {len(diff_data['added_files'])}")
        print(f"   - Deleted Files:    {len(diff_data['deleted_files'])}")

        all_changed = diff_data['modified_files'] + diff_data['added_files']
        if all_changed:
            symbols = GitIntelligence.analyze_diff_symbols(repo_path, all_changed)
            print(f"\n🔍 Affected Symbols in Changed Files ({len(symbols)}):")
            for s in symbols[:15]:
                print(f"   • [{s['type']}] {s['name']} ({s['file']}:{s['line']})")
        print()

def cmd_watch(args):
    """Continuously monitor workspace and incrementally update knowledge model on change."""
    target = args.target.strip()
    interval = args.interval

    with get_db_session() as session:
        repo = get_repo(session, target)
        repo_path = repo.source_path if repo else (target if os.path.exists(target) else None)
        if not repo_path or not os.path.exists(repo_path):
            print(f"❌ Target path '{target}' does not exist.")
            return

        print(f"\n👁️ [WIA Watcher] Monitoring '{repo_path}' every {interval}s (Press Ctrl+C to stop)...")
        _, _, _, previous_hashes = IncrementalIndexer.detect_changes(repo_path, {})

        try:
            while True:
                time.sleep(interval)
                added, modified, deleted, current_hashes = IncrementalIndexer.detect_changes(repo_path, previous_hashes)
                if added or modified or deleted:
                    print(f"\n⚡ Changes detected at {time.strftime('%X')}:")
                    if added:
                        print(f"   + Added ({len(added)}): {', '.join(added[:5])}")
                    if modified:
                        print(f"   ~ Modified ({len(modified)}): {', '.join(modified[:5])}")
                    if deleted:
                        print(f"   - Deleted ({len(deleted)}): {', '.join(deleted[:5])}")
                    
                    if repo:
                        print(f"   🔄 Updating WIA intelligence for '{repo.name}'...")
                        run_ingestion_pipeline(repo.id, repo_path)
                        print("   ✅ Knowledge model and graph updated.")
                    previous_hashes = current_hashes
        except KeyboardInterrupt:
            print("\n🛑 Watcher stopped.")

def cmd_health(args):
    """Run health and complexity audit on a repository."""
    target = args.target.strip()
    with get_db_session() as session:
        repo = get_repo(session, target)
        if not repo:
            print(f"❌ Repository '{target}' not found.")
            return

        symbols = session.exec(select(ASTSymbol).where(ASTSymbol.repo_id == repo.id)).all()
        nodes = session.exec(select(FileNode).where(FileNode.repo_id == repo.id)).all()
        file_nodes = [n for n in nodes if not n.is_dir]

        print(f"\n🏥 Health & Complexity Audit for '{repo.name}':")
        print(f"   - Total LOC:     {repo.total_loc}")
        print(f"   - Files:         {len(file_nodes)}")
        print(f"   - Functions:     {len([s for s in symbols if s.symbol_type == 'function'])}")
        print(f"   - Classes:       {len([s for s in symbols if s.symbol_type == 'class'])}")
        print(f"   - Imports:       {len([s for s in symbols if s.symbol_type == 'import'])}")
        print(f"   - Entry Points:  {repo.entry_points or ['None detected']}")
        print(f"   - Secret Safety: Active\n")

def cmd_onboard(args):
    """Generate onboarding walkthrough for new developers."""
    target = args.target.strip()
    with get_db_session() as session:
        repo = get_repo(session, target)
        if not repo:
            print(f"❌ Repository '{target}' not found.")
            return

        summaries = session.exec(select(WorkspaceSummary).where(WorkspaceSummary.repo_id == repo.id)).all()
        agent = WIACodeUnderstandingAgent(repo, [], summaries)
        res = agent.onboarding_guide()
        print("\n" + res["response"] + "\n")

def cmd_parse(args):
    """Parse AST symbols from a specific file."""
    file_path = args.file
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    ext = os.path.splitext(file_path)[1].lower()
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    symbols = ASTParserEngine.parse_file_symbols(content, ext, file_path)
    print(f"\n🌲 Parsed AST Symbols in '{file_path}' ({len(symbols)} found):\n")
    print(f"{'TYPE':<12} | {'NAME':<24} | {'LINE':<6} | {'SIGNATURE'}")
    print("-" * 75)
    for sym in symbols:
        print(f"{sym.symbol_type:<12} | {sym.name:<24} | {sym.start_line:<6} | {sym.signature}")
    print("-" * 75 + "\n")

def cmd_summarize(args):
    """View 5-level hierarchical summaries."""
    target = args.target.strip()
    with get_db_session() as session:
        repo = get_repo(session, target)
        if not repo:
            print(f"❌ Repository '{target}' not found.")
            return

        summaries = session.exec(select(WorkspaceSummary).where(WorkspaceSummary.repo_id == repo.id)).all()
        print(f"\n📚 5-Level Hierarchical Summaries for '{repo.name}':\n")
        levels = ["repository", "parent_folder", "child_folder", "file", "function"]
        for lvl in levels:
            lvl_summaries = [s for s in summaries if s.level == lvl]
            if lvl_summaries:
                print(f"--- Level: {lvl.upper()} ({len(lvl_summaries)}) ---")
                for s in lvl_summaries[:5]:
                    print(f"  • [{s.name}] ({s.target_path}): {s.summary_text}")
                print()

def cmd_symbols(args):
    """Search and list symbols across the codebase."""
    target = args.target.strip()
    search = args.search.strip().lower() if args.search else None

    with get_db_session() as session:
        repo = get_repo(session, target)
        if not repo:
            print(f"❌ Repository '{target}' not found.")
            return

        query = select(ASTSymbol).where(ASTSymbol.repo_id == repo.id)
        if search:
            query = query.where(ASTSymbol.name.ilike(f"%{search}%"))
        symbols = session.exec(query).all()

        print(f"\n🔍 Symbols in '{repo.name}' ({len(symbols)} matches):\n")
        print(f"{'TYPE':<12} | {'NAME':<24} | {'FILE':<30} | {'LINE'}")
        print("-" * 78)
        for s in symbols[:30]:
            print(f"{s.symbol_type:<12} | {s.name:<24} | {s.file_path[-30:]:<30} | {s.start_line}")
        print("-" * 78 + "\n")

def cmd_dependencies(args):
    """Inspect dependency manifests and import relationships."""
    target = args.target.strip()
    with get_db_session() as session:
        repo = get_repo(session, target)
        if not repo:
            print(f"❌ Repository '{target}' not found.")
            return

        imports = session.exec(select(ASTSymbol).where(ASTSymbol.repo_id == repo.id, ASTSymbol.symbol_type == "import")).all()
        print(f"\n📦 Dependencies & Imports in '{repo.name}':")
        print(f"   - Manifest Files: {repo.dependencies or ['None']}")
        print(f"   - Parsed Imports: {len(imports)}\n")
        
        unique_modules = sorted(list(set([imp.name for imp in imports])))
        print("🔗 Top Imported Modules:")
        for mod in unique_modules[:20]:
            print(f"   • {mod}")
        print()

def cmd_export(args):
    """Export architecture report or Open Knowledge Format (.wia/knowledge/)."""
    target = args.target.strip()
    fmt = args.format
    output = args.output

    with get_db_session() as session:
        repo = get_repo(session, target)
        if not repo:
            print(f"❌ Repository '{target}' not found.")
            return

        if fmt == "okf":
            nodes = session.exec(select(FileNode).where(FileNode.repo_id == repo.id)).all()
            symbols = session.exec(select(ASTSymbol).where(ASTSymbol.repo_id == repo.id)).all()
            summaries = session.exec(select(WorkspaceSummary).where(WorkspaceSummary.repo_id == repo.id)).all()
            graph = CodeKnowledgeGraph(repo.id, session=session)
            graph.build_from_ast_and_files(nodes, symbols)

            out_dir = output or os.path.join(repo.source_path or ".", ".wia", "knowledge")
            manifest = OKFExporter.export_repository_knowledge(
                repo=repo,
                files=nodes,
                symbols=symbols,
                summaries=summaries,
                graph=graph,
                output_dir=out_dir
            )
            print(f"\n📦 Successfully exported Open Knowledge Format (OKF) package to: {out_dir}")
            print(f"   - Manifest:      {manifest['schema_version']}")
            print(f"   - Total Entities:{manifest['entities_count']}")
            print(f"   - Relations:     {manifest['relations_count']}\n")
            return

        elif fmt == "markdown":
            summaries = session.exec(select(WorkspaceSummary).where(WorkspaceSummary.repo_id == repo.id)).all()
            md = f"# Architecture Report: {repo.name}\n\n"
            md += f"**Total Files**: {repo.total_files} | **LOC**: {repo.total_loc}\n\n"
            md += "## Subsystems\n"
            for s in summaries:
                md += f"- **{s.name}** (`{s.target_path}`): {s.summary_text}\n"

            if output:
                with open(output, "w", encoding="utf-8") as f:
                    f.write(md)
                print(f"✅ Architecture report saved to {output}")
            else:
                print("\n" + md)

def cmd_list(args):
    """List all ingested repositories."""
    with get_db_session() as session:
        repos = session.exec(select(Repository)).all()
        print(f"\n📂 Ingested Repositories ({len(repos)} total):\n")
        print(f"{'ID':<38} | {'NAME':<20} | {'FILES':<6} | {'STATUS'}")
        print("-" * 75)
        for r in repos:
            print(f"{r.id:<38} | {r.name[:20]:<20} | {r.total_files:<6} | {r.status}")
        print("-" * 75 + "\n")

def cmd_delete(args):
    """Delete a repository from database and storage."""
    target = args.target.strip()
    with get_db_session() as session:
        repo = get_repo(session, target)
        if not repo:
            print(f"❌ Repository '{target}' not found.")
            return

        session.delete(repo)
        session.commit()
        print(f"🗑️ Successfully deleted repository '{repo.name}' ({repo.id}).\n")

def cmd_serve(args):
    """Start local FastAPI backend server daemon for VS Code extension."""
    import uvicorn
    print(f"\n🚀 Starting WIA Local Daemon Server on http://{args.host}:{args.port}...")
    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)

def cmd_test(args):
    """Run automated test suite."""
    import pytest
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    pytest.main(["-v", os.path.join(root_dir, "backend", "tests")])

def build_parser():
    parser = argparse.ArgumentParser(
        prog="wia",
        description="Workspace Intelligence Agent (WIA) - Code Knowledge Graph & Developer Intelligence CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available WIA CLI Commands")

    # scan
    p_scan = subparsers.add_parser("scan", help="Scan and ingest a repository (local folder or GitHub URL)")
    p_scan.add_argument("path", help="Local directory path or GitHub URL")
    p_scan.add_argument("--name", help="Custom repository name")
    p_scan.set_defaults(func=cmd_scan)

    # query
    p_query = subparsers.add_parser("query", help="Ask AI technical questions about a codebase")
    p_query.add_argument("target", help="Repository ID, name, or path")
    p_query.add_argument("question", help="Natural language question to ask")
    p_query.set_defaults(func=cmd_query)

    # architecture
    p_arch = subparsers.add_parser("architecture", help="View architecture overview and knowledge graph")
    p_arch.add_argument("target", help="Repository ID or name")
    p_arch.set_defaults(func=cmd_architecture)

    # flow
    p_flow = subparsers.add_parser("flow", help="Trace execution call flow starting from an entry point")
    p_flow.add_argument("target", help="Repository ID or name")
    p_flow.add_argument("entry_pos", nargs="?", default=None, help="Function or route entry point name (positional)")
    p_flow.add_argument("--entry", default=None, help="Function or route entry point name")
    p_flow.set_defaults(func=cmd_flow)

    # impact
    p_imp = subparsers.add_parser("impact", help="Analyze ripple change impact for a symbol or file")
    p_imp.add_argument("target", help="Repository ID or name")
    p_imp.add_argument("symbol_pos", nargs="?", default=None, help="Symbol name or file path (positional)")
    p_imp.add_argument("--symbol", default=None, help="Symbol name or file path to analyze")
    p_imp.add_argument("--diff", action="store_true", help="Analyze blast radius from uncommitted git diffs")
    p_imp.set_defaults(func=cmd_impact)

    # diff
    p_diff = subparsers.add_parser("diff", help="Analyze repository Git diff and affected symbols")
    p_diff.add_argument("target", nargs="?", default=".", help="Repository ID, name, or local directory path")
    p_diff.set_defaults(func=cmd_diff)

    # watch
    p_watch = subparsers.add_parser("watch", help="Watch workspace and incrementally reindex on changes")
    p_watch.add_argument("target", help="Repository path or name to watch")
    p_watch.add_argument("--interval", type=int, default=3, help="Polling interval in seconds")
    p_watch.set_defaults(func=cmd_watch)

    # health
    p_health = subparsers.add_parser("health", help="Run repository health and complexity audit")
    p_health.add_argument("target", help="Repository ID or name")
    p_health.set_defaults(func=cmd_health)

    # onboard
    p_onb = subparsers.add_parser("onboard", help="Generate developer onboarding walkthrough")
    p_onb.add_argument("target", help="Repository ID or name")
    p_onb.set_defaults(func=cmd_onboard)

    # symbols
    p_sym = subparsers.add_parser("symbols", help="Search and list AST symbols across the codebase")
    p_sym.add_argument("target", help="Repository ID or name")
    p_sym.add_argument("--search", "-s", help="Filter by symbol name")
    p_sym.set_defaults(func=cmd_symbols)

    # dependencies
    p_dep = subparsers.add_parser("dependencies", help="Inspect import linkages and package dependencies")
    p_dep.add_argument("target", help="Repository ID or name")
    p_dep.set_defaults(func=cmd_dependencies)

    # parse
    p_parse = subparsers.add_parser("parse", help="Parse AST symbols from a source file")
    p_parse.add_argument("file", help="Path to source code file")
    p_parse.set_defaults(func=cmd_parse)

    # summarize
    p_sum = subparsers.add_parser("summarize", help="Show 5-level hierarchical summaries for a repository")
    p_sum.add_argument("target", help="Repository ID or name")
    p_sum.set_defaults(func=cmd_summarize)

    # list
    p_list = subparsers.add_parser("list", help="List all ingested repositories")
    p_list.set_defaults(func=cmd_list)

    # export
    p_exp = subparsers.add_parser("export", help="Export architecture report or Open Knowledge Format (.wia/knowledge/)")
    p_exp.add_argument("target", help="Repository ID or name")
    p_exp.add_argument("--format", choices=["markdown", "json", "okf"], default="markdown", help="Export format")
    p_exp.add_argument("--output", "-o", help="File or directory path to save output")
    p_exp.set_defaults(func=cmd_export)

    # delete
    p_del = subparsers.add_parser("delete", help="Delete a repository and its intelligence index")
    p_del.add_argument("target", help="Repository ID or name")
    p_del.set_defaults(func=cmd_delete)

    # serve
    p_serve = subparsers.add_parser("serve", help="Start the local WIA backend server daemon for VS Code")
    p_serve.add_argument("--host", default="127.0.0.1", help="Host address")
    p_serve.add_argument("--port", type=int, default=8000, help="Port number")
    p_serve.add_argument("--reload", action="store_true", help="Enable auto-reload")
    p_serve.set_defaults(func=cmd_serve)

    # test
    p_test = subparsers.add_parser("test", help="Run automated test suite")
    p_test.set_defaults(func=cmd_test)

    return parser

def cli_entry():
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)
    args.func(args)

if __name__ == "__main__":
    cli_entry()
