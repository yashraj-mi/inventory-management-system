"""
Database connection and session management module.

Provides the central SQLAlchemy async engine, session factory, and declarative
base class for defining ORM models. Includes a dependency for FastAPI routes
to securely yield and manage database sessions.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from .config import get_settings
from app.core.sql_profiling import enable_sql_profiling

settings = get_settings()

engine = create_async_engine(settings.DATABASE_URL)


if settings.SQL_ECHO:
    enable_sql_profiling(engine.sync_engine)  # note: .sync_engine for async engines

AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy declarative models.

    All application ORM models should inherit from this class to be registered
    in the common metadata registry.
    """

    pass


async def get_db():
    """
    Provide a transactional database session for a request.

    Yields an active `AsyncSession`. Automatically commits the transaction if no
    exceptions occur, and rolls it back if an exception is raised, ensuring data integrity.

    Yields:
        AsyncSession: The active asynchronous database session.

    Raises:
        Exception: Re-raises any exception that occurs during the transaction.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()

        except Exception:
            await session.rollback()
            raise
