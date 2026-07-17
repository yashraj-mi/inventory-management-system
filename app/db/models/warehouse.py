"""
Define the database model for physical or logical warehouses.

Manages the geographical or structural nodes where physical inventory is stored
for an organization, facilitating location-based stock tracking.
"""

from sqlalchemy.orm import mapped_column, Mapped

from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from app.constants.warehouse_enum import WarehouseStatus
from app.db.models.base import BaseModel


class Warehouse(BaseModel):
    """
    Represent a distinct physical or logical storage location.

    Warehouses belong to an organization and serve as the physical nodes where
    inventory balances are tracked. They can be toggled active/inactive to manage
    facilities undergoing maintenance or closure.

    Attributes:
        organization_id (int): The foreign key linking the warehouse to its owning organization.
        name (str): The human-readable name identifying the facility (e.g., 'Main Distribution Center').
        code (str): A unique alphanumeric identifier used for quick reference and barcode scanning.
        address (str): The physical street address of the facility.
        status (WarehouseStatus): The current operational state of the facility (e.g., ACTIVE, MAINTENANCE).
    """

    __tablename__ = "warehouses"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "code", name="uq_warehouse_organization_code"
        ),
    )
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(nullable=False)
    code: Mapped[str] = mapped_column(nullable=False)
    address: Mapped[str] = mapped_column()
    status: Mapped[WarehouseStatus] = mapped_column(
        Enum(WarehouseStatus, values_callable=lambda enum: [e.value for e in enum]),
        nullable=False,
        default=WarehouseStatus.ACTIVE,
    )
