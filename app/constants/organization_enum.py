from enum import Enum


class OrganizationStatus(str, Enum):
    """
    Enum representing the lifecycle status of an organization.
    """

    PENDING = "pending"  # still pending to check
    REJECTED = "rejected"  # rejected by platform admin (super admin)
    ACTIVE = "active"  # approved and active
    INACTIVE = "in_active"  # soft delete
