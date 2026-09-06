import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.db.models import Base

logger = logging.getLogger(__name__)

# Database path: default to SQLite in local/dev if DATABASE_URL is not set
DB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(DB_DIR, "lumina.db")

raw_db_url = settings.DATABASE_URL or os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# Render compatibility: SQLAlchemy 2.0 requires postgresql:// instead of postgres://
if raw_db_url.startswith("postgres://"):
    DATABASE_URL = raw_db_url.replace("postgres://", "postgresql://", 1)
else:
    DATABASE_URL = raw_db_url

# Configure engine with dialect-specific options
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def _migrate_sqlite_columns():
    """Ensure SQLite columns added in newer models exist without dropping data."""
    if not DATABASE_URL.startswith("sqlite"):
        return
    with engine.connect() as conn:
        try:
            # Check admin_users columns
            res = conn.execute(text("PRAGMA table_info(admin_users)")).fetchall()
            cols = [r[1] for r in res]
            if cols:
                if "full_name" not in cols:
                    conn.execute(text("ALTER TABLE admin_users ADD COLUMN full_name VARCHAR(255) DEFAULT ''"))
                if "role" not in cols:
                    conn.execute(text("ALTER TABLE admin_users ADD COLUMN role VARCHAR(50) DEFAULT 'asesor'"))
                if "is_active" not in cols:
                    conn.execute(text("ALTER TABLE admin_users ADD COLUMN is_active BOOLEAN DEFAULT 1"))
                conn.commit()
        except Exception as e:
            logger.warning(f"SQLite migration notice for admin_users: {e}")

        try:
            # Check messages columns
            res = conn.execute(text("PRAGMA table_info(messages)")).fetchall()
            cols = [r[1] for r in res]
            if cols:
                if "sender_username" not in cols:
                    conn.execute(text("ALTER TABLE messages ADD COLUMN sender_username VARCHAR(100) DEFAULT ''"))
                conn.commit()
        except Exception as e:
            logger.warning(f"SQLite migration notice for messages: {e}")

def init_db():
    """Create all tables if they do not exist across SQLite and PostgreSQL."""
    Base.metadata.create_all(bind=engine)
    _migrate_sqlite_columns()

def get_db():
    """FastAPI Dependency for database sessions."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
