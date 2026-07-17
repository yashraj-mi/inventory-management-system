"""
Define the database model for physical inventory balances.

Manages the actual stock quantities, batch details, and expiry dates of products
physically located within specific warehouses.
"""

from datetime import date
from sqlalchemy import (
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    String,
    Integer,
    Date,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects import postgresql

from app.db.models.base import BaseModel


class Inventory(BaseModel):
    """
    Represent a localized stock quantity for a product batch.

    This model tracks the real-time physical availability of goods in a specific warehouse.
    It splits stock by batch numbers to manage perishable goods properly and ensure FIFO/FEFO compliance.

    Attributes:
        warehouse_id (int): The foreign key linking to the physical facility holding the stock.
        product_id (int): The foreign key linking to the item catalog definition.
        batch_number (str): The manufacturer or internal batch/lot identifier for tracking recall and expiry.
        expiry_date (date | None): The date when perishable goods are no longer sellable or usable.
        quantity (int): The current physical on-hand amount of the product batch.
        reserved_quantity (int): The amount allocated to pending orders but not yet shipped.
        reorder_level (int): The threshold at which low stock alerts or automated POs should be triggered.
        status (str): The usability state of this batch (e.g., 'active', 'quarantined', 'expired').
    """

    __tablename__ = "inventory"

    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), nullable=False, index=True
    )

    batch_number: Mapped[str] = mapped_column(
        String(50), server_default="DEFAULT", nullable=False
    )
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    quantity: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    reserved_quantity: Mapped[int] = mapped_column(
        Integer, server_default="0", nullable=False
    )
    reorder_level: Mapped[int] = mapped_column(
        Integer, server_default="0", nullable=True
    )

    status: Mapped[str] = mapped_column(
        postgresql.ENUM(
            "active",
            "expired",
            "depleted",
            "damaged",
            "quarantined",
            "disposed",
            name="inventory_status",
            create_type=True,
        ),
        server_default="active",
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "warehouse_id",
            "product_id",
            "batch_number",
            name="uq_inventory_warehouse_product_batch",
        ),
        CheckConstraint("quantity >= 0", name="chk_inventory_quantity_positive"),
        CheckConstraint(
            "reserved_quantity >= 0", name="chk_inventory_reserved_quantity_positive"
        ),
    )
