import os
import logging
from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings

from sqlalchemy import event

logger = logging.getLogger("wia.database")

def get_engine():
    db_url = settings.DATABASE_URL
    if db_url:
        try:
            engine = create_engine(db_url, echo=False, pool_pre_ping=True)
            # Test connection
            with engine.connect() as conn:
                pass
            logger.info(f"Connected to PostgreSQL database at {db_url}")
            return engine
        except Exception as e:
            logger.warning(f"Failed to connect to PostgreSQL ({e}). Falling back to SQLite.")

    # SQLite fallback
    sqlite_file = os.path.join(settings.DATA_DIR, "wia.db")
    sqlite_url = f"sqlite:///{sqlite_file}"
    logger.info(f"Using SQLite database at {sqlite_url}")
    eng = create_engine(sqlite_url, echo=False, connect_args={"check_same_thread": False, "timeout": 30})
    
    # Enable WAL mode and performance PRAGMAs on every SQLite connection
    @event.listens_for(eng, "connect")
    def _set_sqlite_pragmas(dbapi_connection, connection_record):
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.close()
        except Exception:
            pass

    return eng

engine = get_engine()

def init_db():
    from app.models import workspace, knowledge # Ensure all SQLModel models are registered
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
