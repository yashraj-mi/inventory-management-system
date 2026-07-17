"""Manage database interactions for product catalogs.

This module provides the ProductRepository to handle data access for product
definitions, ensuring SKU uniqueness constraints and organizational scoping
are respected during queries.
"""

from app.repositories.base_repository import BaseRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.product import Product


class ProductRepository(BaseRepository[Product]):
    """Manage data access for Product entities.

    Facilitates querying the product catalog, isolating database operations
    from business logic and ensuring tenant separation via organization ID.
    """

    model = Product

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
