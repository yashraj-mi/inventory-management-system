"""
Define the database model for organizations.

Acts as the root tenant entity in the multi-tenant architecture, grouping all
users, warehouses, products, and transactions under a single business account.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from sqlalchemy import ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants.organization_enum import OrganizationStatus
from .base import BaseModel

if TYPE_CHECKING:
    from app.db.models.user import User


class Organization(BaseModel):
    """
    Represent a top-level tenant or business entity.

    Organizations encapsulate all operational data for a specific client business.
    Newly registered organizations begin in a PENDING state and require super admin
    approval before they can perform any inventory actions.

    Attributes:
        name (str): The unique, human-readable name of the business entity.
        email (str): The unique primary contact email for the organization.
        phone (str): The primary contact phone number.
        address (str): The physical headquarters or primary mailing address.
        status (OrganizationStatus): The current operational state (e.g., PENDING, ACTIVE).
        action_by (int | None): The ID of the super admin user who approved or rejected the registration.
        users (list[User]): The collection of users associated with this organization.
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
        ForeignKey("users.id", use_alter=True), nullable=True, index=True
    )

    users: Mapped[list["User"]] = relationship(
        "User", back_populates="organization", foreign_keys="[User.organization_id]"
    )
