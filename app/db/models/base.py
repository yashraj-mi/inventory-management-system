"""
base.py module.

Provides core functionality and components for the base domain.
"""

from datetime import datetime, timezone
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.core.database import Base


class BaseModel(Base):
    """
    Abstract base model that all database models inherit from.

    Provides common columns `id`, `created_at`, and `updated_at` to ensure
    consistent primary key and timestamp tracking across all database tables.
    """

    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.timezone("UTC", func.now()),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.timezone("UTC", func.now()),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
