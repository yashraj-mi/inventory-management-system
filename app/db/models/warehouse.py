"""
warehouse.py module.

Provides core functionality and components for the warehouse domain.
"""

from sqlalchemy.orm import mapped_column, Mapped

from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from app.constants.warehouse_enum import WarehouseStatus
from app.db.models.base import BaseModel


class Warehouse(BaseModel):
    """
    SQLAlchemy model representing a physical or logical Warehouse.

    Warehouses are associated with a specific Organization and track inventory.
    The combination of organization_id and warehouse code must be unique.

    Attributes:
        organization_id (int): Foreign key to the parent Organization.
        name (str): Human-readable name of the warehouse.
        code (str): Unique internal code/identifier for the warehouse within the organization.
        address (str): Physical location of the warehouse.
        status (WarehouseStatus): Operational status (e.g., ACTIVE, INACTIVE, MAINTENANCE).
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
