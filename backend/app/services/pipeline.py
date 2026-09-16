import os
import logging
from typing import Dict, Any, List
from sqlmodel import Session, select
from app.core.database import engine
from app.core.config import settings
from app.models.workspace import Repository, FileNode, ASTSymbol, WorkspaceSummary, VectorChunk
from app.services.ingestion import RepositoryCrawler
from app.services.parser import ASTParserEngine
from app.services.summarizer import HierarchicalSummarizerEngine
from app.services.rag import VectorSearchStore

logger = logging.getLogger("wia.pipeline")

# In-memory vector chunk storage cache for quick retrieval
IN_MEMORY_CHUNKS: Dict[str, List[VectorChunk]] = {}
IN_MEMORY_SUMMARIES: Dict[str, List[WorkspaceSummary]] = {}

def run_ingestion_pipeline(repo_id: str):
    """Full background ingestion and understanding pipeline."""
    with Session(engine) as session:
        repo = session.get(Repository, repo_id)
        if not repo:
            logger.error(f"Repository {repo_id} not found for pipeline processing.")
            return

        try:
            # 1. Repository Ingestion & Crawling
            repo.status = "ingesting"
            repo.progress_pct = 10
            repo.status_message = "Cloning / scanning repository files..."
            session.add(repo)
            session.commit()

            target_dir = os.path.join(settings.REPOS_DIR, repo_id)
            local_path, source_type = RepositoryCrawler.prepare_repository(repo.source_path, target_dir)
            
            repo.local_path = local_path
            repo.source_type = source_type

            nodes, stats = RepositoryCrawler.scan_repository(repo.id, local_path)
            
            # Save FileNodes
            for node in nodes:
                session.add(node)
            
            repo.total_files = stats["total_files"]
            repo.total_loc = stats["total_loc"]
            repo.tech_stack = stats["tech_stack"]
            repo.dependencies = stats["dependencies"]
            repo.config_files = stats["config_files"]
            repo.entry_points = stats["entry_points"]
            
            repo.progress_pct = 35
            repo.status_message = f"Scanned {repo.total_files} files ({repo.total_loc} LOC). Parsing AST..."
            session.add(repo)
            session.commit()

            # 2. Code Understanding - AST Parsing
            repo.status = "parsing"
            session.add(repo)
            session.commit()

            all_symbols: List[ASTSymbol] = []
            file_nodes = [n for n in nodes if not n.is_dir]

            for f_node in file_nodes:
                try:
                    with open(f_node.path, "r", encoding="utf-8", errors="ignore") as f:
                        code = f.read()
                    symbols = ASTParserEngine.parse_file(repo_id, f_node.relative_path, code, f_node.language or "Other")
                    for sym in symbols:
                        session.add(sym)
                        all_symbols.append(sym)
                except Exception as e:
                    logger.debug(f"AST parsing error for {f_node.relative_path}: {e}")

            session.commit()

            # 3. Hierarchical Workspace Summarization
            repo.status = "summarizing"
            repo.progress_pct = 65
            repo.status_message = "Generating 5-level hierarchical summaries..."
            session.add(repo)
            session.commit()

            summaries = HierarchicalSummarizerEngine.generate_all_summaries(repo, nodes, all_symbols)
            for s in summaries:
                session.add(s)
            session.commit()

            IN_MEMORY_SUMMARIES[repo_id] = summaries

            # 4. RAG Vector Search Indexing
            repo.status = "vectorizing"
            repo.progress_pct = 85
            repo.status_message = "Building semantic vector embeddings..."
            session.add(repo)
            session.commit()

            chunks = VectorSearchStore.build_index(repo_id, nodes, summaries, all_symbols)
            for c in chunks:
                session.add(c)
            session.commit()

            IN_MEMORY_CHUNKS[repo_id] = chunks

            # 5. Pipeline Complete
            repo.status = "completed"
            repo.progress_pct = 100
            repo.status_message = "Workspace Intelligence Analysis Complete!"
            session.add(repo)
            session.commit()
            logger.info(f"Pipeline completed successfully for repo {repo_id}")

        except Exception as e:
            logger.error(f"Pipeline failed for repo {repo_id}: {e}", exc_info=True)
            repo.status = "failed"
            repo.error_message = str(e)
            repo.status_message = f"Analysis Failed: {str(e)}"
            session.add(repo)
            session.commit()
