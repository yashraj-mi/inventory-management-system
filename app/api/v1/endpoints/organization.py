"""Provide API endpoints for the Organization domain.

This module defines routes for organization registration, administrative review,
retrieval, and deletion, utilizing background tasks for email notifications.
"""

import secrets
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
from app.constants.auth_enum import AuthMessages
from app.dependencies.pagination import PaginationParams, get_pagination_params
from app.schemas.response import PaginatedData
from app.constants.common_enum import CrudMessages

from app.dependencies.organization import get_organization_service
from app.dependencies.user import get_user_service

router = APIRouter(prefix="/organizations", tags=["Organizations"])


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
    """Submit a request to register a new organization.

    Executes a POST request to `/organizations` to create a new organization record
    in PENDING status and queues a confirmation email.

    Args:
        payload (OrganizationCreate): The registration payload containing organization details.
        background_tasks (BackgroundTasks): Background task manager for email dispatch.
        db (AsyncSession): The asynchronous database session dependency.
        service (OrganizationService): The organization service layer dependency.

    Raises:
        HTTPException (400): If the payload is invalid or email is already registered.

    Returns:
        StandardResponse[OrganizationResponse]: A standardized wrapper containing the pending organization.
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
    response_model=StandardResponse[PaginatedData[OrganizationResponse]],
    dependencies=[Depends(ALLOW_SUPER_ADMIN)],
    summary="List all organizations",
)
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    service: OrganizationService = Depends(get_organization_service),
    params: PaginationParams = Depends(get_pagination_params),
):
    """List all registered organizations.

    Executes a GET request to `/organizations` to fetch a paginated list of all
    organizations. Restricted to super admins.

    Args:
        db (AsyncSession): The asynchronous database session dependency.
        service (OrganizationService): The organization service layer dependency.
        params (PaginationParams): Pagination parameters (page and size).

    Raises:
        HTTPException (403): If the user lacks super admin privileges.

    Returns:
        StandardResponse[PaginatedData[OrganizationResponse]]: A paginated list of all organizations.
    """
    orgs, total = await service.list_organizations(db, params)
    total_pages = (total + params.size - 1) // params.size
    orgs = [OrganizationResponse.model_validate(o) for o in orgs]
    data = PaginatedData(
        items=orgs, total=total, page=params.page, size=params.size, pages=total_pages
    )
    return StandardResponse(
        success=True,
        message=CrudMessages.READ_ALL_SUCCESS.format(module="Organization"),
        data=data,
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
    """Retrieve details of a single organization by ID.

    Executes a GET request to `/organizations/{org_id}` to fetch organization details.

    Args:
        org_id (int): The unique ID of the organization to fetch.
        db (AsyncSession): The asynchronous database session dependency.
        service (OrganizationService): The organization service layer dependency.
        current_user (dict): The authenticated user context.

    Raises:
        HTTPException (403): If the user lacks access to the organization.
        HTTPException (404): If the organization does not exist.

    Returns:
        StandardResponse[OrganizationResponse]: A standardized wrapper containing organization details.
    """
    verify_tenant_access(current_user, org_id)
    org = await service.get_organization(db, org_id)
    org = OrganizationResponse.model_validate(org)
    return StandardResponse(
        success=True,
        message=CrudMessages.READ_ONE_SUCCESS.format(module="Organization"),
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
    user_service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user),
):
    """Review an organization request, updating its status to ACTIVE or REJECTED.

    Executes a PATCH request to `/organizations/{org_id}/status` to approve or reject
    an organization. If approved, an email is dispatched and an initial admin user is created.

    Args:
        org_id (int): The unique ID of the organization to review.
        background_tasks (BackgroundTasks): Background task manager for email dispatch.
        payload (OrganizationStatusUpdate): Payload containing the new status.
        db (AsyncSession): The asynchronous database session dependency.
        service (OrganizationService): The organization service layer dependency.
        user_service (UserService): The user service layer dependency.
        current_user (dict): The authenticated super admin user context.

    Raises:
        HTTPException (400): If the payload is invalid or status transition is invalid.
        HTTPException (401): If the token is invalid or missing sub claim.
        HTTPException (403): If the user lacks super admin privileges.
        HTTPException (404): If the organization does not exist.

    Returns:
        StandardResponse[OrganizationResponse]: A standardized wrapper containing the updated organization details.
    """
    sub = current_user.get("sub")
    if not sub:
        raise AppException(
            message=AuthMessages.INVALID_TOKEN, status_code=status.HTTP_401_UNAUTHORIZED
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
    """Permanently delete an organization from the system.

    Executes a DELETE request to `/organizations/{org_id}` to remove an organization.

    Args:
        org_id (int): The unique ID of the organization to delete.
        db (AsyncSession): The asynchronous database session dependency.
        service (OrganizationService): The organization service layer dependency.

    Raises:
        HTTPException (403): If the user lacks super admin privileges.
        HTTPException (404): If the organization does not exist.

    Returns:
        StandardResponse[None]: A standardized wrapper indicating successful deletion.
    """
    await service.remove_organization(db, org_id)
    return StandardResponse(
        success=True,
        message=CrudMessages.DELETE_SUCCESS.format(module="Organization"),
        data=None,
    )
