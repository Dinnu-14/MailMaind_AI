"""Serverless-optimized SQLAlchemy database session management."""
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

from app.core.config import settings

logger = logging.getLogger("mailmind.database")

# Serverless configuration:
# When using hosted PostgreSQL (e.g. Neon, Supabase), NullPool prevents idle connections
# from accumulating across serverless function invocations.
is_sqlite = settings.database_url.startswith("sqlite")

if is_sqlite:
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )
else:
    # Serverless PostgreSQL: use NullPool to avoid connection leaks across cold/warm starts
    engine = create_engine(
        settings.database_url,
        poolclass=NullPool,
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency for obtaining a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Ensure all database tables are created."""
    try:
        # Import models so Base has registered all tables
        import app.models.models  # noqa: F401
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database tables: {e}")

