"""Manage database interactions for product catalogs.

This module provides the ProductRepository to handle data access for product
definitions, ensuring SKU uniqueness constraints and organizational scoping
are respected during queries.
"""

from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.product import Product
from app.dependencies.pagination import PaginationParams
from app.repositories.base import paginate_query


class ProductRepository:
    """Manage data access for Product entities.

    Facilitates querying the product catalog, isolating database operations
    from business logic and ensuring tenant separation via organization ID.
    """

    async def create(self, db: AsyncSession, product_data: Product) -> Product:
        """Stage a new product definition for insertion into the database.

        Args:
            db (AsyncSession): The active asynchronous database session.
            product_data (Product): The product entity to insert.

        Returns:
            Product: The staged product instance.
        """
        db.add(product_data)
        return product_data

    async def get_all(
        self, db: AsyncSession, org_id: int, params: PaginationParams
    ) -> tuple[Sequence[Product], int]:
        """Fetch a paginated list of all products belonging to an organization.

        Provides base catalog data for listing, reporting, or order entry views,
        sorted by the underlying primary key.

        Args:
            db (AsyncSession): The active asynchronous database session.
            org_id (int): The ID of the parent organization.
            params (PaginationParams): Pagination constraints (offset/limit).

        Returns:
            tuple[Sequence[Product], int]: The fetched products and total count.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        query = (
            select(Product)
            .where(Product.organization_id == org_id)
            .order_by(Product.id)
        )
        return await paginate_query(db, query, params)

    async def get_by_id(self, db: AsyncSession, product_id: int) -> Product | None:
        """Fetch a specific product by its primary key.

        Args:
            db (AsyncSession): The active asynchronous database session.
            product_id (int): The unique identifier of the product.

        Returns:
            Product | None: The requested product, or None if not found.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        return await db.get(Product, product_id)

    async def get_by_sku(
        self, db: AsyncSession, org_id: int, sku: str
    ) -> Product | None:
        """Fetch a product by its Stock Keeping Unit (SKU) within an organization.

        Ensures SKU uniqueness constraints are honored and allows rapid catalog
        lookups via standard product identifiers.

        Args:
            db (AsyncSession): The active asynchronous database session.
            org_id (int): The ID of the parent organization.
            sku (str): The product SKU string.

        Returns:
            Product | None: The matching product, or None if not found.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        return await db.scalar(
            select(Product).where(Product.organization_id == org_id, Product.sku == sku)
        )

    async def delete(self, db: AsyncSession, product: Product) -> None:
        """Stage a product definition for deletion from the database.

        Args:
            db (AsyncSession): The active asynchronous database session.
            product (Product): The product instance to remove.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        await db.delete(product)
