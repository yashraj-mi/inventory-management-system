"""
Define the database model for purchase orders.

Manages the overarching document detailing a formal request to a vendor for
the procurement of goods, tracking its approval and fulfillment lifecycle.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import BaseModel

if TYPE_CHECKING:
    from app.db.models.purchase_order_item import PurchaseOrderItem


class PurchaseOrder(BaseModel):
    """
    Represent an outbound request to acquire inventory from a supplier.

    A Purchase Order (PO) coordinates the procurement workflow from initial draft,
    through internal approval, to eventual receipt of goods at a destination warehouse.

    Attributes:
        supplier_id (int): The foreign key linking to the vendor providing the goods.
        destination_warehouse_id (int): The foreign key linking to the facility where goods will be delivered.
        po_number (str): The unique, human-readable identifier sent to the vendor.
        status (str): The current step in the procurement lifecycle (e.g., 'draft', 'ordered', 'received').
        created_by (int | None): The ID of the employee who drafted the request.
        approved_by (int | None): The ID of the manager or admin who authorized the spend.
        approved_at (datetime | None): The exact timestamp when authorization was granted.
        items (list[PurchaseOrderItem]): The individual lines specifying the requested products and quantities.
    """

    __tablename__ = "purchase_orders"

    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id"), nullable=False, index=True
    )
    destination_warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id"), nullable=False, index=True
    )

    po_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    status: Mapped[str] = mapped_column(
        postgresql.ENUM(
            "draft",
            "pending_approval",
            "approved",
            "ordered",
            "partially_received",
            "received",
            "cancelled",
            name="po_status",
            create_type=True,
        ),
        server_default="draft",
        nullable=False,
    )

    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    approved_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    items: Mapped[list["PurchaseOrderItem"]] = relationship(
        "PurchaseOrderItem",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
