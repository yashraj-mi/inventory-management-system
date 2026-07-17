"""
Define the database model for backorders.

Manages the tracking of unmet customer demand when sales order quantities
exceed currently available physical stock, reserving incoming inventory.
"""

from datetime import date
from sqlalchemy import ForeignKey, Integer, Date
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects import postgresql

from app.db.models.base import BaseModel


class Backorder(BaseModel):
    """
    Represent an unfulfilled portion of a sales order awaiting incoming stock.

    When a warehouse lacks sufficient inventory to completely fulfill a sales order,
    a backorder tracks the deficit. Once new stock arrives (via a PO), it can be allocated here.

    Attributes:
        sales_order_id (int): The foreign key linking to the original sales order missing the stock.
        product_id (int): The foreign key linking to the specific product that is out of stock.
        warehouse_id (int): The foreign key linking to the facility expected to fulfill the deficit.
        quantity_pending (int): The amount of stock still needed to satisfy the customer's request.
        expected_by (date | None): The estimated date when sufficient stock will arrive from suppliers.
        status (str): The current state of the backorder (e.g., 'waiting', 'allocated', 'cancelled').
    """

    __tablename__ = "backorders"

    sales_order_id: Mapped[int] = mapped_column(
        ForeignKey("sales_orders.id"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), nullable=False, index=True
    )
    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id"), nullable=False, index=True
    )

    quantity_pending: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_by: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[str] = mapped_column(
        postgresql.ENUM(
            "waiting",
            "allocated",
            "cancelled",
            name="backorder_status",
            create_type=True,
        ),
        server_default="waiting",
        nullable=False,
    )
