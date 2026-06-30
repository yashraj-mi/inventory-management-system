from enum import Enum


class UserRole(str, Enum):
    """
    Enum representing the different roles a user can have in the system.
    """

    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    WAREHOUSE_MANAGER = "warehouse_manager"
    WAREHOUSE_STAFF = "warehouse_staff"
