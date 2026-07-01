"""
organization.py module.

Provides core functionality and components for the organization domain.
"""

import secrets
from typing import List
from fastapi import APIRouter, Depends, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.organization import (
    OrganizationResponse,
    OrganizationCreate,
    OrganizationStatusUpdate,
)
from app.services.organization_service import OrganizationService
from app.schemas.response import StandardResponse
from app.core.security import get_current_user
from app.core.exceptions import AppException
from app.dependencies.auth import (
    ALLOW_SUPER_ADMIN,
    ALLOW_SUPER_ADMIN_OR_ORG_ADMIN,
    verify_tenant_access,
)
from app.services.email_service import email_service
from app.constants.organization_enum import OrganizationStatus, OrganizationMessages
from app.services.user_service import UserService
from app.constants.user_enum import UserRole
from app.schemas.user import UserCreateInternal

user_service = UserService()
router = APIRouter(prefix="/organizations", tags=["Organizations"])


def get_organization_service() -> OrganizationService:
    """
    Dependency provider factory to instantiate the OrganizationService layer.

    Returns:
        OrganizationService: An instance of the organization business logic service.
    """
    return OrganizationService()


# 1. CREATE: Public request entry point for any logged-in user
@router.post(
    "",
    response_model=StandardResponse[OrganizationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit organization request",
)
async def register_organization(
    payload: OrganizationCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    service: OrganizationService = Depends(get_organization_service),
) -> StandardResponse[OrganizationResponse]:
    """
    Submit a request to register a new organization.

    Creates a new organization record in PENDING status and sends a confirmation email.

    Args:
        payload (OrganizationCreate): The registration payload containing organization details.
        background_tasks (BackgroundTasks): Background task manager for sending emails.
        db (AsyncSession): The active database session context.
        service (OrganizationService): The organization service layer.

    Returns:
        StandardResponse[OrganizationResponse]: A standardized response containing the created organization.
    """

    db_org = await service.register(db, payload)
    email_service.send_pending_review_email(
        background_tasks=background_tasks, recipient=db_org.email, org_name=db_org.name
    )
    db_org = OrganizationResponse.model_validate(db_org)
    return StandardResponse(
        success=True,
        message=OrganizationMessages.REGISTERED_SUCCESSFULLY,
        data=db_org,
    )


# 2. READ ALL: Super Admin only
@router.get(
    "",
    response_model=StandardResponse[List[OrganizationResponse]],
    dependencies=[Depends(ALLOW_SUPER_ADMIN)],
    summary="List all organizations",
)
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    service: OrganizationService = Depends(get_organization_service),
):
    """
    List all registered organizations (Super Admin only).

    Args:
        db (AsyncSession): The active database session context.
        service (OrganizationService): The organization service layer.

    Returns:
        StandardResponse[List[OrganizationResponse]]: A list of all organizations.
    """
    orgs = await service.list_organizations(db)
    orgs = [OrganizationResponse.model_validate(o) for o in orgs]
    return StandardResponse(
        success=True,
        message=OrganizationMessages.LIST_RETRIEVED,
        data=orgs,
    )


# 3. READ ONE: Accessible by standard organization workers
@router.get(
    "/{org_id}",
    response_model=StandardResponse[OrganizationResponse],
    dependencies=[Depends(ALLOW_SUPER_ADMIN_OR_ORG_ADMIN)],
    summary="Get details of a single organization",
)
async def get_organization(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    service: OrganizationService = Depends(get_organization_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Retrieve details of a single organization by ID.

    Accessible by standard organization workers.

    Args:
        org_id (int): The ID of the organization to fetch.
        db (AsyncSession): The active database session context.
        service (OrganizationService): The organization service layer.

    Returns:
        StandardResponse[OrganizationResponse]: The requested organization details.
    """
    verify_tenant_access(current_user, org_id)
    org = await service.get_organization(db, org_id)
    org = OrganizationResponse.model_validate(org)
    return StandardResponse(
        success=True,
        message=OrganizationMessages.DETAILS_RETRIEVED,
        data=org,
    )


# 4. UPDATE STATUS: Super Admin review logic (Approve / Reject)
@router.patch(
    "/{org_id}/status",
    response_model=StandardResponse[OrganizationResponse],
    dependencies=[Depends(ALLOW_SUPER_ADMIN)],
    summary="Approve, reject or update organization status",
)
async def review_organization(
    org_id: int,
    background_tasks: BackgroundTasks,
    payload: OrganizationStatusUpdate,
    db: AsyncSession = Depends(get_db),
    service: OrganizationService = Depends(get_organization_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Review an organization request, updating its status to ACTIVE or REJECTED.

    If approved, an email is dispatched and an initial admin user is created.

    Args:
        org_id (int): The ID of the organization to review.
        background_tasks (BackgroundTasks): Background task manager for sending emails.
        payload (OrganizationStatusUpdate): Payload containing the new status.
        db (AsyncSession): The active database session context.
        service (OrganizationService): The organization service layer.
        current_user (UserResponse): The current authenticated super admin user.

    Returns:
        StandardResponse[OrganizationResponse]: The updated organization details.
    """
    sub = current_user.get("sub")
    if not sub:
        raise AppException(
            message="Invalid token: missing user identifier.", status_code=401
        )
    admin_id = int(sub)

    # Core status update transaction execution
    updated_org = await service.update_status(db, org_id, payload, admin_id)

    if updated_org.status == OrganizationStatus.ACTIVE:
        # Offload approval transactional email dispatch down to background runner pool
        email_service.send_approval_email(
            background_tasks=background_tasks,
            recipient=updated_org.email,
            org_name=updated_org.name,
        )

        temp_password = secrets.token_urlsafe(16)
        user_payload = UserCreateInternal(
            organization_id=updated_org.id,
            role=UserRole.ORG_ADMIN,
            first_name=updated_org.name,
            last_name="Admin",
            email=updated_org.email,
            password=temp_password,
        )

        await user_service.create_user(db=db, payload=user_payload)
        email_service.send_credentials_email(
            background_tasks=background_tasks,
            first_name=user_payload.first_name,
            recipient=user_payload.email,
            org_name=updated_org.name,
            temp_password=temp_password,
        )

    org = OrganizationResponse.model_validate(updated_org)

    return StandardResponse(
        success=True,
        message=OrganizationMessages.STATUS_UPDATED,
        data=org,
    )


# 5. DELETE: Restrictive deletion endpoint
@router.delete(
    "/{org_id}",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[None],
    dependencies=[Depends(ALLOW_SUPER_ADMIN)],
    summary="Permanently delete an organization",
)
async def delete_organization(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    service: OrganizationService = Depends(get_organization_service),
) -> StandardResponse[None]:
    """
    Permanently delete an organization from the system.

    Args:
        org_id (int): The ID of the organization to delete.
        db (AsyncSession): The active database session context.
        service (OrganizationService): The organization service layer.

    Returns:
        StandardResponse[None]: Success message.
    """
    await service.remove_organization(db, org_id)
    return StandardResponse(
        success=True,
        message=OrganizationMessages.DELETED_SUCCESSFULLY,
        data=None,
    )
