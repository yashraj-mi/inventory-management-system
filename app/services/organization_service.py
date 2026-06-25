from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.organization_repository import OrganizationRepository
from app.db.models.organization import Organization
from app.schemas.organization import OrganizationCreate


class OrganizationService:
    """Service layer managing business logic rules for company organization

    profiles.
    """

    def __init__(self, organization_repo: OrganizationRepository | None = None) -> None:
        """Initializes the OrganizationService with a data access repository.

        Args:
            organization_repo (OrganizationRepository | None): An optional repository instance
                for mocking/testing, defaults to a fresh initialization.
        """
        self.organization_repo = organization_repo or OrganizationRepository()

    async def register(
        self, db: AsyncSession, payload: OrganizationCreate
    ) -> Organization:
        """Processes logic rules to instantiate and register a new corporate profile.

        Args:
            db (AsyncSession): The active asynchronous database session engine.
            payload (OrganizationCreate): Inbound validated data metrics schema.

        Returns:
            Organization: The persisted database model instance updated with its system ID.
        """
        # Instantiate a clean database model mapping from the Pydantic input payload
        organization = Organization(
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            address=payload.address,
        )

        # Persist the object record buffer down into the database tracking system
        db_org = await self.organization_repo.create(db, organization)

        # PRODUCTION REQUIREMENT: Commit the structural transaction safely to the disk storage
        # so changes aren't auto-rolled back by the connection pool exit lifecycle.
        await db.commit()

        return db_org
