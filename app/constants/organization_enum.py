"""
organization_enum.py module.

Provides core functionality and components for the organization_enum domain.
"""

from enum import Enum


class OrganizationStatus(str, Enum):
    """
    Enum representing the lifecycle status of an organization.
    """

    PENDING = "pending"  # still pending to check
    REJECTED = "rejected"  # rejected by platform admin (super admin)
    ACTIVE = "active"  # approved and active
    INACTIVE = "in_active"  # soft delete


class OrganizationMessages(str, Enum):
    # --- Success Response Messages (Router Layer) ---
    """
    Represents the OrganizationMessages component.
    """

    REGISTERED_SUCCESSFULLY = "Organization registered successfully. Awaiting approval."
    DETAILS_RETRIEVED = "Organization details retrieved successfully."
    LIST_RETRIEVED = "List of all organizations retrieved successfully."
    STATUS_UPDATED = "Organization status updated successfully."
    APPROVED_SUCCESSFULLY = (
        "Organization approved successfully. Default admin account created."
    )
    REJECTED_SUCCESSFULLY = "Organization rejected successfully."
    DELETED_SUCCESSFULLY = "Organization deleted successfully."

    # --- Error Response Messages (Service Layer) ---
    ALREADY_EXISTS = "An organization with this name or email already exists."
    NOT_FOUND = "Organization not found."
    INVALID_TRANSITION = "Cannot transition from '{current}' to '{target}'."

    # --- Database Transaction Failures ---
    DB_CONSTRAINT_UPDATE = (
        "Failed to update organization status due to a database constraint violation."
    )
    DB_CONSTRAINT_APPROVE = (
        "Failed to approve organization due to a database constraint violation."
    )
    DB_CONSTRAINT_REJECT = (
        "Failed to reject organization due to a database constraint violation."
    )
    DB_RELATIONAL_CONSTRAINTS = (
        "Cannot delete organization due to existing relational constraints."
    )
    DB_UNEXPECTED_REGISTRATION = (
        "An unexpected database error occurred during organization registration."
    )
    DB_UNEXPECTED_UPDATE = "An unexpected database error occurred during status update."
    DB_UNEXPECTED_APPROVAL = (
        "An unexpected database error occurred during organization approval."
    )
    DB_UNEXPECTED_REJECTION = (
        "An unexpected database error occurred during organization rejection."
    )
    DB_UNEXPECTED_DELETION = (
        "An unexpected database error occurred during organization deletion."
    )

    def format(self, **kwargs) -> str:
        """
        Dynamically inject context variables into the enum message string.
        """
        return self.value.format(**kwargs)
