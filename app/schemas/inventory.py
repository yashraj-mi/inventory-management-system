"""
Provide schemas for inventory tracking and stock adjustments.

This module contains Pydantic models for managing stock levels of products
within specific warehouses, including creation, manual adjustments, and responses.
"""

from datetime import date, datetime
from pydantic import BaseModel, Field

from app.constants.inventory_enum import InventoryStatus, InventoryTransactionType


class InventoryCreate(BaseModel):
    """Represent the payload for creating a new inventory record.

    Used when adding a new product or batch to a warehouse for the first time.

    Attributes:
        warehouse_id (int): Identifier of the warehouse holding the stock.
        product_id (int): Identifier of the product being stocked.
        batch_number (str): The lot or batch identifier, defaults to "DEFAULT".
        quantity (int): Initial quantity of stock available.
        reserved_quantity (int): Quantity set aside for pending orders.
        reorder_level (int): Threshold at which a new order should be triggered.
        status (InventoryStatus): Current operational status of this inventory record.
    """

    warehouse_id: int
    product_id: int
    batch_number: str = Field(default="DEFAULT", max_length=50)
    quantity: int = Field(default=0, ge=0)
    reserved_quantity: int = Field(default=0, ge=0)
    reorder_level: int = Field(default=0, ge=0)
    status: InventoryStatus = InventoryStatus.ACTIVE


class InventoryAdjustPayload(BaseModel):
    """Represent the payload for manual API stock corrections.

    Used in request bodies for endpoints that adjust stock up or down (e.g., due to damage, loss, or audits).

    Attributes:
        delta_quantity (int): The amount to add (positive) or remove (negative) from stock.
        transaction_type (InventoryTransactionType): Reason classification for this adjustment.
        remarks (str | None): Optional notes explaining the adjustment context.
    """

    delta_quantity: int = Field(
        ..., description="The amount to add (positive) or remove (negative) from stock."
    )
    transaction_type: InventoryTransactionType
    remarks: str | None = None


class InventoryUpdate(BaseModel):
    """Represent the payload for updating inventory record metadata.

    Used in request bodies for modifying parameters like reorder levels or expiry dates,
    but NOT for updating quantity (which requires an adjustment transaction).

    Attributes:
        batch_number (str | None): Updated batch or lot number.
        expiry_date (date | None): Updated expiration date for the stock.
        reserved_quantity (int | None): Updated quantity set aside for orders.
        reorder_level (int | None): Updated threshold for restocking alerts.
        status (InventoryStatus | None): Updated operational status of the inventory.
    """

    batch_number: str | None = Field(default=None, max_length=50)
    expiry_date: date | None = None
    reserved_quantity: int | None = Field(default=None, ge=0)
    reorder_level: int | None = Field(default=None, ge=0)
    status: InventoryStatus | None = None


class InventoryResponse(BaseModel):
    """Represent an inventory record returned to clients.

    Used in response bodies to provide complete stock information for a product
    in a specific warehouse and batch.

    Attributes:
        id (int): Unique identifier of the inventory record.
        warehouse_id (int): Identifier of the warehouse holding the stock.
        product_id (int): Identifier of the product.
        batch_number (str): The lot or batch identifier.
        expiry_date (date | None): Date when the stock expires, if applicable.
        quantity (int): Current available stock count.
        reserved_quantity (int): Stock currently reserved for pending orders.
        reorder_level (int | None): Configured threshold for restocking alerts.
        status (InventoryStatus): Current operational status.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp of the last modification.
    """

    id: int
    warehouse_id: int
    product_id: int
    batch_number: str
    expiry_date: date | None
    quantity: int
    reserved_quantity: int
    reorder_level: int | None
    status: InventoryStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
