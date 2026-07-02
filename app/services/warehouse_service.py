"""
warehouse_service.py module.

Provides core functionality and components for the warehouse_service domain.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import status
from app.repositories.warehouse_repository import WarehouseRepository
from app.db.models.warehouse import Warehouse
from app.schemas.warehouse import WarehouseCreateInternal, WarehouseUpdate
from app.core.exceptions import AppException
from app.repositories.organization_repository import OrganizationRepository
from app.constants.organization_enum import OrganizationStatus
from app.constants.warehouse_enum import WarehouseMessages


class WarehouseService:
    """
    Service layer driving data validation, business rule execution, and
    transactions for Warehouse entities.
    """

    def __init__(self, warehouse_repo: WarehouseRepository | None = None):
        """
        Executes the __init__ operation.

        Args:
            warehouse_repo: Parameter description.

        Returns:
            Execution result.
        """
        self.warehouse_repo = warehouse_repo or WarehouseRepository()
        self.org_repo = OrganizationRepository()

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
                message=WarehouseMessages.ORG_NOT_FOUND.format(
                    org_id=warehouse_data.organization_id
                ),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if org.status != OrganizationStatus.ACTIVE:
            raise AppException(
                message=WarehouseMessages.ORG_NOT_ACTIVE.format(
                    org_id=warehouse_data.organization_id
                ),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Check unique constraint: organization_id + code
        existing = await self.warehouse_repo.get_by_code(
            db, warehouse_data.organization_id, warehouse_data.code
        )
        if existing:
            raise AppException(
                message=WarehouseMessages.CODE_ALREADY_EXISTS.format(
                    code=warehouse_data.code
                ),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        warehouse_model = Warehouse(**warehouse_data.model_dump())
        try:
            warehouse = await self.warehouse_repo.create(db, warehouse_model)
            await db.flush()
            await db.refresh(warehouse)
            return warehouse
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=WarehouseMessages.CODE_ALREADY_EXISTS.format(
                    code=warehouse_data.code
                ),
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=WarehouseMessages.DB_UNEXPECTED_CREATION,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    async def get_warehouse(self, db: AsyncSession, warehouse_id: int) -> Warehouse:
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
        warehouse = await self.warehouse_repo.get(db, warehouse_id)
        if not warehouse:
            raise AppException(
                message=WarehouseMessages.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return warehouse

    async def get_all_warehouses(self, db: AsyncSession) -> list[Warehouse]:
        """
        Retrieves all warehouses.

        Args:
            db (AsyncSession): The active database session context.

        Returns:
            list[Warehouse]: List of all warehouses.
        """
        return await self.warehouse_repo.get_all(db)

    async def update_warehouse(
        self, db: AsyncSession, warehouse_id: int, update_data: WarehouseUpdate
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
        warehouse = await self.get_warehouse(db, warehouse_id)

        # Extract only fields that were explicitly set in the request
        data_to_update = update_data.model_dump(exclude_unset=True)

        if "code" in data_to_update and data_to_update["code"] != warehouse.code:
            existing = await self.warehouse_repo.get_by_code(
                db, warehouse.organization_id, data_to_update["code"]
            )
            if existing:
                raise AppException(
                    message=WarehouseMessages.CODE_IN_USE,
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        for key, value in data_to_update.items():
            setattr(warehouse, key, value)

        try:
            warehouse = await self.warehouse_repo.update(db, warehouse)
            await db.flush()
            await db.refresh(warehouse)
            return warehouse
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=WarehouseMessages.DB_CONSTRAINT_UPDATE,
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=WarehouseMessages.DB_UNEXPECTED_UPDATE,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    async def delete_warehouse(self, db: AsyncSession, warehouse_id: int) -> None:
        """
        Deletes a warehouse by ID.

        Args:
            db (AsyncSession): The active database session context.
            warehouse_id (int): The ID of the warehouse to delete.
        """
        warehouse = await self.get_warehouse(db, warehouse_id)
        try:
            await self.warehouse_repo.delete(db, warehouse)
            await db.flush()
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=WarehouseMessages.DB_RELATIONAL_CONSTRAINTS,
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=WarehouseMessages.DB_UNEXPECTED_DELETION,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    async def get_by_organization(self, db: AsyncSession, organization_id: int):
        """
        Retrieves all warehouses belonging to a specific organization.

        Args:
            db (AsyncSession): The active database session context.
            organization_id (int): The parent organization ID.

        Returns:
            Sequence[Warehouse]: The warehouses for the organization.

        Raises:
            AppException: If the organization doesn't exist (404).
        """
        organization = await self.org_repo.get_by_id(
            organization_id=organization_id, db=db
        )

        if not organization:
            raise AppException(
                message=WarehouseMessages.ORG_NOT_FOUND.format(org_id=organization_id),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return await self.warehouse_repo.get_by_organization(
            organization_id=organization_id, db=db
        )
