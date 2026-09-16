from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query, Response
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from sqlmodel import Session, select
import os
import shutil

from app.core.database import get_session
from app.core.config import settings
from app.models.workspace import Repository, FileNode, ASTSymbol, WorkspaceSummary, VectorChunk
from app.services.pipeline import run_ingestion_pipeline, IN_MEMORY_CHUNKS, IN_MEMORY_SUMMARIES
from app.agent.nooa_agent import WIACodeUnderstandingAgent
from app.services.rag.vector_store import VectorSearchStore

router = APIRouter(prefix="/api/v1", tags=["WIA Core API"])

class IngestRequest(BaseModel):
    source_path: str = Field(..., description="GitHub Repository URL or local directory path")
    name: Optional[str] = None

class IngestResponse(BaseModel):
    repo_id: str
    name: str
    status: str
    message: str

class QueryRequest(BaseModel):
    query: str

@router.post("/ingest", response_model=IngestResponse)
def ingest_repository(request: IngestRequest, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    """Accepts a GitHub repository URL or local project path and starts background analysis."""
    source_path = request.source_path.strip()
    if not source_path:
        raise HTTPException(status_code=400, detail="source_path cannot be empty")

    name = request.name or os.path.basename(source_path.rstrip("/\\")) or "Workspace Repo"

    repo = Repository(
        name=name,
        source_type="github" if source_path.startswith("http") else "local",
        source_path=source_path,
        local_path="",
        status="pending",
        progress_pct=0,
        status_message="Ingestion queued..."
    )
    session.add(repo)
    session.commit()
    session.refresh(repo)

    # Launch pipeline in background thread
    background_tasks.add_task(run_ingestion_pipeline, repo.id)

    return IngestResponse(
        repo_id=repo.id,
        name=repo.name,
        status=repo.status,
        message="Repository ingestion started in background."
    )

@router.get("/repos/{repo_id}/status")
def get_analysis_status(repo_id: str, session: Session = Depends(get_session)):
    """Get current status and progress of repository analysis."""
    repo = session.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    return {
        "repo_id": repo.id,
        "name": repo.name,
        "source_type": repo.source_type,
        "source_path": repo.source_path,
        "status": repo.status,
        "progress_pct": repo.progress_pct,
        "status_message": repo.status_message,
        "total_files": repo.total_files,
        "total_loc": repo.total_loc,
        "tech_stack": repo.tech_stack,
        "dependencies": repo.dependencies,
        "entry_points": repo.entry_points,
        "config_files": repo.config_files,
        "error_message": repo.error_message,
        "created_at": repo.created_at
    }

@router.get("/repos/{repo_id}/tree")
def get_repository_tree(repo_id: str, session: Session = Depends(get_session)):
    """Get file and folder structure of the repository."""
    repo = session.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    nodes = session.exec(select(FileNode).where(FileNode.repo_id == repo_id)).all()
    return {
        "repo_id": repo_id,
        "name": repo.name,
        "total_files": repo.total_files,
        "total_loc": repo.total_loc,
        "nodes": [n.model_dump() for n in nodes]
    }

@router.get("/repos/{repo_id}/file")
def get_file_details(repo_id: str, path: str = Query(..., description="Relative file path"), session: Session = Depends(get_session)):
    """Get code content, AST symbols, and summary for a specific file."""
    repo = session.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    node = session.exec(select(FileNode).where(FileNode.repo_id == repo_id, FileNode.relative_path == path)).first()
    if not node or node.is_dir:
        raise HTTPException(status_code=404, detail="File not found")

    # Read code content
    code_content = ""
    if os.path.exists(node.path):
        try:
            with open(node.path, "r", encoding="utf-8", errors="ignore") as f:
                code_content = f.read()
        except Exception as e:
            code_content = f"Error reading file: {e}"

    symbols = session.exec(select(ASTSymbol).where(ASTSymbol.repo_id == repo_id, ASTSymbol.file_path == path)).all()
    summary = session.exec(select(WorkspaceSummary).where(WorkspaceSummary.repo_id == repo_id, WorkspaceSummary.target_path == path)).first()

    return {
        "file": node.model_dump(),
        "content": code_content,
        "symbols": [s.model_dump() for s in symbols],
        "summary": summary.summary_text if summary else "No summary available."
    }

@router.get("/repos/{repo_id}/function/{func_id}")
def get_function_details(repo_id: str, func_id: str, session: Session = Depends(get_session)):
    """Get details of a specific function or AST symbol."""
    symbol = session.get(ASTSymbol, func_id)
    if not symbol or symbol.repo_id != repo_id:
        raise HTTPException(status_code=404, detail="Function symbol not found")

    return symbol.model_dump()

@router.get("/repos/{repo_id}/summary")
def get_workspace_summary(repo_id: str, session: Session = Depends(get_session)):
    """Get full hierarchical workspace summaries (Repo -> Folder -> File -> Function)."""
    repo = session.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    summaries = session.exec(select(WorkspaceSummary).where(WorkspaceSummary.repo_id == repo_id)).all()
    
    # Group by level
    repo_summary = [s.model_dump() for s in summaries if s.level == "repository"]
    folder_summaries = [s.model_dump() for s in summaries if s.level in ("child_folder", "parent_folder")]
    file_summaries = [s.model_dump() for s in summaries if s.level == "file"]
    function_summaries = [s.model_dump() for s in summaries if s.level == "function"]

    return {
        "repo_id": repo_id,
        "repository_summary": repo_summary[0] if repo_summary else None,
        "folder_summaries": folder_summaries,
        "file_summaries": file_summaries,
        "function_summaries": function_summaries
    }

@router.post("/repos/{repo_id}/query")
def query_workspace(repo_id: str, request: QueryRequest, session: Session = Depends(get_session)):
    """Natural-language question answering about the codebase using NOOA Agent + RAG."""
    repo = session.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Load chunks & summaries (cache or database)
    chunks = IN_MEMORY_CHUNKS.get(repo_id)
    if not chunks:
        chunks = session.exec(select(VectorChunk).where(VectorChunk.repo_id == repo_id)).all()

    summaries = IN_MEMORY_SUMMARIES.get(repo_id)
    if not summaries:
        summaries = session.exec(select(WorkspaceSummary).where(WorkspaceSummary.repo_id == repo_id)).all()

    agent = WIACodeUnderstandingAgent(repo, chunks, summaries)
    result = agent.answer_question(request.query)

    return result

@router.get("/repos/{repo_id}/symbols/search")
def search_symbols(
    repo_id: str,
    q: str = Query(..., min_length=1, description="Search term for symbol name"),
    symbol_type: Optional[str] = Query(None, description="Filter by function, class, import"),
    session: Session = Depends(get_session)
):
    """Search AST symbols across the repository by name or symbol type."""
    repo = session.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    statement = select(ASTSymbol).where(ASTSymbol.repo_id == repo_id)
    if symbol_type:
        statement = statement.where(ASTSymbol.symbol_type == symbol_type)
    
    symbols = session.exec(statement).all()
    q_lower = q.lower()
    matches = [s.model_dump() for s in symbols if q_lower in s.name.lower()]

    return {
        "repo_id": repo_id,
        "query": q,
        "total_matches": len(matches),
        "symbols": matches
    }

@router.get("/repos/{repo_id}/metrics")
def get_repository_metrics(repo_id: str, session: Session = Depends(get_session)):
    """Get code metrics including language breakdown, file sizes, and symbol counts."""
    repo = session.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    nodes = session.exec(select(FileNode).where(FileNode.repo_id == repo_id)).all()
    symbols = session.exec(select(ASTSymbol).where(ASTSymbol.repo_id == repo_id)).all()

    file_nodes = [n for n in nodes if not n.is_dir]
    total_files = len(file_nodes)
    total_directories = len([n for n in nodes if n.is_dir])
    total_loc = sum(n.loc_count for n in file_nodes)
    total_bytes = sum(n.size_bytes for n in file_nodes)

    symbol_counts = {
        "functions": len([s for s in symbols if s.symbol_type == "function"]),
        "classes": len([s for s in symbols if s.symbol_type == "class"]),
        "imports": len([s for s in symbols if s.symbol_type == "import"]),
        "total_symbols": len(symbols)
    }

    largest_files = sorted(file_nodes, key=lambda n: n.loc_count, reverse=True)[:10]

    return {
        "repo_id": repo_id,
        "name": repo.name,
        "total_files": total_files,
        "total_directories": total_directories,
        "total_loc": total_loc,
        "total_bytes": total_bytes,
        "tech_stack": repo.tech_stack,
        "symbol_counts": symbol_counts,
        "largest_files": [
            {"path": f.relative_path, "loc": f.loc_count, "language": f.language, "size_bytes": f.size_bytes}
            for f in largest_files
        ]
    }

@router.get("/repos/{repo_id}/dependencies/graph")
def get_dependency_graph(repo_id: str, session: Session = Depends(get_session)):
    """Extract file import linkages and dependency graph for the codebase."""
    repo = session.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    imports = session.exec(
        select(ASTSymbol).where(ASTSymbol.repo_id == repo_id, ASTSymbol.symbol_type == "import")
    ).all()

    graph = []
    for imp in imports:
        graph.append({
            "source_file": imp.file_path,
            "imported_module": imp.name,
            "symbols": imp.imported_symbols,
            "line": imp.start_line
        })

    return {
        "repo_id": repo_id,
        "total_import_statements": len(graph),
        "external_dependencies": repo.dependencies,
        "import_graph": graph
    }

@router.get("/repos/{repo_id}/export")
def export_repository_report(
    repo_id: str,
    format: str = Query("markdown", description="Export format: 'markdown' or 'json'"),
    session: Session = Depends(get_session)
):
    """Export complete architecture summary, symbols, and metrics as Markdown or JSON."""
    repo = session.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    summaries = session.exec(select(WorkspaceSummary).where(WorkspaceSummary.repo_id == repo_id)).all()
    symbols = session.exec(select(ASTSymbol).where(ASTSymbol.repo_id == repo_id)).all()
    nodes = session.exec(select(FileNode).where(FileNode.repo_id == repo_id)).all()

    if format.lower() == "json":
        return {
            "repository": repo.model_dump(),
            "summaries": [s.model_dump() for s in summaries],
            "symbols_count": len(symbols),
            "files_count": len(nodes)
        }

    # Markdown export
    repo_sum = next((s.summary_text for s in summaries if s.level == "repository"), "No overview available.")
    folder_sums = [s for s in summaries if s.level in ("parent_folder", "child_folder")]
    file_sums = [s for s in summaries if s.level == "file"]

    md_lines = [
        f"# Architecture & Intelligence Report: {repo.name}",
        f"",
        f"- **Source**: `{repo.source_path}` ({repo.source_type})",
        f"- **Total Files**: {repo.total_files} | **Total LOC**: {repo.total_loc}",
        f"- **Tech Stack**: {', '.join([f'{k} ({v} LOC)' for k, v in (repo.tech_stack or {}).items()])}",
        f"- **Entry Points**: {', '.join(repo.entry_points or ['None detected'])}",
        f"",
        f"## High-Level Architecture Overview",
        f"{repo_sum}",
        f"",
        f"## Directory Modules Breakdown",
    ]

    for f_sum in folder_sums:
        md_lines.append(f"### 📁 `{f_sum.target_path}` ({f_sum.name})")
        md_lines.append(f"{f_sum.summary_text}\n")

    md_lines.append(f"## Key File Summaries")
    for fl_sum in file_sums[:25]:
        md_lines.append(f"- **`{fl_sum.target_path}`**: {fl_sum.summary_text}")

    md_content = "\n".join(md_lines)
    return Response(content=md_content, media_type="text/markdown")

@router.delete("/repos/{repo_id}")
def delete_repository(repo_id: str, session: Session = Depends(get_session)):
    """Delete a repository and all associated nodes, symbols, summaries, and chunks."""
    repo = session.get(Repository, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Delete disk files if in data/repos
    target_dir = os.path.join(settings.REPOS_DIR, repo_id)
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir, ignore_errors=True)

    # Delete database records
    nodes = session.exec(select(FileNode).where(FileNode.repo_id == repo_id)).all()
    for n in nodes:
        session.delete(n)

    symbols = session.exec(select(ASTSymbol).where(ASTSymbol.repo_id == repo_id)).all()
    for s in symbols:
        session.delete(s)

    summaries = session.exec(select(WorkspaceSummary).where(WorkspaceSummary.repo_id == repo_id)).all()
    for sum_item in summaries:
        session.delete(sum_item)

    chunks = session.exec(select(VectorChunk).where(VectorChunk.repo_id == repo_id)).all()
    for c in chunks:
        session.delete(c)

    session.delete(repo)
    session.commit()

    # Clear memory cache
    IN_MEMORY_CHUNKS.pop(repo_id, None)
    IN_MEMORY_SUMMARIES.pop(repo_id, None)

    return {"message": f"Repository '{repo.name}' ({repo_id}) and all analysis data successfully deleted."}

@router.get("/repos")
def list_repositories(session: Session = Depends(get_session)):
    """List all ingested repositories."""
    repos = session.exec(select(Repository)).all()
    return {"repositories": [r.model_dump() for r in repos]}
