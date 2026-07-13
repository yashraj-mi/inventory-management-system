"""
Define the database model for inventory suppliers.

Manages the schema for external vendors who provide the organization with goods,
tracking contact details for procurement and purchase orders.
"""

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel
from app.db.models.mixins import StatusMixin


class Supplier(BaseModel, StatusMixin):
    """
    Represent an external vendor or provider of inventory goods.

    Suppliers are organization-specific entities used to fulfill purchase orders
    and track where incoming stock originates. Email and phone must be unique
    per organization to prevent duplicate vendor records.

    Attributes:
        organization_id (int): The foreign key linking the vendor to the purchasing organization.
        name (str): The official business name of the vendor.
        contact_person (str): The name of the primary representative or account manager at the vendor.
        email (str): The primary email address for sending purchase orders.
        phone (str): The primary contact phone number.
    """

    __tablename__ = "suppliers"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(nullable=False)
    contact_person: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)
    phone: Mapped[str] = mapped_column(nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "email", name="uq_supplier_org_email"),
        UniqueConstraint("organization_id", "phone", name="uq_supplier_org_phone"),
    )
