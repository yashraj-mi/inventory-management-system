from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.user import User


class UserRepository:
    """
    Repository layer responsible strictly for low-level
    database operations and SQL formulation.
    """

    async def create(self, db: AsyncSession, user: User) -> User:
        """Adds a transient User model instance to the session."""
        db.add(user)
        return user

    async def get_all(self, db: AsyncSession) -> Sequence[User]:
        """Retrieves all user records from the database."""
        result = await db.scalars(select(User))
        return result.all()

    async def get_by_id(self, db: AsyncSession, user_id: int) -> User | None:
        """Retrieves a specific user by primary key identity map or query."""
        return await db.get(User, user_id)

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        """Retrieves a user by unique email address string matching."""
        return await db.scalar(select(User).where(User.email == email))

    async def delete(self, db: AsyncSession, user: User) -> None:
        """Removes an active tracked user instance from the session persistence."""
        await db.delete(user)
