"""Define enumerations for product entities.

Provides operational statuses indicating a product's availability and
stage in its lifecycle within the inventory system.
"""

from enum import Enum


class ProductStatus(str, Enum):
    """Represent the operational status of a product.

    Determines if a product can be sold/purchased (ACTIVE), is no longer
    supported (DISCONTINUED), or is currently being set up (DRAFT).
    """

    ACTIVE = "active"
    DISCONTINUED = "discontinued"
    DRAFT = "draft"
