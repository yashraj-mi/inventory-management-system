"""Base Repository for shared database operations.

This module provides a generic BaseRepository class that implements common CRUD
operations and pagination, eliminating boilerplate from individual repository classes.
"""

from typing import Generic, TypeVar, Type, Sequence, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base
from app.dependencies.pagination import PaginationParams

ModelType = TypeVar("ModelType", bound=Base)


async def paginate_query(
    db: AsyncSession, query: Any, params: PaginationParams
) -> tuple[Sequence[ModelType], int]:
    """Execute a paginated database query and return results alongside the total count."""
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    paginated_query = query.offset(params.offset).limit(params.size)
    result = await db.execute(paginated_query)
    items = result.scalars().all()

    return items, total


class BaseRepository(Generic[ModelType]):
    """Generic base repository for standard CRUD operations."""

    model: Type[ModelType]

    async def create(self, db: AsyncSession, obj: ModelType) -> ModelType:
        """Add a new record to the active database session."""
        db.add(obj)
        return obj

    async def get_by_id(self, db: AsyncSession, id: int) -> ModelType | None:
        """Fetch a specific record by its primary key."""
        return await db.get(self.model, id)

    async def get_all(
        self, db: AsyncSession, params: PaginationParams
    ) -> tuple[Sequence[ModelType], int]:
        """Fetch a paginated list of all records."""
        query = select(self.model)
        return await paginate_query(db, query, params)

    async def get_by_organization(
        self, db: AsyncSession, organization_id: int, params: PaginationParams
    ) -> tuple[Sequence[ModelType], int]:
        """Fetch a paginated list of records scoped to an organization."""
        org_col = getattr(self.model, "organization_id", None)
        if org_col is None:
            raise ValueError(
                f"Model {self.model.__name__} does not have an organization_id column."
            )

        query = select(self.model).where(org_col == organization_id)
        return await paginate_query(db, query, params)

    async def update(self, db: AsyncSession, obj: ModelType) -> ModelType:
        """Update an existing record."""
        return obj

    async def delete(self, db: AsyncSession, obj: ModelType) -> None:
        """Remove a record from the database."""
        await db.delete(obj)
