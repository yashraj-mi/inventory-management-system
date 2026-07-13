"""
Define the database model for application users.

Manages authentication credentials and role-based access control mapping for
individuals interacting with the inventory system on behalf of an organization.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from datetime import datetime

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel
from .mixins import StatusMixin
from app.constants.user_enum import UserRole

if TYPE_CHECKING:
    from app.db.models.organization import Organization


class User(BaseModel, StatusMixin):
    """
    Represent an authenticated individual accessing the system.

    Users are intrinsically linked to a single organization (unless they are super admins)
    and their assigned role determines what actions they can perform (e.g., view stock, create orders).

    Attributes:
        organization_id (int): The foreign key linking the user to their employer organization.
        organization (Organization): The ORM relationship to the parent organization.
        role (UserRole): The predefined security role granting specific application permissions.
        first_name (str): The user's given name.
        last_name (str): The user's family name or surname.
        email (str): The unique email address used as the login credential.
        password_hash (str): The securely hashed password string for authentication.
        last_login (datetime | None): The timestamp indicating when the user last authenticated successfully.
    """

    __tablename__ = "users"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, index=True
    )

    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="users", foreign_keys=[organization_id]
    )

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, values_callable=lambda enum: [e.value for e in enum]),
        nullable=False,
    )

    first_name: Mapped[str] = mapped_column(nullable=False)

    last_name: Mapped[str] = mapped_column(nullable=True)

    email: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)

    password_hash: Mapped[str] = mapped_column(nullable=False)

    last_login: Mapped[datetime | None] = mapped_column(nullable=True)
