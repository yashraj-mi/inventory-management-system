from sqlalchemy.orm import mapped_column, Mapped

from sqlalchemy import ForeignKey, UniqueConstraint
from app.db.models.base import BaseModel


class WarehouseUsers(BaseModel):
    """
    SQLAlchemy model representing a many-to-many relationship mapping Users to Warehouses.

    This mapping table determines which users have access/roles in which warehouses.
    A unique constraint ensures a user is not assigned to the same warehouse multiple times.

    Attributes:
        warehouse_id (int): Foreign key to the assigned Warehouse.
        user_id (int): Foreign key to the assigned User.
        assigned_by (int): Foreign key to the User (typically an Admin) who made the assignment.
    """

    __tablename__ = "warehouse_users"
    __table_args__ = (
        UniqueConstraint("warehouse_id", "user_id", name="uq_warehouse_user"),
    )

    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    assigned_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
