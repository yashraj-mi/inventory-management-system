"""
Define the base model for all SQLAlchemy database models.

Establishes the foundational SQLAlchemy declarative base class used across the
application to ensure consistent primary key structure and automated timestamp tracking.
"""

from datetime import datetime, timezone
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.core.database import Base


class BaseModel(Base):
    """
    Represent the abstract base model for all database tables.

    Provides the universally required `id`, `created_at`, and `updated_at` columns.
    By inheriting from this class, models automatically gain consistent primary keys
    and timezone-aware timestamp auditing without duplicating column definitions.

    Attributes:
        id (int): The primary key identifier for the record.
        created_at (datetime): The UTC timestamp when the record was inserted.
        updated_at (datetime): The UTC timestamp when the record was last modified.
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
