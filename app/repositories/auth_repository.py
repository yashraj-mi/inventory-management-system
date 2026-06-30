from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.user import User


class AuthRepository:
    """
    Repository layer responsible for database interactions during the
    authentication lifecycle.
    """

    async def get_user(self, db: AsyncSession, email: str) -> User | None:
        """
        Retrieves a single user instance matching the provided email address.

        Args:
            db (AsyncSession): The active database session context.
            email (str): The target email address to match.

        Returns:
            User | None: The found database user instance, or None if no record exists.
        """
        statement = select(User).where(User.email == email)
        result = await db.execute(statement)
        return result.scalars().first()

    async def update_last_login(self, db: AsyncSession, user: User) -> User:
        """
        Updates the last_login timestamp for a specific user instance.

        Uses a database-compatible naive UTC datetime payload.

        Args:
            db (AsyncSession): The active database session context.
            user (User): The user entity to be updated.

        Returns:
            User: The updated user instance with the new timestamp.
        """
        # Generates a clean, timezone-naive UTC timestamp to match your TIMESTAMP WITHOUT TIME ZONE column
        user.last_login = datetime.now(timezone.utc).replace(tzinfo=None)

        # Synchronizes state changes to the database buffer pipeline within the current running transaction
        await db.flush()

        return user
