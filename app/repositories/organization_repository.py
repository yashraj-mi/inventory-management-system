"""Manage database interactions for organizations.

This module encapsulates data access for the Organization model, representing
top-level tenants in the multi-tenant architecture. It handles queries for
creating and fetching root organizational records.
"""

from app.repositories.base_repository import BaseRepository
from app.db.models.organization import Organization


class OrganizationRepository(BaseRepository[Organization]):
    """Manage data access for Organization entities.

    This repository performs CRUD operations on the top-level Organization
    model. It is central to tenant isolation since most other models link
    back to an organization.
    """

    model = Organization
