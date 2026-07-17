"""
Provide schemas for tracking historical inventory transactions.

This module defines Pydantic models for recording and returning ledger entries
of stock movements, adjustments, and receipts.
"""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from app.constants.inventory_enum import InventoryTransactionType


class InventoryTransactionCreate(BaseModel):
    """Represent the payload for creating a new inventory ledger entry.

    Used internally when stock levels change due to sales, purchases, or adjustments.
    It guarantees an audit trail for every change in inventory quantity.

    Attributes:
        warehouse_id (int): Identifier of the warehouse where the change occurred.
        product_id (int): Identifier of the product whose stock is changing.
        batch_number (str): The batch or lot identifier for the affected stock.
        transaction_type (InventoryTransactionType): Classification of the movement (e.g., ADJUSTMENT, SALE).
        quantity (int): The amount changed; positive for inbound, negative for outbound.
        unit_cost_snapshot (Decimal | None): Cost per unit at the time of the transaction, for valuation.
        reference_type (str | None): Source document type (e.g., 'sales_order', 'purchase_order').
        reference_id (int | None): Identifier of the source document triggering the transaction.
        remarks (str | None): Optional context or reasoning for the transaction.
        created_by (int | None): Identifier of the user who initiated the transaction.
    """

    warehouse_id: int
    product_id: int
    batch_number: str = Field(default="DEFAULT", max_length=50)
    transaction_type: InventoryTransactionType
    quantity: int = Field(...)
    unit_cost_snapshot: Decimal | None = Field(
        default=None, max_digits=10, decimal_places=2
    )
    reference_type: str | None = Field(default=None, max_length=50)
    reference_id: int | None = None
    remarks: str | None = None
    created_by: int | None = None


class InventoryTransactionResponse(BaseModel):
    """Represent a ledger entry returned to clients for audit and history views.

    Used in API responses providing the historical record of stock movements.

    Attributes:
        id (int): Unique identifier of the transaction record.
        warehouse_id (int): Identifier of the warehouse involved.
        product_id (int): Identifier of the product involved.
        batch_number (str): Batch identifier involved in the transaction.
        transaction_type (InventoryTransactionType): Category of the movement.
        quantity (int): The recorded change in stock.
        unit_cost_snapshot (Decimal | None): Cost recorded during this movement.
        reference_type (str | None): The linked document type.
        reference_id (int | None): The linked document identifier.
        remarks (str | None): Explanatory notes provided during creation.
        created_by (int | None): User who executed the action.
        created_at (datetime): Timestamp when the transaction was recorded.
        updated_at (datetime): Timestamp of the last modification.
    """

    id: int
    warehouse_id: int
    product_id: int
    batch_number: str
    transaction_type: InventoryTransactionType
    quantity: int
    unit_cost_snapshot: Decimal | None
    reference_type: str | None
    reference_id: int | None
    remarks: str | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
