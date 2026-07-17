"""
RBAC Models module.

Defines SQLAlchemy ORM models for roles, permissions, and their assignments.
"""

from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.db.models.user import User


class Role(Base):
    """
    Represents a role within the system.
    """

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(50), unique=True
    )  # "org_admin", "warehouse_staff"
    is_system_role: Mapped[bool] = mapped_column(
        default=True
    )  # False = org-custom role


class Permission(Base):
    """
    Represents a granular permission for a specific action.
    """

    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(
        String(100), unique=True
    )  # "product:create", "sales_order:approve"
    description: Mapped[str] = mapped_column(String(255))


class RolePermission(Base):
    """
    Mapping table linking roles to their granted permissions.
    """

    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id"))


class UserRole(Base):
    """Assigns a role to a user, scoped to an org (and optionally a warehouse)."""

    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", "org_id", "warehouse_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    org_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id"), nullable=True
    )
    warehouse_id: Mapped[int | None] = mapped_column(
        ForeignKey("warehouses.id"), nullable=True
    )

    user: Mapped["User"] = relationship("User", back_populates="user_roles")
    role: Mapped["Role"] = relationship("Role", lazy="joined")
