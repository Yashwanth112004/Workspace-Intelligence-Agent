import os
import sys
import argparse
import logging
from typing import Optional
from sqlmodel import Session, select

# Ensure UTF-8 output on Windows consoles
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(level=logging.WARNING, format="%(message)s")
logger = logging.getLogger("wia.cli")

def get_db_session():
    from app.core.database import init_db, engine
    from sqlmodel import Session
    init_db()
    return Session(engine)

def get_repo(session, target: str):
    from sqlmodel import select
    from app.models.workspace import Repository
    repo = session.get(Repository, target)
    if not repo:
        repo = session.exec(select(Repository).where(Repository.name == target)).first()
    if not repo:
        repo = session.exec(select(Repository).where(Repository.source_path == target)).first()
    return repo

def cmd_scan(args):
    """Scan and ingest a repository directly from CLI."""
    from app.models.workspace import Repository
    from app.services.pipeline import run_ingestion_pipeline
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

        repo_id = repo.id
        print(f"📦 Repository ID: {repo_id}")
        print(f"⏳ Running ingestion, knowledge graph build & intelligence pipeline...")

        run_ingestion_pipeline(repo_id)

        session.refresh(repo)
        if repo.status == "completed":
            print(f"\n✅ Ingestion & Analysis Completed Successfully!")
            print(f"   - Name:         {repo.name}")
            print(f"   - Total Files:  {repo.total_files}")
            print(f"   - Total LOC:    {repo.total_loc}")
            print(f"   - Tech Stack:   {dict(repo.tech_stack or {})}")
            print(f"   - Entry Points: {repo.entry_points or []}")
            print(f"   - Dependencies: {len(repo.dependencies or [])} detected")
            print(f"\n💡 Query with: wia query \"{repo.name}\" \"Explain architecture\"\n")
        else:
            print(f"\n❌ Pipeline failed: {repo.error_message}")

def cmd_query(args):
    """Query codebase via NOOA Agent & Hybrid RAG from CLI."""
    from sqlmodel import select
    from app.models.workspace import VectorChunk, WorkspaceSummary, ASTSymbol, FileNode
    from app.services.graph.code_graph import CodeKnowledgeGraph
    from app.agent.nooa_agent import WIACodeUnderstandingAgent
    target = args.target.strip()
    question = args.question.strip()

    with get_db_session() as session:
        repo = get_repo(session, target)
        if not repo:
            print(f"❌ Error: Repository '{target}' not found. Ingest it first with 'scan' or check 'list'.")
            return

        chunks = session.exec(select(VectorChunk).where(VectorChunk.repo_id == repo.id)).all()
        summaries = session.exec(select(WorkspaceSummary).where(WorkspaceSummary.repo_id == repo.id)).all()
        symbols = session.exec(select(ASTSymbol).where(ASTSymbol.repo_id == repo.id)).all()
        nodes = session.exec(select(FileNode).where(FileNode.repo_id == repo.id)).all()

        graph = CodeKnowledgeGraph(repo.id, session=session)
        graph.build_from_ast_and_files(nodes, symbols)

        print(f"\n🧠 [WIA Agent] Querying '{repo.name}': \"{question}\"")
        agent = WIACodeUnderstandingAgent(repo, chunks, summaries, symbols=symbols, graph=graph)
        result = agent.answer_question(question)

        print("\n" + "=" * 65)
        print("🤖 ANSWER:")
        print("=" * 65)
        print(result.get("response", "No response generated."))
        if result.get("citations"):
            print("\n" + "=" * 65)
            print("📑 CONTEXT CITATIONS:")
            print("=" * 65)
            for idx, cite in enumerate(result.get("citations", []), 1):
                lines = f" (Lines {cite['start_line']}-{cite['end_line']})" if cite.get("start_line") else ""
                print(f" {idx}. [{cite.get('chunk_type', 'code').upper()}] {cite.get('file_path')}{lines} (Score: {cite.get('score', 0)})")
        print("=" * 65 + "\n")

def cmd_architecture(args):
    """View architecture breakdown and knowledge graph stats."""
    from sqlmodel import select
    from app.models.workspace import WorkspaceSummary, FileNode, ASTSymbol
    from app.services.graph.code_graph import CodeKnowledgeGraph
    target = args.target.strip()
    with get_db_session() as session:
        repo = get_repo(session, target)
        if not repo:
            print(f"❌ Repository '{target}' not found.")
            return

        summaries = session.exec(select(WorkspaceSummary).where(WorkspaceSummary.repo_id == repo.id)).all()
        nodes = session.exec(select(FileNode).where(FileNode.repo_id == repo.id)).all()
        symbols = session.exec(select(ASTSymbol).where(ASTSymbol.repo_id == repo.id)).all()

        graph = CodeKnowledgeGraph(repo.id, session=session)
        graph.build_from_ast_and_files(nodes, symbols)
        arch = graph.get_architecture_graph()

        repo_sum = next((s.summary_text for s in summaries if s.level == "repository"), "Architecture summary available.")
        folder_sums = [s for s in summaries if s.level in ("parent_folder", "child_folder")]

        print(f"\n🏛️ Architecture Overview for '{repo.name}':")
        print(f"   - Nodes in Graph: {arch['total_nodes']} (Files & Classes)")
        print(f"   - Edges in Graph: {arch['total_edges']} (Contains, Calls, Defines, Imports)")
        print(f"\n📖 High-Level Summary:\n{repo_sum}\n")
        print("📁 Subsystems:")
        for f in folder_sums[:8]:
            print(f"   • [{f.name}] ({f.target_path}): {f.summary_text}")
        print()

