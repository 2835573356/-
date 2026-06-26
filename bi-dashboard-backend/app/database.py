"""
Database connection and session management.
Supports local SQLite and remote PostgreSQL/Supabase.
"""
import logging

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

logger = logging.getLogger("bi-dashboard.database")


def normalize_database_url(raw_url: str) -> str:
    """Normalize common Supabase pooler URL paste formats for SQLAlchemy."""
    if raw_url.startswith(("sqlite", "postgresql://", "postgresql+psycopg2://")):
        return raw_url
    if raw_url.startswith("postgres://"):
        return raw_url.replace("postgres://", "postgresql://", 1)
    if raw_url.startswith("postgres.") and "@" in raw_url:
        return f"postgresql://{raw_url}"
    return raw_url


DATABASE_URL = normalize_database_url(settings.DATABASE_URL)
IS_SQLITE = DATABASE_URL.startswith("sqlite")

if IS_SQLITE:
    logger.info("Database mode: SQLite")
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=settings.DEBUG,
    )
else:
    logger.info("Database mode: PostgreSQL")
    engine = create_engine(
        DATABASE_URL,
        pool_size=20,
        max_overflow=40,
        pool_pre_ping=True,
        echo=settings.DEBUG,
    )


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if IS_SQLITE:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_type() -> str:
    return "sqlite" if IS_SQLITE else "postgresql"
