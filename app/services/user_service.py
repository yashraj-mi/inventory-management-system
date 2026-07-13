"""
User service for identity and access management.

Manages user creation (including secure password hashing), profile updates,
role assignments, and tenant-scoped user queries.
"""

from collections.abc import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import status
from app.db.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreateInternal, UserUpdate
from app.core.security import PasswordManager
from app.core.exceptions import AppException
from app.repositories.organization_repository import OrganizationRepository
from app.constants.common_enum import CrudMessages
from app.dependencies.pagination import PaginationParams


from app.core.profiling import log_timing


class UserService:
    """
    Service layer driving data validation, security operations,
    business rule validation, and transaction orchestrations for Users.
    """

    def __init__(
        self, user_repo: UserRepository, org_repo: OrganizationRepository
    ) -> None:
        """
        Initialize the UserService with required repositories.

        Args:
            user_repo: Data access layer for user queries and persistence.
            org_repo: Data access layer for organization existence validation.
        """
        self.user_repo = user_repo
        self.org_repo = org_repo

    @log_timing
    async def create_user(self, db: AsyncSession, payload: UserCreateInternal) -> User:
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

        hashed_password = PasswordManager.hash_password(payload.password)
        user = User(
            organization_id=payload.organization_id,
            role=payload.role,
            first_name=payload.first_name,
            last_name=payload.last_name or None,
            email=payload.email,
            password_hash=hashed_password,
        )

        try:
            await self.user_repo.create(db=db, user=user)
            await db.flush()
            await db.refresh(user)
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.ALREADY_EXISTS_FIELD.format(
                    module="User", field="email", value=payload.email
                ),
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_UNEXPECTED.format(
                    module="User", action="creation"
                ),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return user

    @log_timing
    async def update_user(
        self, db: AsyncSession, user_id: int, payload: UserUpdate
    ) -> User:
        """
        Applies patch delta payloads onto validated model definitions safely.

        Args:
            db (AsyncSession): The active database session context.
            user_id (int): The ID of the user to update.
            payload (UserUpdate): Payload containing the fields to update.

        Returns:
            User: The updated user instance.
        """
        user = await self.get_user(db=db, user_id=user_id)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        try:
            await db.flush()
            await db.refresh(user)
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_CONSTRAINT.format(module="User"),
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_UNEXPECTED.format(
                    module="User", action="update"
                ),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return user

    @log_timing
    async def delete_user(self, db: AsyncSession, user_id: int) -> None:
        """
        Delete a user entity from the system.

        Validates the user exists before dropping. Enforces relational constraints
        if the user is associated with active orders, transactions, or logs.

        Args:
            db: The active database session context.
            user_id: The ID of the user to delete.
        """
        user = await self.get_user(db=db, user_id=user_id)

        try:
            await self.user_repo.delete(db=db, user=user)
            await db.flush()
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_RELATIONAL_CONSTRAINT.format(module="User"),
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_UNEXPECTED.format(
                    module="User", action="deletion"
                ),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

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
    async def get_user(self, db: AsyncSession, user_id: int) -> User:
        """
        Retrieves a specific user by ID, raising a 404 if not found.

        Args:
            db (AsyncSession): The active database session context.
            user_id (int): The ID of the user to retrieve.

        Returns:
            User: The found user instance.

        Raises:
            AppException: If the user does not exist (404).
        """
        user = await self.user_repo.get_by_id(db=db, user_id=user_id)
        if not user:
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

        organization_exists = await self.org_repo.get_by_id(db, organization_id=org_id)
        if not organization_exists:
            raise AppException(
                message=CrudMessages.ORG_NOT_FOUND.format(module="User"),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # 2. Extract collection matching target database elements safely
        return await self.user_repo.get_org_users(db=db, org_id=org_id, params=params)
