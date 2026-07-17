"""
Provide schemas for sales order processing and fulfillment.

This module contains Pydantic models for managing customer orders, tracking
items requested from specific warehouses, and updating order fulfillment statuses.
"""

from datetime import date, datetime
from pydantic import BaseModel, Field
from decimal import Decimal
from app.constants.sales_order_enum import SalesOrderStatus


class SalesOrderItemCreate(BaseModel):
    """Represent an individual product line item in a sales order.

    Used as a nested model when submitting a new customer order.

    Attributes:
        product_id (int): Identifier of the product being sold.
        quantity (int): Number of units requested.
        unit_price (Decimal): Agreed selling price per unit.
        batch_number (str | None): Optional specific batch to fulfill from.
    """

    product_id: int
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0)
    batch_number: str | None = None


class SalesOrderCreate(BaseModel):
    """Represent the payload for creating a new sales order via API.

    Used in request bodies by sales staff to log a new customer purchase.

    Attributes:
        customer_id (int): Identifier of the purchasing customer.
        source_warehouse_id (int): Identifier of the warehouse fulfilling the order.
        due_date (date | None): Expected delivery or fulfillment date.
        items (list[SalesOrderItemCreate]): Products and quantities ordered.
    """

    customer_id: int
    source_warehouse_id: int
    due_date: date | None = None
    items: list[SalesOrderItemCreate]


class SalesOrderCreateInternal(BaseModel):
    """Represent the payload for internal creation of a sales order.

    Used by the service layer to append system-managed context before persisting.

    Attributes:
        customer_id (int): Identifier of the customer.
        source_warehouse_id (int): Identifier of the fulfilling warehouse.
        due_date (date | None): Expected fulfillment date.
        status (SalesOrderStatus): Initial state of the order, defaults to DRAFT.
        created_by (int): Identifier of the user creating the order.
        actor_org_id (int): Organization context of the creator.
        items (list[SalesOrderItemCreate]): Products and quantities ordered.
    """

    customer_id: int
    source_warehouse_id: int
    due_date: date | None = None
    status: SalesOrderStatus = SalesOrderStatus.DRAFT
    created_by: int
    actor_org_id: int
    items: list[SalesOrderItemCreate]


class SalesOrderItemCreateInternal(BaseModel):
    """Represent the payload for internally linking items to a sales order.

    Attributes:
        sales_order_id (int): Parent order identifier.
        items (list[SalesOrderItemCreate]): Items to associate with the order.
    """

    sales_order_id: int
    items: list[SalesOrderItemCreate]


class SalesOrderStatusUpdate(BaseModel):
    """Represent the payload for modifying the status of a sales order.

    Used to transition orders through their lifecycle (e.g., DRAFT to APPROVED).

    Attributes:
        status (SalesOrderStatus): The target operational state.
    """

    status: SalesOrderStatus


class SalesOrderItemResponse(BaseModel):
    """Represent an individual sales order line item in responses.

    Used to serialize item progress, including fulfillment tracking.

    Attributes:
        id (int): Unique identifier of the line item.
        sales_order_id (int): Identifier of the parent sales order.
        product_id (int): Identifier of the product.
        batch_number (str | None): Specific batch assigned, if any.
        quantity (int): Total requested quantity.
        unit_price (Decimal): Selling price per unit.
        fulfilled_quantity (int): Quantity successfully picked/shipped so far.
        created_at (datetime): Timestamp of creation.
        updated_at (datetime): Timestamp of last update.
    """

    id: int
    sales_order_id: int
    product_id: int
    batch_number: str | None
    quantity: int
    unit_price: Decimal
    fulfilled_quantity: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SalesOrderResponse(BaseModel):
    """Represent a complete sales order returned to clients.

    Used in API responses to provide order details, fulfillment status, and items.

    Attributes:
        id (int): Unique identifier of the sales order.
        customer_id (int): Identifier of the purchasing customer.
        source_warehouse_id (int): Identifier of the fulfilling warehouse.
        order_number (str): Auto-generated human-readable order reference.
        due_date (date | None): Expected fulfillment deadline.
        status (SalesOrderStatus): Current operational state of the order.
        created_by (int | None): User who recorded the order.
        created_at (datetime): Timestamp of creation.
        updated_at (datetime): Timestamp of last update.
        items (list[SalesOrderItemResponse]): Nested list of order items.
    """

    id: int
    customer_id: int
    source_warehouse_id: int
    order_number: str
    due_date: date | None
    status: SalesOrderStatus
    created_by: int | None
    created_at: datetime
    updated_at: datetime
    items: list[SalesOrderItemResponse] = []

    model_config = {"from_attributes": True}


class PartiallyFulfillItem(BaseModel):
    """Represent an individual item being fulfilled from warehouse stock.

    Attributes:
        product_id (int): Identifier of the product being picked/shipped.
        quantity (int): Amount successfully fulfilled in this action.
    """

    product_id: int
    quantity: int = Field(..., gt=0)


class PartiallyFulfillPayload(BaseModel):
    """Represent the payload for recording fulfillment progress against an order.

    Used when warehouse staff pack or ship portions of a sales order.

    Attributes:
        items (list[PartiallyFulfillItem]): List of products and quantities fulfilled.
    """

    items: list[PartiallyFulfillItem]
