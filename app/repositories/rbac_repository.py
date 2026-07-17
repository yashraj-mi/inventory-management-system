"""
RBAC Repository module.

Provides database access operations for roles, permissions, and user role assignments.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.rbac import UserRole, RolePermission, Permission, Role


class RbacRepository:
    """
    Repository for handling Role-Based Access Control (RBAC) database queries.
    """

    async def get_user_permissions(
        self,
        db: AsyncSession,
        user_id: int,
        org_id: int | None,
        warehouse_id: int | None = None,
    ) -> set[str]:
        """
        Get all permission codes assigned to a specific user within a given organization and warehouse.

        Args:
            db (AsyncSession): The database session.
            user_id (int): The ID of the user.
            org_id (int | None): The ID of the organization context.
            warehouse_id (int | None, optional): The ID of the warehouse context.

        Returns:
            set[str]: A set of permission code strings.
        """
        query = (
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(
                UserRole.user_id == user_id,
                UserRole.org_id == org_id,
            )
        )
        if warehouse_id is not None:
            query = query.where(
                (UserRole.warehouse_id == warehouse_id)
                | (UserRole.warehouse_id.is_(None))
            )
        result = await db.execute(query)
        return set(result.scalars().all())

    async def has_platform_role(
        self, db: AsyncSession, user_id: int, role_name: str
    ) -> bool:
        """Checks if a user has a platform-wide role (org_id is None)."""
        query = (
            select(UserRole.id)
            .join(Role, Role.id == UserRole.role_id)
            .where(
                UserRole.user_id == user_id,
                UserRole.org_id.is_(None),
                Role.name == role_name,
            )
            .limit(1)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_role_by_name(self, db: AsyncSession, role_name: str) -> Role | None:
        """Fetches a role by its name."""
        query = select(Role).where(Role.name == role_name)
        result = await db.execute(query)
        return result.scalar_one_or_none()
