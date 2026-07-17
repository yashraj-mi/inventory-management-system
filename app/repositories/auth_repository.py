"""Manage database interactions for user authentication.

This module provides the repository for querying and updating user records
during authentication flows, isolating the database logic from security layers.
"""

from app.repositories.base_repository import BaseRepository
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.user import User


class AuthRepository(BaseRepository[User]):
    """Manage data access for authentication-related operations.

    This repository handles retrieving user records by email for login validation
    and updating metadata such as the last login timestamp.
    """

    model = User

    async def get_user(self, db: AsyncSession, email: str) -> User | None:
        """Retrieve a user instance by their email address.

        Searches the database for a user matching the provided email to support
        authentication or identity verification.

        Args:
            db (AsyncSession): The active asynchronous database session.
            email (str): The email address to look up.

        Returns:
            User | None: The matching user record if found, otherwise None.

        Raises:
            SQLAlchemyError: If an error occurs during the database query.
        """
        statement = select(User).where(User.email == email)
        result = await db.execute(statement)
        return result.scalars().first()

    async def update_last_login(self, db: AsyncSession, user: User) -> User:
        """Update the last login timestamp for the given user.

        Modifies the user's last_login attribute to the current UTC time (as a
        naive datetime) to track recent system access.

        Args:
            db (AsyncSession): The active asynchronous database session.
            user (User): The user entity to update.

        Returns:
            User: The updated user instance.

        Raises:
            SQLAlchemyError: If an error occurs during the database transaction.
        """
        # Generates a clean, timezone-naive UTC timestamp to match your TIMESTAMP WITHOUT TIME ZONE column
        user.last_login = datetime.now(timezone.utc).replace(tzinfo=None)

        return user
