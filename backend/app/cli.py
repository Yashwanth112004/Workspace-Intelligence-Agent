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

from app.core.database import init_db, engine
from app.models.workspace import Repository, FileNode, ASTSymbol, WorkspaceSummary, VectorChunk
from app.services.ingestion import RepositoryCrawler
from app.services.parser import ASTParserEngine
from app.services.summarizer import HierarchicalSummarizerEngine
from app.services.rag import VectorSearchStore
from app.agent.nooa_agent import WIACodeUnderstandingAgent
from app.services.pipeline import run_ingestion_pipeline, IN_MEMORY_CHUNKS, IN_MEMORY_SUMMARIES

logging.basicConfig(level=logging.WARNING, format="%(message)s")
logger = logging.getLogger("wia.cli")

def get_db_session():
    init_db()
    return Session(engine)

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

        repo_id = repo.id
        print(f"📦 Repository ID: {repo_id}")
        print(f"⏳ Running ingestion & code intelligence pipeline...")

        # Run pipeline synchronously for CLI
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
            print(f"\n💡 Ask questions with: python main.py query {repo_id} \"Explain architecture\"\n")
        else:
            print(f"\n❌ Pipeline failed: {repo.error_message}")

def cmd_query(args):
    """Query codebase via NOOA Agent & RAG from CLI."""
    target = args.target.strip()
    question = args.question.strip()

    with get_db_session() as session:
        # Try matching by ID first, then by name, then by path
        repo = session.get(Repository, target)
        if not repo:
            repo = session.exec(select(Repository).where(Repository.name == target)).first()
        if not repo:
            repo = session.exec(select(Repository).where(Repository.source_path == target)).first()

        if not repo:
            print(f"❌ Error: Repository '{target}' not found. Ingest it first with 'scan' or check 'list'.")
            return

        chunks = session.exec(select(VectorChunk).where(VectorChunk.repo_id == repo.id)).all()
        summaries = session.exec(select(WorkspaceSummary).where(WorkspaceSummary.repo_id == repo.id)).all()

        print(f"\n🧠 [WIA Agent] Querying '{repo.name}' for: \"{question}\"")
        agent = WIACodeUnderstandingAgent(repo, chunks, summaries)
        result = agent.answer_question(question)

        print("\n" + "=" * 60)
        print("🤖 ANSWER:")
        print("=" * 60)
        print(result.get("response", "No response generated."))
        print("\n" + "=" * 60)
        print("📑 CONTEXT CITATIONS:")
        print("=" * 60)
        for idx, cite in enumerate(result.get("citations", []), 1):
            lines = f" (Lines {cite['start_line']}-{cite['end_line']})" if cite.get("start_line") else ""
            print(f" {idx}. [{cite.get('chunk_type', 'code').upper()}] {cite.get('file_path')}{lines} (Score: {cite.get('score', 0)})")
        print("=" * 60 + "\n")

def cmd_parse(args):
    """Parse AST symbols from a specific file."""
    file_path = args.file
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    ext = os.path.splitext(file_path)[1].lower()
    from app.services.ingestion.crawler import LANG_EXTENSIONS
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

def cmd_summarize(args):
    """View hierarchical summaries for a repository."""
    target = args.target.strip()
    with get_db_session() as session:
        repo = session.get(Repository, target) or session.exec(select(Repository).where(Repository.name == target)).first()
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
    with get_db_session() as session:
        repos = session.exec(select(Repository)).all()
        print(f"\n📦 Ingested Repositories ({len(repos)}):\n")
        print(f"{'REPO ID':<38} | {'NAME':<20} | {'STATUS':<10} | {'FILES':<6} | {'LOC':<8}")
        print("-" * 90)
        for r in repos:
            print(f"{r.id:<38} | {r.name:<20} | {r.status:<10} | {r.total_files:<6} | {r.total_loc:<8}")
        print("-" * 90 + "\n")

