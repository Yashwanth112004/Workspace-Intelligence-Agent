from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, JSON, Column
from datetime import datetime
from enum import Enum
import uuid

class ProvenanceType(str, Enum):
    DETERMINISTIC_FACT = "DETERMINISTIC_FACT"
    LLM_SUMMARY = "LLM_SUMMARY"
    LLM_INFERENCE = "LLM_INFERENCE"
    USER_INPUT = "USER_INPUT"

class RelationshipType(str, Enum):
    CONTAINS = "CONTAINS"
    DEFINES = "DEFINES"
    IMPORTS = "IMPORTS"
    REFERENCES = "REFERENCES"
    DEPENDS_ON = "DEPENDS_ON"
    CALLS = "CALLS"
    INHERITS = "INHERITS"
    IMPLEMENTS = "IMPLEMENTS"
    TESTS = "TESTS"

class EntityType(str, Enum):
    REPOSITORY = "REPOSITORY"
    DIRECTORY = "DIRECTORY"
    FILE = "FILE"
    MODULE = "MODULE"
    CLASS = "CLASS"
    INTERFACE = "INTERFACE"
    FUNCTION = "FUNCTION"
    METHOD = "METHOD"
    ENDPOINT = "ENDPOINT"
    TEST = "TEST"
    SUMMARY = "SUMMARY"

class KnowledgeEntity(SQLModel, table=True):
    """Core domain entity node in the WIA Code Knowledge Graph."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    repo_id: str = Field(index=True)
    entity_type: str = Field(index=True) # EntityType
    name: str = Field(index=True)
    qualified_name: Optional[str] = Field(default=None, index=True)
    file_path: Optional[str] = Field(default=None, index=True)
    start_line: int = 0
    end_line: int = 0
    signature: Optional[str] = None
    docstring: Optional[str] = None
    language: Optional[str] = None
    loc: int = 0
    complexity: int = 1
    visibility: str = "public"
    provenance_type: str = Field(default=ProvenanceType.DETERMINISTIC_FACT.value)
    properties: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class KnowledgeRelationship(SQLModel, table=True):
    """Explicit directed relationship edge in the WIA Code Knowledge Graph."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    repo_id: str = Field(index=True)
    source_id: str = Field(index=True)
    target_id: str = Field(index=True)
    source_name: str
    target_name: str
    relationship_type: str = Field(index=True) # RelationshipType
    provenance_type: str = Field(default=ProvenanceType.DETERMINISTIC_FACT.value)
    source_location: Optional[str] = None # file:start-end
    confidence: float = 1.0
    properties: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class ProvenanceRecord(SQLModel, table=True):
    """Audit trail for deterministic vs LLM-inferred knowledge."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    repo_id: str = Field(index=True)
    entity_or_rel_id: str = Field(index=True)
    provenance_type: str # ProvenanceType
    extraction_method: str # AST_VISITOR, REGEX_PARSER, LLM_SUMMARY, etc.
    source_file: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    commit_hash: Optional[str] = None
    details: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
