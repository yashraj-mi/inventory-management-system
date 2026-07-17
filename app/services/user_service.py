"""
User service for identity and access management.

Manages user creation (including secure password hashing), profile updates,
role assignments, and tenant-scoped user queries.
"""

from app.db.session_utils import db_transaction
from collections.abc import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
from app.db.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreateInternal, UserUpdate
from app.core.security import PasswordManager
from app.core.exceptions import AppException
from app.repositories.organization_repository import OrganizationRepository
from app.constants.common_enum import CrudMessages
from app.dependencies.pagination import PaginationParams
from app.constants.common_enum import Status

from app.core.profiling import log_timing


class UserService:
    """
    Service layer driving data validation, security operations,
    business rule validation, and transaction orchestrations for Users.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        org_repo: OrganizationRepository,
        warehouse_repo=None,
    ) -> None:
        """
        Initialize the UserService with required repositories.

        Args:
            user_repo: Data access layer for user queries and persistence.
            org_repo: Data access layer for organization existence validation.
        """
        self.user_repo = user_repo
        self.org_repo = org_repo
        self.warehouse_repo = warehouse_repo

    @log_timing
    async def create_user(
        self, db: AsyncSession, payload: UserCreateInternal, current_user: User
    ) -> User:
        """
        Orchestrates user creation flow, including password hashing and session commit.

        Args:
            db (AsyncSession): The active database session context.
            payload (UserCreateInternal): The payload containing user details.

        Returns:
            User: The newly created user instance.

        Raises:
            AppException: If a user with the given email already exists (409).
        """
        existing_user = await self.user_repo.get_by_email(db, payload.email)
        if existing_user:
            raise AppException(
                message=CrudMessages.ALREADY_EXISTS_FIELD.format(
                    module="User", field="email", value=payload.email
                ),
                status_code=status.HTTP_409_CONFLICT,
            )

        if payload.organization_id is not None:
            org = await self.org_repo.get_by_id(db, payload.organization_id)
            if not org:
                raise AppException(
                    message=CrudMessages.ORG_NOT_FOUND.format(module="User"),
                    status_code=status.HTTP_404_NOT_FOUND,
                )

        from app.repositories.rbac_repository import get_role_by_name, has_platform_role
        from app.db.models.rbac import UserRole

        role_record = await get_role_by_name(db, payload.role)
        if not role_record:
            raise AppException(
                message=f"Role '{payload.role}' does not exist.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if role_record.name.upper() == "SUPER_ADMIN":
            caller_is_super = await has_platform_role(
                db, current_user.id, "SUPER_ADMIN"
            )
            if not caller_is_super:
                raise AppException(
                    message="Only super_admin can create super_admin users.",
                    status_code=status.HTTP_403_FORBIDDEN,
                )

        if payload.warehouse_id is not None:
            if not role_record.name.upper().startswith("WAREHOUSE"):
                raise AppException(
                    message="Cannot assign a warehouse to an organization-wide role.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            if self.warehouse_repo:
                warehouse = await self.warehouse_repo.get_by_id(
                    db, payload.warehouse_id
                )
                if (
                    not warehouse
                    or warehouse.organization_id != payload.organization_id
                ):
                    raise AppException(
                        message="Invalid warehouse_id for the given organization.",
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )
        else:
            if role_record.name.upper().startswith("WAREHOUSE"):
                raise AppException(
                    message="Warehouse-scoped roles require a warehouse_id.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        hashed_password = PasswordManager.hash_password(payload.password)
        user = User(
            organization_id=payload.organization_id,
            first_name=payload.first_name,
            last_name=payload.last_name or None,
            email=payload.email,
            password_hash=hashed_password,
            user_roles=[
                UserRole(
                    role_id=role_record.id,
                    org_id=payload.organization_id,
                    warehouse_id=payload.warehouse_id,
                )
            ],
        )

        async with db_transaction(db, module="User", action="operation"):
            await self.user_repo.create(db=db, obj=user)
            await db.flush()
            await db.refresh(user)
        return user

    @log_timing
    async def update_user(
        self, db: AsyncSession, user_id: int, payload: UserUpdate, current_user: User
    ) -> User:
        """
        Applies patch delta payloads onto validated model definitions safely.

        Args:
            db (AsyncSession): The active database session context.
            user_id (int): The ID of the user to update.
            payload (UserUpdate): Payload containing the fields to update.
            current_user (User): The user executing the update.
            org_id (int): The organization ID.

        Returns:
            User: The updated user instance.
        """
        user = await self.get_user(
            db=db, user_id=user_id, org_id=current_user.organization_id
        )

        update_data = payload.model_dump(exclude_unset=True)
        new_role = update_data.pop("role", None)
        new_warehouse_id = update_data.pop("warehouse_id", None)

        if new_role:
            from app.repositories.rbac_repository import (
                get_role_by_name,
                has_platform_role,
            )
            from app.db.models.rbac import UserRole
            from sqlalchemy import delete

            role_record = await get_role_by_name(db, new_role)
            if not role_record:
                raise AppException(
                    message=f"Role '{new_role}' does not exist.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            if role_record.name.upper() == "SUPER_ADMIN":
                caller_is_super = await has_platform_role(
                    db, current_user.id, "SUPER_ADMIN"
                )
                if not caller_is_super:
                    raise AppException(
                        message="Only super_admin can assign super_admin role.",
                        status_code=status.HTTP_403_FORBIDDEN,
                    )

            if new_warehouse_id is not None:
                if not role_record.name.upper().startswith("WAREHOUSE"):
                    raise AppException(
                        message="Cannot assign a warehouse to an organization-wide role.",
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )
                if self.warehouse_repo:
                    warehouse = await self.warehouse_repo.get_by_id(
                        db, new_warehouse_id
                    )
                    if (
                        not warehouse
                        or warehouse.organization_id != user.organization_id
                    ):
                        raise AppException(
                            message="Invalid warehouse_id for the given organization.",
                            status_code=status.HTTP_400_BAD_REQUEST,
                        )
            else:
                if role_record.name.upper().startswith("WAREHOUSE"):
                    raise AppException(
                        message="Warehouse-scoped roles require a warehouse_id.",
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )

            # Clean replacement
            await db.execute(delete(UserRole).where(UserRole.user_id == user_id))
            user.user_roles.append(
                UserRole(
                    role_id=role_record.id,
                    org_id=user.organization_id,
                    warehouse_id=new_warehouse_id,
                )
            )

        for field, value in update_data.items():
            setattr(user, field, value)

        async with db_transaction(db, module="User", action="operation"):
            await db.flush()
            await db.refresh(user)
        return user

    @log_timing
    async def delete_user(self, db: AsyncSession, user_id: int, org_id: int) -> None:
        """
        Delete a user entity from the system.

        Validates the user exists before dropping. Performs a soft-delete (status = INACTIVE). Relational constraints are handled safely at the DB level, but soft-deletion is the primary mechanism to avoid breaking historical records.

        Args:
            db: The active database session context.
            user_id: The ID of the user to delete.
            org_id: The organization ID.
        """
        user = await self.get_user(db=db, user_id=user_id, org_id=org_id)

        async with db_transaction(db, module="User", action="operation"):
            user.status = Status.IN_ACTIVE
            await db.flush()

    @log_timing
    async def get_all_users(
        self, db: AsyncSession, params: PaginationParams
    ) -> tuple[Sequence[User], int]:
        """
        Retrieves all users from the system.

        Args:
            db (AsyncSession): The active database session context.

        Returns:
            Sequence[User]: A sequence of all users.
        """
        return await self.user_repo.get_all(db, params)

    @log_timing
    async def get_user(self, db: AsyncSession, user_id: int, org_id: int) -> User:
        """
        Retrieves a specific user by ID, raising a 404 if not found.

        Args:
            db (AsyncSession): The active database session context.
            user_id (int): The ID of the user to retrieve.
            org_id (int): The organization ID.

        Returns:
            User: The found user instance.

        Raises:
            AppException: If the user does not exist (404).
        """
        user = await self.user_repo.get_by_id(db=db, user_id=user_id)
        if not user or user.organization_id != org_id:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="User"),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return user

    @log_timing
    async def get_org_users(
        self, db: AsyncSession, org_id: int, params: PaginationParams
    ) -> tuple[Sequence[User], int]:
        """
        Retrieve all active users scoped to a specific organization.

        Args:
            db: Active database transactional session context.
            org_id: Organization ID to filter users by.
            params: Pagination parameters.

        Raises:
            AppException: If the organization does not exist (404).

        Returns:
            A tuple of user sequences and total count.
        """
        # 1. Structural Validation - Verify the organization partition exists first

        organization_exists = await self.org_repo.get_by_id(db, org_id)
        if not organization_exists:
            raise AppException(
                message=CrudMessages.ORG_NOT_FOUND.format(module="User"),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # 2. Extract collection matching target database elements safely
        return await self.user_repo.get_org_users(db=db, org_id=org_id, params=params)
