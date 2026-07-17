"""
Define the database model linking products to suppliers.

Manages the mapping between an organization's internal product catalog
and the external vendors who supply them, including vendor-specific SKUs and negotiated pricing.
"""

from decimal import Decimal
from sqlalchemy import ForeignKey, UniqueConstraint, String, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel


class ProductSupplier(BaseModel):
    """
    Represent the procurement relationship between a product and a supplier.

    This association table allows purchasing agents to track which vendors sell which items,
    what the vendor calls the item, and the negotiated cost price. This enables
    automated PO generation and cost comparison.

    Attributes:
        product_id (int): The foreign key linking to the internal product catalog item.
        supplier_id (int): The foreign key linking to the vendor supplying the item.
        supplier_sku (str | None): The vendor's internal identification code for this item.
        cost_price (Decimal | None): The specific negotiated or last-known purchase price from this vendor.
    """

    __tablename__ = "product_suppliers"

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), nullable=False, index=True
    )
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id"), nullable=False, index=True
    )

    supplier_sku: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cost_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    __table_args__ = (
        UniqueConstraint("product_id", "supplier_id", name="uq_product_supplier"),
    )
