from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.warehouse_repository import WarehouseRepository
from app.db.models.warehouse import Warehouse
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate
from app.core.exceptions import AppException
from app.repositories.organization_repository import OrganizationRepository
from app.constants.organization_enum import OrganizationStatus


class WarehouseService:
    """
    Service layer driving data validation, business rule execution, and
    transactions for Warehouse entities.
    """

    def __init__(self, warehouse_repo: WarehouseRepository | None = None):
        self.warehouse_repo = warehouse_repo or WarehouseRepository()
        self.org_repo = OrganizationRepository()

    async def create_warehouse(
        self, db: AsyncSession, warehouse_data: WarehouseCreate
    ) -> Warehouse:
        """
        Creates a new warehouse after validating organization status and unique constraints.

        Args:
            db (AsyncSession): The active database session context.
            warehouse_data (WarehouseCreate): The warehouse payload.

        Returns:
            Warehouse: The newly created warehouse.

        Raises:
            AppException: If the organization doesn't exist, isn't active, or code is duplicate.
        """
        # Validate that the organization exists and is active
        org = await self.org_repo.get_by_id(db, warehouse_data.organization_id)
        if not org:
            raise AppException(
                message=f"Organization with id {warehouse_data.organization_id} not found.",
                status_code=404,
            )
        if org.status != OrganizationStatus.ACTIVE:
            raise AppException(
                message=f"Organization with organization id:{warehouse_data.organization_id} is not currently active.",
                status_code=400,
            )

        # Check unique constraint: organization_id + code
        existing = await self.warehouse_repo.get_by_code(
            db, warehouse_data.organization_id, warehouse_data.code
        )
        if existing:
            raise AppException(
                message=f"Warehouse with code '{warehouse_data.code}' already exists for this organization.",
                status_code=400,
            )

        warehouse_model = Warehouse(**warehouse_data.model_dump())
        return await self.warehouse_repo.create(db, warehouse_model)

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
            raise AppException(message="Warehouse not found", status_code=404)
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
                    message="Warehouse code already in use for this organization.",
                    status_code=400,
                )

        for key, value in data_to_update.items():
            setattr(warehouse, key, value)

        return await self.warehouse_repo.update(db, warehouse)

    async def delete_warehouse(self, db: AsyncSession, warehouse_id: int) -> None:
        """
        Deletes a warehouse by ID.

        Args:
            db (AsyncSession): The active database session context.
            warehouse_id (int): The ID of the warehouse to delete.
        """
        warehouse = await self.get_warehouse(db, warehouse_id)
        await self.warehouse_repo.delete(db, warehouse)

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
                message=f"Organization with id {organization_id} not found",
                status_code=404,
            )

        return await self.warehouse_repo.get_by_organization(
            organization_id=organization_id, db=db
        )
