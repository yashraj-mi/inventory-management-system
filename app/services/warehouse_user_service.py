"""
warehouse_user_service.py module.

Provides core functionality and components for the warehouse_user_service domain.
"""

from typing import Sequence
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.repositories.warehouse_user_repository import WarehouseUserRepository
from app.db.models.warehouse_users import WarehouseUsers
from app.schemas.warehouse_user import WarehouseUserAssign
from app.core.exceptions import AppException
from app.constants.warehouse_user_enum import WarehouseUserMessages


class WarehouseUserService:
    """
    Manages the operational validation and rules for assigning users to physical warehouses.
    """

    def __init__(self, repo: WarehouseUserRepository | None = None) -> None:
        """
        Executes the __init__ operation.

        Args:
            repo: Parameter description.

        Returns:
            Execution result.
        """
        self.repo = repo or WarehouseUserRepository()

    async def list_users_in_warehouse(
        self, db: AsyncSession, warehouse_id: int
    ) -> Sequence[WarehouseUsers]:
        """
        Retrieves all user assignments for a given warehouse.

        Args:
            db (AsyncSession): The active database session context.
            warehouse_id (int): The ID of the warehouse.

        Returns:
            Sequence[WarehouseUsers]: A sequence of mapping records.
        """
        return await self.repo.list_by_warehouse(db, warehouse_id)

    async def assign_user_to_warehouse(
        self,
        db: AsyncSession,
        warehouse_id: int,
        payload: WarehouseUserAssign,
        actor_id: int,
    ) -> WarehouseUsers:
        """
        Assigns a user to a warehouse, ensuring no duplicate assignments exist.

        Args:
            db (AsyncSession): The active database session context.
            warehouse_id (int): The ID of the warehouse.
            payload (WarehouseUserAssign): Payload containing the user ID to assign.
            actor_id (int): The ID of the user performing the assignment.

        Returns:
            WarehouseUsers: The newly created assignment record.

        Raises:
            AppException: If the user is already assigned to the warehouse.
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

        try:
            assignment = await self.repo.add(db, new_assignment)
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=WarehouseUserMessages.ALREADY_ASSIGNED,
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=WarehouseUserMessages.DB_UNEXPECTED_ASSIGNMENT,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return assignment

    async def remove_user_from_warehouse(
        self, db: AsyncSession, warehouse_id: int, user_id: int
    ) -> None:
        """
        Removes a user's warehouse assignment.

        Args:
            db (AsyncSession): The active database session context.
            warehouse_id (int): The ID of the warehouse.
            user_id (int): The ID of the assigned user.

        Raises:
            AppException: If the assignment mapping record is not found (404).
        """
        assignment = await self.repo.get_assignment(db, warehouse_id, user_id)
        if not assignment:
            raise AppException(
                message=WarehouseUserMessages.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND,
            )

        try:
            await self.repo.delete(db, assignment)
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=WarehouseUserMessages.DB_RELATIONAL_CONSTRAINTS,
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=WarehouseUserMessages.DB_UNEXPECTED_REMOVAL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
