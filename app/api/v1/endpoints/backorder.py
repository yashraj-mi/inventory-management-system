"""Provide endpoints for backorder management operations.

This module defines routes for creating and retrieving backorders, utilizing
dependency injection for authentication, database sessions, and services.
"""

from fastapi import APIRouter, Depends, Path, status
from app.db.models.user import User
from app.core.security import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.backorder import BackorderCreate, BackorderResponse
from app.services.backorder_service import BackorderService
from app.schemas.response import StandardResponse
from app.dependencies.rbac import require_permission
from app.core.permissions import Permissions
from app.constants.common_enum import CrudMessages
from app.dependencies.backorder import get_backorder_service

router = APIRouter(prefix="/backorders", tags=["Backorders"])


@router.post(
    "",
    response_model=StandardResponse[BackorderResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a Backorder",
    dependencies=[Depends(require_permission(Permissions.BACKORDER_CREATE))],
)
async def create_backorder(
    payload: BackorderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: BackorderService = Depends(get_backorder_service),
) -> StandardResponse[BackorderResponse]:
    """Create a new backorder for a product.

    Executes a POST request to `/backorders` to register a backorder when a
    product is out of stock. It requires organization-level authentication.

    Args:
        payload (BackorderCreate): The backorder details including product ID and quantity.
        db (AsyncSession): The asynchronous database session dependency injected by `get_db`.
        service (BackorderService): The backorder service layer dependency injected by `get_backorder_service`.

    Raises:
        HTTPException (400): If the requested quantity is invalid or payload is malformed.
        HTTPException (403): If the user lacks proper organization privileges.
        HTTPException (404): If the associated product or order is not found.

    Returns:
        StandardResponse[BackorderResponse]: A standardized wrapper containing the newly created backorder.
    """
    record = await service.create(db, payload, current_user.organization_id)
    return StandardResponse(
        success=True,
        message=CrudMessages.CREATE_SUCCESS.format(module="Backorder"),
        data=record,
    )


@router.get(
    "/{backorder_id}",
    response_model=StandardResponse[BackorderResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Backorder",
    dependencies=[Depends(require_permission(Permissions.BACKORDER_READ))],
)
async def get_backorder(
    backorder_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: BackorderService = Depends(get_backorder_service),
) -> StandardResponse[BackorderResponse]:
    """Retrieve a specific backorder by its ID.

    Executes a GET request to `/backorders/{backorder_id}` to fetch the specified
    backorder record. Requires organization-level authentication.

    Args:
        backorder_id (int): The unique identifier of the backorder to retrieve. Must be greater than 0.
        db (AsyncSession): The asynchronous database session dependency injected by `get_db`.
        service (BackorderService): The backorder service layer dependency injected by `get_backorder_service`.

    Raises:
        HTTPException (400): If the provided `backorder_id` is invalid.
        HTTPException (403): If the user lacks proper organization privileges.
        HTTPException (404): If no backorder is found for the given ID.

    Returns:
        StandardResponse[BackorderResponse]: A standardized wrapper containing the backorder details.
    """
    record = await service.get_by_id(db, backorder_id, current_user.organization_id)
    return StandardResponse(
        success=True,
        message=CrudMessages.FETCH_SUCCESS.format(module="Backorder"),
        data=record,
    )
