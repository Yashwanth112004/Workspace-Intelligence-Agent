import os
import logging
from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings

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
    return create_engine(sqlite_url, echo=False, connect_args={"check_same_thread": False})

engine = get_engine()

def init_db():
    from app.models import workspace # Ensure models are imported
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
