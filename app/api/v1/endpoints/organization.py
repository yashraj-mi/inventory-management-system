from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.organization import OrganizationResponse, OrganizationCreate
from app.services.organization_service import OrganizationService
from app.schemas.response import StandardResponse

router = APIRouter(prefix="/organizations", tags=["Organizations"])


def get_organization_service() -> OrganizationService:
    """Dependency provider that instantiates and returns the Organization business

    logic service layer.

    Returns:
        OrganizationService: A fresh instance of the organization service class.
    """
    return OrganizationService()


@router.post(
    "",
    response_model=StandardResponse[OrganizationResponse],
    status_code=201,
    summary="Register a new organization",
)
async def register_organization(
    payload: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    service: OrganizationService = Depends(get_organization_service),
) -> StandardResponse[OrganizationResponse]:
    """Endpoint to provision and register a brand new corporate entity into the

    Inventory Management System.

    Args:
        payload (OrganizationCreate): Validated request body containing name,
        email, phone, address, and status.
        db (AsyncSession): The active database session context managed by
        FastAPI.
        service (OrganizationService): The business logic processor instance.

    Returns:
        StandardResponse[OrganizationResponse]: A standardized API wrapper containing
        the freshly generated unique organization record.
    """
    # 1. Execute core business logic (returns a DB entity model or data dict)
    db_org = await service.register(db, payload)

    # 2. Convert the raw database object explicitly into your target Pydantic schema
    # This prevents the ResponseValidationError by supplying exactly what data expects
    validated_data = OrganizationResponse.model_validate(db_org)

    # 3. Envelop inside your standardized layout schema
    return StandardResponse(
        success=True,
        message="Organization Registered successfully.",
        data=validated_data,
    )
