from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.common_enum import Status


class StatusMixin:
    status: Mapped[Status] = mapped_column(
        Enum(Status, values_callable=lambda enum: [e.value for e in enum]),
        nullable=False,
        default=Status.ACTIVE,
    )
