from __future__ import annotations

from typing import TYPE_CHECKING
from datetime import datetime

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel
from .mixins import StatusMixin
from app.constants.user_enum import UserRole

if TYPE_CHECKING:
    from .organization import Organization


class User(BaseModel, StatusMixin):
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

    organization: Mapped["Organization"] = relationship(back_populates="users")
