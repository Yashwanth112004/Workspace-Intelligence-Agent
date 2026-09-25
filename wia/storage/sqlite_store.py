"""SQLite database store for persistent relational workspace indexing."""

import json
import sqlite3
from pathlib import Path
from wia.core.index_model import WorkspaceIndex, BatchRecord
from wia.core.metadata import FileRecord, IndexingStatus


class SQLiteStore:
    """Relational SQLite database persistence layer for WIA Workspace Index."""

    @classmethod
    def get_connection(cls, db_path: str | Path) -> sqlite3.Connection:
        """Create or connect to SQLite database with optimized PRAGMA settings."""
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
        # Performance tuning: WAL mode, memory temp store, 64MB cache, normalized synchronous
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA cache_size = -64000;")
        conn.execute("PRAGMA temp_store = MEMORY;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    @classmethod
    def init_schema(cls, conn: sqlite3.Connection) -> None:
        """Initialize SQLite database schema tables and query performance indices."""
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    path TEXT PRIMARY KEY,
                    file_size INTEGER NOT NULL,
                    modified_time REAL NOT NULL,
                    extension TEXT NOT NULL,
                    content_hash TEXT,
                    language TEXT NOT NULL,
                    indexing_status TEXT NOT NULL,
                    extra_metadata TEXT,
                    batch_id TEXT
                );
            """)
            # Migration check: add batch_id column if created previously without it
            cursor = conn.cursor()
            cols = [row["name"] for row in cursor.execute("PRAGMA table_info(files)").fetchall()]
            if "batch_id" not in cols:
                conn.execute("ALTER TABLE files ADD COLUMN batch_id TEXT")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS symbols (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    symbol_name TEXT NOT NULL,
                    symbol_type TEXT NOT NULL,
                    line_number INTEGER,
                    FOREIGN KEY(file_path) REFERENCES files(path) ON DELETE CASCADE
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS batches (
                    batch_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    discovered_count INTEGER NOT NULL,
                    indexed_count INTEGER NOT NULL,
                    ignored_count INTEGER NOT NULL,
                    duration_seconds REAL NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    error_message TEXT,
                    failure_stage TEXT,
                    file_paths_json TEXT NOT NULL,
                    narrative_summary TEXT
                );
            """)
            # Migration check: add narrative_summary column if not present
            cursor = conn.cursor()
            b_cols = [row["name"] for row in cursor.execute("PRAGMA table_info(batches)").fetchall()]
            if "narrative_summary" not in b_cols:
                conn.execute("ALTER TABLE batches ADD COLUMN narrative_summary TEXT")

            # High performance query indices
            conn.execute("CREATE INDEX IF NOT EXISTS idx_files_language ON files(language);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_files_status ON files(indexing_status);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_files_batch ON files(batch_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_symbols_file ON symbols(file_path);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(symbol_name);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_symbols_type ON symbols(symbol_type);")

    @classmethod
    def save_index(cls, db_path: str | Path, index: WorkspaceIndex) -> None:
        """Persist a WorkspaceIndex object into SQLite tables using batch operations."""
        conn = cls.get_connection(db_path)
        cls.init_schema(conn)

        with conn:
            # Save metadata in batch
            meta_entries = [
                ("index_version", index.index_version),
                ("wia_version", index.wia_version),
                ("workspace_path", index.workspace_path),
                ("indexed_at", index.indexed_at),
                ("stats", json.dumps(index.stats)),
                ("languages", json.dumps(index.languages)),
                ("frameworks", json.dumps(index.frameworks)),
                ("batches", json.dumps([b.to_dict() for b in index.batches])),
            ]
            conn.executemany("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", meta_entries)

            # Clear existing files and symbols to rewrite accumulated state
            conn.execute("DELETE FROM symbols")
            conn.execute("DELETE FROM files")

            # Batch prepare file records and extracted symbols
            file_rows = []
            symbol_rows = []
            for rel_p, rec in index.files.items():
                extra_json = json.dumps(rec.extra_metadata)
                status_val = rec.indexing_status.value if hasattr(rec.indexing_status, "value") else str(rec.indexing_status)
                batch_id = rec.extra_metadata.get("batch_id", "")
                file_rows.append((
                    rec.relative_path,
                    rec.file_size,
                    rec.modified_time,
                    rec.extension,
                    rec.content_hash,
                    rec.language,
                    status_val,
                    extra_json,
                    batch_id,
                ))

                symbols = rec.extra_metadata.get("symbols", [])
                for sym in symbols:
                    symbol_rows.append((
                        rec.relative_path,
                        sym.get("name", ""),
                        sym.get("symbol_type", ""),
                        sym.get("line_number", 0),
                    ))

            if file_rows:
                conn.executemany(
                    """
                    INSERT INTO files (path, file_size, modified_time, extension, content_hash, language, indexing_status, extra_metadata, batch_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    file_rows,
                )
            if symbol_rows:
                conn.executemany(
                    """
                    INSERT INTO symbols (file_path, symbol_name, symbol_type, line_number)
                    VALUES (?, ?, ?, ?)
                    """,
                    symbol_rows,
                )

            # Save batch records in batch
            conn.execute("DELETE FROM batches")
            batch_rows = [
                (
                    b.batch_id,
                    b.status,
                    b.discovered_count,
                    b.indexed_count,
                    b.ignored_count,
                    b.duration_seconds,
                    b.started_at,
                    b.completed_at,
                    b.error_message,
                    b.failure_stage,
                    json.dumps(b.file_paths),
                    b.narrative_summary,
                )
                for b in index.batches
            ]
            if batch_rows:
                conn.executemany(
                    """
                    INSERT OR REPLACE INTO batches (batch_id, status, discovered_count, indexed_count, ignored_count, duration_seconds, started_at, completed_at, error_message, failure_stage, file_paths_json, narrative_summary)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    batch_rows,
                )
                        b.batch_id,
                        b.status,
                        b.discovered_count,
                        b.indexed_count,
                        b.ignored_count,
                        b.duration_seconds,
                        b.started_at,
                        b.completed_at,
                        b.error_message,
                        b.failure_stage,
                        json.dumps(b.file_paths),
                        b.narrative_summary,
                    ),
                )
        conn.close()

    @classmethod
    def load_index(cls, db_path: str | Path) -> WorkspaceIndex | None:
        """Load a WorkspaceIndex object from SQLite tables."""
        path = Path(db_path)
        if not path.is_file():
            return None

        conn = cls.get_connection(path)
        try:
            cursor = conn.cursor()

            # Read metadata
            meta_rows = cursor.execute("SELECT key, value FROM meta").fetchall()
            meta_dict = {row["key"]: row["value"] for row in meta_rows}

            if not meta_dict:
                return None

            # Read file records
            file_rows = cursor.execute("SELECT * FROM files").fetchall()
            files_map: dict[str, FileRecord] = {}

            for f_row in file_rows:
                extra_meta = json.loads(f_row["extra_metadata"]) if f_row["extra_metadata"] else {}
                if "batch_id" in f_row.keys() and f_row["batch_id"]:
                    extra_meta["batch_id"] = f_row["batch_id"]
                status_enum = f_row["indexing_status"]

                rec = FileRecord(
                    relative_path=f_row["path"],
                    file_size=f_row["file_size"],
                    modified_time=f_row["modified_time"],
                    extension=f_row["extension"],
                    content_hash=f_row["content_hash"] or "",
                    language=f_row["language"],
                    indexing_status=status_enum,
                    extra_metadata=extra_meta,
                )
                files_map[f_row["path"]] = rec

            # Read batch records
            batch_records: list[BatchRecord] = []
            try:
                batch_rows = cursor.execute("SELECT * FROM batches").fetchall()
                for b_row in batch_rows:
                    file_paths = json.loads(b_row["file_paths_json"]) if b_row["file_paths_json"] else []
                    batch_records.append(
                        BatchRecord(
                            batch_id=b_row["batch_id"],
                            status=b_row["status"],
                            discovered_count=b_row["discovered_count"],
                            indexed_count=b_row["indexed_count"],
                            ignored_count=b_row["ignored_count"],
                            duration_seconds=b_row["duration_seconds"],
                            started_at=b_row["started_at"],
                            completed_at=b_row["completed_at"],
                            error_message=b_row["error_message"],
                            failure_stage=b_row["failure_stage"],
                            file_paths=file_paths,
                            narrative_summary=b_row["narrative_summary"] if "narrative_summary" in b_row.keys() else None,
                        )
                    )
            except Exception:
                # If batches table does not exist yet or legacy data in meta
                meta_batches = meta_dict.get("batches")
                if meta_batches:
                    for b_dict in json.loads(meta_batches):
                        batch_records.append(BatchRecord.from_dict(b_dict))

            return WorkspaceIndex(
                index_version=meta_dict.get("index_version", "1.1"),
                wia_version=meta_dict.get("wia_version", "0.1.0"),
                workspace_path=meta_dict.get("workspace_path", ""),
                indexed_at=meta_dict.get("indexed_at", ""),
                files=files_map,
                languages=json.loads(meta_dict.get("languages", "{}")),
                frameworks=json.loads(meta_dict.get("frameworks", "[]")),
                batches=batch_records,
                stats=json.loads(meta_dict.get("stats", "{}")),
            )
        finally:
            conn.close()
