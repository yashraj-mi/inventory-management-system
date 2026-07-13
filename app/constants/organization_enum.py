"""Define enumerations for organizational workflows.

Provides standard statuses and message templates related to the lifecycle
of organization accounts, including registration, approval, and rejections.
"""

from enum import Enum


class OrganizationStatus(str, Enum):
    """Represent the lifecycle status of an organization account.

    Determines if an organization can operate within the system, requires
    super admin approval, or has been denied access.
    """

    PENDING = "pending"  # still pending to check
    REJECTED = "rejected"  # rejected by platform admin (super admin)
    ACTIVE = "active"  # approved and active
    INACTIVE = "in_active"  # soft delete


class OrganizationMessages(str, Enum):
    """Represent standardized messages for organization operations.

    Used primarily in routing and service layers to provide clear feedback
    on status transitions, database errors, and duplicated entries.
    """

    # --- Success Response Messages (Router Layer) ---
    REGISTERED_SUCCESSFULLY = "Organization registered successfully. Awaiting approval."
    STATUS_UPDATED = "Organization status updated successfully."
    APPROVED_SUCCESSFULLY = (
        "Organization approved successfully. Default admin account created."
    )
    REJECTED_SUCCESSFULLY = "Organization rejected successfully."

    # --- Error Response Messages (Service Layer) ---
    ALREADY_EXISTS = "An organization with this name or email already exists."
    INVALID_TRANSITION = "Cannot transition from '{current}' to '{target}'."

    # --- Database Transaction Failures ---
    DB_CONSTRAINT_APPROVE = (
        "Failed to approve organization due to a database constraint violation."
    )
    DB_CONSTRAINT_REJECT = (
        "Failed to reject organization due to a database constraint violation."
    )
    DB_UNEXPECTED_APPROVAL = (
        "An unexpected database error occurred during organization approval."
    )
    DB_UNEXPECTED_REJECTION = (
        "An unexpected database error occurred during organization rejection."
    )

    def format(self, **kwargs) -> str:
        """Inject context variables dynamically into the message string.

        Args:
            **kwargs: Dynamic variables like current and target statuses.

        Returns:
            str: The formatted message string.
        """
        return self.value.format(**kwargs)
