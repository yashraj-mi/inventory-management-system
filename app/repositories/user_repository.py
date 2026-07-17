"""Manage database interactions for user accounts.

This module provides the UserRepository, handling data access for user profile
management, authentication lookups, and organizational scoping queries.
"""

from app.repositories.base_repository import BaseRepository
from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.user import User
from app.dependencies.pagination import PaginationParams
from app.repositories.base import paginate_query


class UserRepository(BaseRepository[User]):
    """Manage data access for User entities.

    Abstracts database operations for tracking and authenticating platform users,
    supporting global and organization-scoped pagination.
    """

    model = User

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
