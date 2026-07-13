"""
Provide schemas for backorder-related data validation and formatting.

This module defines Pydantic models for creating and representing backorders,
which track items that are out of stock but requested in sales orders.
"""

from datetime import date, datetime
from pydantic import BaseModel, Field
from app.constants.sales_order_enum import BackorderStatus


class BackorderCreate(BaseModel):
    """Define the required fields for creating a new backorder.

    Used in request bodies or internal service calls when a sales order
    contains products that cannot be fully fulfilled from current inventory.

    Attributes:
        sales_order_id (int): Identifier of the sales order triggering the backorder.
        warehouse_id (int): Identifier of the warehouse where stock is missing.
        product_id (int): Identifier of the out-of-stock product.
        quantity_pending (int): Number of units still needed, must be greater than 0.
        expected_by (date | None): Optional estimated date when stock will arrive.
        status (BackorderStatus): Current state of the backorder, defaults to WAITING.
    """

    sales_order_id: int
    warehouse_id: int
    product_id: int
    quantity_pending: int = Field(..., gt=0)
    expected_by: date | None = None
    status: BackorderStatus = BackorderStatus.WAITING


class BackorderResponse(BaseModel):
    """Represent a backorder entity returned in API responses.

    Used to serialize backorder data from the database to clients.

    Attributes:
        id (int): Unique identifier of the backorder.
        sales_order_id (int): Identifier of the related sales order.
        warehouse_id (int): Identifier of the warehouse.
        product_id (int): Identifier of the product on backorder.
        quantity_pending (int): Remaining quantity waiting to be fulfilled.
        expected_by (date | None): Estimated fulfillment date, if known.
        status (BackorderStatus): Current progression state of the backorder.
        created_at (datetime): Timestamp when the backorder was first recorded.
        updated_at (datetime): Timestamp of the most recent change.
    """

    id: int
    sales_order_id: int
    warehouse_id: int
    product_id: int
    quantity_pending: int
    expected_by: date | None
    status: BackorderStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
