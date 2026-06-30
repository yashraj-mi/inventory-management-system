from sqlalchemy import select, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.warehouse import Warehouse


class WarehouseRepository:
    """
    Repository layer for managing Warehouse entities in the database.
    """

    async def create(self, db: AsyncSession, warehouse: Warehouse) -> Warehouse:
        """
        Creates a new warehouse record in the database.

        Args:
            db (AsyncSession): The active database session context.
            warehouse (Warehouse): The warehouse entity to create.

        Returns:
            Warehouse: The created warehouse instance with its assigned ID.
        """
        db.add(warehouse)
        await db.commit()
        await db.refresh(warehouse)
        return warehouse

    async def get_all(self, db: AsyncSession) -> list[Warehouse]:
        """
        Retrieves all warehouse records from the database.

        Args:
            db (AsyncSession): The active database session context.

        Returns:
            list[Warehouse]: A list of all warehouses.
        """
        result = await db.scalars(select(Warehouse))
        return list(result.all())

    async def get(self, db: AsyncSession, warehouse_id: int) -> Warehouse | None:
        """
        Retrieves a single warehouse by its primary key.

        Args:
            db (AsyncSession): The active database session context.
            warehouse_id (int): The ID of the warehouse to fetch.

        Returns:
            Warehouse | None: The found warehouse, or None if it doesn't exist.
        """
        return await db.get(Warehouse, warehouse_id)

    async def get_by_code(
        self, db: AsyncSession, organization_id: int, code: str
    ) -> Warehouse | None:
        """
        Retrieves a warehouse by its organization ID and unique code.

        Args:
            db (AsyncSession): The active database session context.
            organization_id (int): The ID of the parent organization.
            code (str): The unique code of the warehouse.

        Returns:
            Warehouse | None: The found warehouse, or None if not found.
        """
        stmt = select(Warehouse).where(
            Warehouse.organization_id == organization_id, Warehouse.code == code
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_organization(
        self, db: AsyncSession, organization_id: int
    ) -> Sequence[Warehouse] | None:
        """
        Retrieves all warehouses belonging to a specific organization.

        Args:
            db (AsyncSession): The active database session context.
            organization_id (int): The ID of the parent organization.

        Returns:
            Sequence[Warehouse] | None: A sequence of warehouses, or None if none exist.
        """
        stmt = select(Warehouse).where(Warehouse.organization_id == organization_id)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def update(self, db: AsyncSession, warehouse: Warehouse) -> Warehouse:
        """
        Commits updates made to a tracked warehouse instance.

        Args:
            db (AsyncSession): The active database session context.
            warehouse (Warehouse): The warehouse entity to update.

        Returns:
            Warehouse: The updated warehouse instance.
        """
        await db.commit()
        await db.refresh(warehouse)
        return warehouse

    async def delete(self, db: AsyncSession, warehouse: Warehouse) -> None:
        """
        Deletes a warehouse record from the database.

        Args:
            db (AsyncSession): The active database session context.
            warehouse (Warehouse): The warehouse entity to delete.
        """
        await db.delete(warehouse)
        await db.commit()
