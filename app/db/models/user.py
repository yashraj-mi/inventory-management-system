from __future__ import annotations

from typing import TYPE_CHECKING
from datetime import datetime

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModel
from .mixins import StatusMixin
from app.constants.user_enum import UserRole

if TYPE_CHECKING:
    pass


class User(BaseModel, StatusMixin):
    """
    SQLAlchemy model representing a User in the system.

    Users belong to a specific Organization and are assigned a Role which
    dictates their permissions (e.g., SUPER_ADMIN, ORG_ADMIN, WAREHOUSE_MANAGER).

    Attributes:
        organization_id (int): Foreign key linking the user to an Organization.
        role (UserRole): The authorization role assigned to the user.
        first_name (str): User's given name.
        last_name (str): User's family name.
        email (str): Unique email address, used for login.
        password_hash (str): Bcrypt hashed password.
        last_login (datetime, optional): Timestamp of the user's most recent login.
    """

    __tablename__ = "users"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, values_callable=lambda enum: [e.value for e in enum]),
        nullable=False,
    )

    first_name: Mapped[str] = mapped_column(nullable=False)

    last_name: Mapped[str] = mapped_column(nullable=False)

    email: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)

    password_hash: Mapped[str] = mapped_column(nullable=False)

    last_login: Mapped[datetime | None] = mapped_column(nullable=True)
