from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel
from .mixins import StatusMixin

if TYPE_CHECKING:
    from .user import User


class Organization(BaseModel, StatusMixin):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)

    email: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)

    phone: Mapped[str] = mapped_column(nullable=False)

    address: Mapped[str] = mapped_column(nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="organization")
