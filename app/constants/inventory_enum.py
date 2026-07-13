"""Define enumerations for inventory management.

Provides statuses and transaction types critical to tracking stock levels,
batch conditions, and inventory movements throughout the system.
"""

from enum import Enum


class InventoryStatus(str, Enum):
    """Represent the physical or operational condition of an inventory batch.

    Used to determine if stock can be sold, needs to be thrown away, or is
    currently quarantined for quality inspection.
    """

    ACTIVE = "active"
    EXPIRED = "expired"
    DEPLETED = "depleted"
    DAMAGED = "damaged"
    QUARANTINED = "quarantined"
    DISPOSED = "disposed"


class InventoryTransactionType(str, Enum):
    """Represent the business reason behind an inventory stock movement.

    Records the nature of a change in quantity, allowing for accurate
    auditing and historical tracking of stock adjustments.
    """

    PURCHASE = "purchase"
    SALE = "sale"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    ADJUSTMENT = "adjustment"
    RETURN = "return"
    DISPOSAL = "disposal"


class InventoryMessages(str, Enum):
    """Represent standard messages for inventory operations.

    Used by services to communicate success and failure scenarios regarding
    stock level modifications and batch existence.
    """

    # Success Messages
    ADJUSTED_SUCCESSFULLY = "Stock adjusted successfully."

    # Error Messages
    DIRECT_UPDATE_FORBIDDEN = (
        "Direct quantity updates are forbidden. Use the adjust stock method."
    )
    ZERO_DELTA = "Delta quantity cannot be zero."
    INSUFFICIENT_STOCK = "Insufficient stock to complete this transaction."
    NON_EXISTENT_BATCH = "Cannot deduct stock from a non-existent batch."


class InventoryTransactionMessages(str, Enum):
    """Represent messages specifically for inventory transaction logging.

    Used when recording or retrieving historical movements of stock.
    """

    # Success Messages
    LOGGED_SUCCESSFULLY = "Inventory transaction logged successfully."
    RETRIEVED_SUCCESSFULLY = "Inventory transaction retrieved successfully."
    RETRIEVED_ALL_SUCCESSFULLY = "Transactions retrieved successfully."
