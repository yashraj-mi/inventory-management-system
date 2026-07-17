"""Define constants and enumerations for the Purchase Order domain.

Provides status states, allowed transition flows, and standardized messages
necessary for tracking external supplier orders and receiving workflows.
"""

from enum import Enum


class PurchaseOrderStatus(str, Enum):
    """Represent the operational lifecycle status of a purchase order.

    Used to enforce business rules restricting modifications and controlling
    when a purchase order can be received into inventory.
    """

    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    ORDERED = "ordered"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"


po_allowed_transitions = {
    PurchaseOrderStatus.DRAFT: [
        PurchaseOrderStatus.PENDING_APPROVAL,
        PurchaseOrderStatus.CANCELLED,
    ],
    PurchaseOrderStatus.PENDING_APPROVAL: [
        PurchaseOrderStatus.APPROVED,
        PurchaseOrderStatus.CANCELLED,
    ],
    PurchaseOrderStatus.APPROVED: [
        PurchaseOrderStatus.ORDERED,
        PurchaseOrderStatus.CANCELLED,
    ],
    PurchaseOrderStatus.ORDERED: [
        PurchaseOrderStatus.PARTIALLY_RECEIVED,
        PurchaseOrderStatus.RECEIVED,
    ],
    PurchaseOrderStatus.PARTIALLY_RECEIVED: [
        PurchaseOrderStatus.PARTIALLY_RECEIVED,
        PurchaseOrderStatus.RECEIVED,
    ],
    PurchaseOrderStatus.RECEIVED: [],
    PurchaseOrderStatus.CANCELLED: [],
}


class PurchaseOrderMessages(str, Enum):
    """Represent standardized messages for Purchase Order operations.

    Used by the purchase order service to communicate results of state transitions,
    item updates, receiving actions, and error handling for unauthorized actions.
    """

    # Success Messages
    STATUS_UPDATED = "Purchase Order status updated successfully."
    ITEMS_UPDATED = "Purchase Order items updated successfully."
    RECEIVED_SUCCESSFULLY = "Order received successfully."
    PARTIALLY_RECEIVED = "Order partially received successfully."

    # Error Messages
    NOT_DRAFT_UPDATE = "Cannot update a purchase order that is not in draft status."
    NOT_DRAFT_DELETE = "Cannot delete a purchase order unless it is in draft status. Consider cancelling it instead."
    PENDING_APPROVAL_UNAUTHORIZED = "Only a warehouse manager can modify order items when the order is pending approval."
    UPDATE_INVALID_STATUS = (
        "Cannot update items for a purchase order in '{status}' status."
    )
    INVALID_PRODUCTS = (
        "Product(s) {invalid_product_ids} are not part of this purchase order."
    )
    OVER_RECEIVE = "Cannot receive {amount_to_receive} for product {product_id}. Only {remaining} remaining."
    ALREADY_RECEIVED = "Purchase Order is already marked as received."
    INVALID_RECEIVE_STATUS = (
        "Purchase Order must be Approved or Partially Received to mark it as received."
    )
    ALL_ITEMS_RECEIVED = "All items are already fully received."
    PARTIAL_RECEIVE_INVALID_STATUS = (
        "Purchase Order must be Approved or Partially Received to receive items."
    )

    def format(self, **kwargs) -> str:
        """Inject context variables dynamically into the message string.

        Args:
            **kwargs: Dynamic variables like product ids, statuses, or amounts.

        Returns:
            str: The formatted message string.
        """
        return self.value.format(**kwargs)
