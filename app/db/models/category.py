"""
Define the database model for product categories.

Manages the schema for logical groupings of products within a specific organization,
allowing users to classify inventory for reporting and filtering purposes.
"""

from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import ForeignKey, UniqueConstraint, String
from app.db.models.base import BaseModel


class Category(BaseModel):
    """
    Represent a product categorization hierarchy unit.

    Categories belong to an organization and serve as a grouping mechanism for products.
    They ensure inventory can be segmented logically, such as 'Electronics' or 'Apparel'.

    Attributes:
        organization_id (int): The foreign key linking this category to its parent organization.
        name (str): The unique (within the organization) human-readable name of the category.
        description (str | None): Additional details about what items belong in this category.
    """

    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "name", name="uq_category_organization_name"
        ),
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
