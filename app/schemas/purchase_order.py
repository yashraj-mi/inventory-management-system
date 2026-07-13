"""
Provide schemas for purchase order lifecycle management.

This module defines Pydantic models for creating, receiving, and monitoring
purchase orders that procure inventory from suppliers into specific warehouses.
"""

from datetime import datetime
from pydantic import BaseModel, Field

from app.constants.purchase_order_enum import PurchaseOrderStatus


class OrderItem(BaseModel):
    """Represent an individual item within a purchase order request.

    Used as a nested model when submitting product quantities for purchase.

    Attributes:
        product_id (int): Identifier of the product being ordered.
        quantity (int): Number of units requested.
    """

    product_id: int
    quantity: int


class PurchaseOrderCreate(BaseModel):
    """Represent the payload for creating a new purchase order via API.

    Used in request bodies by warehouse managers to initiate a new procurement request
    from a supplier to a destination warehouse.

    Attributes:
        supplier_id (int): Identifier of the supplier providing the goods.
        destination_warehouse_id (int): Identifier of the receiving warehouse.
        items (list[OrderItem]): List of products and quantities to order.
    """

    supplier_id: int
    destination_warehouse_id: int
    items: list[OrderItem]


class PurchaseOrderItemCreateInternal(BaseModel):
    """Represent the payload for internal creation of purchase order items.

    Used by background services to link ordered items directly to a generated PO.

    Attributes:
        po_id (int): Identifier of the parent purchase order.
        supplier_id (int): Identifier of the supplier for pricing reference.
        items (list[OrderItem]): List of products and quantities to link.
    """

    po_id: int
    supplier_id: int
    items: list[OrderItem]


class PurchaseOrderItemsUpdate(BaseModel):
    """Represent the payload for updating the item list of an existing PO.

    Used when a draft purchase order's requested quantities or products change.

    Attributes:
        items (list[OrderItem]): Complete updated list of products and quantities.
    """

    items: list[OrderItem]


class PurchaseOrderCreateInternal(PurchaseOrderCreate):
    """Represent the payload for creating a PO with system-managed metadata.

    Used internally by the service layer to attach auto-generated fields and user context
    before saving to the database.

    Attributes:
        po_number (str): Auto-generated unique tracking number for the PO.
        created_by (int): Identifier of the user initiating the PO.
        actor_org_id (int): Organization context derived from the actor.
        status (PurchaseOrderStatus): Initial state of the PO, defaults to DRAFT.
    """

    po_number: str
    created_by: int
    actor_org_id: int
    status: PurchaseOrderStatus = PurchaseOrderStatus.DRAFT


class PurchaseOrderUpdate(BaseModel):
    """Represent the payload for updating PO metadata.

    Used to change the supplier or destination warehouse of a draft purchase order.

    Attributes:
        supplier_id (int | None): New supplier identifier, if updating.
        destination_warehouse_id (int | None): New warehouse destination, if updating.
    """

    supplier_id: int | None = None
    destination_warehouse_id: int | None = None


class ReceiveItemPayload(BaseModel):
    """Represent an individual item being received into stock.

    Used as a nested model when recording warehouse receipts against a PO.

    Attributes:
        product_id (int): Identifier of the product received.
        quantity (int): Number of units received in this specific batch.
    """

    product_id: int
    quantity: int = Field(..., gt=0, description="Amount being received in this batch")


class PartiallyReceivePayload(BaseModel):
    """Represent the payload for recording a partial or full receipt against a PO.

    Used in request bodies by warehouse staff when stock arrives, allowing
    multiple items to be received simultaneously.

    Attributes:
        items (list[ReceiveItemPayload]): List of products and received quantities.
    """

    items: list[ReceiveItemPayload] = Field(..., min_length=1)


class PurchaseOrderStatusUpdate(BaseModel):
    """Represent the payload for updating the status of a PO.

    Used to transition a purchase order through its lifecycle (e.g., from DRAFT to APPROVED).

    Attributes:
        status (PurchaseOrderStatus): The target status state.
    """

    status: PurchaseOrderStatus


class PurchaseOrderItemResponse(BaseModel):
    """Represent an individual purchase order line item in responses.

    Used to serialize item details, including pricing and fulfillment progress.

    Attributes:
        product_id (int): Identifier of the ordered product.
        quantity (int): Total quantity requested.
        unit_price (float): Price per unit agreed for this order.
        received_quantity (int): Quantity successfully received so far.
    """

    product_id: int
    quantity: int
    unit_price: float
    received_quantity: int

    model_config = {"from_attributes": True}


class PurchaseOrderResponse(BaseModel):
    """Represent a complete purchase order returned to clients.

    Used in API responses to provide the full context of a procurement request,
    including line items and approval metadata.

    Attributes:
        id (int): Unique identifier of the purchase order.
        supplier_id (int): Identifier of the supplier providing goods.
        destination_warehouse_id (int): Identifier of the receiving warehouse.
        po_number (str): Human-readable unique PO reference number.
        status (PurchaseOrderStatus): Current lifecycle state.
        items (list[PurchaseOrderItemResponse]): Nested list of order line items.
        created_by (int | None): User who originally created the draft.
        approved_by (int | None): User who authorized the order.
        approved_at (datetime | None): Timestamp of authorization.
        created_at (datetime): Timestamp of initial creation.
        updated_at (datetime): Timestamp of the last modification.
    """

    id: int
    supplier_id: int
    destination_warehouse_id: int
    po_number: str
    status: PurchaseOrderStatus
    items: list[PurchaseOrderItemResponse]
    created_by: int | None
    approved_by: int | None
    approved_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
