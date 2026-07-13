"""
Define the database model for purchase order items.

Manages the individual line items within a purchase order, detailing exact
quantities and negotiated prices for specific products being procured.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Numeric, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal
from app.db.models.base import BaseModel

if TYPE_CHECKING:
    from app.db.models.purchase_order import PurchaseOrder
    from app.db.models.product import Product


class PurchaseOrderItem(BaseModel):
    """
    Represent a specific product line within a purchase order.

    This model breaks down a procurement request into granular, item-level
    expectations, allowing the warehouse to receive shipments partially and track discrepancies.

    Attributes:
        po_id (int): The foreign key linking to the parent purchase order.
        product_id (int): The foreign key linking to the catalog item being ordered.
        quantity (int): The number of units requested from the vendor.
        unit_price (Decimal): The agreed-upon price per unit for this specific order.
        received_quantity (int): The number of units actually delivered and checked into the warehouse so far.
        purchase_order (PurchaseOrder): The ORM relationship to the parent PO document.
        product (Product): The ORM relationship to the defined product metadata.
    """

    __tablename__ = "purchase_order_items"

    po_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_orders.id"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column()
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    received_quantity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder", back_populates="items"
    )
    product: Mapped["Product"] = relationship("Product")
