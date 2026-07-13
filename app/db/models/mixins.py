"""
Provide reusable mixin classes for database models.

Contains composable SQLAlchemy model components that can be mixed into various
domain models to grant standardized column structures and behaviors, such as status tracking.
"""

from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.common_enum import Status


class StatusMixin:
    """
    Provide a standardized operational status column for database records.

    Allows models to track lifecycle states (e.g., ACTIVE, INACTIVE) using a shared
    enum, standardizing soft-delete or visibility logic across different domains.

    Attributes:
        status (Status): The current operational state of the record, defaulting to ACTIVE.
    """

    status: Mapped[Status] = mapped_column(
        Enum(Status, values_callable=lambda enum: [e.value for e in enum]),
        nullable=False,
        default=Status.ACTIVE,
        server_default="active",
    )
