"""
organization.py module.

Provides core functionality and components for the organization domain.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from sqlalchemy import ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.organization_enum import OrganizationStatus
from .base import BaseModel

if TYPE_CHECKING:
    pass


class Organization(BaseModel):
    """
    SQLAlchemy model representing an Organization in the system.

    Organizations are the top-level tenant in the multi-tenant architecture.
    Users and Warehouses are tied to a specific Organization. Newly registered
    organizations start in a PENDING status until approved by a super admin.

    Attributes:
        name (str): Unique name of the organization.
        email (str): Unique contact email for the organization.
        phone (str): Contact phone number.
        address (str): Physical or mailing address.
        status (OrganizationStatus): Current status (PENDING, ACTIVE, REJECTED).
        action_by (int, optional): ID of the super admin who approved/rejected the request.
    """

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    phone: Mapped[str] = mapped_column(nullable=False)
    address: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[OrganizationStatus] = mapped_column(
        Enum(OrganizationStatus, values_callable=lambda enum: [e.value for e in enum]),
        nullable=False,
        default=OrganizationStatus.PENDING,
    )
    action_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
