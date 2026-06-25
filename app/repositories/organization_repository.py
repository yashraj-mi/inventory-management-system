from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.organization import Organization


class OrganizationRepository:
    """Repository layer handling raw database persistence operations for corporate

    Organization entities.
    """

    async def create(
        self, db: AsyncSession, organization: Organization
    ) -> Organization:
        """Persists a new organization record instance inside the running database transaction.

        Args:
            db (AsyncSession): The active asynchronous database session bridge.
            organization (Organization): The un-persisted declarative model instance.

        Returns:
            Organization: The database-synchronized model instance populated with primary keys
                and server-side timestamps.
        """
        # Place the model instance into the session state tracking map
        db.add(organization)

        # Flush pending changes to the database buffer to trigger constraint checks and IDs
        await db.flush()

        # Reload the instance state from the database to populate server-generated default columns
        await db.refresh(organization)

        return organization
