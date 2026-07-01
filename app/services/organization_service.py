"""
organization_service.py module.

Provides core functionality and components for the organization_service domain.
"""

from typing import Sequence
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.repositories.organization_repository import OrganizationRepository
from app.db.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationStatusUpdate
from app.core.exceptions import AppException
from app.constants.organization_enum import OrganizationStatus, OrganizationMessages


class OrganizationService:
    """
    Service layer executing business logic for Organization entities.

    Handles organization registration, status management (approvals/rejections),
    and queries.
    """

    def __init__(self, organization_repo: OrganizationRepository | None = None) -> None:
        """
        Executes the __init__ operation.

        Args:
            organization_repo: Parameter description.

        Returns:
            Execution result.
        """
        self.organization_repo = organization_repo or OrganizationRepository()

    async def register(
        self, db: AsyncSession, payload: OrganizationCreate
    ) -> Organization:
        """
        Registers a new organization with a default PENDING status.

        Args:
            db (AsyncSession): The active database session context.
            payload (OrganizationCreate): The registration details.

        Returns:
            Organization: The newly created organization instance.
        """
        organization = Organization(
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            address=payload.address,
            status=OrganizationStatus.PENDING,
        )
        try:
            db_org = await self.organization_repo.create(db, organization)
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=OrganizationMessages.ALREADY_EXISTS,
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=OrganizationMessages.DB_UNEXPECTED_REGISTRATION,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return db_org

    async def get_organization(self, db: AsyncSession, org_id: int) -> Organization:
        """
        Retrieves a specific organization by its ID, raising an error if not found.

        Args:
            db (AsyncSession): The active database session context.
            org_id (int): The ID of the organization to fetch.

        Returns:
            Organization: The found organization instance.

        Raises:
            AppException: If the organization with the given ID does not exist (404).
        """
        org = await self.organization_repo.get_by_id(db, org_id)
        if not org:
            raise AppException(
                message=OrganizationMessages.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return org

    async def list_organizations(self, db: AsyncSession) -> Sequence[Organization]:
        """
        Retrieves a paginated list of all organizations.

        Args:
            db (AsyncSession): The active database session context.

        Returns:
            Sequence[Organization]: A sequence of organization instances.
        """
        return await self.organization_repo.get_all(db)

    async def update_status(
        self,
        db: AsyncSession,
        org_id: int,
        payload: OrganizationStatusUpdate,
        admin_id: int,
    ) -> Organization:
        """
        Updates the operational status of an organization (e.g., ACTIVE, REJECTED).

        Args:
            db (AsyncSession): The active database session context.
            org_id (int): The ID of the organization to update.
            payload (OrganizationStatusUpdate): Payload containing the new status.
            admin_id (int): The ID of the super admin performing the update.

        Returns:
            Organization: The updated organization instance.
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

        try:
            await db.flush()
            await db.refresh(org)
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=OrganizationMessages.DB_CONSTRAINT_UPDATE,
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=OrganizationMessages.DB_UNEXPECTED_UPDATE,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return org

    # async def approve_organization(self, db: AsyncSession, org_id: int, admin_id: int):
    #     """
    #     Helper method to explicitly approve an organization, setting its status to ACTIVE.
    #
    #     Args:
    #         db (AsyncSession): The active database session context.
    #         org_id (int): The ID of the organization to approve.
    #         admin_id (int): The ID of the super admin performing the approval.
    #
    #     Returns:
    #         Organization: The approved organization instance.
    #     """
    #     org = await self.get_organization(db, org_id)
    #
    #     # Assign enum member directly, not .value string
    #     org.status = OrganizationStatus.ACTIVE
    #     org.action_by = admin_id
    #
    #     try:
    #         await db.flush()
    #         await db.refresh(org)
    #     except IntegrityError:
    #         await db.rollback()
    #         raise AppException(
    #             message=OrganizationMessages.DB_CONSTRAINT_APPROVE,
    #             status_code=status.HTTP_409_CONFLICT,
    #         )
    #     except SQLAlchemyError:
    #         await db.rollback()
    #         raise AppException(
    #             message=OrganizationMessages.DB_UNEXPECTED_APPROVAL,
    #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         )
    #
    #     return org
    #
    # async def reject_organization(self, db: AsyncSession, org_id: int, admin_id: int):
    #     """
    #     Helper method to explicitly reject an organization, setting its status to REJECTED.
    #
    #     Args:
    #         db (AsyncSession): The active database session context.
    #         org_id (int): The ID of the organization to reject.
    #         admin_id (int): The ID of the super admin performing the rejection.
    #
    #     Returns:
    #         Organization: The rejected organization instance.
    #     """
    #     org = await self.get_organization(db, org_id)
    #
    #     # Assign enum member directly, not .value string
    #     org.status = OrganizationStatus.REJECTED
    #     org.action_by = admin_id
    #
    #     try:
    #         await db.flush()
    #         await db.refresh(org)
    #     except IntegrityError:
    #         await db.rollback()
    #         raise AppException(
    #             message=OrganizationMessages.DB_CONSTRAINT_REJECT,
    #             status_code=status.HTTP_409_CONFLICT,
    #         )
    #     except SQLAlchemyError:
    #         await db.rollback()
    #         raise AppException(
    #             message=OrganizationMessages.DB_UNEXPECTED_REJECTION,
    #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         )
    #     return org

    async def remove_organization(self, db: AsyncSession, org_id: int) -> None:
        """
        Permanently deletes an organization from the system.

        Args:
            db (AsyncSession): The active database session context.
            org_id (int): The ID of the organization to delete.
        """
        org = await self.get_organization(db, org_id)
        try:
            await self.organization_repo.delete(db, org)
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=OrganizationMessages.DB_RELATIONAL_CONSTRAINTS,
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=OrganizationMessages.DB_UNEXPECTED_DELETION,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
