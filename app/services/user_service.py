from collections.abc import Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import PasswordManager
from app.core.exceptions import AppException


class UserService:
    """
    Service layer driving data validation, security operations,
    business rule validation, and transaction orchestrations.
    """

    def __init__(self, user_repo: UserRepository | None = None) -> None:
        self.user_repo = user_repo or UserRepository()

    async def create_user(self, db: AsyncSession, payload: UserCreate) -> User:
        """Orchestrates creation flow and commits the session transaction."""
        existing_user = await self.user_repo.get_by_email(db, payload.email)
        if existing_user:
            raise AppException(
                message=f"User with email '{payload.email}' already exists.",
                status_code=409,
            )

        hashed_password = PasswordManager.hash_password(payload.password)
        user = User(
            organization_id=payload.organization_id,
            role=payload.role,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            password_hash=hashed_password,
        )

        await self.user_repo.create(db=db, user=user)

        # Explicitly commit the active transaction lifecycle here
        await db.commit()
        await db.refresh(user)
        return user

    async def update_user(
        self, db: AsyncSession, user_id: int, payload: UserUpdate
    ) -> User:
        """Applies patch delta payloads onto validated model definitions safely."""
        user = await self.get_user(db=db, user_id=user_id)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        # Commit changes tracked by SQLAlchemy automatically
        await db.commit()
        await db.refresh(user)
        return user

    async def delete_user(self, db: AsyncSession, user_id: int) -> None:
        """Validates record scope existence and drops the target structural data entry."""
        user = await self.get_user(db=db, user_id=user_id)

        await self.user_repo.delete(db=db, user=user)
        await db.commit()

    async def get_all_users(self, db: AsyncSession) -> Sequence[User]:
        return await self.user_repo.get_all(db)

    async def get_user(self, db: AsyncSession, user_id: int) -> User:
        user = await self.user_repo.get_by_id(db=db, user_id=user_id)
        if not user:
            raise AppException(
                message=f"User with ID {user_id} not found.", status_code=404
            )
        return user
