from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, JSON, Column
from datetime import datetime
import uuid

class Repository(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    source_type: str # "github" or "local"
    source_path: str # URL or local directory
    local_path: str # Cloned / local path on disk
    status: str = "pending" # pending, ingesting, parsing, summarizing, vectorizing, completed, failed
    progress_pct: int = 0
    status_message: str = "Initialized"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    # Metadata
    total_files: int = 0
    total_loc: int = 0
    tech_stack: Dict[str, int] = Field(default_factory=dict, sa_column=Column(JSON)) # lang -> LOC or file count
    dependencies: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    entry_points: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    config_files: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    error_message: Optional[str] = None

class FileNode(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    repo_id: str = Field(index=True)
    path: str # Absolute path
    relative_path: str # Path relative to repo root
    name: str
    is_dir: bool = False
    language: Optional[str] = None
    size_bytes: int = 0
    loc_count: int = 0
    parent_path: str = ""
    depth: int = 0

class ASTSymbol(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    repo_id: str = Field(index=True)
    file_path: str = Field(index=True) # relative path
    symbol_type: str # "function", "class", "method", "import", "variable"
    name: str
    signature: Optional[str] = None
    start_line: int = 0
    end_line: int = 0
    docstring: Optional[str] = None
    parameters: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    return_type: Optional[str] = None
    calls: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    imported_symbols: List[str] = Field(default_factory=list, sa_column=Column(JSON))

class WorkspaceSummary(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    repo_id: str = Field(index=True)
    level: str # "function", "file", "child_folder", "parent_folder", "repository"
    target_path: str = Field(index=True) # relative path or "" for repo
    name: str
    summary_text: str
    key_components: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    dependencies: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class VectorChunk(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    repo_id: str = Field(index=True)
    file_path: str = Field(index=True)
    chunk_type: str # "code", "summary", "function"
    content: str
    start_line: int = 0
    end_line: int = 0
    embedding: List[float] = Field(default_factory=list, sa_column=Column(JSON))
