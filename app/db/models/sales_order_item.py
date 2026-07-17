"""
Define the database model for sales order items.

Manages the individual line items within a sales order, detailing exact
quantities, prices, and specific batches of products being sold.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal
from app.db.models.base import BaseModel

if TYPE_CHECKING:
    from app.db.models.sales_order import SalesOrder
    from app.db.models.product import Product


class SalesOrderItem(BaseModel):
    """
    Represent a specific product line within a sales order.

    This model defines exactly what is being sold and at what price, tracking how much
    has physically left the warehouse. Optionally links to a specific batch to enforce FIFO.

    Attributes:
        sales_order_id (int): The foreign key linking to the parent sales order.
        product_id (int): The foreign key linking to the catalog item being sold.
        batch_number (str | None): The specific lot identifier if the customer requested or was allocated a specific batch.
        quantity (int): The total number of units the customer ordered.
        unit_price (Decimal): The selling price charged per unit.
        fulfilled_quantity (int): The number of units that have successfully shipped out.
        sales_order (SalesOrder): The ORM relationship to the parent SO document.
        product (Product): The ORM relationship to the defined product metadata.
    """

    __tablename__ = "sales_order_items"

    sales_order_id: Mapped[int] = mapped_column(
        ForeignKey("sales_orders.id"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), nullable=False, index=True
    )

    batch_number: Mapped[str | None] = mapped_column(String(50), nullable=True)

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    fulfilled_quantity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    # Relationships
    sales_order: Mapped["SalesOrder"] = relationship(
        "SalesOrder", back_populates="items"
    )
    product: Mapped["Product"] = relationship("Product")
