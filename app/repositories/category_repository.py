"""Manage database interactions for product categories.

This module provides the CategoryRepository which abstracts the SQL queries
required to manage organizational product hierarchies, allowing the service
layer to execute CRUD operations on the Category model seamlessly.
"""

from app.repositories.base_repository import BaseRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.category import Category


class CategoryRepository(BaseRepository[Category]):
    """Manage data access for Category entities.

    This repository handles all database interactions for product categories,
    including organization-scoped queries and unique name validations.
    """

    model = Category

    async def get_by_name(
        self, db: AsyncSession, organization_id: int, name: str
    ) -> Category | None:
        """Fetch a category by its name within a specific organization.

        Ensures category name uniqueness at the organization level by checking
        if a category with the specified name already exists.

        Args:
            db (AsyncSession): The active asynchronous database session.
            organization_id (int): The ID of the parent organization.
            name (str): The name of the category to search for.

        Returns:
            Category | None: The matching category, or None if not found.

        Raises:
            SQLAlchemyError: If the database query fails.
        """
        stmt = select(Category).where(
            Category.organization_id == organization_id, Category.name == name
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
