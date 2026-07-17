"""
Organization service for tenant management.

Handles registration, status lifecycle (approvals, rejections, deactivation),
and deletion of organizations within the multi-tenant architecture.
"""

from app.db.session_utils import db_transaction
from typing import Sequence
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.organization_repository import OrganizationRepository
from app.db.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationStatusUpdate
from app.core.exceptions import AppException
from app.constants.organization_enum import OrganizationStatus, OrganizationMessages
from app.constants.common_enum import CrudMessages
from app.dependencies.pagination import PaginationParams
from app.schemas.organization import OrganizationResponse


from app.core.profiling import log_timing


class OrganizationService:
    """
    Service layer executing business logic for Organization entities.

    Handles organization registration, status management (approvals/rejections),
    and queries.
    """

    def __init__(self, organization_repo: OrganizationRepository) -> None:
        """
        Initialize the OrganizationService with repository dependencies.

        Args:
            organization_repo: Repository for organization persistence and state management.
        """
        self.organization_repo = organization_repo

    @log_timing
    async def register(
        self, db: AsyncSession, payload: OrganizationCreate
    ) -> Organization:
        """
        Register a new organization and initialize it with a PENDING status.

        Requires super-admin approval before users can interact with the organization.

        Args:
            db: The active database session context.
            payload: The registration details provided by the client.

        Returns:
            The newly created Organization instance.

        Raises:
            AppException: If unique constraints (e.g. email) fail (409).
        """
        organization = Organization(
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            address=payload.address,
            status=OrganizationStatus.PENDING,
        )
        async with db_transaction(db, module="Organization", action="operation"):
            db_org = await self.organization_repo.create(db, organization)
            await db.flush()
            await db.refresh(db_org)
        return db_org

    @log_timing
    async def get_organization(self, db: AsyncSession, org_id: int) -> Organization:
        """
        Retrieve a specific organization by its ID.

        Args:
            db: The active database session context.
            org_id: The ID of the organization to fetch.

        Returns:
            The found Organization instance.

        Raises:
            AppException: If the organization does not exist (404).
        """
        org = await self.organization_repo.get_by_id(db, org_id)
        if not org:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Organization"),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return org

    @log_timing
    async def list_organizations(
        self, db: AsyncSession, params: PaginationParams
    ) -> tuple[Sequence[OrganizationResponse], int]:
        """
        Retrieve a paginated list of all registered organizations.

        Args:
            db: The active database session context.
            params: Pagination parameters.

        Returns:
            A tuple of organization sequences and the total count.
        """
        return await self.organization_repo.get_all(db, params)

    @log_timing
    async def update_status(
        self,
        db: AsyncSession,
        org_id: int,
        payload: OrganizationStatusUpdate,
        admin_id: int,
    ) -> Organization:
        """
        Update the operational status of an organization through a strict state machine.

        Controls transitions such as PENDING -> ACTIVE or ACTIVE -> INACTIVE. Updates
        the identity of the admin who performed the action.

        Args:
            db: The active database session context.
            org_id: The ID of the organization to update.
            payload: Payload containing the target status.
            admin_id: The ID of the super admin performing the update.

        Returns:
            The updated Organization instance.

        Raises:
            AppException: For invalid state transitions (400) or DB errors.
        """
        org = await self.get_organization(db, org_id)

        # State machine guard: validate allowed transitions
        allowed_transitions = {
            OrganizationStatus.PENDING: [
                OrganizationStatus.ACTIVE,
                OrganizationStatus.REJECTED,
            ],
            OrganizationStatus.REJECTED: [OrganizationStatus.PENDING],
            OrganizationStatus.ACTIVE: [OrganizationStatus.INACTIVE],
            OrganizationStatus.INACTIVE: [OrganizationStatus.ACTIVE],
        }
        if payload.status not in allowed_transitions.get(org.status, []):
            raise AppException(
                message=OrganizationMessages.INVALID_TRANSITION.format(
                    current=org.status.value, target=payload.status.value
                ),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Modify fields and register tracking identity
        org.status = payload.status
        org.action_by = admin_id

        async with db_transaction(db, module="Organization", action="operation"):
            await db.flush()
            await db.refresh(org)
        return org

    @log_timing
    async def remove_organization(self, db: AsyncSession, org_id: int) -> None:
        """
        Permanently delete an organization from the system.

        Fails if related records (users, products, etc.) still exist due to DB constraints.

        Args:
            db: The active database session context.
            org_id: The ID of the organization to delete.

        Raises:
            AppException: On relational constraint failures (409) or unknown DB errors.
        """
        org = await self.get_organization(db, org_id)
        async with db_transaction(db, module="Organization", action="operation"):
            await self.organization_repo.delete(db, org)
            await db.flush()
