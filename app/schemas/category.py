"""
Provide schemas for product category management.

This module contains Pydantic models for creating, updating, and responding with
product category data, which are used to group products logically within an organization.
"""

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CategoryBase(BaseModel):
    """Define shared attributes for a product category.

    Used as a foundation for other category schemas to ensure consistent field definitions.

    Attributes:
        name (str): The display name of the category, max 255 characters.
        description (str | None): Optional detailed information about the category, max 500 characters.
    """

    name: str = Field(..., description="The name of the category.", max_length=255)
    description: str | None = Field(
        None, description="Optional description of the category.", max_length=500
    )


class CategoryCreate(CategoryBase):
    """Represent the payload for creating a new product category via public API.

    Used in request bodies for category creation endpoints. Inherits base fields
    and intentionally excludes organization_id, which is inferred from the authenticated user.
    """

    pass


class CategoryCreateInternal(CategoryBase):
    """Represent the payload for creating a category with internal system context.

    Used by service-layer functions where the organization context must be explicitly provided,
    unlike the public API where it is inferred.

    Attributes:
        organization_id (int): The unique identifier of the owning organization.
    """

    organization_id: int


class CategoryUpdate(BaseModel):
    """Represent the payload for modifying an existing product category.

    Used in request bodies for category update (PATCH/PUT) endpoints. All fields are
    optional to support partial updates.

    Attributes:
        name (str | None): The new name of the category, if being updated.
        description (str | None): The new description of the category, if being updated.
    """

    name: str | None = Field(
        None, description="The name of the category.", max_length=255
    )
    description: str | None = Field(
        None, description="Optional description of the category.", max_length=500
    )


class CategoryResponse(CategoryBase):
    """Represent the complete product category data returned to clients.

    Used in response bodies when retrieving or creating categories. Includes
    system-managed fields like IDs and timestamps.

    Attributes:
        id (int): The unique identifier of the category.
        organization_id (int): The identifier of the organization this category belongs to.
        created_at (datetime): Timestamp when the category was initially created.
        updated_at (datetime): Timestamp of the last modification.
    """

    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
