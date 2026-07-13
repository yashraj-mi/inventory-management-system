"""
Define the database model for external customers.

Manages the schema for the individuals or business entities that purchase goods
from an organization, tracking their contact and billing information.
"""

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel


class Customer(BaseModel):
    """
    Represent a purchasing client or business entity.

    Tracks the details of a customer associated with a specific organization.
    This model acts as the counterparty for sales orders and outward inventory movements.

    Attributes:
        organization_id (int): The foreign key linking the customer to the organization they buy from.
        name (str): The full name or business name of the customer.
        email (str | None): The primary email address for communication and invoicing.
        phone (str | None): The primary contact phone number.
        address (str | None): The physical billing or shipping address for the customer.
    """

    __tablename__ = "customers"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("organization_id", "email", name="uq_customer_org_email"),
        UniqueConstraint("organization_id", "phone", name="uq_customer_org_phone"),
    )