def cmd_flow(args):
    """Trace code execution flow starting from a symbol or entry point."""
    from sqlmodel import select
    from app.models.workspace import FileNode, ASTSymbol
    from app.services.graph.code_graph import CodeKnowledgeGraph
    target = args.target.strip()
    entry = args.entry.strip()

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
    from sqlmodel import select
    from app.models.workspace import FileNode, ASTSymbol
    from app.services.graph.code_graph import CodeKnowledgeGraph
    target = args.target.strip()
    symbol = args.symbol.strip()

    with get_db_session() as session:
        repo = get_repo(session, target)
        if not repo:
            print(f"❌ Repository '{target}' not found.")
            return

        nodes = session.exec(select(FileNode).where(FileNode.repo_id == repo.id)).all()
        symbols = session.exec(select(ASTSymbol).where(ASTSymbol.repo_id == repo.id)).all()
        graph = CodeKnowledgeGraph(repo.id, session=session)
        graph.build_from_ast_and_files(nodes, symbols)

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

def cmd_health(args):
    """Run health and complexity audit on a repository."""
    from sqlmodel import select
    from app.models.workspace import ASTSymbol, FileNode
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
    from sqlmodel import select
    from app.models.workspace import WorkspaceSummary
    from app.agent.nooa_agent import WIACodeUnderstandingAgent
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
    from app.services.ingestion.crawler import LANG_EXTENSIONS
    from app.services.parser import ASTParserEngine
    lang = LANG_EXTENSIONS.get(ext, "Other")

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    symbols = ASTParserEngine.parse_file("cli_dummy", os.path.basename(file_path), content, lang)
    print(f"\n🔍 AST Analysis for: {file_path} ({lang} - {len(content.splitlines())} LOC)")
    print(f"Found {len(symbols)} symbols:\n")
    print(f"{'TYPE':<12} | {'NAME':<24} | {'LINE':<8} | {'SIGNATURE / DETAILS'}")
    print("-" * 75)
    for s in symbols:
        details = s.signature or (", ".join(s.imported_symbols) if s.imported_symbols else "")
        print(f"{s.symbol_type:<12} | {s.name:<24} | {s.start_line:<8} | {details}")
    print("-" * 75 + "\n")

def cmd_symbols(args):
    """Search symbols across repository."""
    from sqlmodel import select
    from app.models.workspace import ASTSymbol
    target = args.target.strip()
    search_term = args.search.lower() if args.search else ""

    with get_db_session() as session:
        repo = get_repo(session, target)
        if not repo:
            print(f"❌ Repository '{target}' not found.")
            return

        statement = select(ASTSymbol).where(ASTSymbol.repo_id == repo.id)
        symbols = session.exec(statement).all()
        if search_term:
            symbols = [s for s in symbols if search_term in s.name.lower()]

        print(f"\n🔍 Symbols in '{repo.name}' ({len(symbols)} matches):\n")
        print(f"{'TYPE':<12} | {'NAME':<24} | {'FILE':<30} | {'LINE':<6}")
        print("-" * 78)
        for s in symbols[:30]:
            print(f"{s.symbol_type:<12} | {s.name:<24} | {s.file_path:<30} | {s.start_line:<6}")
        print("-" * 78 + "\n")

def cmd_dependencies(args):
    """Inspect import dependencies for a repository."""
    from sqlmodel import select
    from app.models.workspace import ASTSymbol
    target = args.target.strip()
    with get_db_session() as session:
        repo = get_repo(session, target)
        if not repo:
            print(f"❌ Repository '{target}' not found.")
            return

        imports = session.exec(select(ASTSymbol).where(ASTSymbol.repo_id == repo.id, ASTSymbol.symbol_type == "import")).all()
        print(f"\n📦 Dependencies & Imports in '{repo.name}' ({len(imports)} statements):\n")
        print(f"Manifests: {repo.dependencies or []}\n")
        for imp in imports[:20]:
            symbols_str = f" -> ({', '.join(imp.imported_symbols)})" if imp.imported_symbols else ""
            print(f"  • {imp.file_path}:{imp.start_line} imports `{imp.name}`{symbols_str}")
        print()

