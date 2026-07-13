"""Provide base repository utilities.

This module contains shared database interaction helpers, such as pagination,
which abstract common boilerplate away from individual repository classes to
ensure consistent behavior across all data access operations.
"""

from typing import TypeVar, Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.dependencies.pagination import PaginationParams

T = TypeVar("T")


async def paginate_query(
    db: AsyncSession, query, params: PaginationParams
) -> tuple[Sequence[T], int]:
    """Execute a paginated database query and return results alongside the total count.

    Calculates the total number of records matching the base query, applies limit
    and offset constraints based on the pagination parameters, and fetches the
    current page of results.

    Args:
        db (AsyncSession): The active asynchronous database session.
        query: The SQLAlchemy select query object to paginate.
        params (PaginationParams): The pagination parameters including offset and size.

    Returns:
        tuple[Sequence[T], int]: A tuple containing the sequence of items for the current page and the total count of items.

    Raises:
        SQLAlchemyError: If a database execution error occurs during counting or fetching.
    """
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    paginated_query = query.offset(params.offset).limit(params.size)
    result = await db.execute(paginated_query)
    items = result.scalars().all()

    return items, total
