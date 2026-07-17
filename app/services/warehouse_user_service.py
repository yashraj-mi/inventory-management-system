"""
Warehouse user service managing role scoping.

Controls the physical location assignments for staff, determining which
warehouses a user has permissions to operate in.
"""

from app.db.session_utils import db_transaction
from typing import Sequence
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.warehouse_user_repository import WarehouseUserRepository
from app.db.models.warehouse_users import WarehouseUsers
from app.schemas.warehouse_user import WarehouseUserAssign
from app.core.exceptions import AppException
from app.constants.warehouse_user_enum import WarehouseUserMessages
from app.constants.common_enum import CrudMessages
from app.dependencies.pagination import PaginationParams
from app.core.profiling import log_timing


class WarehouseUserService:
    """
    Manages the operational validation and rules for assigning users to physical warehouses.
    """

    def __init__(self, repo: WarehouseUserRepository) -> None:
        """
        Initialize the WarehouseUserService.

        Args:
            repo: Data access layer for warehouse user mapping.
        """
        self.repo = repo

    @log_timing
    async def list_users_in_warehouse(
        self, db: AsyncSession, warehouse_id: int, params: PaginationParams
    ) -> tuple[Sequence[WarehouseUsers], int]:
        """
        Retrieve all users assigned to a specific warehouse.

        Args:
            db: The active database session context.
            warehouse_id: Target warehouse ID.
            params: Pagination parameters.

        Returns:
            Tuple containing user assignments and total count.
        """
        return await self.repo.list_by_warehouse(db, warehouse_id, params)

    @log_timing
    async def assign_user_to_warehouse(
        self,
        db: AsyncSession,
        warehouse_id: int,
        payload: WarehouseUserAssign,
        actor_id: int,
    ) -> WarehouseUsers:
        """
        Assign a user to a specific warehouse location.

        Prevents duplicate assignment mappings for the same user-warehouse pair.

        Args:
            db: The active database session context.
            warehouse_id: Target warehouse ID.
            payload: Body containing user ID to assign.
            actor_id: ID of the admin performing the assignment.

        Returns:
            The created WarehouseUsers mapping entity.

        Raises:
            AppException: If assignment already exists (400/409) or DB errors.
        """
        # Prevent duplication entries
        existing = await self.repo.get_assignment(db, warehouse_id, payload.user_id)
        if existing:
            raise AppException(
                message=WarehouseUserMessages.ALREADY_ASSIGNED,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        new_assignment = WarehouseUsers(
            warehouse_id=warehouse_id, user_id=payload.user_id, assigned_by=actor_id
        )

        async with db_transaction(db, module="Warehouse User", action="operation"):
            assignment = await self.repo.add(db, new_assignment)
            await db.flush()
        return assignment

    @log_timing
    async def remove_user_from_warehouse(
        self, db: AsyncSession, warehouse_id: int, user_id: int
    ) -> None:
        """
        Remove a user's warehouse assignment.

        Args:
            db: Active database session context.
            warehouse_id: Target warehouse ID.
            user_id: ID of the user being removed.

        Raises:
            AppException: If mapping doesn't exist (404) or unknown DB error.
        """
        assignment = await self.repo.get_assignment(db, warehouse_id, user_id)
        if not assignment:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Warehouse assignment"),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        async with db_transaction(db, module="Warehouse User", action="operation"):
            await self.repo.delete(db, assignment)
            await db.flush()
