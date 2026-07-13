"""
Provide schemas for product catalog management.

This module contains Pydantic models for creating, validating, and returning
product data, including custom validation logic for parsing shelf-life duration strings.
"""

from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, condecimal, field_validator
import re
from app.constants.product_enum import ProductStatus


class ProductCreate(BaseModel):
    """Represent the payload for creating a new product from user input.

    Used in request bodies to validate incoming product creation payloads,
    including automatic parsing of shelf-life duration strings into integer days.

    Attributes:
        category_id (int | None): Identifier of the product's category.
        sku (str): Unique Stock Keeping Unit identifier, max 50 characters.
        name (str): Product display name, max 150 characters.
        description (str | None): Detailed product information.
        unit (str | None): Unit of measurement (e.g., 'pcs', 'kg'), defaults to 'pcs'.
        base_cost_price (Decimal | None): Default purchasing cost of the product.
        base_selling_price (Decimal | None): Default selling price of the product.
        is_perishable (bool): Indicates if the product expires.
        shelf_life (int): Shelf life duration in total days.
        supplier_id (int | None): Primary supplier identifier for this product.
        supplier_sku (str | None): Supplier's specific SKU for this product.
    """

    category_id: int | None = None
    sku: str = Field(..., max_length=50)
    name: str = Field(..., max_length=150)
    description: str | None = None
    unit: str | None = Field(default="pcs", max_length=20)

    base_cost_price: condecimal(ge=0, max_digits=10, decimal_places=2) | None = None
    base_selling_price: condecimal(ge=0, max_digits=10, decimal_places=2) | None = None

    is_perishable: bool = False

    shelf_life: int = Field(
        default=0,
        description="Shelf life duration format. Input can be a string like '1Y 2M 0D' (Years, Months, Days). It will be converted and stored as total days.",
        json_schema_extra={"examples": ["1Y 2M 0D", "6M", "15D", 425]},
    )
    supplier_id: int | None = Field(default=None, ge=0)
    supplier_sku: str | None = Field(default=None)

    # status: ProductStatus = ProductStatus.ACTIVE

    @field_validator("shelf_life", mode="before")
    @classmethod
    def parse_shelf_life(cls, v) -> int:
        """Parse a mixed duration string or integer into total days.

        Args:
            v: A boolean, integer, float, or string representing duration.

        Returns:
            int: The calculated shelf life in days.

        Raises:
            ValueError: If the duration format is invalid or negative.
        """
        if v is None or v == "":
            return 0
        if isinstance(v, bool):  # bool is subclass of int, guard against True/False
            raise ValueError("Shelf life must be a number or duration string")
        if isinstance(v, (int, float)):
            if v < 0:
                raise ValueError("Shelf life cannot be negative")
            return int(v)
        if isinstance(v, str):
            v_stripped = v.strip()
            if v_stripped.lstrip("-").isdigit():
                val = int(v_stripped)
                if val < 0:
                    raise ValueError("Shelf life cannot be negative")
                return val
            years = re.search(r"(\d+)\s*[Yy]", v)
            months = re.search(r"(\d+)\s*[Mm]", v)
            days = re.search(r"(\d+)\s*[Dd]", v)
            if not any([years, months, days]):
                raise ValueError("Invalid format. Use something like '1Y 2M 0D'")
            y = int(years.group(1)) if years else 0
            m = int(months.group(1)) if months else 0
            d = int(days.group(1)) if days else 0
            return (y * 365) + (m * 30) + d
        raise ValueError(
            f"Duration must be a string format (e.g., '1Y 2M 1D') or an integer. Received: {v}"
        )


class ProductCreateInternal(ProductCreate):
    """Represent the payload for internal creation of a product.

    Used by background services or internal APIs that require system-managed fields
    such as organization context and default status.

    Attributes:
        organization_id (int): Identifier of the organization owning the product.
        status (ProductStatus): Operational status of the product, defaults to ACTIVE.
    """

    organization_id: int
    status: ProductStatus = Field(default=ProductStatus.ACTIVE.value)


class ProductResponse(BaseModel):
    """Represent a product record returned in API responses.

    Used to serialize product data from the database to clients, providing complete
    visibility into product details and system timestamps.

    Attributes:
        id (int): Unique identifier of the product.
        organization_id (int): Identifier of the organization owning the product.
        category_id (int | None): Identifier of the product's category.
        sku (str): Unique Stock Keeping Unit identifier.
        name (str): Product display name.
        description (str | None): Detailed product information.
        unit (str | None): Unit of measurement.
        base_cost_price (Decimal | None): Default purchasing cost.
        base_selling_price (Decimal | None): Default selling price.
        is_perishable (bool): Indicates if the product expires.
        shelf_life (int): Shelf life duration in total days.
        status (ProductStatus): Current operational status.
        created_at (datetime): Timestamp when the product was created.
        updated_at (datetime): Timestamp of the last modification.
    """

    id: int
    organization_id: int
    category_id: int | None = None
    sku: str
    name: str
    description: str | None = None
    unit: str | None = None
    base_cost_price: Decimal | None = None
    base_selling_price: Decimal | None = None
    is_perishable: bool
    shelf_life: int
    status: ProductStatus
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class ProductUpdate(BaseModel):
    """Represent the payload for modifying an existing product.

    Used in request bodies for product update (PATCH/PUT) endpoints, allowing partial
    updates to product attributes.

    Attributes:
        category_id (int | None): The new category identifier, if updating.
        sku (str | None): The new product SKU, if updating.
        name (str | None): The new product name, if updating.
        description (str | None): The new description, if updating.
        unit (str | None): The new measurement unit, if updating.
        base_cost_price (Decimal | None): The new base cost price, if updating.
        base_selling_price (Decimal | None): The new base selling price, if updating.
        is_perishable (bool | None): The new perishability flag, if updating.
        shelf_life (int | None): The new shelf life in days, if updating.
        status (ProductStatus | None): The new product status, if updating.
    """

    category_id: int | None = None
    sku: str | None = Field(default=None, max_length=50)
    name: str | None = Field(default=None, max_length=150)
    description: str | None = None
    unit: str | None = Field(default=None, max_length=20)

    base_cost_price: condecimal(ge=0, max_digits=10, decimal_places=2) | None = None
    base_selling_price: condecimal(ge=0, max_digits=10, decimal_places=2) | None = None

    is_perishable: bool | None = None
    shelf_life: int | None = Field(default=None, ge=0)
    status: ProductStatus | None = None
