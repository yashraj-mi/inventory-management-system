"""
Define the association table between users and warehouses.

Maps the many-to-many relationship dictating which personnel are authorized
to operate within or manage specific storage locations.
"""

from sqlalchemy.orm import mapped_column, Mapped

from sqlalchemy import ForeignKey, UniqueConstraint
from app.db.models.base import BaseModel


class WarehouseUsers(BaseModel):
    """
    Represent the access authorization mapping for users to warehouses.

    This association table enforces location-based access control, ensuring a user
    can only view or manipulate inventory at facilities they are explicitly assigned to.
    The `assigned_by` field provides an audit trail for access provisioning.

    Attributes:
        warehouse_id (int): The foreign key linking to the authorized warehouse.
        user_id (int): The foreign key linking to the authorized user.
        assigned_by (int): The foreign key linking to the administrator who granted this access.
    """

    __tablename__ = "warehouse_users"
    __table_args__ = (
        UniqueConstraint("warehouse_id", "user_id", name="uq_warehouse_user"),
    )

    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    assigned_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
