"""
Centralized permission definitions for Role-Based Access Control (RBAC).

This module defines all granular permissions across the entire Inventory Management System.
These permissions can be assigned to roles or directly to users.
"""


class Permissions:
    """
    Constant registry of all granular permission strings used for RBAC checks.
    """

    # --- Organizations ---
    ORGANIZATION_CREATE = "organization:create"
    ORGANIZATION_READ = "organization:read"
    ORGANIZATION_UPDATE = "organization:update"
    ORGANIZATION_DELETE = "organization:delete"
    ORGANIZATION_UPDATE_STATUS = "organization:update_status"

    # --- Users ---
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # --- Categories ---
    CATEGORY_CREATE = "category:create"
    CATEGORY_READ = "category:read"
    CATEGORY_UPDATE = "category:update"
    CATEGORY_DELETE = "category:delete"

    # --- Products ---
    PRODUCT_CREATE = "product:create"
    PRODUCT_READ = "product:read"
    PRODUCT_UPDATE = "product:update"
    PRODUCT_DELETE = "product:delete"

    # --- Suppliers ---
    SUPPLIER_CREATE = "supplier:create"
    SUPPLIER_READ = "supplier:read"
    SUPPLIER_UPDATE = "supplier:update"
    SUPPLIER_DELETE = "supplier:delete"

    # --- Customers ---
    CUSTOMER_CREATE = "customer:create"
    CUSTOMER_READ = "customer:read"
    CUSTOMER_UPDATE = "customer:update"
    CUSTOMER_DELETE = "customer:delete"

    # --- Warehouses ---
    WAREHOUSE_CREATE = "warehouse:create"
    WAREHOUSE_READ = "warehouse:read"
    WAREHOUSE_UPDATE = "warehouse:update"
    WAREHOUSE_DELETE = "warehouse:delete"

    # --- Warehouse Users ---
    WAREHOUSE_USER_ASSIGN = "warehouse_user:assign"
    WAREHOUSE_USER_REMOVE = "warehouse_user:remove"
    WAREHOUSE_USER_READ = "warehouse_user:read"

    # --- Inventory ---
    INVENTORY_CREATE = "inventory:create"
    INVENTORY_READ = "inventory:read"
    INVENTORY_UPDATE = "inventory:update"
    INVENTORY_DELETE = "inventory:delete"
    INVENTORY_ADJUST = "inventory:adjust"

    # --- Inventory Transactions ---
    INVENTORY_TRANSACTION_CREATE = "inventory_transaction:create"
    INVENTORY_TRANSACTION_READ = "inventory_transaction:read"

    # --- Purchase Orders ---
    PURCHASE_ORDER_CREATE = "purchase_order:create"
    PURCHASE_ORDER_READ = "purchase_order:read"
    PURCHASE_ORDER_UPDATE = "purchase_order:update"
    PURCHASE_ORDER_DELETE = "purchase_order:delete"
    PURCHASE_ORDER_UPDATE_STATUS = "purchase_order:update_status"
    PURCHASE_ORDER_RECEIVE = "purchase_order:receive"
    PURCHASE_ORDER_UPDATE_ITEMS = "purchase_order:update_items"

    # --- Sales Orders ---
    SALES_ORDER_CREATE = "sales_order:create"
    SALES_ORDER_READ = "sales_order:read"
    SALES_ORDER_UPDATE = "sales_order:update"
    SALES_ORDER_DELETE = "sales_order:delete"
    SALES_ORDER_UPDATE_STATUS = "sales_order:update_status"
    SALES_ORDER_FULFILL = "sales_order:fulfill"

    # --- Backorders ---
    BACKORDER_CREATE = "backorder:create"
    BACKORDER_READ = "backorder:read"
    BACKORDER_UPDATE = "backorder:update"
    BACKORDER_DELETE = "backorder:delete"
    BACKORDER_SETTLE = "backorder:settle"
    BACKORDER_CANCEL = "backorder:cancel"

    # --- Product Suppliers (Mapping) ---
    PRODUCT_SUPPLIER_CREATE = "product_supplier:create"
    PRODUCT_SUPPLIER_READ = "product_supplier:read"
    PRODUCT_SUPPLIER_UPDATE = "product_supplier:update"
    PRODUCT_SUPPLIER_DELETE = "product_supplier:delete"

    # Roles
    ROLE_CREATE = "role:create"
    ROLE_READ = "role:read"
    ROLE_UPDATE = "role:update"
    ROLE_DELETE = "role:delete"

    # Permissions
    PERMISSION_CREATE = "permission:create"
    PERMISSION_READ = "permission:read"
    PERMISSION_UPDATE = "permission:update"
    PERMISSION_DELETE = "permission:delete"

    # User Role Assignment
    USER_ROLE_ASSIGN = "user_role:assign"
    USER_ROLE_REMOVE = "user_role:remove"
    USER_ROLE_READ = "user_role:read"

    @classmethod
    def all(cls) -> list[str]:
        """
        Retrieve all defined permissions.

        Returns:
            A list of all permission strings defined in this class.
        """
        return [
            v
            for k, v in vars(cls).items()
            if not k.startswith("_") and isinstance(v, str)
        ]
