"""
Seed RBAC roles, permissions, and role-permission mappings.

System roles:
    - super_admin
    - org_admin
    - inventory_manager
    - purchase_manager
    - sales_executive
    - warehouse_staff

Run:
    uv run python scripts/seed_rbac.py
"""

import asyncio
import os
import sys

# Ensure root directory is available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from app.core.config import get_settings
from app.core.database import AsyncSessionLocal

from app.core.permissions import Permissions
from app.db.models.rbac import Role, Permission, RolePermission


settings = get_settings()


ROLE_PERMISSION_MAP: dict[str, list[str]] = {
    "super_admin": [
        Permissions.ORGANIZATION_CREATE,
        Permissions.ORGANIZATION_READ,
        Permissions.ORGANIZATION_UPDATE,
        Permissions.ORGANIZATION_DELETE,
        Permissions.ORGANIZATION_UPDATE_STATUS,
        Permissions.USER_READ,
        Permissions.ROLE_CREATE,
        Permissions.ROLE_READ,
        Permissions.ROLE_UPDATE,
        Permissions.ROLE_DELETE,
        Permissions.PERMISSION_CREATE,
        Permissions.PERMISSION_READ,
        Permissions.PERMISSION_UPDATE,
        Permissions.PERMISSION_DELETE,
        Permissions.USER_ROLE_ASSIGN,
        Permissions.USER_ROLE_REMOVE,
        Permissions.USER_ROLE_READ,
    ],
    "org_admin": [
        Permissions.ORGANIZATION_READ,
        Permissions.ORGANIZATION_UPDATE,
        Permissions.USER_CREATE,
        Permissions.USER_READ,
        Permissions.USER_UPDATE,
        Permissions.USER_DELETE,
        Permissions.USER_ROLE_ASSIGN,
        Permissions.USER_ROLE_REMOVE,
        Permissions.USER_ROLE_READ,
        Permissions.WAREHOUSE_CREATE,
        Permissions.WAREHOUSE_READ,
        Permissions.WAREHOUSE_UPDATE,
        Permissions.WAREHOUSE_DELETE,
        Permissions.WAREHOUSE_USER_ASSIGN,
        Permissions.WAREHOUSE_USER_REMOVE,
        Permissions.WAREHOUSE_USER_READ,
        Permissions.CATEGORY_CREATE,
        Permissions.CATEGORY_READ,
        Permissions.CATEGORY_UPDATE,
        Permissions.CATEGORY_DELETE,
        Permissions.PRODUCT_CREATE,
        Permissions.PRODUCT_READ,
        Permissions.PRODUCT_UPDATE,
        Permissions.PRODUCT_DELETE,
        Permissions.SUPPLIER_CREATE,
        Permissions.SUPPLIER_READ,
        Permissions.SUPPLIER_UPDATE,
        Permissions.SUPPLIER_DELETE,
        Permissions.CUSTOMER_CREATE,
        Permissions.CUSTOMER_READ,
        Permissions.CUSTOMER_UPDATE,
        Permissions.CUSTOMER_DELETE,
        Permissions.INVENTORY_READ,
        Permissions.INVENTORY_ADJUST,
        Permissions.INVENTORY_TRANSACTION_READ,
        Permissions.PURCHASE_ORDER_READ,
        Permissions.SALES_ORDER_READ,
        Permissions.BACKORDER_READ,
    ],
    "inventory_manager": [
        Permissions.CATEGORY_READ,
        Permissions.PRODUCT_READ,
        Permissions.SUPPLIER_READ,
        Permissions.CUSTOMER_READ,
        Permissions.WAREHOUSE_READ,
        Permissions.INVENTORY_READ,
        Permissions.INVENTORY_ADJUST,
        Permissions.INVENTORY_TRANSACTION_READ,
        Permissions.PURCHASE_ORDER_READ,
        Permissions.SALES_ORDER_READ,
        Permissions.BACKORDER_READ,
    ],
    "purchase_manager": [
        Permissions.PRODUCT_READ,
        Permissions.SUPPLIER_CREATE,
        Permissions.SUPPLIER_READ,
        Permissions.SUPPLIER_UPDATE,
        Permissions.SUPPLIER_DELETE,
        Permissions.PRODUCT_SUPPLIER_CREATE,
        Permissions.PRODUCT_SUPPLIER_READ,
        Permissions.PRODUCT_SUPPLIER_UPDATE,
        Permissions.PRODUCT_SUPPLIER_DELETE,
        Permissions.WAREHOUSE_READ,
        Permissions.INVENTORY_READ,
        Permissions.PURCHASE_ORDER_CREATE,
        Permissions.PURCHASE_ORDER_READ,
        Permissions.PURCHASE_ORDER_UPDATE,
        Permissions.PURCHASE_ORDER_DELETE,
        Permissions.PURCHASE_ORDER_UPDATE_STATUS,
    ],
    "sales_executive": [
        Permissions.PRODUCT_READ,
        Permissions.CUSTOMER_CREATE,
        Permissions.CUSTOMER_READ,
        Permissions.CUSTOMER_UPDATE,
        Permissions.INVENTORY_READ,
        Permissions.WAREHOUSE_READ,
        Permissions.SALES_ORDER_CREATE,
        Permissions.SALES_ORDER_READ,
        Permissions.SALES_ORDER_UPDATE,
        Permissions.SALES_ORDER_UPDATE_STATUS,
        Permissions.BACKORDER_CREATE,
        Permissions.BACKORDER_READ,
    ],
    "warehouse_staff": [
        Permissions.PRODUCT_READ,
        Permissions.WAREHOUSE_READ,
        Permissions.INVENTORY_READ,
        Permissions.INVENTORY_TRANSACTION_READ,
        Permissions.INVENTORY_TRANSACTION_CREATE,
        Permissions.PURCHASE_ORDER_READ,
        Permissions.PURCHASE_ORDER_RECEIVE,
        Permissions.SALES_ORDER_READ,
        Permissions.SALES_ORDER_FULFILL,
        Permissions.BACKORDER_READ,
    ],
}


