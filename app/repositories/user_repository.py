"""Manage database interactions for user accounts.

This module provides the UserRepository, handling data access for user profile
management, authentication lookups, and organizational scoping queries.
"""

from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.user import User
from app.dependencies.pagination import PaginationParams
from app.repositories.base import paginate_query


class UserRepository:
    """Manage data access for User entities.

    Abstracts database operations for tracking and authenticating platform users,
    supporting global and organization-scoped pagination.
    """

    async def create(self, db: AsyncSession, user: User) -> User:
        """Stage a new user record for database insertion.

        Args:
            db (AsyncSession): The active asynchronous database session.
            user (User): The user entity to create.

        Returns:
            User: The staged user instance.
        """
        db.add(user)
        return user

    async def get_all(
        self, db: AsyncSession, params: PaginationParams
    ) -> tuple[Sequence[User], int]:
        """Fetch a paginated list of all system users globally.

        Primarily used by super-admin roles to manage global user accounts
        across the entire platform.

        Args:
            db (AsyncSession): The active asynchronous database session.
            params (PaginationParams): Pagination constraints (offset/limit).

        Returns:
            tuple[Sequence[User], int]: The fetched users and the total count.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        query = select(User)
        return await paginate_query(db, query, params)

    async def get_by_id(self, db: AsyncSession, user_id: int) -> User | None:
        """Fetch a specific user by their primary key.

        Args:
            db (AsyncSession): The active asynchronous database session.
            user_id (int): The unique identifier of the user.

        Returns:
            User | None: The requested user, or None if not found.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        return await db.get(User, user_id)

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        """Fetch a user by their email address.

        Used extensively during authentication flows and to enforce email
        uniqueness constraints during user registration.

        Args:
            db (AsyncSession): The active asynchronous database session.
            email (str): The email address to look up.

        Returns:
            User | None: The matching user, or None if not found.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        return await db.scalar(select(User).where(User.email == email))

    async def delete(self, db: AsyncSession, user: User) -> None:
        """Stage a user account for deletion from the database.

        Args:
            db (AsyncSession): The active asynchronous database session.
            user (User): The user instance to remove.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        await db.delete(user)

    async def get_org_users(
        self, db: AsyncSession, org_id: int, params: PaginationParams
    ) -> tuple[Sequence[User], int]:
        """Fetch a paginated list of users scoped to a specific organization.

        Enforces tenant isolation by retrieving only the user accounts
        belonging to the specified organization.

        Args:
            db (AsyncSession): The active asynchronous database session.
            org_id (int): The ID of the target organization.
            params (PaginationParams): Pagination constraints (offset/limit).

        Returns:
            tuple[Sequence[User], int]: The fetched users and total count.

        Raises:
            SQLAlchemyError: If the database operation fails.
        """
        query = select(User).where(User.organization_id == org_id)
        return await paginate_query(db, query, params)
