"""
Define the database model for inventory products.

Manages the catalog of physical goods sold or tracked by an organization,
including stock-keeping units (SKU), baseline pricing, and shelf-life constraints.
"""

from decimal import Decimal
from sqlalchemy import (
    ForeignKey,
    UniqueConstraint,
    String,
    Text,
    Numeric,
    Boolean,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects import postgresql

from app.db.models.base import BaseModel


class Product(BaseModel):
    """
    Represent a distinct item type available for stocking or sale.

    Products belong to a specific organization. The SKU uniquely identifies
    the item globally across all of the organization's warehouses.

    Attributes:
        organization_id (int): The foreign key linking the product to its owning organization.
        category_id (int | None): The foreign key linking the product to a logical category.
        unit (str | None): The unit of measure for tracking quantities (e.g., 'pcs', 'kg', 'liters').
        sku (str): The unique Stock Keeping Unit identifier for internal and barcode tracking.
        name (str): The human-readable commercial name of the product.
        description (str | None): Additional details or marketing copy describing the product.
        base_cost_price (Decimal | None): The default expected purchase cost of the item.
        base_selling_price (Decimal | None): The default retail or wholesale price.
        is_perishable (bool): Indicates if the product spoils and requires expiry tracking.
        shelf_life (int | None): The standard number of days the product remains viable after production/receipt.
        status (str): The lifecycle state of the product (e.g., 'active', 'discontinued').
    """

    __tablename__ = "products"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False, index=True
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id"), nullable=True, index=True
    )

    unit: Mapped[str | None] = mapped_column(
        String(20), server_default="pcs", nullable=True
    )
    sku: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    base_cost_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    base_selling_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )

    is_perishable: Mapped[bool] = mapped_column(
        Boolean, server_default="false", nullable=False
    )
    shelf_life: Mapped[int | None] = mapped_column(Integer, nullable=True)

    status: Mapped[str] = mapped_column(
        postgresql.ENUM(
            "active", "discontinued", "draft", name="product_status", create_type=True
        ),
        server_default="active",
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "sku", name="uq_product_org_sku"),
    )