async def get_or_create_permission(db: AsyncSession, code: str):
    result = await db.execute(select(Permission).where(Permission.code == code))

    permission = result.scalar_one_or_none()

    if permission is None:
        permission = Permission(code=code, description=code.replace(":", " "))

        db.add(permission)

        await db.flush()

        print(f"+ Permission created: {code}")

    return permission


async def get_or_create_role(db: AsyncSession, name: str):
    result = await db.execute(select(Role).where(Role.name == name))

    role = result.scalar_one_or_none()

    if role is None:
        role = Role(name=name, is_system_role=True)

        db.add(role)

        await db.flush()

        print(f"+ Role created: {name}")

    return role


async def assign_permission(db: AsyncSession, role: Role, permission: Permission):
    result = await db.execute(
        select(RolePermission).where(
            RolePermission.role_id == role.id,
            RolePermission.permission_id == permission.id,
        )
    )

    exists = result.scalar_one_or_none()

    if not exists:
        db.add(RolePermission(role_id=role.id, permission_id=permission.id))

        print(f"  {role.name} -> {permission.code}")


async def seed():
    async with AsyncSessionLocal() as db:
        try:
            print("Seeding permissions...")

            permission_map = {}

            for permission_code in Permissions.all():
                permission_map[permission_code] = await get_or_create_permission(
                    db, permission_code
                )

            print("Seeding roles...")

            for role_name, permissions in ROLE_PERMISSION_MAP.items():
                role = await get_or_create_role(db, role_name)

                for permission_code in permissions:
                    await assign_permission(db, role, permission_map[permission_code])

            await db.commit()

            print("--------------------------------")
            print("RBAC seeded successfully")
            print("--------------------------------")

        except Exception as e:
            await db.rollback()

            print(f"RBAC seed failed: {e}")


if __name__ == "__main__":
    asyncio.run(seed())
