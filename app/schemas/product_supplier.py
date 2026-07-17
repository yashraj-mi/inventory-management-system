"""
Provide schemas for product and supplier relationships.

This module defines Pydantic models for mapping products to their corresponding
suppliers, tracking supplier-specific SKUs, and storing supplier cost prices.
"""

from datetime import datetime
from pydantic import BaseModel, Field, condecimal


class ProductSupplierCreate(BaseModel):
    """Represent the payload for assigning a supplier to a product.

    Used when adding a new supplier option for purchasing a specific product,
    capturing the supplier's SKU and agreed cost price.

    Attributes:
        product_id (int): Identifier of the internal product.
        supplier_id (int): Identifier of the supplier providing the product.
        supplier_sku (str | None): The supplier's specific SKU for this item.
        cost_price (Decimal | None): Agreed purchase cost per unit from this supplier.
    """

    product_id: int
    supplier_id: int
    supplier_sku: str | None = Field(default=None, max_length=50)
    cost_price: condecimal(ge=0, max_digits=10, decimal_places=2) | None = None


class ProductSupplierUpdate(BaseModel):
    """Represent the payload for updating an existing product-supplier mapping.

    Used when a supplier changes their SKU or pricing for an existing mapped product.

    Attributes:
        supplier_sku (str | None): The updated supplier SKU.
        cost_price (Decimal | None): The updated purchase cost per unit.
    """

    supplier_sku: str | None = Field(default=None, max_length=50)
    cost_price: condecimal(ge=0, max_digits=10, decimal_places=2) | None = None


class ProductSupplierResponse(BaseModel):
    """Represent a product-supplier mapping returned in API responses.

    Used to serialize the relationship details back to clients, often nested
    within product or supplier detailed responses.

    Attributes:
        id (int): Unique identifier of the mapping record.
        product_id (int): Identifier of the internal product.
        supplier_id (int): Identifier of the supplier.
        supplier_sku (str | None): The supplier's specific SKU.
        cost_price (float | None): The recorded cost price from the supplier.
        created_at (datetime): Timestamp when the mapping was created.
        updated_at (datetime): Timestamp of the last modification.
    """

    id: int
    product_id: int
    supplier_id: int
    supplier_sku: str | None
    cost_price: float | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
