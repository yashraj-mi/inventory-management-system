"""Define constants and enumerations for the Sales Order domain.

Provides status states, allowed transition flows, and standardized messages
necessary for handling outbound customer orders and backorders.
"""

from enum import Enum


class SalesOrderStatus(str, Enum):
    """Represent the operational lifecycle status of a sales order.

    Used to enforce business rules restricting modifications and controlling
    when a sales order can be fulfilled from inventory.
    """

    DRAFT = "draft"
    PENDING = "pending"
    AWAITING_CONFIRMED = "awaiting_confirmed"
    CONFIRMED = "confirmed"
    PARTIALLY_FULFILLED = "partially_fulfilled"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"


class BackorderStatus(str, Enum):
    """Represent the lifecycle status of a backorder.

    Indicates whether a backorder is still waiting for stock or has
    been successfully allocated.
    """

    WAITING = "waiting"
    ALLOCATED = "allocated"
    CANCELLED = "cancelled"


so_allowed_transitions = {
    SalesOrderStatus.DRAFT: [SalesOrderStatus.PENDING, SalesOrderStatus.CANCELLED],
    SalesOrderStatus.PENDING: [
        SalesOrderStatus.AWAITING_CONFIRMED,
        SalesOrderStatus.CONFIRMED,
        SalesOrderStatus.CANCELLED,
    ],
    SalesOrderStatus.AWAITING_CONFIRMED: [
        SalesOrderStatus.CONFIRMED,
        SalesOrderStatus.CANCELLED,
    ],
    SalesOrderStatus.CONFIRMED: [
        SalesOrderStatus.PARTIALLY_FULFILLED,
        SalesOrderStatus.FULFILLED,
        SalesOrderStatus.CONFIRMED,
    ],
    SalesOrderStatus.PARTIALLY_FULFILLED: [
        SalesOrderStatus.PARTIALLY_FULFILLED,
        SalesOrderStatus.FULFILLED,
    ],
    SalesOrderStatus.FULFILLED: [],
    SalesOrderStatus.CANCELLED: [],
}

bo_allowed_transitions = {
    BackorderStatus.WAITING: [BackorderStatus.ALLOCATED, BackorderStatus.CANCELLED],
    BackorderStatus.ALLOCATED: [],
    BackorderStatus.CANCELLED: [],
}


class SalesOrderMessages(str, Enum):
    """Represent standardized messages for Sales Order operations.

    Used by the sales order service to communicate results of state transitions,
    item updates, fulfillment actions, and error handling for unauthorized actions.
    """

    # Success Messages
    STATUS_UPDATED = "Status changed successfully"
    FULFILLED_SUCCESSFULLY = "Order fulfilled successfully."
    PARTIALLY_FULFILLED = "Order partially fulfilled successfully."

    # Error Messages
    NOT_DRAFT_UPDATE = "Cannot update a sales order that is not in draft status."
    NOT_DRAFT_DELETE = "Cannot delete a sales order unless it is in draft status. Consider cancelling it instead."
    PENDING_UNAUTHORIZED = (
        "Only a warehouse manager can modify order items when the order is pending."
    )
    UPDATE_INVALID_STATUS = (
        "Cannot update items for a sales order in '{status}' status."
    )
    INVALID_PRODUCTS = (
        "Product(s) {invalid_product_ids} are not part of this sales order."
    )
    OVER_FULFILL = "Cannot fulfill {amount_to_fulfill} for product {product_id}. Only {remaining} remaining."
    ALREADY_FULFILLED = "Sales Order is already marked as fulfilled."
    INVALID_FULFILL_STATUS = (
        "Sales Order must be Confirmed or Partially Fulfilled to mark it as fulfilled."
    )
    ALL_ITEMS_FULFILLED = "All items are already fully fulfilled."
    PARTIAL_FULFILL_INVALID_STATUS = (
        "Sales Order must be Confirmed or Partially Fulfilled to fulfill items."
    )
    NOT_ENOUGH_STOCK = (
        "Not enough stock to fulfill {amount_to_fulfill} for product {product_id}."
    )

    def format(self, **kwargs) -> str:
        """Inject context variables dynamically into the message string.

        Args:
            **kwargs: Dynamic variables like product ids, statuses, or amounts.

        Returns:
            str: The formatted message string.
        """
        return self.value.format(**kwargs)


class BackorderMessages(str, Enum):
    """Represent standardized messages for Backorder operations.

    Used by the backorder service to communicate results of database operations.
    """

    CREATE_FK_ERROR = "Error with foreign key constraints while creating Backorder"
    CREATE_UNEXPECTED_ERROR = "Unexpected error while creating Backorder"
