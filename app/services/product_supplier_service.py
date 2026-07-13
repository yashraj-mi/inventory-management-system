"""
Product-Supplier mapping service.

Manages relationships between products and the suppliers who provide them.
Tracks supplier-specific SKUs and cost prices for replenishment logic.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import status
from collections.abc import Sequence

from app.core.exceptions import AppException
from app.constants.common_enum import CrudMessages
from app.repositories.product_supplier_repository import ProductSupplierRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.product_supplier import ProductSupplierCreate, ProductSupplierUpdate
from app.db.models.product_supplier import ProductSupplier
from app.dependencies.pagination import PaginationParams
from app.core.profiling import log_timing


class ProductSupplierService:
    """
    Service layer driving data validation and business rules for Product-Supplier assignments.
    """

    def __init__(
        self,
        repo: ProductSupplierRepository,
        product_repo: ProductRepository,
        supplier_repo: SupplierRepository,
    ) -> None:
        """
        Initialize the ProductSupplierService with required repositories.

        Args:
            repo: Data access layer for mapping entities.
            product_repo: Data access layer for validating product tenants.
            supplier_repo: Data access layer for validating supplier tenants.
        """
        self.repo = repo
        self.product_repo = product_repo
        self.supplier_repo = supplier_repo

    @log_timing
    async def create(
        self, db: AsyncSession, payload: ProductSupplierCreate, actor_org_id: int
    ) -> ProductSupplier:
        """
        Create a new product-to-supplier association.

        Ensures that both the product and supplier exist and belong to the
        actor's organization, preventing cross-tenant mapping.

        Args:
            db: The active database session context.
            payload: Validated schema containing mapping specifics.
            actor_org_id: Organization ID of the requesting user.

        Returns:
            The created ProductSupplier entity.
        """
        # Validate that Product exists and belongs to the actor's organization
        product = await self.product_repo.get_by_id(db, payload.product_id)
        if not product or product.organization_id != actor_org_id:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Product"),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Validate that Supplier exists and belongs to the actor's organization
        supplier = await self.supplier_repo.get_by_id(db, payload.supplier_id)
        if not supplier or supplier.organization_id != actor_org_id:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Supplier"),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Check for existing mapping
        existing = await self.repo.get_assignment(
            db, payload.product_id, payload.supplier_id
        )
        if existing:
            raise AppException(
                message=CrudMessages.ALREADY_EXISTS_FIELD.format(
                    module="ProductSupplier",
                    field="mapping",
                    value=f"{payload.product_id}-{payload.supplier_id}",
                ),
                status_code=status.HTTP_409_CONFLICT,
            )

        mapping = ProductSupplier(
            product_id=payload.product_id,
            supplier_id=payload.supplier_id,
            supplier_sku=payload.supplier_sku,
            cost_price=payload.cost_price,
        )

        try:
            await self.repo.create(db, mapping)
            await db.flush()
            await db.refresh(mapping)
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_CONSTRAINT.format(module="ProductSupplier"),
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_UNEXPECTED.format(
                    module="ProductSupplier", action="creation"
                ),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return mapping

    @log_timing
    async def get_by_product(
        self,
        db: AsyncSession,
        product_id: int,
        actor_org_id: int,
        params: PaginationParams,
    ) -> tuple[Sequence[ProductSupplier], int]:
        """
        Retrieves all supplier mappings for a specific product.
        """
        product = await self.product_repo.get_by_id(db, product_id)
        if not product or product.organization_id != actor_org_id:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Product"),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return await self.repo.get_by_product_id(db, product_id, params)

    @log_timing
    async def get_by_supplier(
        self,
        db: AsyncSession,
        supplier_id: int,
        actor_org_id: int,
        params: PaginationParams,
    ) -> tuple[Sequence[ProductSupplier], int]:
        """
        Retrieves all product mappings for a specific supplier.
        """
        supplier = await self.supplier_repo.get_by_id(db, supplier_id)
        if not supplier or supplier.organization_id != actor_org_id:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Supplier"),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return await self.repo.get_by_supplier_id(db, supplier_id, params)

    @log_timing
    async def get(self, db: AsyncSession, mapping_id: int) -> ProductSupplier:
        """
        Retrieves a mapping by ID.
        """
        mapping = await self.repo.get_by_id(db, mapping_id)
        if not mapping:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="ProductSupplier"),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return mapping

    @log_timing
    async def update(
        self,
        db: AsyncSession,
        mapping_id: int,
        payload: ProductSupplierUpdate,
        actor_org_id: int,
    ) -> ProductSupplier:
        """
        Update an existing product-supplier relationship.

        Useful for updating supplier-specific SKUs or negotiated cost prices.

        Args:
            db: The active database session context.
            mapping_id: ID of the mapping to update.
            payload: Partial data for the update.
            actor_org_id: Organization ID of the actor for ownership checks.

        Returns:
            The updated ProductSupplier entity.
        """
        mapping = await self.get(db, mapping_id)

        # Validate ownership via the linked product
        product = await self.product_repo.get_by_id(db, mapping.product_id)
        if not product or product.organization_id != actor_org_id:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="ProductSupplier"),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(mapping, field, value)

        try:
            await db.flush()
            await db.refresh(mapping)
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_CONSTRAINT.format(module="ProductSupplier"),
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_UNEXPECTED.format(
                    module="ProductSupplier", action="update"
                ),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return mapping

    @log_timing
    async def delete(
        self, db: AsyncSession, mapping_id: int, actor_org_id: int
    ) -> None:
        """
        Deletes a mapping by ID.
        """
        mapping = await self.get(db, mapping_id)

        # Validate ownership via the linked product
        product = await self.product_repo.get_by_id(db, mapping.product_id)
        if not product or product.organization_id != actor_org_id:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="ProductSupplier"),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        try:
            await self.repo.delete(db, mapping)
            await db.flush()
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_RELATIONAL_CONSTRAINT.format(
                    module="ProductSupplier"
                ),
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_UNEXPECTED.format(
                    module="ProductSupplier", action="deletion"
                ),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
