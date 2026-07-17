"""
Define the database model for sales orders.

Manages the overarching document detailing a formal commitment to supply goods
to a customer, coordinating the fulfillment lifecycle from a specific warehouse.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from datetime import date
from sqlalchemy import ForeignKey, String, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects import postgresql

from app.db.models.base import BaseModel

if TYPE_CHECKING:
    from app.db.models.sales_order_item import SalesOrderItem


class SalesOrder(BaseModel):
    """
    Represent an outbound commitment to deliver inventory to a customer.

    A Sales Order (SO) initiates the fulfillment workflow, decrementing reserved stock
    and tracking progress until the physical goods are shipped out of the warehouse.

    Attributes:
        customer_id (int): The foreign key linking to the purchasing client entity.
        source_warehouse_id (int): The foreign key linking to the facility fulfilling the order.
        order_number (str): The unique, human-readable identifier provided to the customer.
        due_date (date | None): The agreed-upon deadline for delivery or pickup.
        status (str): The current phase in the fulfillment lifecycle (e.g., 'confirmed', 'fulfilled').
        created_by (int | None): The ID of the employee who recorded the customer's order.
        items (list[SalesOrderItem]): The individual lines specifying the requested products and quantities.
    """

    __tablename__ = "sales_orders"

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"), nullable=False, index=True
    )
    source_warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id"), nullable=False, index=True
    )

    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[str] = mapped_column(
        postgresql.ENUM(
            "draft",
            "pending",
            "awaiting_confirmed",
            "confirmed",
            "partially_fulfilled",
            "fulfilled",
            "cancelled",
            name="so_status",
            create_type=True,
        ),
        server_default="draft",
        nullable=False,
    )

    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )

    # Relationships
    items: Mapped[list["SalesOrderItem"]] = relationship(
        "SalesOrderItem",
        back_populates="sales_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
