"""
Warehouse service for physical location management.

Handles creation, updating, and deletion of warehouses within a tenant's scope.
Validates code uniqueness and ensures the parent organization is active.
"""

from app.db.session_utils import db_transaction
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
from app.repositories.warehouse_repository import WarehouseRepository
from app.db.models.warehouse import Warehouse
from app.schemas.warehouse import WarehouseCreateInternal, WarehouseUpdate
from app.core.exceptions import AppException
from app.repositories.organization_repository import OrganizationRepository
from app.constants.organization_enum import OrganizationStatus
from app.constants.common_enum import CrudMessages
from app.dependencies.pagination import PaginationParams
from collections.abc import Sequence


from app.core.profiling import log_timing


class WarehouseService:
    """
    Service layer driving data validation, business rule execution, and
    transactions for Warehouse entities.
    """

    def __init__(
        self, warehouse_repo: WarehouseRepository, org_repo: OrganizationRepository
    ):
        """
        Initialize the WarehouseService with needed repositories.

        Args:
            warehouse_repo: Data access layer for warehouse models.
            org_repo: Data access layer for organization validation.
        """
        self.warehouse_repo = warehouse_repo
        self.org_repo = org_repo

    @log_timing
    async def create_warehouse(
        self, db: AsyncSession, warehouse_data: WarehouseCreateInternal
    ) -> Warehouse:
        """
        Creates a new warehouse after validating organization status and unique constraints.

        Args:
            db (AsyncSession): The active database session context.
            warehouse_data (WarehouseCreateInternal): The warehouse payload.

        Returns:
            Warehouse: The newly created warehouse.

        Raises:
            AppException: If the organization doesn't exist, isn't active, or code is duplicate.
        """
        # Validate that the organization exists and is active
        org = await self.org_repo.get_by_id(db, warehouse_data.organization_id)
        if not org:
            raise AppException(
                message=CrudMessages.ORG_NOT_FOUND.format(module="Warehouse"),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if org.status != OrganizationStatus.ACTIVE:
            raise AppException(
                message=CrudMessages.ORG_NOT_ACTIVE.format(module="Warehouse"),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Check unique constraint: organization_id + code
        existing = await self.warehouse_repo.get_by_code(
            db, warehouse_data.organization_id, warehouse_data.code
        )
        if existing:
            raise AppException(
                message=CrudMessages.ALREADY_EXISTS_FIELD.format(
                    module="Warehouse", field="code", value=warehouse_data.code
                ),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        warehouse_model = Warehouse(**warehouse_data.model_dump())
        async with db_transaction(db, module="Warehouse", action="operation"):
            warehouse = await self.warehouse_repo.create(db, warehouse_model)
            await db.flush()
            await db.refresh(warehouse)
            return warehouse

    @log_timing
    async def get_warehouse(
        self, db: AsyncSession, warehouse_id: int, actor_org_id: int
    ) -> Warehouse:
        """
        Retrieves a warehouse by ID, raising an error if not found.

        Args:
            db (AsyncSession): The active database session context.
            warehouse_id (int): The ID of the warehouse.

        Returns:
            Warehouse: The found warehouse.

        Raises:
            AppException: If not found (404).
        """
        warehouse = await self.warehouse_repo.get_by_id(db, warehouse_id)
        if not warehouse or warehouse.organization_id != actor_org_id:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Warehouse"),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return warehouse

    @log_timing
    async def get_all_warehouses(
        self, db: AsyncSession, params: PaginationParams
    ) -> tuple[Sequence[Warehouse], int]:
        """
        Retrieve a paginated list of all warehouses in the system.

        Args:
            db: The active database session context.
            params: Pagination filters.

        Returns:
            Tuple of warehouse models and the total count.
        """
        return await self.warehouse_repo.get_all(db, params)

    @log_timing
    async def update_warehouse(
        self,
        db: AsyncSession,
        warehouse_id: int,
        update_data: WarehouseUpdate,
        actor_org_id: int,
    ) -> Warehouse:
        """
        Updates an existing warehouse with partial data.

        Args:
            db (AsyncSession): The active database session context.
            warehouse_id (int): The ID of the warehouse to update.
            update_data (WarehouseUpdate): The fields to update.

        Returns:
            Warehouse: The updated warehouse instance.

        Raises:
            AppException: If a duplicate warehouse code is provided.
        """
        warehouse = await self.get_warehouse(db, warehouse_id, actor_org_id)

        # Extract only fields that were explicitly set in the request
        data_to_update = update_data.model_dump(exclude_unset=True)

        if "code" in data_to_update and data_to_update["code"] != warehouse.code:
            existing = await self.warehouse_repo.get_by_code(
                db, warehouse.organization_id, data_to_update["code"]
            )
            if existing:
                raise AppException(
                    message=CrudMessages.ALREADY_IN_USE.format(
                        module="Warehouse", field="code"
                    ),
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        for key, value in data_to_update.items():
            setattr(warehouse, key, value)

        async with db_transaction(db, module="Warehouse", action="operation"):
            warehouse = await self.warehouse_repo.update(db, warehouse)
            await db.flush()
            await db.refresh(warehouse)
            return warehouse

    @log_timing
    async def delete_warehouse(
        self, db: AsyncSession, warehouse_id: int, actor_org_id: int
    ) -> None:
        """
        Permanently delete a warehouse from the system.

        Deletion will fail if the warehouse still holds inventory or pending orders.

        Args:
            db: The active database session context.
            warehouse_id: The ID of the warehouse to delete.
            actor_org_id: Organization ID of the requesting user.
        """
        warehouse = await self.get_warehouse(db, warehouse_id, actor_org_id)
        async with db_transaction(db, module="Warehouse", action="operation"):
            await self.warehouse_repo.delete(db, warehouse)
            await db.flush()

    @log_timing
    async def get_by_organization(
        self, db: AsyncSession, organization_id: int, params: PaginationParams
    ) -> tuple[Sequence[Warehouse], int]:
        """
        Retrieves all warehouses belonging to a specific organization.

        Args:
            db (AsyncSession): The active database session context.
            organization_id (int): The parent organization ID.

        Returns:
            tuple: The warehouses for the organization and total count.

        Raises:
            AppException: If the organization doesn't exist (404).
        """
        organization = await self.org_repo.get_by_id(db, organization_id)

        if not organization:
            raise AppException(
                message=CrudMessages.ORG_NOT_FOUND.format(module="Warehouse"),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return await self.warehouse_repo.get_by_organization(
            organization_id=organization_id, db=db, params=params
        )