def cmd_metrics(args):
    """Show detailed metrics for a repository."""
    target = args.target.strip()
    with get_db_session() as session:
        repo = session.get(Repository, target) or session.exec(select(Repository).where(Repository.name == target)).first()
        if not repo:
            print(f"❌ Repository '{target}' not found.")
            return

        nodes = session.exec(select(FileNode).where(FileNode.repo_id == repo.id)).all()
        symbols = session.exec(select(ASTSymbol).where(ASTSymbol.repo_id == repo.id)).all()

        file_nodes = [n for n in nodes if not n.is_dir]
        print(f"\n📊 Metrics for '{repo.name}':")
        print(f"   - Files:       {len(file_nodes)}")
        print(f"   - Folders:     {len([n for n in nodes if n.is_dir])}")
        print(f"   - Total LOC:   {repo.total_loc}")
        print(f"   - Functions:   {len([s for s in symbols if s.symbol_type == 'function'])}")
        print(f"   - Classes:     {len([s for s in symbols if s.symbol_type == 'class'])}")
        print(f"   - Imports:     {len([s for s in symbols if s.symbol_type == 'import'])}")
        print(f"   - Tech Stack:  {dict(repo.tech_stack or {})}")
        print(f"   - Entry Points:{repo.entry_points or []}\n")

def cmd_export(args):
    """Export architecture report as Markdown or JSON."""
    target = args.target.strip()
    out_format = args.format or "markdown"
    output_path = args.output

    with get_db_session() as session:
        repo = session.get(Repository, target) or session.exec(select(Repository).where(Repository.name == target)).first()
        if not repo:
            print(f"❌ Repository '{target}' not found.")
            return

        summaries = session.exec(select(WorkspaceSummary).where(WorkspaceSummary.repo_id == repo.id)).all()
        
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
    target = args.target.strip()
    with get_db_session() as session:
        repo = session.get(Repository, target) or session.exec(select(Repository).where(Repository.name == target)).first()
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
    """Run FastAPI server."""
    import uvicorn
    host = args.host or "0.0.0.0"
    port = args.port or 8000
    print(f"🌐 Starting WIA Backend on http://{host}:{port}")
    uvicorn.run("app.main:app", host=host, port=port, reload=args.reload)

def cmd_dev(args):
    """Run dev server."""
    import subprocess
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    runner = os.path.join(root_dir, "run_dev.py")
    subprocess.run([sys.executable, runner])

def cmd_test(args):
    """Run test suite."""
    import pytest
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    pytest.main(["-v", os.path.join(root_dir, "backend", "tests")])

def build_parser():
    parser = argparse.ArgumentParser(
        prog="wia",
        description="Workspace Intelligence Agent (WIA) - AI Multi-Agent Code Understanding Platform"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available WIA CLI Commands")

    # scan
    p_scan = subparsers.add_parser("scan", help="Scan and ingest a repository (local folder or GitHub URL)")
    p_scan.add_argument("path", help="Local directory path or GitHub URL")
    p_scan.add_argument("--name", help="Custom repository name")
    p_scan.set_defaults(func=cmd_scan)

    # query
    p_query = subparsers.add_parser("query", help="Ask AI technical questions about an ingested codebase")
    p_query.add_argument("target", help="Repository ID, name, or path")
    p_query.add_argument("question", help="Natural language question to ask")
    p_query.set_defaults(func=cmd_query)

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

    # metrics
    p_metrics = subparsers.add_parser("metrics", help="Show code metrics, language breakdown, and symbol stats")
    p_metrics.add_argument("target", help="Repository ID or name")
    p_metrics.set_defaults(func=cmd_metrics)

    # export
    p_exp = subparsers.add_parser("export", help="Export architecture report as Markdown or JSON")
    p_exp.add_argument("target", help="Repository ID or name")
    p_exp.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Export format")
    p_exp.add_argument("--output", "-o", help="File path to save output")
    p_exp.set_defaults(func=cmd_export)

    # delete
    p_del = subparsers.add_parser("delete", help="Delete a repository and its intelligence index")
    p_del.add_argument("target", help="Repository ID or name")
    p_del.set_defaults(func=cmd_delete)

    # serve
    p_serve = subparsers.add_parser("serve", help="Start the FastAPI backend server")
    p_serve.add_argument("--host", default="0.0.0.0", help="Host address")
    p_serve.add_argument("--port", type=int, default=8000, help="Port number")
    p_serve.add_argument("--reload", action="store_true", help="Enable auto-reload")
    p_serve.set_defaults(func=cmd_serve)

    # dev
    p_dev = subparsers.add_parser("dev", help="Launch full development environment (FastAPI + React)")
    p_dev.set_defaults(func=cmd_dev)

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
