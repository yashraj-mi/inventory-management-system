from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.user import User


class UserRepository:
    """
    Repository layer responsible strictly for low-level
    database operations and SQL formulation for Users.
    """

    async def create(self, db: AsyncSession, user: User) -> User:
        """
        Adds a new User entity to the database session.

        Args:
            db (AsyncSession): The active database session context.
            user (User): The user entity to be created.

        Returns:
            User: The tracked user instance.
        """
        db.add(user)
        return user

    async def get_all(self, db: AsyncSession) -> Sequence[User]:
        """
        Retrieves all user records from the database.

        Args:
            db (AsyncSession): The active database session context.

        Returns:
            Sequence[User]: A sequence of all users.
        """
        result = await db.scalars(select(User))
        return result.all()

    async def get_by_id(self, db: AsyncSession, user_id: int) -> User | None:
        """
        Retrieves a specific user by its primary key.

        Args:
            db (AsyncSession): The active database session context.
            user_id (int): The unique ID of the user.

        Returns:
            User | None: The found user instance, or None if not found.
        """
        return await db.get(User, user_id)

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        """
        Retrieves a user by their unique email address.

        Args:
            db (AsyncSession): The active database session context.
            email (str): The email address to look up.

        Returns:
            User | None: The found user instance, or None if not found.
        """
        return await db.scalar(select(User).where(User.email == email))

    async def delete(self, db: AsyncSession, user: User) -> None:
        """
        Removes a tracked user instance from the database.

        Args:
            db (AsyncSession): The active database session context.
            user (User): The user entity to delete.
        """
        await db.delete(user)

    async def get_org_users(self, db: AsyncSession, org_id: int) -> Sequence[User]:
        """
            Retrieve all users belongs to an organization.

        Args:
            db (AsyncSession): The active database abstraction transaction instance session.
            org_id (int): Target tracking unique primary key constraint matching the organization.

        Returns:
            Sequence[User]: A database results sequence containing instantiated User models.
        """
        result = await db.scalars(select(User).where(User.organization_id == org_id))
        return result.all()
