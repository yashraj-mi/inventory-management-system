from __future__ import annotations


from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel
from .mixins import StatusMixin


class Organization(BaseModel, StatusMixin):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)

    email: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)

    phone: Mapped[str] = mapped_column(nullable=False)

    address: Mapped[str] = mapped_column(nullable=False)
