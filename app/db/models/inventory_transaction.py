"""
Define the database model for inventory transactions.

Manages the immutable ledger of all stock movements, adjustments, and corrections,
serving as the single source of truth for auditing stock level changes.
"""

from decimal import Decimal
from sqlalchemy import ForeignKey, String, Integer, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects import postgresql

from app.db.models.base import BaseModel


class InventoryTransaction(BaseModel):
    """
    Represent a historical change in stock quantity.

    Transactions form an append-only ledger detailing every time stock enters,
    leaves, or is adjusted within a warehouse. This guarantees traceability for financial
    reconciliation and loss-prevention.

    Attributes:
        warehouse_id (int): The foreign key linking to the facility where the event occurred.
        product_id (int): The foreign key linking to the item affected.
        batch_number (str): The specific batch or lot involved in the movement.
        transaction_type (str): The nature of the event (e.g., 'purchase', 'sale', 'adjustment').
        quantity (int): The delta amount (positive for incoming, negative for outgoing).
        unit_cost_snapshot (Decimal | None): The financial value of one unit at the exact time of the transaction.
        reference_type (str | None): The context origin of the transaction (e.g., 'PO', 'SO').
        reference_id (int | None): The foreign key ID of the triggering document (e.g., Purchase Order ID).
        remarks (str | None): Manual justification or notes from the operator.
        created_by (int | None): The ID of the user who initiated or recorded the transaction.
    """

    __tablename__ = "inventory_transactions"

    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), nullable=False, index=True
    )
    batch_number: Mapped[str] = mapped_column(
        String(50), server_default="DEFAULT", nullable=False
    )

    transaction_type: Mapped[str] = mapped_column(
        postgresql.ENUM(
            "purchase",
            "sale",
            "transfer_in",
            "transfer_out",
            "adjustment",
            "return",
            "disposal",
            name="inv_transaction_type",
            create_type=True,
        ),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost_snapshot: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )

    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
