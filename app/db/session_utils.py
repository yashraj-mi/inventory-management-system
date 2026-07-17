"""
Database session utilities.

Provides context managers for safe transaction handling and error translations.
"""

from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette import status

from app.core.exceptions import AppException


# from app.core.logger import logger  # your structured logger, if you want [SQL]-style tags here
@asynccontextmanager
async def db_transaction(db: AsyncSession, module: str, action: str):
    """
    Wraps a DB write block with rollback + consistent error translation.

    Usage:
        async with safe_db_operation(db, module="Product", action="creation"):
            await db.flush()
            await db.refresh(record)
    """
    try:
        yield
    except IntegrityError as e:
        await db.rollback()
        # logger.warning(f"[DB] Integrity error during {module} {action}: {e}")
        raise AppException(
            message=f"{module} {action} failed due to a data conflict.",
            status_code=status.HTTP_409_CONFLICT,
        ) from e
    except SQLAlchemyError as e:
        await db.rollback()
        # logger.error(f"[DB] Unexpected DB error during {module} {action}: {e}")
        raise AppException(
            message=f"{module} {action} failed due to an internal error.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e
