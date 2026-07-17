"""
Product service managing catalog and item details.

Handles creation, updating, retrieval, and deletion of products. Enforces SKU
uniqueness and manages product-to-category constraints within a multi-tenant environment.
"""

from app.db.session_utils import db_transaction
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status

from app.core.exceptions import AppException
from app.constants.common_enum import CrudMessages
from app.constants.organization_enum import OrganizationStatus
from app.repositories.product_repository import ProductRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.category_repository import CategoryRepository
from app.schemas.product import ProductCreateInternal, ProductUpdate
from app.db.models.product import Product
from app.dependencies.pagination import PaginationParams
from collections.abc import Sequence

from app.core.profiling import log_timing
from app.schemas.product_supplier import ProductSupplierCreate
from app.services.product_supplier_service import ProductSupplierService


class ProductService:
    """
    Service layer driving data validation and business rules for Products.
    """

    def __init__(
        self,
        product_repo: ProductRepository,
        org_repo: OrganizationRepository,
        category_repo: CategoryRepository,
        product_supplier_service: ProductSupplierService,
    ) -> None:
        """
        Initialize ProductService with necessary dependencies.

        Args:
            product_repo: Data access layer for product persistence.
            org_repo: Data access layer for organization validation.
            category_repo: Data access layer to validate category relationships.
            product_supplier_service: Service to map default suppliers during product creation.
        """
        self.product_repo = product_repo
        self.org_repo = org_repo
        self.category_repo = category_repo
        self.product_supplier_service = product_supplier_service

    @log_timing
    async def create(self, db: AsyncSession, payload: ProductCreateInternal) -> Product:
        """
        Create a new product within an active organization.

        Validates parent organization and optional category. Configures initial
        supplier mapping if provided in the payload.

        Args:
            db: The active database session context.
            payload: Validated schema containing product details.

        Returns:
            The created Product entity.

        Raises:
            AppException: If SKU is duplicate (409) or category/org invalid.
        """
        # Validate Organization
        org = await self.org_repo.get_by_id(db, payload.organization_id)
        if not org:
            raise AppException(
                message=CrudMessages.ORG_NOT_FOUND.format(module="Product"),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if org.status != OrganizationStatus.ACTIVE:
            raise AppException(
                message=CrudMessages.ORG_NOT_ACTIVE.format(module="Product"),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Validate Category if provided
        if payload.category_id:
            category = await self.category_repo.get_by_id(db, payload.category_id)
            if not category or category.organization_id != payload.organization_id:
                raise AppException(
                    message=CrudMessages.NOT_FOUND.format(module="Category"),
                    status_code=status.HTTP_404_NOT_FOUND,
                )

        # Validate Uniqueness
        if await self.product_repo.get_by_sku(db, payload.organization_id, payload.sku):
            raise AppException(
                message=CrudMessages.ALREADY_EXISTS_FIELD.format(
                    module="Product", field="sku", value=payload.sku
                ),
                status_code=status.HTTP_409_CONFLICT,
            )

        product = Product(
            organization_id=payload.organization_id,
            category_id=payload.category_id,
            sku=payload.sku,
            name=payload.name,
            description=payload.description,
            unit=payload.unit,
            base_cost_price=payload.base_cost_price,
            base_selling_price=payload.base_selling_price,
            is_perishable=payload.is_perishable,
            shelf_life=payload.shelf_life,
            status=payload.status,
        )

        async with db_transaction(db, module="Product", action="operation"):
            await self.product_repo.create(db, product)
            await db.flush()
            await db.refresh(product)
        if payload.supplier_id and payload.supplier_sku:
            product_supplier_data = ProductSupplierCreate(
                product_id=product.id,
                supplier_id=payload.supplier_id,
                supplier_sku=payload.supplier_sku,
                cost_price=payload.base_cost_price,
            )
            try:
                await self.product_supplier_service.create(
                    db, product_supplier_data, payload.organization_id
                )
            except AppException:
                await db.rollback()
                raise AppException(
                    message=CrudMessages.DB_CONSTRAINT.format(module="ProductSupplier"),
                    status_code=status.HTTP_409_CONFLICT,
                )
        return product

    @log_timing
    async def get_all_by_org(
        self, db: AsyncSession, org_id: int, params: PaginationParams
    ) -> tuple[Sequence[Product], int]:
        """
        Retrieve all products belonging to a specific organization.

        Args:
            db: The active database session context.
            org_id: The ID of the parent organization.
            params: Parameters for pagination.

        Returns:
            A tuple of product sequences and total count.
        """
        org = await self.org_repo.get_by_id(db, org_id)
        if not org:
            raise AppException(
                message=CrudMessages.ORG_NOT_FOUND.format(module="Products"),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return await self.product_repo.get_by_organization(db, org_id, params)

    @log_timing
    async def get(
        self, db: AsyncSession, product_id: int, actor_org_id: int
    ) -> Product:
        """
        Retrieve a specific product and enforce tenant isolation.

        Args:
            db: The active database session context.
            product_id: The ID of the product to fetch.
            actor_org_id: Organization ID of the requesting user.

        Returns:
            The matching Product entity.
        """
        product = await self.product_repo.get_by_id(db, product_id)
        if not product or product.organization_id != actor_org_id:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Product"),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return product

    @log_timing
    async def update(
        self,
        db: AsyncSession,
        product_id: int,
        payload: ProductUpdate,
        actor_org_id: int,
    ) -> Product:
        """
        Update an existing product's catalog details.

        Verifies ownership and ensures any modified SKU remains unique.

        Args:
            db: The active database session context.
            product_id: The ID of the product to update.
            payload: Partial product data.
            actor_org_id: Organization ID of the actor.

        Returns:
            The updated Product entity.
        """
        product = await self.get(db, product_id, actor_org_id)

        update_data = payload.model_dump(exclude_unset=True)

        # Validate Category if provided
        if "category_id" in update_data and update_data["category_id"] is not None:
            category = await self.category_repo.get_by_id(
                db, update_data["category_id"]
            )
            if not category or category.organization_id != product.organization_id:
                raise AppException(
                    message=CrudMessages.NOT_FOUND.format(module="Category"),
                    status_code=status.HTTP_404_NOT_FOUND,
                )

        # If sku is updated, check for conflicts
        if "sku" in update_data and update_data["sku"] != product.sku:
            if await self.product_repo.get_by_sku(
                db, product.organization_id, update_data["sku"]
            ):
                raise AppException(
                    message=CrudMessages.ALREADY_EXISTS_FIELD.format(
                        module="Product", field="sku", value=update_data["sku"]
                    ),
                    status_code=status.HTTP_409_CONFLICT,
                )

        for field, value in update_data.items():
            setattr(product, field, value)

        async with db_transaction(db, module="Product", action="operation"):
            await db.flush()
            await db.refresh(product)
        return product

    @log_timing
    async def delete(
        self, db: AsyncSession, product_id: int, actor_org_id: int
    ) -> None:
        """
        Delete a product from the database.

        Checks ownership prior to deletion. Will fail if the product is bound
        to existing inventory or order lines.

        Args:
            db: The active database session context.
            product_id: The ID of the product to delete.
            actor_org_id: Organization ID of the actor.

        Raises:
            AppException: If related records prevent deletion (409) or unknown DB error.
        """
        product = await self.get(db, product_id, actor_org_id)
        async with db_transaction(db, module="Product", action="operation"):
            await self.product_repo.delete(db, product)
            await db.flush()
