"""Define enumerations for system user roles.

Provides standardized role definitions and messages used to manage
user authentication, authorization, and administrative actions.
"""

from enum import Enum


class UserRole(str, Enum):
    """Represent the permission level and access role of a user.

    Determines what actions a user can take in the system, ranging from
    global platform management (SUPER_ADMIN) to specific warehouse duties.
    """

    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    WAREHOUSE_MANAGER = "warehouse_manager"
    WAREHOUSE_STAFF = "warehouse_staff"


class UserMessages(str, Enum):
    """Represent standard messages for User operations.

    Currently serves as a placeholder for user-specific success or error
    messages to maintain consistency across the app.
    """

    pass