def cmd_summarize(args):
    """View hierarchical summaries for a repository."""
    from sqlmodel import select
    from app.models.workspace import WorkspaceSummary
    target = args.target.strip()
    with get_db_session() as session:
        repo = get_repo(session, target)
        if not repo:
            print(f"❌ Repository '{target}' not found.")
            return

        summaries = session.exec(select(WorkspaceSummary).where(WorkspaceSummary.repo_id == repo.id)).all()
        print(f"\n📚 Hierarchical Summaries for '{repo.name}' ({len(summaries)} total summaries):\n")
        for s in summaries:
            level_tag = f"[{s.level.upper()}]"
            path = f"({s.target_path})" if s.target_path else "(Root)"
            print(f"{level_tag:<18} {s.name} {path}")
            print(f"  └─ {s.summary_text}\n")

def cmd_list(args):
    """List all ingested repositories."""
    from sqlmodel import select
    from app.models.workspace import Repository
    with get_db_session() as session:
        repos = session.exec(select(Repository)).all()
        print(f"\n📦 Ingested Repositories ({len(repos)}):\n")
        print(f"{'REPO ID':<38} | {'NAME':<20} | {'STATUS':<10} | {'FILES':<6} | {'LOC':<8}")
        print("-" * 90)
        for r in repos:
            print(f"{r.id:<38} | {r.name:<20} | {r.status:<10} | {r.total_files:<6} | {r.total_loc:<8}")
        print("-" * 90 + "\n")

def cmd_export(args):
    """Export architecture report or OKF knowledge base."""
    from sqlmodel import select
    from app.models.workspace import WorkspaceSummary, FileNode, ASTSymbol
    from app.services.export.okf_exporter import OKFExporter
    target = args.target.strip()
    out_format = args.format or "markdown"
    output_path = args.output

    with get_db_session() as session:
        repo = get_repo(session, target)
        if not repo:
            print(f"❌ Repository '{target}' not found.")
            return

        summaries = session.exec(select(WorkspaceSummary).where(WorkspaceSummary.repo_id == repo.id)).all()
        nodes = session.exec(select(FileNode).where(FileNode.repo_id == repo.id)).all()
        symbols = session.exec(select(ASTSymbol).where(ASTSymbol.repo_id == repo.id)).all()

        if out_format.lower() == "okf":
            target_dir = output_path or repo.local_path or "."
            okf_dir = OKFExporter.export_okf_tree(repo, nodes, symbols, summaries, target_dir)
            print(f"✅ Open Knowledge Format export generated at: {okf_dir}")
            return

        repo_sum = next((s.summary_text for s in summaries if s.level == "repository"), "N/A")
        content = f"# Architecture Report: {repo.name}\n\n- Source: {repo.source_path}\n- Total LOC: {repo.total_loc}\n- Tech Stack: {dict(repo.tech_stack or {})}\n\n## Overview\n{repo_sum}\n"

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Exported report to {output_path}")
        else:
            print(content)

def cmd_delete(args):
    """Delete a repository from database."""
    from sqlmodel import select
    from app.models.workspace import FileNode, ASTSymbol, WorkspaceSummary, VectorChunk
    target = args.target.strip()
    with get_db_session() as session:
        repo = get_repo(session, target)
        if not repo:
            print(f"❌ Repository '{target}' not found.")
            return

        repo_id = repo.id
        nodes = session.exec(select(FileNode).where(FileNode.repo_id == repo_id)).all()
        for n in nodes: session.delete(n)
        symbols = session.exec(select(ASTSymbol).where(ASTSymbol.repo_id == repo_id)).all()
        for s in symbols: session.delete(s)
        summaries = session.exec(select(WorkspaceSummary).where(WorkspaceSummary.repo_id == repo_id)).all()
        for s in summaries: session.delete(s)
        chunks = session.exec(select(VectorChunk).where(VectorChunk.repo_id == repo_id)).all()
        for c in chunks: session.delete(c)
        session.delete(repo)
        session.commit()
        print(f"✅ Repository '{repo.name}' ({repo_id}) deleted.")

def cmd_serve(args):
    """Run FastAPI server daemon for VS Code and APIs."""
    import uvicorn
    host = args.host or "127.0.0.1"
    port = args.port or 8000
    print(f"🌐 Starting WIA Local Engine on http://{host}:{port}")
    uvicorn.run("app.main:app", host=host, port=port, reload=args.reload)

def cmd_test(args):
    """Run test suite."""
    import pytest
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    pytest.main(["-v", os.path.join(root_dir, "backend", "tests")])

def build_parser():
    from app.core.config import settings
    parser = argparse.ArgumentParser(
        prog="wia",
        description="Workspace Intelligence Agent (WIA) - Code Knowledge Graph & Developer Intelligence CLI"
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"wia version {settings.VERSION}",
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
    p_flow.add_argument("--entry", required=True, help="Function or route entry point name")
    p_flow.set_defaults(func=cmd_flow)

    # impact
    p_imp = subparsers.add_parser("impact", help="Analyze ripple change impact for a symbol or file")
    p_imp.add_argument("target", help="Repository ID or name")
    p_imp.add_argument("--symbol", required=True, help="Symbol name or file path to analyze")
    p_imp.set_defaults(func=cmd_impact)

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
