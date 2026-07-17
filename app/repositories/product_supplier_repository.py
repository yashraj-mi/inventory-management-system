"""Manage database interactions for product-supplier relationships.

This module provides the repository for the ProductSupplier linking table,
handling the queries needed to establish, verify, and dissolve the relationships
between specific products and the vendors that supply them.
"""

from app.repositories.base_repository import BaseRepository
from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.product_supplier import ProductSupplier
from app.dependencies.pagination import PaginationParams
from app.repositories.base import paginate_query


class ProductSupplierRepository(BaseRepository[ProductSupplier]):
    """Manage data access for ProductSupplier link records.

    Handles the bidirectional lookup of suppliers for a product or products
    for a supplier, supporting supply chain planning and purchase order creation.
    """

    model = ProductSupplier

    async def get_assignment(
        self, db: AsyncSession, product_id: int, supplier_id: int
    ) -> ProductSupplier | None:
        """Fetch a specific linkage between a product and a supplier.

        Typically used to verify if a vendor is authorized to supply a given
        item before generating purchase orders.

        Args:
            db (AsyncSession): The active asynchronous database session.
            product_id (int): The ID of the supplied product.
            supplier_id (int): The ID of the supplying vendor.

        Returns:
            ProductSupplier | None: The active link, or None if not established.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        return await db.scalar(
            select(ProductSupplier).where(
                ProductSupplier.product_id == product_id,
                ProductSupplier.supplier_id == supplier_id,
            )
        )

    async def get_by_product_id(
        self, db: AsyncSession, product_id: int, params: PaginationParams
    ) -> tuple[Sequence[ProductSupplier], int]:
        """Fetch a paginated list of suppliers authorized for a specific product.

        Args:
            db (AsyncSession): The active asynchronous database session.
            product_id (int): The target product ID.
            params (PaginationParams): Pagination constraints (offset/limit).

        Returns:
            tuple[Sequence[ProductSupplier], int]: The fetched mappings and total count.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        query = (
            select(ProductSupplier)
            .where(ProductSupplier.product_id == product_id)
            .order_by(ProductSupplier.id)
        )
        return await paginate_query(db, query, params)

    async def get_by_supplier_id(
        self, db: AsyncSession, supplier_id: int, params: PaginationParams
    ) -> tuple[Sequence[ProductSupplier], int]:
        """Fetch a paginated list of products authorized for a specific supplier.

        Args:
            db (AsyncSession): The active asynchronous database session.
            supplier_id (int): The target vendor ID.
            params (PaginationParams): Pagination constraints (offset/limit).

        Returns:
            tuple[Sequence[ProductSupplier], int]: The fetched mappings and total count.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        query = (
            select(ProductSupplier)
            .where(ProductSupplier.supplier_id == supplier_id)
            .order_by(ProductSupplier.id)
        )
        return await paginate_query(db, query, params)
