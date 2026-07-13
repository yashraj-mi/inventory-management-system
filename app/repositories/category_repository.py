"""Manage database interactions for product categories.

This module provides the CategoryRepository which abstracts the SQL queries
required to manage organizational product hierarchies, allowing the service
layer to execute CRUD operations on the Category model seamlessly.
"""

from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.category import Category
from app.dependencies.pagination import PaginationParams
from app.repositories.base import paginate_query


class CategoryRepository:
    """Manage data access for Category entities.

    This repository handles all database interactions for product categories,
    including organization-scoped queries and unique name validations.
    """

    async def create(self, db: AsyncSession, category: Category) -> Category:
        """Add a new category record to the active database session.

        Stages a Category entity for insertion. The calling service is responsible
        for committing the transaction.

        Args:
            db (AsyncSession): The active asynchronous database session.
            category (Category): The populated Category instance to insert.

        Returns:
            Category: The staged category instance.
        """
        db.add(category)
        return category

    async def get_all(
        self, db: AsyncSession, params: PaginationParams
    ) -> tuple[Sequence[Category], int]:
        """Fetch a globally paginated list of all categories.

        Retrieves all categories across all organizations in a paginated format.
        Typically used by system administrators or global catalog views.

        Args:
            db (AsyncSession): The active asynchronous database session.
            params (PaginationParams): Pagination constraints (offset/limit).

        Returns:
            tuple[Sequence[Category], int]: The fetched categories and the total record count.

        Raises:
            SQLAlchemyError: If the database query fails.
        """
        query = select(Category)
        return await paginate_query(db, query, params)

    async def get_by_id(self, db: AsyncSession, category_id: int) -> Category | None:
        """Fetch a specific category by its primary key.

        Args:
            db (AsyncSession): The active asynchronous database session.
            category_id (int): The unique identifier of the category.

        Returns:
            Category | None: The requested category or None if it does not exist.

        Raises:
            SQLAlchemyError: If the database query fails.
        """
        return await db.get(Category, category_id)

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

    async def get_by_organization(
        self, db: AsyncSession, organization_id: int, params: PaginationParams
    ) -> tuple[Sequence[Category], int]:
        """Fetch a paginated list of categories scoped to an organization.

        Retrieves only the categories that belong to the specified organization,
        supporting tenant-isolated views.

        Args:
            db (AsyncSession): The active asynchronous database session.
            organization_id (int): The ID of the parent organization.
            params (PaginationParams): Pagination constraints (offset/limit).

        Returns:
            tuple[Sequence[Category], int]: The fetched categories and total count.

        Raises:
            SQLAlchemyError: If the database query fails.
        """
        query = select(Category).where(Category.organization_id == organization_id)
        return await paginate_query(db, query, params)

    async def update(self, db: AsyncSession, category: Category) -> Category:
        """Update an existing category record.

        Accepts a modified Category instance and assumes it is attached to the
        current session. The caller must commit the transaction.

        Args:
            db (AsyncSession): The active asynchronous database session.
            category (Category): The updated category instance.

        Returns:
            Category: The updated category instance.
        """
        return category

    async def delete(self, db: AsyncSession, category: Category) -> None:
        """Remove a category record from the database.

        Stages a specific Category instance for deletion. The calling service
        must commit the transaction to finalize the removal.

        Args:
            db (AsyncSession): The active asynchronous database session.
            category (Category): The category instance to delete.

        Raises:
            SQLAlchemyError: If the deletion staging fails.
        """
        await db.delete(category)
