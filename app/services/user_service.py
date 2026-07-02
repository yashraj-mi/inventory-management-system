"""
user_service.py module.

Provides core functionality and components for the user_service domain.
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
from app.constants.user_enum import UserMessages


class UserService:
    """
    Service layer driving data validation, security operations,
    business rule validation, and transaction orchestrations for Users.
    """

    def __init__(self, user_repo: UserRepository | None = None) -> None:
        """
        Executes the __init__ operation.

        Args:
            user_repo: Parameter description.

        Returns:
            Execution result.
        """
        self.user_repo = user_repo or UserRepository()
        self.org_repo = OrganizationRepository()

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
                message=UserMessages.ALREADY_EXISTS.format(email=payload.email),
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
                message=UserMessages.ALREADY_EXISTS.format(email=payload.email),
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=UserMessages.DB_UNEXPECTED_CREATION,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return user

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
                message=UserMessages.DB_CONSTRAINT_VIOLATION,
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=UserMessages.DB_UNEXPECTED_UPDATE,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return user

    async def delete_user(self, db: AsyncSession, user_id: int) -> None:
        """
        Validates record scope existence and drops the target user data entry.

        Args:
            db (AsyncSession): The active database session context.
            user_id (int): The ID of the user to delete.
        """
        user = await self.get_user(db=db, user_id=user_id)

        try:
            await self.user_repo.delete(db=db, user=user)
            await db.flush()
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=UserMessages.DB_RELATIONAL_CONSTRAINTS,
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=UserMessages.DB_UNEXPECTED_DELETION,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    async def get_all_users(self, db: AsyncSession) -> Sequence[User]:
        """
        Retrieves all users from the system.

        Args:
            db (AsyncSession): The active database session context.

        Returns:
            Sequence[User]: A sequence of all users.
        """
        return await self.user_repo.get_all(db)

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
                message=UserMessages.NOT_FOUND.format(user_id=user_id),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return user

    async def get_org_users(self, db: AsyncSession, org_id: int) -> list[User]:
        """
        Validates target entity integrity bounds and fetches the complete list
        of users belonging to the corporate organization matching the org_id.

        Args:
            db (AsyncSession): Active database transactional session context.
            org_id (int): Primary tracking key matching the organizational record profile.

        Raises:
            AppException: HTTP 404 error if the specified organization footprint
                          is missing or unverified inside the system.

        Returns:
            list[User]: A type-converted list containing matching user profile system records.
        """
        # 1. Structural Validation - Verify the organization partition exists first

        organization_exists = await self.org_repo.get_by_id(db, organization_id=org_id)
        if not organization_exists:
            raise AppException(
                message=UserMessages.ORG_NOT_FOUND.format(org_id=org_id),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # 2. Extract collection matching target database elements safely
        user_data = await self.user_repo.get_org_users(db=db, org_id=org_id)
        return list(user_data)
